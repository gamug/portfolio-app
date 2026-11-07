import asyncio
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from app.connector.http import HttpResponse
from app.connector.models import ConnectorError
from app.connector.settings import Settings
from app.connector.tool_loop import TOOL_LIST_PATH, ToolLoop

TOOL_YAML = """\
openapi: "3.1.0"
info:
  title: "Tools"
paths:
  /now:
    post:
      operationId: "now"
      description: "Current time"
      requestBody:
        content:
          application/json:
            schema:
              type: "object"
              properties: {}
  /sparql_query:
    post:
      operationId: "sparql_query"
      description: "Run SPARQL"
      requestBody:
        content:
          application/json:
            schema:
              type: "object"
              properties:
                query:
                  type: "string"
              required:
                - "query"
"""


@dataclass
class FakeHttp:
    calls: list[tuple[str, str]]

    def __init__(self) -> None:
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
        self.calls.append((method, path))
        if method == "GET" and path == TOOL_LIST_PATH.format(agent_id="agent-1"):
            return HttpResponse(200, TOOL_YAML)
        if method == "POST" and path.endswith("/sparql_query"):
            return HttpResponse(200, '{"rows": []}')
        return HttpResponse(404, "")


class FakeCompletions:
    def __init__(self, responses: list[Any] | None = None, error: Exception | None = None):
        self.responses = responses or []
        self.error = error
        self.calls = 0

    async def create(self, **kwargs: Any) -> Any:
        self.calls += 1
        if self.error is not None:
            raise self.error
        if not self.responses:
            raise RuntimeError("no fake response")
        return self.responses.pop(0)


@dataclass
class FakeLLM:
    completions: FakeCompletions

    @property
    def chat(self) -> Any:
        return SimpleNamespace(completions=self.completions)


def _settings(max_iterations: int = 4) -> Settings:
    return Settings(
        kg_host="http://graphdb:7200",
        kg_user="reader",
        kg_password="secret",
        kg_agent_id="agent-1",
        chat_mode="tool_loop",
        llm_api_key="llm-secret",
        llm_model="deepseek-chat",
        llm_url="https://api.deepseek.com",
        chat_timeout_seconds=30,
        tool_max_iterations=max_iterations,
    )


def _tool_call() -> Any:
    return SimpleNamespace(
        id="call-1",
        function=SimpleNamespace(
            name="sparql_query",
            arguments='{"query": "SELECT * WHERE { ?s ?p ?o } LIMIT 1"}',
        ),
    )


def _response(content: str | None = None, tool_calls: list[Any] | None = None) -> Any:
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    choice = SimpleNamespace(message=message, finish_reason="tool_calls" if tool_calls else "stop")
    usage = SimpleNamespace(model_dump=lambda: {"totalTokens": 12})
    return SimpleNamespace(choices=[choice], usage=usage)


def test_tool_loop_returns_final_answer() -> None:
    http = FakeHttp()
    llm = FakeLLM(
        FakeCompletions([_response(tool_calls=[_tool_call()]), _response("Final answer")])
    )
    result = asyncio.run(ToolLoop(_settings(), http=http, llm=llm).answer("question"))
    assert result.text == "Final answer"
    assert result.mode == "tool_loop"
    assert result.total_tokens == 12
    assert any(method == "POST" for method, _ in http.calls)


def test_tool_loop_stops_at_iteration_limit() -> None:
    http = FakeHttp()
    completions = FakeCompletions(
        [_response(tool_calls=[_tool_call()]), _response(tool_calls=[_tool_call()])]
    )
    llm = FakeLLM(completions)
    with pytest.raises(ConnectorError, match="did not finish"):
        asyncio.run(ToolLoop(_settings(max_iterations=2), http=http, llm=llm).answer("question"))
    assert completions.calls == 2


def test_tool_loop_does_not_retry_llm_errors() -> None:
    http = FakeHttp()
    completions = FakeCompletions(error=RuntimeError("provider failed"))
    llm = FakeLLM(completions)
    with pytest.raises(ConnectorError, match="tool loop failed"):
        asyncio.run(ToolLoop(_settings(), http=http, llm=llm).answer("question"))
    assert completions.calls == 1


def test_startup_loads_tool_list() -> None:
    http = FakeHttp()
    asyncio.run(ToolLoop(_settings(), http=http, llm=FakeLLM(FakeCompletions())).check_startup())
    assert http.calls == [("GET", TOOL_LIST_PATH.format(agent_id="agent-1"))]
