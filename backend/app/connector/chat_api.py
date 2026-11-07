"""Client for the accepted adr-010 Workbench chat API path."""

import asyncio
import json
import time
from typing import Any

from .http import GraphDBHttp, GraphDBTimeout, GraphDBUnavailable
from .models import AnswerResult, ConnectorError, ConnectorTimeout, total_tokens
from .settings import Settings

CREATE_CHAT_PATH = "/rest/chat/chats"
ASK_PATH = "/rest/chat/chats/question"
TZ_OFFSET = -300


class ChatAPIClient:
    """Create a conversation and ask one question; no retries."""

    def __init__(self, settings: Settings, http: GraphDBHttp | None = None) -> None:
        self.settings = settings
        self.http = http or GraphDBHttp(
            settings.kg_base_url, settings.kg_user, settings.kg_password
        )

    async def check_startup(self) -> None:
        await asyncio.to_thread(self._check_startup_sync)

    def _check_startup_sync(self) -> None:
        deadline = time.monotonic() + min(self.settings.chat_timeout_seconds, 15.0)
        for path in (CREATE_CHAT_PATH, ASK_PATH):
            try:
                response = self.http.options(path, deadline)
            except GraphDBTimeout as error:
                raise ConnectorTimeout(
                    "The GraphDB chat API did not respond during the startup check."
                ) from error
            except GraphDBUnavailable as error:
                raise ConnectorError(
                    "The GraphDB chat API is unreachable during the startup check.",
                    status_code=502,
                ) from error
            if response.status in (401, 403):
                raise ConnectorError(
                    "The GraphDB chat API rejected the configured read-only user.",
                    status_code=502,
                )
            if response.status == 404:
                raise ConnectorError(
                    f"The GraphDB chat endpoint {path} was not found.",
                    status_code=502,
                )
            if response.status >= 500:
                raise ConnectorError(
                    f"The GraphDB chat endpoint {path} returned HTTP {response.status}.",
                    status_code=502,
                )

    async def answer(self, question: str) -> AnswerResult:
        return await asyncio.to_thread(self._answer_sync, question)

    def _answer_sync(self, question: str) -> AnswerResult:
        started = time.monotonic()
        deadline = started + self.settings.chat_timeout_seconds
        try:
            create = self._post_json(
                CREATE_CHAT_PATH,
                {
                    "agentId": self.settings.kg_agent_id,
                    "question": question,
                    "tzOffset": TZ_OFFSET,
                },
                deadline,
            )
            conversation_id = create.get("conversationId")
            if not isinstance(conversation_id, str) or not conversation_id:
                raise ConnectorError(
                    "The GraphDB chat API returned no conversation id.", status_code=502
                )
            answer_response = self._post_json(
                ASK_PATH,
                {
                    "agentId": self.settings.kg_agent_id,
                    "conversationId": conversation_id,
                    "question": question,
                    "tzOffset": TZ_OFFSET,
                },
                deadline,
            )
        except GraphDBTimeout as error:
            raise ConnectorTimeout(
                f"The GraphDB chat API timed out after {self.settings.chat_timeout_seconds:g} s."
            ) from error
        except GraphDBUnavailable as error:
            raise ConnectorError("The GraphDB chat API is unreachable.", status_code=502) from error

        answer = _extract_answer(answer_response)
        if answer is None:
            raise ConnectorError("The GraphDB chat API returned no answer text.", status_code=502)
        usage = _extract_usage(answer_response)
        return AnswerResult(
            text=answer.strip(),
            mode="chat",
            latency_seconds=round(time.monotonic() - started, 3),
            conversation_id=conversation_id,
            usage=usage,
            total_tokens=total_tokens(usage),
        )

    def _post_json(self, path: str, payload: dict[str, Any], deadline: float) -> dict[str, Any]:
        response = self.http.request(
            "POST", path, payload=payload, deadline=deadline, accept="application/json"
        )
        if response.status != 200:
            raise ConnectorError(
                f"The GraphDB chat API returned HTTP {response.status}.", status_code=502
            )
        try:
            document = json.loads(response.body)
        except json.JSONDecodeError as error:
            raise ConnectorError(
                "The GraphDB chat API returned invalid JSON.", status_code=502
            ) from error
        if not isinstance(document, dict):
            raise ConnectorError(
                "The GraphDB chat API returned an invalid response.", status_code=502
            )
        return document


def _extract_answer(payload: dict[str, Any]) -> str | None:
    messages = payload.get("messages")
    if isinstance(messages, list):
        for message in reversed(messages):
            if not isinstance(message, dict):
                continue
            value = message.get("message")
            if isinstance(value, str) and value.strip():
                return value
    for key in ("answer", "message", "response"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _extract_usage(payload: dict[str, Any]) -> dict[str, Any] | None:
    usage = payload.get("usage")
    if isinstance(usage, dict):
        return usage
    messages = payload.get("messages")
    if isinstance(messages, list):
        for message in reversed(messages):
            if isinstance(message, dict):
                nested = message.get("usage")
                if isinstance(nested, dict):
                    return nested
    return None
