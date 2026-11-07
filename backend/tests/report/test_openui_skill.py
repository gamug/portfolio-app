import asyncio
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from app.connector.settings import Settings
from app.report.chart_plan import DEFAULT_PROMPT_PATH as PLAN_PROMPT_PATH
from app.report.models import ChartPlan, ReportSkillError
from app.report.openui import (
    DEFAULT_PROMPT_PATH,
    DEFAULT_REFERENCE_PATH,
    DEFAULT_VALIDATOR_PATH,
    NodeOpenUIParser,
    OpenUIReportSkill,
)

PLAN = ChartPlan(
    title="Quarter",
    summary="Revenue rose.",
    charts=(),
    conclusions="The quarter improved.",
)


def _settings() -> Settings:
    return Settings(
        kg_host="http://graphdb:7200",
        kg_user="reader",
        kg_password="secret",
        kg_agent_id="agent-1",
        chat_mode="chat",
        llm_api_key="llm-secret",
        llm_model="deepseek-chat",
        llm_url="https://api.deepseek.com",
        chat_timeout_seconds=30,
    )


class FakeStream:
    def __init__(self, chunks: list[str], error: Exception | None = None) -> None:
        self.chunks = chunks
        self.error = error
        self.index = 0
        self.closed = False

    def __aiter__(self) -> "FakeStream":
        return self

    async def __anext__(self) -> Any:
        if self.index >= len(self.chunks):
            if self.error is not None:
                raise self.error
            raise StopAsyncIteration
        content = self.chunks[self.index]
        self.index += 1
        return SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content=content))],
            usage=None,
        )

    async def close(self) -> None:
        self.closed = True


class FakeCompletions:
    def __init__(self, chunks: list[str] | None = None, error: Exception | None = None) -> None:
        self.stream = FakeStream(chunks or [], error)
        self.calls = 0
        self.calls_args: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> FakeStream:
        self.calls += 1
        self.calls_args.append(kwargs)
        return self.stream


@dataclass
class FakeLLM:
    completions: FakeCompletions

    @property
    def chat(self) -> Any:
        return SimpleNamespace(completions=self.completions)


class FakeValidator:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.texts: list[str] = []

    async def validate(self, text: str) -> None:
        self.texts.append(text)
        if self.error is not None:
            raise self.error


def _skill(
    tmp_path: Path,
    completions: FakeCompletions,
    validator: FakeValidator | None = None,
) -> OpenUIReportSkill:
    prompt = tmp_path / "prompt.txt"
    reference = tmp_path / "reference.txt"
    prompt.write_text("REPORT PROMPT", encoding="utf-8")
    reference.write_text("COMPONENT REFERENCE BODY", encoding="utf-8")
    return OpenUIReportSkill(
        _settings(),
        llm=FakeLLM(completions),
        prompt_path=prompt,
        reference_path=reference,
        validator=validator or FakeValidator(),
    )


async def _collect(skill: OpenUIReportSkill) -> str:
    return "".join([chunk async for chunk in skill.stream(PLAN, "en")])


def test_prompt_files_are_drafts_and_exist() -> None:
    assert DEFAULT_PROMPT_PATH.is_file()
    assert DEFAULT_REFERENCE_PATH.is_file()
    assert PLAN_PROMPT_PATH.is_file()
    assert "DRAFT" in DEFAULT_PROMPT_PATH.read_text(encoding="utf-8")
    assert "DRAFT" in PLAN_PROMPT_PATH.read_text(encoding="utf-8")


def test_stream_uses_the_chat_prompt_as_reference(tmp_path: Path) -> None:
    completions = FakeCompletions(["root = Card([])"])
    skill = _skill(tmp_path, completions)
    text = asyncio.run(_collect(skill))
    assert text == "root = Card([])"
    assert completions.calls == 1
    args = completions.calls_args[0]
    system = str(args["messages"][0]["content"])
    assert "REPORT PROMPT" in system
    assert "COMPONENT REFERENCE BODY" in system
    assert args["stream"] is True
    payload = json.loads(args["messages"][1]["content"])
    assert payload["title"] == "Quarter"


def test_empty_stream_is_a_clear_error(tmp_path: Path) -> None:
    completions = FakeCompletions([])
    with pytest.raises(ReportSkillError, match="empty response"):
        asyncio.run(_collect(_skill(tmp_path, completions)))
    assert completions.calls == 1


def test_stream_failure_is_not_retried(tmp_path: Path) -> None:
    completions = FakeCompletions(["root = Card(["], error=RuntimeError("stream failed"))
    with pytest.raises(ReportSkillError, match="failed"):
        asyncio.run(_collect(_skill(tmp_path, completions)))
    assert completions.calls == 1


def test_missing_prompt_is_a_clear_error(tmp_path: Path) -> None:
    skill = OpenUIReportSkill(
        _settings(),
        llm=FakeLLM(FakeCompletions(["root = Card([])"])),
        prompt_path=tmp_path / "missing-prompt.txt",
        reference_path=tmp_path / "reference.txt",
        validator=FakeValidator(),
    )
    with pytest.raises(ReportSkillError, match="prompt is missing"):
        asyncio.run(_collect(skill))


def test_validate_delegates_to_the_parser(tmp_path: Path) -> None:
    validator = FakeValidator()
    skill = _skill(tmp_path, FakeCompletions([]), validator)
    asyncio.run(skill.validate("root = Card([])"))
    assert validator.texts == ["root = Card([])"]


def test_invalid_output_raises_one_clear_error(tmp_path: Path) -> None:
    validator = FakeValidator(ReportSkillError("The report is not valid OpenUI Lang."))
    skill = _skill(tmp_path, FakeCompletions([]), validator)
    with pytest.raises(ReportSkillError, match="not valid OpenUI Lang"):
        asyncio.run(skill.validate("root = Unknown([])"))


@pytest.mark.skipif(
    shutil.which("node") is None
    or not DEFAULT_VALIDATOR_PATH.is_file()
    or not (DEFAULT_VALIDATOR_PATH.parents[1] / "node_modules" / "@openuidev").is_dir(),
    reason="Node.js and the frontend dependencies are required for the parser check",
)
def test_node_parser_accepts_valid_openui_and_rejects_invalid() -> None:
    parser = NodeOpenUIParser()
    asyncio.run(
        parser.validate(
            "root = Card([title, chart])\n"
            'title = CardHeader("Synthetic", "Report")\n'
            'chart = BarChart(["A", "B"], [Series("S", [1, 2])])'
        )
    )
    with pytest.raises(ReportSkillError, match="not valid OpenUI Lang"):
        asyncio.run(parser.validate('root = Unknown([x])\nx = TextContent("Hi")'))
