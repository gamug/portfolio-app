from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app.connector.models import (
    AnswerResult,
    ChatAnswer,
    ConnectorError,
    ConnectorTimeout,
    ConversionResult,
)
from app.main import create_app


@dataclass
class FakeConnector:
    result: ChatAnswer | None = None
    error: ConnectorError | None = None
    checked: bool = False
    session_id: str | None = None

    async def check_startup(self) -> None:
        self.checked = True

    async def answer_and_store(self, question: str, session_id: str) -> ChatAnswer:
        if self.error is not None:
            raise self.error
        self.session_id = session_id
        assert self.result is not None
        return self.result


def test_chat_endpoint_streams_the_answer() -> None:
    connector = FakeConnector(
        result=ChatAnswer(
            raw=AnswerResult(
                text="streamed answer", mode="chat", latency_seconds=1.0, total_tokens=10
            ),
            conversion=ConversionResult(
                text="root = Card([])", latency_seconds=0.1, total_tokens=5
            ),
        )
    )
    app = create_app(connector)  # type: ignore[arg-type]
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"question": "question", "session_id": "s1"})
    assert connector.checked is True
    assert connector.session_id == "s1"
    assert response.status_code == 200
    assert response.text == "streamed answer"
    assert response.headers["content-type"].startswith("text/plain")


def test_chat_endpoint_returns_a_clear_timeout() -> None:
    connector = FakeConnector(error=ConnectorTimeout("timed out"))
    app = create_app(connector)  # type: ignore[arg-type]
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"question": "question"})
    assert response.status_code == 504
    assert response.json() == {"error": "timed out"}


def test_chat_endpoint_rejects_an_empty_question() -> None:
    connector = FakeConnector(
        result=ChatAnswer(
            raw=AnswerResult(text="unused", mode="chat", latency_seconds=0),
            conversion=ConversionResult(text="root = Card([])", latency_seconds=0),
        )
    )
    app = create_app(connector)  # type: ignore[arg-type]
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"question": ""})
    assert response.status_code == 422


def test_startup_error_prevents_the_app_from_starting() -> None:
    class BrokenConnector(FakeConnector):
        async def check_startup(self) -> None:
            raise ConnectorError("startup failed", status_code=502)

    app = create_app(BrokenConnector())  # type: ignore[arg-type]
    with pytest.raises(ConnectorError, match="startup failed"):
        with TestClient(app):
            pass
