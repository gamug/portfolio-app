import asyncio
from dataclasses import dataclass, field

import pytest

from app.connector.models import AnswerResult, ConnectorError, ConversionResult
from app.connector.service import KnowledgeGraphConnector
from app.connector.settings import Settings
from app.connector.storage import QuestionAnswerPair


@dataclass
class FakeChatAPI:
    events: list[str]
    error: ConnectorError | None = None

    async def check_startup(self) -> None:
        self.events.append("startup")

    async def answer(self, question: str) -> AnswerResult:
        self.events.append("answer")
        if self.error is not None:
            raise self.error
        return AnswerResult(text="raw answer", mode="chat", latency_seconds=1.0)


@dataclass
class FakeConverter:
    events: list[str]
    error: ConnectorError | None = None

    async def convert(self, answer: str) -> ConversionResult:
        self.events.append("convert")
        if self.error is not None:
            raise self.error
        return ConversionResult(text="root = Card([])", latency_seconds=0.1)


@dataclass
class FakeStore:
    events: list[str]
    pairs: list[QuestionAnswerPair] = field(default_factory=list)

    async def save(self, pair: QuestionAnswerPair) -> None:
        self.events.append("store")
        self.pairs.append(pair)

    async def list_for_session(self, session_id: str) -> list[QuestionAnswerPair]:
        return [pair for pair in self.pairs if pair.session_id == session_id]


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
        tool_max_iterations=4,
    )


def test_answer_and_store_runs_answer_then_conversion_then_store() -> None:
    events: list[str] = []
    store = FakeStore(events)
    connector = KnowledgeGraphConnector(
        _settings(),
        chat_api=FakeChatAPI(events),  # type: ignore[arg-type]
        tool_loop=object(),  # type: ignore[arg-type]
        converter=FakeConverter(events),  # type: ignore[arg-type]
        store=store,
    )
    result = asyncio.run(connector.answer_and_store("question", "session-1"))
    assert events == ["answer", "convert", "store"]
    assert result.raw.text == "raw answer"
    assert result.conversion.text == "root = Card([])"
    assert len(store.pairs) == 1
    assert store.pairs[0].session_id == "session-1"
    assert store.pairs[0].relevant is True


def test_conversion_failure_does_not_store() -> None:
    events: list[str] = []
    store = FakeStore(events)
    connector = KnowledgeGraphConnector(
        _settings(),
        chat_api=FakeChatAPI(events),  # type: ignore[arg-type]
        tool_loop=object(),  # type: ignore[arg-type]
        converter=FakeConverter(events, ConnectorError("conversion failed")),  # type: ignore[arg-type]
        store=store,
    )
    with pytest.raises(ConnectorError, match="conversion failed"):
        asyncio.run(connector.answer_and_store("question"))
    assert events == ["answer", "convert"]
    assert store.pairs == []


def test_answer_failure_does_not_convert_or_store() -> None:
    events: list[str] = []
    store = FakeStore(events)
    connector = KnowledgeGraphConnector(
        _settings(),
        chat_api=FakeChatAPI(events, ConnectorError("answer failed")),  # type: ignore[arg-type]
        tool_loop=object(),  # type: ignore[arg-type]
        converter=FakeConverter(events),  # type: ignore[arg-type]
        store=store,
    )
    with pytest.raises(ConnectorError, match="answer failed"):
        asyncio.run(connector.answer_and_store("question"))
    assert events == ["answer"]
    assert store.pairs == []
