import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

import app.api.reports as reports_api
from app.connector.settings import Settings
from app.main import create_app
from app.report.agent import ReportAgent
from app.report.models import ChartPlan, ReportSkillError
from app.storage import QuestionAnswerPair, SQLiteQuestionAnswerStore

PLAN = ChartPlan(
    title="Quarter",
    summary="Revenue rose.",
    charts=(),
    conclusions="The quarter improved.",
)


@dataclass
class FakeConnector:
    async def check_startup(self) -> None:
        return None


@dataclass
class FakePlanSkill:
    async def build(self, pairs: Any, language: str = "en") -> ChartPlan:
        return PLAN


@dataclass
class SlowPlanSkill(FakePlanSkill):
    delay: float = 0.1

    async def build(self, pairs: Any, language: str = "en") -> ChartPlan:
        await asyncio.sleep(self.delay)
        return PLAN


@dataclass
class FakeRenderSkill:
    chunks: list[str] = field(
        default_factory=lambda: [
            "root = Card([title])\n",
            'title = CardHeader("Quarter", "Report")',
        ]
    )
    validated: list[str] = field(default_factory=list)

    async def stream(self, plan: ChartPlan, language: str = "en") -> Any:
        for chunk in self.chunks:
            yield chunk

    async def validate(self, text: str) -> None:
        self.validated.append(text)


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
class FailingRenderSkill(FakeRenderSkill):
    async def stream(self, plan: ChartPlan, language: str = "en") -> Any:
        for chunk in self.chunks:
            yield chunk
        raise ReportSkillError("provider stopped")


def _agent(
    store: SQLiteQuestionAnswerStore,
    render: FakeRenderSkill | None = None,
    plan: FakePlanSkill | None = None,
) -> ReportAgent:
    return ReportAgent(
        _settings(),
        store,
        plan_skill=(plan or FakePlanSkill()),  # type: ignore[arg-type]
        render_skill=(render or FakeRenderSkill()),  # type: ignore[arg-type]
    )


def _pair(
    *,
    session_id: str = "s1",
    question: str = "How did revenue change?",
    relevant: bool = True,
) -> QuestionAnswerPair:
    return QuestionAnswerPair(
        session_id=session_id,
        question=question,
        raw_answer="Revenue was 100 and 120.",
        openui_lang="root = Card([])",
        relevant=relevant,
    )


def _sse(response: Any) -> list[tuple[str, Any]]:
    events: list[tuple[str, Any]] = []
    name = ""
    for line in response.iter_lines():
        if line.startswith("event: "):
            name = line[len("event: ") :]
        elif line.startswith("data: "):
            events.append((name, json.loads(line[len("data: ") :])))
    return events


def test_generation_streams_progress_deltas_and_done(tmp_path: Path) -> None:
    store = SQLiteQuestionAnswerStore(tmp_path / "app.sqlite3")
    asyncio.run(store.save(_pair()))
    app = create_app(  # type: ignore[arg-type]
        connector=FakeConnector(), store=store, report_agent=_agent(store)
    )
    with TestClient(app) as client:
        with client.stream(
            "POST", "/api/threads/s1/report/generate", json={"language": "en"}
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            events = _sse(response)
        report = asyncio.run(store.get_report("s1"))

    assert [name for name, _ in events[:2]] == ["progress", "progress"]
    assert events[0][1] == {"stage": "planning"}
    assert events[1][1] == {"stage": "rendering"}
    assert [name for name, _ in events[2:-1]] == ["delta", "delta"]
    assert events[-1][0] == "done"
    assert events[-1][1]["report"]["incomplete"] is False
    assert report is not None
    assert report.openui_lang == "".join(FakeRenderSkill().chunks)


def test_generation_streams_keep_alive_while_waiting_for_the_next_event(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setattr(reports_api, "REPORT_KEEP_ALIVE_SECONDS", 0.02)
    store = SQLiteQuestionAnswerStore(tmp_path / "app.sqlite3")
    asyncio.run(store.save(_pair()))
    app = create_app(
        connector=FakeConnector(),  # type: ignore[arg-type]
        store=store,
        report_agent=_agent(store, plan=SlowPlanSkill(delay=0.1)),
    )
    with TestClient(app) as client:
        with client.stream(
            "POST", "/api/threads/s1/report/generate", json={"language": "en"}
        ) as response:
            assert response.status_code == 200
            body = "".join(response.iter_text())

    assert ": keep-alive\n\n" in body
    assert body.index(": keep-alive") < body.index('"stage": "rendering"')
    assert "event: done" in body


def test_failure_streams_a_safe_error_and_stores_the_partial_report(tmp_path: Path) -> None:
    store = SQLiteQuestionAnswerStore(tmp_path / "app.sqlite3")
    asyncio.run(store.save(_pair()))
    app = create_app(  # type: ignore[arg-type]
        connector=FakeConnector(),
        store=store,
        report_agent=_agent(store, render=FailingRenderSkill()),
    )
    with TestClient(app) as client:
        with client.stream(
            "POST", "/api/threads/s1/report/generate", json={"language": "en"}
        ) as response:
            events = _sse(response)
        report = asyncio.run(store.get_report("s1"))

    assert events[-1][0] == "error"
    assert events[-1][1]["incomplete"] is True
    assert "partial report" in events[-1][1]["error"]
    assert report is not None
    assert report.incomplete is True
    assert report.openui_lang == "".join(FakeRenderSkill().chunks)


def test_no_history_is_rejected_before_streaming(tmp_path: Path) -> None:
    store = SQLiteQuestionAnswerStore(tmp_path / "app.sqlite3")
    session = asyncio.run(store.create_session("Empty"))
    app = create_app(  # type: ignore[arg-type]
        connector=FakeConnector(), store=store, report_agent=_agent(store)
    )
    with TestClient(app) as client:
        response = client.post(f"/api/threads/{session.id}/report/generate", json={})
    assert response.status_code == 400
    assert "no history" in response.json()["error"]
    assert "Start the data exploration" in response.json()["error"]


def test_no_relevant_pair_is_rejected_in_the_analyst_language(tmp_path: Path) -> None:
    store = SQLiteQuestionAnswerStore(tmp_path / "app.sqlite3")
    asyncio.run(store.save(_pair(question="¿Cómo evolucionó el ingreso?", relevant=False)))
    app = create_app(  # type: ignore[arg-type]
        connector=FakeConnector(), store=store, report_agent=_agent(store)
    )
    with TestClient(app) as client:
        response = client.post("/api/threads/s1/report/generate", json={})
    assert response.status_code == 400
    assert "relevante" in response.json()["error"]


def test_missing_session_is_a_404(tmp_path: Path) -> None:
    store = SQLiteQuestionAnswerStore(tmp_path / "app.sqlite3")
    app = create_app(  # type: ignore[arg-type]
        connector=FakeConnector(), store=store, report_agent=_agent(store)
    )
    with TestClient(app) as client:
        response = client.post("/api/threads/missing/report/generate", json={})
    assert response.status_code == 404
    assert response.json() == {"error": "The session was not found."}


def test_missing_report_agent_is_a_503(tmp_path: Path) -> None:
    store = SQLiteQuestionAnswerStore(tmp_path / "app.sqlite3")
    app = create_app(connector=FakeConnector(), store=store)  # type: ignore[arg-type]
    with TestClient(app) as client:
        response = client.post("/api/threads/s1/report/generate", json={})
    assert response.status_code == 503
    assert "not available" in response.json()["error"]
