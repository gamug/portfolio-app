"""Second DeepSeek call that converts a completed answer to OpenUI Lang."""

import time
from pathlib import Path
from typing import Any

from openai import APITimeoutError, AsyncOpenAI

from .models import ConnectorError, ConnectorTimeout, ConversionResult, total_tokens
from .settings import Settings

CONVERSION_TASK = """Convert the answer text into a short OpenUI Lang chat response
using the chat component library. Keep it to at most 6 statements. Do not invent facts
beyond the answer text. Return only OpenUI Lang, without markdown fences."""
DEFAULT_PROMPT_PATH = Path(__file__).with_name("openui_chat_prompt.txt")


class OpenUIConverter:
    """Convert the final answer with one additional DeepSeek call; no retries."""

    def __init__(
        self,
        settings: Settings,
        llm: Any = None,
        prompt_path: Path | None = None,
    ) -> None:
        self.settings = settings
        self.prompt_path = prompt_path or DEFAULT_PROMPT_PATH
        self.llm: Any = llm or AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_url,
            timeout=settings.chat_timeout_seconds,
            max_retries=0,
        )

    async def convert(self, answer: str) -> ConversionResult:
        started = time.monotonic()
        try:
            prompt = self.prompt_path.read_text(encoding="utf-8")
        except OSError as error:
            raise ConnectorError(
                "The OpenUI conversion prompt is missing.", status_code=502
            ) from error
        try:
            response = await self.llm.chat.completions.create(
                model=self.settings.llm_model,
                messages=[
                    {"role": "system", "content": f"{prompt}\n\n{CONVERSION_TASK}"},
                    {"role": "user", "content": answer},
                ],
                temperature=0,
                max_tokens=1500,
                timeout=self.settings.chat_timeout_seconds,
            )
        except APITimeoutError as error:
            raise ConnectorTimeout(
                f"The OpenUI conversion timed out after {self.settings.chat_timeout_seconds:g} s."
            ) from error
        except Exception as error:  # noqa: BLE001 - convert provider failures
            raise ConnectorError("The OpenUI conversion failed.", status_code=502) from error

        content = response.choices[0].message.content or ""
        converted = _strip_fences(content)
        if not converted:
            raise ConnectorError(
                "The OpenUI conversion returned an empty response.", status_code=502
            )
        usage = response.usage.model_dump() if response.usage else None
        return ConversionResult(
            text=converted,
            latency_seconds=round(time.monotonic() - started, 3),
            usage=usage,
            total_tokens=total_tokens(usage),
        )


def _strip_fences(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()
