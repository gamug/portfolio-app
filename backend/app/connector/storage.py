"""Storage boundary for completed question-answer pairs.

TASK-023 replaces the in-memory implementation with the SQLite schema. Keeping the
boundary here lets TASK-021 integrate storage without changing the database schema.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class QuestionAnswerPair:
    session_id: str
    question: str
    raw_answer: str
    openui_lang: str
    relevant: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class QuestionAnswerStore(Protocol):
    async def save(self, pair: QuestionAnswerPair) -> None: ...

    async def list_for_session(self, session_id: str) -> list[QuestionAnswerPair]: ...


class InMemoryQuestionAnswerStore:
    """Process-local storage used until TASK-023 introduces SQLite."""

    def __init__(self) -> None:
        self._pairs: list[QuestionAnswerPair] = []

    async def save(self, pair: QuestionAnswerPair) -> None:
        self._pairs.append(pair)

    async def list_for_session(self, session_id: str) -> list[QuestionAnswerPair]:
        return [pair for pair in self._pairs if pair.session_id == session_id]
