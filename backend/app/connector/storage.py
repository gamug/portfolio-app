"""Storage boundary for completed question-answer pairs.

TASK-023 replaces the in-memory implementation with the SQLite schema. Keeping the
boundary here lets TASK-021 integrate storage without changing the database schema.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class QuestionAnswerPair:
    session_id: str
    question: str
    raw_answer: str
    openui_lang: str
    id: str = field(default_factory=lambda: uuid4().hex)
    relevant: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class QuestionAnswerStore(Protocol):
    async def save(self, pair: QuestionAnswerPair) -> None: ...

    async def list_for_session(self, session_id: str) -> list[QuestionAnswerPair]: ...
