import asyncio
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from app.connector.settings import Settings
from app.report.agent import ReportAgent
from app.report.models import (
    ChartPlan,
    ReportDelta,
    ReportDone,
    ReportError,
    ReportFailed,
    ReportProgress,
    ReportSkillError,
)
from app.report.openui import DEFAULT_VALIDATOR_PATH, NodeOpenUIParser
from app.storage import QuestionAnswerPair, SQLiteQuestionAnswerStore

PLAN = ChartPlan(
    title="Quarter",
    summary="Revenue rose.",
    charts=(),
    conclusions="The quarter improved.",
)
CHUNKS = [
    "root = Card([title, chart])\n",
    'title = CardHeader("Quarter", "Report")\n',
    'chart = TextContent("Revenue rose.")',
]
DISCLAIMER = (
    "Interpretación generada por un modelo de lenguaje el 3 de noviembre de 2026, a partir del "
    "informe disponible en la fecha D. Por su entrenamiento, el modelo pudo conocer hechos "
    "posteriores a D. No es un dato de la fecha D ni un hecho verificado."
)
PROVENANCE = "Provenance: /reports/2026/report.html"


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


@dataclass
class FakePlanSkill:
    plan: ChartPlan = PLAN
    error: Exception | None = None
    calls: int = 0
    languages: list[str] = field(default_factory=list)

    async def build(self, pairs: Any, language: str = "en") -> ChartPlan:
        self.calls += 1
        self.languages.append(language)
        if self.error is not None:
            raise self.error
        return self.plan


@dataclass
class FakeRenderSkill:
    chunks: list[str] = field(default_factory=lambda: list(CHUNKS))
    stream_error: Exception | None = None
    validate_error: Exception | None = None
    calls: int = 0
    validated: list[str] = field(default_factory=list)
    closed: bool = False
    languages: list[str] = field(default_factory=list)

    async def stream(self, plan: ChartPlan, language: str = "en") -> Any:
        self.calls += 1
        self.languages.append(language)
        try:
            for chunk in self.chunks:
                yield chunk
            if self.stream_error is not None:
                raise self.stream_error
        finally:
            self.closed = True

    async def validate(self, text: str) -> None:
        self.validated.append(text)
        if self.validate_error is not None:
            raise self.validate_error


def _pair(
    session_id: str = "s1",
    *,
    question: str = "How did revenue change?",
    answer: str = "Revenue was 100 in January and 120 in February.",
    relevant: bool = True,
) -> QuestionAnswerPair:
    return QuestionAnswerPair(
        session_id=session_id,
        question=question,
        raw_answer=answer,
        openui_lang="root = Card([])",
        relevant=relevant,
    )


def _store(tmp_path: Path) -> SQLiteQuestionAnswerStore:
    return SQLiteQuestionAnswerStore(tmp_path / "app.sqlite3")


def _agent(
    store: SQLiteQuestionAnswerStore,
    plan: FakePlanSkill | None = None,
    render: FakeRenderSkill | None = None,
) -> ReportAgent:
    return ReportAgent(
        _settings(),
        store,
        plan_skill=(plan or FakePlanSkill()),  # type: ignore[arg-type]
        render_skill=(render or FakeRenderSkill()),  # type: ignore[arg-type]
    )


def test_success_stores_the_complete_report_after_streaming(tmp_path: Path) -> None:
    store = _store(tmp_path)
    asyncio.run(store.save(_pair()))
    render = FakeRenderSkill()
    agent = _agent(store, render=render)

    async def scenario() -> tuple[list[Any], Any]:
        context = await agent.prepare("s1")
        events = [event async for event in agent.stream(context)]
        report = await store.get_report("s1")
        return events, report

    events, report = asyncio.run(scenario())
    assert isinstance(events[0], ReportProgress) and events[0].stage == "planning"
    assert isinstance(events[1], ReportProgress) and events[1].stage == "rendering"
    assert all(isinstance(event, ReportDelta) for event in events[2:-1])
    assert isinstance(events[-1], ReportDone)
    assert render.calls == 1
    assert render.validated == ["".join(CHUNKS)]
    assert report is not None
    assert report.openui_lang == "".join(CHUNKS)
    assert report.incomplete is False


def test_success_strips_markdown_fences_before_storing(tmp_path: Path) -> None:
    store = _store(tmp_path)
    asyncio.run(store.save(_pair()))
    render = FakeRenderSkill(chunks=["```openui\n", "root = Card([])\n", "```"])
    agent = _agent(store, render=render)

    async def scenario() -> Any:
        context = await agent.prepare("s1")
        [event async for event in agent.stream(context)]
        return await store.get_report("s1")

    report = asyncio.run(scenario())
    assert render.validated == ["root = Card([])"]
    assert report is not None
    assert report.openui_lang == "root = Card([])"


def test_stream_injects_missing_disclaimers_before_validation_and_storage(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    asyncio.run(store.save(_pair()))
    plan = ChartPlan(
        title="Quarter",
        summary="Revenue rose.",
        charts=(),
        conclusions="The quarter improved.",
        disclaimers=(DISCLAIMER, PROVENANCE),
    )
    render = FakeRenderSkill(chunks=["root = Card([title])\n", 'title = TextContent("Quarter")'])
    agent = _agent(store, plan=FakePlanSkill(plan=plan), render=render)

    async def scenario() -> Any:
        context = await agent.prepare("s1")
        [event async for event in agent.stream(context)]
        return await store.get_report("s1")

    report = asyncio.run(scenario())
    assert report is not None
    assert DISCLAIMER in report.openui_lang
    assert PROVENANCE in report.openui_lang
    assert "mandatoryNote1" in report.openui_lang
    assert render.validated == [report.openui_lang]

    dependencies = DEFAULT_VALIDATOR_PATH.parents[1] / "node_modules" / "@openuidev" / "react-lang"
    if shutil.which("node") is not None and dependencies.is_dir():
        asyncio.run(NodeOpenUIParser().validate(report.openui_lang))


def test_regenerate_replaces_the_previous_report(tmp_path: Path) -> None:
    store = _store(tmp_path)
    asyncio.run(store.save(_pair()))
    asyncio.run(store.set_report("s1", "root = Card([])", incomplete=False))
    agent = _agent(store, render=FakeRenderSkill(chunks=["root = Card([title])"]))

    async def scenario() -> Any:
        context = await agent.prepare("s1")
        [event async for event in agent.stream(context)]
        return await store.get_report("s1")

    report = asyncio.run(scenario())
    assert report is not None
    assert report.openui_lang == "root = Card([title])"
    assert report.incomplete is False


def test_cancel_keeps_the_previous_report_and_does_not_store(tmp_path: Path) -> None:
    store = _store(tmp_path)
    asyncio.run(store.save(_pair()))
    asyncio.run(store.set_report("s1", "previous report", incomplete=False))
    render = FakeRenderSkill()
    agent = _agent(store, render=render)

    async def scenario() -> None:
        context = await agent.prepare("s1")
        stream = agent.stream(context)
        assert isinstance(await anext(stream), ReportProgress)
        assert isinstance(await anext(stream), ReportProgress)
        assert isinstance(await anext(stream), ReportDelta)
        await stream.aclose()
        report = await store.get_report("s1")
        assert report is not None
        assert report.openui_lang == "previous report"
        assert report.incomplete is False

    asyncio.run(scenario())
    assert render.closed is True


def test_failure_stores_the_partial_report_flagged_incomplete(tmp_path: Path) -> None:
    store = _store(tmp_path)
    asyncio.run(store.save(_pair()))
    asyncio.run(store.set_report("s1", "previous report", incomplete=False))
    render = FakeRenderSkill(
        chunks=["root = Card([title])\n", 'title = TextContent("Partial")'],
        stream_error=ReportSkillError("provider stopped"),
    )
    agent = _agent(store, render=render)

    async def scenario() -> Any:
        context = await agent.prepare("s1")
        events = [event async for event in agent.stream(context)]
        report = await store.get_report("s1")
        return events, report

    events, report = asyncio.run(scenario())
    assert isinstance(events[-1], ReportFailed)
    assert events[-1].incomplete is True
    assert "partial report" in events[-1].error
    assert report is not None
    assert report.openui_lang == 'root = Card([title])\ntitle = TextContent("Partial")'
    assert report.incomplete is True


def test_failure_logs_the_exception_type(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    store = _store(tmp_path)
    asyncio.run(store.save(_pair()))
    render = FakeRenderSkill(
        chunks=["root = Card([title])"],
        stream_error=ReportSkillError("provider stopped"),
    )
    agent = _agent(store, render=render)

    async def scenario() -> None:
        context = await agent.prepare("s1")
        [event async for event in agent.stream(context)]

    with caplog.at_level(logging.ERROR):
        asyncio.run(scenario())

    assert "ReportSkillError" in caplog.text
    assert "provider stopped" in caplog.text


def test_failure_log_redacts_the_api_key_and_truncates(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    store = _store(tmp_path)
    asyncio.run(store.save(_pair()))
    render = FakeRenderSkill(
        chunks=["root = Card([title])"],
        stream_error=ReportSkillError(f"provider llm-secret {'x' * 400}"),
    )
    agent = _agent(store, render=render)

    async def scenario() -> None:
        context = await agent.prepare("s1")
        [event async for event in agent.stream(context)]

    with caplog.at_level(logging.ERROR):
        asyncio.run(scenario())

    assert "llm-secret" not in caplog.text
    assert "<redacted>" in caplog.text
    assert "x" * 280 in caplog.text
    assert "x" * 281 not in caplog.text


def test_invalid_openui_output_keeps_the_partial_report_in_spanish(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    asyncio.run(store.save(_pair(question="¿Cómo evolucionó el ingreso?", answer="100 y 120.")))
    render = FakeRenderSkill(
        chunks=["root = Unknown([])"],
        validate_error=ReportSkillError("The report is not valid OpenUI Lang."),
    )
    agent = _agent(store, render=render)

    async def scenario() -> Any:
        context = await agent.prepare("s1")
        events = [event async for event in agent.stream(context)]
        report = await store.get_report("s1")
        return context, events, report

    context, events, report = asyncio.run(scenario())
    assert context.language == "es"
    assert isinstance(events[-1], ReportFailed)
    assert events[-1].incomplete is True
    assert "informe parcial" in events[-1].error
    assert report is not None
    assert report.openui_lang == "root = Unknown([])"
    assert report.incomplete is True


def test_skill_failure_before_output_keeps_the_previous_report(tmp_path: Path) -> None:
    store = _store(tmp_path)
    asyncio.run(store.save(_pair()))
    asyncio.run(store.set_report("s1", "previous report", incomplete=False))
    agent = _agent(store, plan=FakePlanSkill(error=ReportSkillError("plan failed")))

    async def scenario() -> Any:
        context = await agent.prepare("s1")
        events = [event async for event in agent.stream(context)]
        report = await store.get_report("s1")
        return events, report

    events, report = asyncio.run(scenario())
    assert isinstance(events[-1], ReportFailed)
    assert events[-1].incomplete is False
    assert report is not None
    assert report.openui_lang == "previous report"


def test_no_history_is_rejected_with_a_clear_message(tmp_path: Path) -> None:
    store = _store(tmp_path)
    session = asyncio.run(store.create_session("Empty"))
    agent = _agent(store)

    with pytest.raises(ReportError) as raised:
        asyncio.run(agent.prepare(session.id))
    assert raised.value.kind == "no_history"
    assert raised.value.status_code == 400


def test_no_relevant_pair_is_rejected_with_a_clear_message(tmp_path: Path) -> None:
    store = _store(tmp_path)
    asyncio.run(store.save(_pair(relevant=False)))
    agent = _agent(store)

    with pytest.raises(ReportError) as raised:
        asyncio.run(agent.prepare("s1"))
    assert raised.value.kind == "no_relevant"
    assert raised.value.status_code == 400


def test_missing_session_is_a_not_found(tmp_path: Path) -> None:
    agent = _agent(_store(tmp_path))
    with pytest.raises(ReportError) as raised:
        asyncio.run(agent.prepare("missing"))
    assert raised.value.kind == "not_found"
    assert raised.value.status_code == 404


def test_requested_language_overrides_detection(tmp_path: Path) -> None:
    store = _store(tmp_path)
    asyncio.run(store.save(_pair(question="¿Cómo evolucionó el ingreso?")))
    agent = _agent(store)

    context = asyncio.run(agent.prepare("s1", "en"))
    assert context.language == "en"
    assert len(context.pairs) == 1
