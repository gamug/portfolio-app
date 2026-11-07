from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app.connector.models import AnswerResult, ConnectorError, ConnectorTimeout
from app.main import create_app


@dataclass
class FakeConnector:
    result: AnswerResult | None = None
    error: ConnectorError | None = None
    checked: bool = False

    async def check_startup(self) -> None:
        self.checked = True

    async def answer(self, question: str) -> AnswerResult:
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


def test_chat_endpoint_streams_the_answer() -> None:
    connector = FakeConnector(
        result=AnswerResult(
            text="streamed answer", mode="chat", latency_seconds=1.0, total_tokens=10
        )
    )
    app = create_app(connector)  # type: ignore[arg-type]
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"question": "question"})
    assert connector.checked is True
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
    connector = FakeConnector(result=AnswerResult(text="unused", mode="chat", latency_seconds=0))
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
