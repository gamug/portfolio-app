"""Rows returned by the SQLite storage."""

from dataclasses import dataclass


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
