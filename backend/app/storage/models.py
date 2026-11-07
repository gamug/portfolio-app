"""Neutral storage types shared by the connector and SQLite layers."""

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


@dataclass(frozen=True, slots=True)
class Session:
    id: str
    title: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class Report:
    session_id: str
    openui_lang: str
    incomplete: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class RelevanceMark:
    pair_id: str
    relevant: bool
    updated_at: str
