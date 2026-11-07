import asyncio
from dataclasses import dataclass
from typing import Any

import pytest

from app.connector.chat_api import ASK_PATH, CREATE_CHAT_PATH, ChatAPIClient
from app.connector.http import GraphDBTimeout, HttpResponse
from app.connector.models import ConnectorError, ConnectorTimeout
from app.connector.settings import Settings


@dataclass
class FakeHttp:
    responses: dict[tuple[str, str], HttpResponse]
    calls: list[tuple[str, str, dict[str, Any] | None]]

    def __init__(self, responses: dict[tuple[str, str], HttpResponse]) -> None:
        self.responses = responses
        self.calls = []

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        deadline: float | None = None,
        accept: str = "application/json",
    ) -> HttpResponse:
        self.calls.append((method, path, payload))
        return self.responses[(method, path)]

    def options(self, path: str, deadline: float | None = None) -> HttpResponse:
        self.calls.append(("OPTIONS", path, None))
        return self.responses[("OPTIONS", path)]


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


def _responses() -> dict[tuple[str, str], HttpResponse]:
    return {
        ("POST", CREATE_CHAT_PATH): HttpResponse(200, '{"conversationId": "c1"}'),
        ("POST", ASK_PATH): HttpResponse(
            200,
            '{"messages": [{"message": "Synthetic answer"}], "usage": {"totalTokens": 42}}',
        ),
    }


def test_answer_uses_chat_api_without_retry() -> None:
    http = FakeHttp(_responses())
    result = asyncio.run(ChatAPIClient(_settings(), http=http).answer("question"))
    assert result.text == "Synthetic answer"
    assert result.total_tokens == 42
    assert result.conversation_id == "c1"
    assert result.mode == "chat"
    assert len(http.calls) == 2
    assert "Answer in English" in str(http.calls[0][2]["question"])
    assert "Answer in English" in str(http.calls[1][2]["question"])


def test_spanish_question_sends_spanish_instruction() -> None:
    http = FakeHttp(_responses())
    asyncio.run(ChatAPIClient(_settings(), http=http).answer("question", "es"))
    assert "Responde en español" in str(http.calls[0][2]["question"])


def test_http_error_is_not_retried() -> None:
    http = FakeHttp({("POST", CREATE_CHAT_PATH): HttpResponse(502, "upstream error")})
    with pytest.raises(ConnectorError, match="HTTP 502"):
        asyncio.run(ChatAPIClient(_settings(), http=http).answer("question"))
    assert len(http.calls) == 1


def test_timeout_is_reported() -> None:
    class TimeoutHttp(FakeHttp):
        def request(self, *args: Any, **kwargs: Any) -> HttpResponse:
            raise GraphDBTimeout("timed out")

    http = TimeoutHttp({})
    with pytest.raises(ConnectorTimeout):
        asyncio.run(ChatAPIClient(_settings(), http=http).answer("question"))
    assert len(http.calls) == 0


def test_startup_checks_both_endpoints() -> None:
    http = FakeHttp(
        {
            ("OPTIONS", CREATE_CHAT_PATH): HttpResponse(200, ""),
            ("OPTIONS", ASK_PATH): HttpResponse(200, ""),
        }
    )
    asyncio.run(ChatAPIClient(_settings(), http=http).check_startup())
    assert [call[1] for call in http.calls] == [CREATE_CHAT_PATH, ASK_PATH]


def test_startup_rejects_bad_auth() -> None:
    http = FakeHttp(
        {
            ("OPTIONS", CREATE_CHAT_PATH): HttpResponse(401, ""),
            ("OPTIONS", ASK_PATH): HttpResponse(200, ""),
        }
    )
    with pytest.raises(ConnectorError, match="read-only user"):
        asyncio.run(ChatAPIClient(_settings(), http=http).check_startup())
