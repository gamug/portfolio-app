"""Bounded adr-007 DeepSeek tool loop, selectable as the fallback mode."""

import asyncio
import json
import time
from typing import Any

import yaml  # type: ignore[import-untyped]
from openai import APITimeoutError, AsyncOpenAI

from .http import GraphDBHttp, GraphDBTimeout, GraphDBUnavailable
from .models import AnswerResult, ConnectorError, ConnectorTimeout, total_tokens
from .settings import Settings

TOOL_LIST_PATH = "/rest/llm/tool/ttyg/{agent_id}"
MAX_MODEL_TOOL_CHARS = 20_000
SYSTEM_PROMPT = """You answer questions about a knowledge graph stored in GraphDB.

Use the provided tools before answering factual questions. Never invent values, names,
dates or causes. For sparql_query, send a complete SPARQL SELECT, CONSTRUCT or DESCRIBE
query in the query field.

Never run an unfiltered full scan over ?s ?p ?o. Do not use text filters such as
FILTER(CONTAINS(STR(?s), ...)) or FILTER(REGEX(STR(?s), ...)) over ?s ?p ?o. Start from a
specific named graph, class or predicate, add selective filters, and always use a small
LIMIT (for example 50) for lists. Use COUNT, SUM or other aggregations for totals.

If the graph does not contain the requested data, say so explicitly. Answer in the
language of the question and keep the final answer concise."""


class ToolLoop:
    """Run DeepSeek over GraphDB's LLM tools with a hard iteration bound."""

    def __init__(
        self,
        settings: Settings,
        http: GraphDBHttp | None = None,
        llm: Any = None,
    ) -> None:
        self.settings = settings
        self.http = http or GraphDBHttp(
            settings.kg_base_url, settings.kg_user, settings.kg_password
        )
        self.llm: Any = llm or AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_url,
            timeout=settings.chat_timeout_seconds,
            max_retries=0,
        )

    async def check_startup(self) -> None:
        await asyncio.to_thread(self._load_tools)

    async def answer(self, question: str) -> AnswerResult:
        started = time.monotonic()
        deadline = started + self.settings.chat_timeout_seconds
        tools, tool_paths = await asyncio.to_thread(self._load_tools)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]

        for _ in range(self.settings.tool_max_iterations):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ConnectorTimeout(
                    f"The tool loop timed out after {self.settings.chat_timeout_seconds:g} s."
                )
            try:
                response = await self.llm.chat.completions.create(
                    model=self.settings.llm_model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0,
                    max_tokens=1500,
                    timeout=remaining,
                )
            except APITimeoutError as error:
                raise ConnectorTimeout(
                    f"The tool loop timed out after {self.settings.chat_timeout_seconds:g} s."
                ) from error
            except Exception as error:  # noqa: BLE001 - convert provider failures
                raise ConnectorError("The DeepSeek tool loop failed.", status_code=502) from error

            choice = response.choices[0]
            message = choice.message
            content = message.content or ""
            tool_calls = list(message.tool_calls or [])
            if not tool_calls:
                answer = content.strip()
                if not answer:
                    raise ConnectorError(
                        "The DeepSeek tool loop returned an empty answer.", status_code=502
                    )
                usage = response.usage.model_dump() if response.usage else None
                return AnswerResult(
                    text=answer,
                    mode="tool_loop",
                    latency_seconds=round(time.monotonic() - started, 3),
                    usage=usage,
                    total_tokens=total_tokens(usage),
                )

            messages.append(
                {
                    "role": "assistant",
                    "content": content or None,
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments,
                            },
                        }
                        for call in tool_calls
                    ],
                }
            )
            for call in tool_calls:
                tool_message = await self._run_tool(call, tool_paths, deadline)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": tool_message,
                    }
                )

        raise ConnectorError(
            "The DeepSeek tool loop did not finish within "
            f"{self.settings.tool_max_iterations} iterations.",
            status_code=502,
        )

    async def _run_tool(self, call: Any, tool_paths: dict[str, str], deadline: float) -> str:
        name = call.function.name
        try:
            arguments = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError:
            return json.dumps({"error": "invalid tool arguments"})
        if not isinstance(arguments, dict):
            return json.dumps({"error": "invalid tool arguments"})
        path = tool_paths.get(name)
        if path is None:
            return json.dumps({"error": "unknown tool"})
        try:
            response = await asyncio.to_thread(
                self.http.request,
                "POST",
                f"{TOOL_LIST_PATH.format(agent_id=self.settings.kg_agent_id)}/{name}",
                payload=arguments,
                deadline=deadline,
                accept="application/json, text/plain;q=0.9, */*;q=0.8",
            )
        except GraphDBTimeout as error:
            raise ConnectorTimeout(
                f"The GraphDB tool {name} timed out after {self.settings.chat_timeout_seconds:g} s."
            ) from error
        except GraphDBUnavailable as error:
            raise ConnectorError("GraphDB is unreachable.", status_code=502) from error
        if response.status != 200:
            return json.dumps({"error": f"tool returned HTTP {response.status}"})
        return response.body[:MAX_MODEL_TOOL_CHARS]

    def _load_tools(self) -> tuple[list[dict[str, Any]], dict[str, str]]:
        deadline = time.monotonic() + min(self.settings.chat_timeout_seconds, 30.0)
        try:
            response = self.http.request(
                "GET",
                TOOL_LIST_PATH.format(agent_id=self.settings.kg_agent_id),
                deadline=deadline,
                accept="application/yaml",
            )
        except GraphDBTimeout as error:
            raise ConnectorTimeout("The GraphDB tool list timed out.") from error
        except GraphDBUnavailable as error:
            raise ConnectorError("GraphDB is unreachable.", status_code=502) from error
        if response.status != 200:
            raise ConnectorError(
                f"The GraphDB tool list returned HTTP {response.status}.", status_code=502
            )
        document = yaml.safe_load(response.body)
        if not isinstance(document, dict):
            raise ConnectorError("The GraphDB tool list is invalid.", status_code=502)
        paths = document.get("paths")
        if not isinstance(paths, dict) or not paths:
            raise ConnectorError("The GraphDB tool list has no tools.", status_code=502)

        tools: list[dict[str, Any]] = []
        tool_paths: dict[str, str] = {}
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            operation = methods.get("post")
            if not isinstance(operation, dict):
                continue
            name = str(operation.get("operationId") or str(path).strip("/"))
            parameters: Any = {"type": "object", "properties": {}}
            request_body = operation.get("requestBody")
            if isinstance(request_body, dict):
                content = request_body.get("content")
                if isinstance(content, dict):
                    media = content.get("application/json")
                    if isinstance(media, dict) and isinstance(media.get("schema"), dict):
                        parameters = media["schema"]
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": str(operation.get("description") or f"Call {name}"),
                        "parameters": parameters,
                    },
                }
            )
            tool_paths[name] = str(path)
        if not tools:
            raise ConnectorError("The GraphDB tool list has no POST tools.", status_code=502)
        return tools, tool_paths
