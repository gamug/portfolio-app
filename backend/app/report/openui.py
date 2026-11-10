"""Skill 2 and validation: turn a chart plan into renderable OpenUI Lang."""

import asyncio
import inspect
import json
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Protocol

from openai import APITimeoutError, AsyncOpenAI

from app.connector.language import Language
from app.connector.models import total_tokens
from app.connector.settings import Settings

from .language import render_language_instruction
from .models import ChartPlan, ReportSkillError

DEFAULT_PROMPT_PATH = Path(__file__).with_name("prompts") / "report_skill_2_openui_prompt.txt"
DEFAULT_REFERENCE_PATH = (
    Path(__file__).resolve().parents[1] / "connector" / "openui_chat_prompt.txt"
)
DEFAULT_VALIDATOR_PATH = (
    Path(__file__).resolve().parents[3] / "frontend" / "scripts" / "validate-openui-report.mjs"
)
DEFAULT_MAX_TOKENS = 4000
VALIDATOR_TIMEOUT_SECONDS = 60.0


def strip_code_fences(text: str) -> str:
    """Remove one surrounding markdown fence from a completed OpenUI response."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def plan_payload(plan: ChartPlan) -> dict[str, Any]:
    """Serialize the validated plan for the skill 2 user message."""
    charts: list[dict[str, Any]] = []
    for chart in plan.charts:
        item: dict[str, Any] = {
            "type": chart.type,
            "title": chart.title,
            "takeaway": chart.takeaway,
        }
        if chart.x_label:
            item["x_label"] = chart.x_label
        if chart.y_label:
            item["y_label"] = chart.y_label
        if chart.labels:
            item["labels"] = list(chart.labels)
        if chart.series:
            item["series"] = [
                {"category": series.category, "values": list(series.values)}
                for series in chart.series
            ]
        if chart.values:
            item["values"] = list(chart.values)
        if chart.columns:
            item["columns"] = [
                {"label": column.label, "values": list(column.values)} for column in chart.columns
            ]
        charts.append(item)
    return {
        "title": plan.title,
        "summary": plan.summary,
        "charts": charts,
        "conclusions": plan.conclusions,
    }


class OpenUIParser(Protocol):
    async def validate(self, text: str) -> None: ...


class NodeOpenUIParser:
    """Validate with the same @openuidev/react-lang parser the TASK-019 spike used."""

    def __init__(
        self,
        node: str = "node",
        script_path: Path | None = None,
        timeout: float = VALIDATOR_TIMEOUT_SECONDS,
    ) -> None:
        self.node = node
        self.script_path = script_path or DEFAULT_VALIDATOR_PATH
        self.timeout = timeout

    async def validate(self, text: str) -> None:
        if not self.script_path.is_file():
            raise ReportSkillError("The OpenUI validator script is missing.")
        try:
            process = await asyncio.create_subprocess_exec(
                self.node,
                str(self.script_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as error:
            raise ReportSkillError(
                "The OpenUI validator could not run. Is Node.js installed?"
            ) from error
        try:
            stdout, _stderr = await asyncio.wait_for(
                process.communicate(text.encode("utf-8")), timeout=self.timeout
            )
        except TimeoutError as error:
            process.kill()
            await process.wait()
            raise ReportSkillError("The OpenUI validator timed out.") from error
        try:
            result = json.loads(stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ReportSkillError("The OpenUI validator returned an invalid response.") from error
        if (
            process.returncode != 0
            or not isinstance(result, dict)
            or not result.get("parsed")
            or not result.get("root_present")
            or result.get("errors") != 0
            or result.get("unresolved")
            or result.get("orphaned")
            or result.get("incomplete", True)
        ):
            raise ReportSkillError("The report is not valid OpenUI Lang.")


class OpenUIReportSkill:
    """Run skill 2 as one streamed DeepSeek call and validate the complete text."""

    def __init__(
        self,
        settings: Settings,
        llm: Any = None,
        prompt_path: Path | None = None,
        reference_path: Path | None = None,
        validator: OpenUIParser | None = None,
    ) -> None:
        self.settings = settings
        self.prompt_path = prompt_path or DEFAULT_PROMPT_PATH
        self.reference_path = reference_path or DEFAULT_REFERENCE_PATH
        self.validator: OpenUIParser = validator or NodeOpenUIParser()
        self.llm: Any = llm or AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_url,
            timeout=settings.chat_timeout_seconds,
            max_retries=0,
        )
        self.last_usage: dict[str, Any] | None = None
        self.last_total_tokens: int | None = None
        self.last_latency_seconds: float | None = None
        self.last_error: str | None = None

    def _system_prompt(self, language: Language) -> str:
        try:
            prompt = self.prompt_path.read_text(encoding="utf-8")
            reference = self.reference_path.read_text(encoding="utf-8")
        except OSError as error:
            raise ReportSkillError("The OpenUI report prompt is missing.") from error
        return (
            f"{prompt}\n\n{render_language_instruction(language)}\n\n"
            f"=== COMPONENT REFERENCE (openui_chat_prompt.txt) ===\n{reference}"
        )

    async def stream(self, plan: ChartPlan, language: Language = "en") -> AsyncIterator[str]:
        payload = json.dumps(plan_payload(plan), ensure_ascii=False)
        system_prompt = self._system_prompt(language)
        self.last_usage = None
        self.last_total_tokens = None
        self.last_latency_seconds = None
        self.last_error = None
        started = time.monotonic()
        try:
            response = await self.llm.chat.completions.create(
                model=self.settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": payload},
                ],
                temperature=0,
                max_tokens=DEFAULT_MAX_TOKENS,
                timeout=self.settings.chat_timeout_seconds,
                stream=True,
                stream_options={"include_usage": True},
            )
        except APITimeoutError as error:
            self.last_error = "timeout"
            raise ReportSkillError("The OpenUI report skill timed out.") from error
        except Exception as error:  # noqa: BLE001 - one clear skill failure, no retry
            self.last_error = type(error).__name__
            raise ReportSkillError("The OpenUI report skill failed.") from error

        yielded = False
        try:
            async for chunk in response:
                usage = getattr(chunk, "usage", None)
                if usage is not None:
                    self.last_usage = usage.model_dump() if hasattr(usage, "model_dump") else None
                    self.last_total_tokens = total_tokens(self.last_usage)
                choices = getattr(chunk, "choices", None) or []
                if not choices:
                    continue
                delta = getattr(choices[0], "delta", None)
                content = getattr(delta, "content", None)
                if isinstance(content, str) and content:
                    yielded = True
                    yield content
        except asyncio.CancelledError:
            raise
        except Exception as error:  # noqa: BLE001 - surface one skill failure
            self.last_error = type(error).__name__
            raise ReportSkillError("The OpenUI report skill failed.") from error
        finally:
            self.last_latency_seconds = round(time.monotonic() - started, 3)
            close = getattr(response, "close", None)
            if callable(close):
                try:
                    closed = close()
                    if inspect.isawaitable(closed):
                        await closed
                except Exception:  # noqa: BLE001 - closing must not mask the real error
                    pass
        if not yielded:
            self.last_error = "empty"
            raise ReportSkillError("The OpenUI report skill returned an empty response.")

    async def validate(self, text: str) -> None:
        await self.validator.validate(text)
