"""Shared connector result and error types."""

from dataclasses import dataclass
from typing import Any, Literal

ChatMode = Literal["chat", "tool_loop"]


class ConnectorError(RuntimeError):
    """A connector failure that the HTTP layer can turn into a clear response."""

    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


class ConnectorTimeout(ConnectorError):
    """The knowledge graph did not answer before the per-question deadline."""

    def __init__(self, message: str = "The knowledge graph did not answer before the timeout."):
        super().__init__(message, status_code=504)


@dataclass(frozen=True, slots=True)
class AnswerResult:
    """A completed answer and the metadata needed by the caller."""

    text: str
    mode: ChatMode
    latency_seconds: float
    conversation_id: str | None = None
    usage: dict[str, Any] | None = None
    total_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class ConversionResult:
    """The OpenUI Lang conversion and its provider metadata."""

    text: str
    latency_seconds: float
    usage: dict[str, Any] | None = None
    total_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class ChatAnswer:
    """The raw answer, its OpenUI Lang conversion and the stored pair."""

    raw: AnswerResult
    conversion: ConversionResult


def total_tokens(usage: dict[str, Any] | None) -> int | None:
    """Return a token total from the common usage shapes, when present."""
    if not isinstance(usage, dict):
        return None
    for key in ("totalTokens", "total_tokens", "total"):
        value = usage.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    prompt = next(
        (
            usage[key]
            for key in ("promptTokens", "prompt_tokens", "inputTokens", "input_tokens")
            if isinstance(usage.get(key), int) and not isinstance(usage.get(key), bool)
        ),
        None,
    )
    completion = next(
        (
            usage[key]
            for key in (
                "completionTokens",
                "completion_tokens",
                "outputTokens",
                "output_tokens",
            )
            if isinstance(usage.get(key), int) and not isinstance(usage.get(key), bool)
        ),
        None,
    )
    if prompt is not None and completion is not None:
        return int(prompt) + int(completion)
    return None
