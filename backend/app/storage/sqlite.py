"""SQLite implementation of the connector and thread storage boundaries."""

import asyncio
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .database import SQLiteDatabase
from .models import QuestionAnswerPair, RelevanceMark, Report, Session

DEFAULT_SESSION_TITLE = "New Chat"


def _now() -> str:
    return datetime.now(UTC).isoformat()


class SQLiteQuestionAnswerStore:
    """Persist sessions, completed pairs, relevance marks and current reports."""

    def __init__(self, path: str | Path) -> None:
        self.database = SQLiteDatabase(path)

    async def save(self, pair: QuestionAnswerPair) -> None:
        await asyncio.to_thread(self._save_sync, pair)

    async def list_for_session(self, session_id: str) -> list[QuestionAnswerPair]:
        return await asyncio.to_thread(self._list_sync, session_id)

    async def list_sessions(
        self, cursor: int = 0, limit: int = 50
    ) -> tuple[list[Session], int | None]:
        return await asyncio.to_thread(self._list_sessions_sync, cursor, limit)

    async def create_session(self, title: str = DEFAULT_SESSION_TITLE) -> Session:
        return await asyncio.to_thread(self._create_session_sync, title)

    async def get_session(self, session_id: str) -> Session | None:
        return await asyncio.to_thread(self._get_session_sync, session_id)

    async def rename_session(self, session_id: str, title: str) -> Session | None:
        return await asyncio.to_thread(self._rename_session_sync, session_id, title)

    async def delete_session(self, session_id: str) -> bool:
        return await asyncio.to_thread(self._delete_session_sync, session_id)

    async def get_report(self, session_id: str) -> Report | None:
        return await asyncio.to_thread(self._get_report_sync, session_id)

    async def set_report(
        self, session_id: str, openui_lang: str, incomplete: bool = False
    ) -> Report:
        return await asyncio.to_thread(self._set_report_sync, session_id, openui_lang, incomplete)

    async def get_relevance(self, session_id: str, pair_id: str) -> RelevanceMark | None:
        return await asyncio.to_thread(self._get_relevance_sync, session_id, pair_id)

    async def get_raw_answer(self, session_id: str, pair_id: str) -> str | None:
        return await asyncio.to_thread(self._get_raw_answer_sync, session_id, pair_id)

    async def set_relevance(
        self, session_id: str, pair_id: str, relevant: bool
    ) -> RelevanceMark | None:
        return await asyncio.to_thread(self._set_relevance_sync, session_id, pair_id, relevant)

    async def delete_pair(self, session_id: str, pair_id: str) -> bool:
        return await asyncio.to_thread(self._delete_pair_sync, session_id, pair_id)

    async def erase_history(self, session_id: str) -> None:
        await asyncio.to_thread(self._erase_history_sync, session_id)

    async def erase_report(self, session_id: str) -> None:
        await asyncio.to_thread(self._erase_report_sync, session_id)

    def _save_sync(self, pair: QuestionAnswerPair) -> None:
        timestamp = pair.created_at
        with self.database.connect() as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO sessions (id, title, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET updated_at = excluded.updated_at
                    """,
                    (
                        pair.session_id,
                        DEFAULT_SESSION_TITLE,
                        timestamp,
                        timestamp,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO question_answer_pairs
                        (id, session_id, question, raw_answer, openui_lang, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pair.id,
                        pair.session_id,
                        pair.question,
                        pair.raw_answer,
                        pair.openui_lang,
                        timestamp,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO question_answer_relevance (pair_id, relevant, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (pair.id, 1 if pair.relevant else 0, timestamp),
                )

    def _list_sync(self, session_id: str) -> list[QuestionAnswerPair]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT p.id, p.session_id, p.question, p.raw_answer, p.openui_lang,
                       p.created_at, r.relevant
                FROM question_answer_pairs AS p
                JOIN question_answer_relevance AS r ON r.pair_id = p.id
                WHERE p.session_id = ?
                ORDER BY p.created_at, p.rowid
                """,
                (session_id,),
            ).fetchall()
        return [
            QuestionAnswerPair(
                id=str(row["id"]),
                session_id=str(row["session_id"]),
                question=str(row["question"]),
                raw_answer=str(row["raw_answer"]),
                openui_lang=str(row["openui_lang"]),
                relevant=bool(row["relevant"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]

    def _list_sessions_sync(self, cursor: int, limit: int) -> tuple[list[Session], int | None]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM sessions
                ORDER BY created_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (limit + 1, cursor),
            ).fetchall()
        has_more = len(rows) > limit
        sessions = [_session_from_row(row) for row in rows[:limit]]
        return sessions, cursor + limit if has_more else None

    def _create_session_sync(self, title: str) -> Session:
        session = Session(
            id=uuid4().hex,
            title=title.strip() or DEFAULT_SESSION_TITLE,
            created_at=_now(),
            updated_at=_now(),
        )
        with self.database.connect() as connection, connection:
            connection.execute(
                """
                INSERT INTO sessions (id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session.id,
                    session.title,
                    session.created_at,
                    session.updated_at,
                ),
            )
        return session

    def _get_session_sync(self, session_id: str) -> Session | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM sessions
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
        return _session_from_row(row) if row is not None else None

    def _rename_session_sync(self, session_id: str, title: str) -> Session | None:
        updated_at = _now()
        with self.database.connect() as connection, connection:
            result = connection.execute(
                """
                UPDATE sessions
                SET title = ?, updated_at = ?
                WHERE id = ?
                """,
                (title.strip() or DEFAULT_SESSION_TITLE, updated_at, session_id),
            )
        return self._get_session_sync(session_id) if result.rowcount else None

    def _delete_session_sync(self, session_id: str) -> bool:
        with self.database.connect() as connection, connection:
            result = connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return bool(result.rowcount)

    def _get_report_sync(self, session_id: str) -> Report | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT session_id, openui_lang, incomplete, created_at, updated_at
                FROM reports
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        return _report_from_row(row) if row is not None else None

    def _set_report_sync(self, session_id: str, openui_lang: str, incomplete: bool) -> Report:
        timestamp = _now()
        with self.database.connect() as connection, connection:
            connection.execute(
                """
                INSERT INTO reports
                    (session_id, openui_lang, incomplete, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    openui_lang = excluded.openui_lang,
                    incomplete = excluded.incomplete,
                    updated_at = excluded.updated_at
                """,
                (session_id, openui_lang, 1 if incomplete else 0, timestamp, timestamp),
            )
        report = self._get_report_sync(session_id)
        if report is None:
            raise RuntimeError("report was not stored")
        return report

    def _get_relevance_sync(self, session_id: str, pair_id: str) -> RelevanceMark | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT r.pair_id, r.relevant, r.updated_at
                FROM question_answer_relevance AS r
                JOIN question_answer_pairs AS p ON p.id = r.pair_id
                WHERE p.session_id = ? AND r.pair_id = ?
                """,
                (session_id, pair_id),
            ).fetchone()
        return _relevance_from_row(row) if row is not None else None

    def _get_raw_answer_sync(self, session_id: str, pair_id: str) -> str | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT raw_answer
                FROM question_answer_pairs
                WHERE id = ? AND session_id = ?
                """,
                (pair_id, session_id),
            ).fetchone()
        return str(row["raw_answer"]) if row is not None else None

    def _delete_pair_sync(self, session_id: str, pair_id: str) -> bool:
        with self.database.connect() as connection, connection:
            result = connection.execute(
                """
                DELETE FROM question_answer_pairs
                WHERE id = ? AND session_id = ?
                """,
                (pair_id, session_id),
            )
        return bool(result.rowcount)

    def _erase_history_sync(self, session_id: str) -> None:
        with self.database.connect() as connection, connection:
            connection.execute(
                "DELETE FROM question_answer_pairs WHERE session_id = ?",
                (session_id,),
            )
            connection.execute(
                "DELETE FROM reports WHERE session_id = ?",
                (session_id,),
            )

    def _erase_report_sync(self, session_id: str) -> None:
        with self.database.connect() as connection, connection:
            connection.execute(
                "DELETE FROM reports WHERE session_id = ?",
                (session_id,),
            )

    def _set_relevance_sync(
        self, session_id: str, pair_id: str, relevant: bool
    ) -> RelevanceMark | None:
        updated_at = _now()
        with self.database.connect() as connection, connection:
            result = connection.execute(
                """
                UPDATE question_answer_relevance
                SET relevant = ?, updated_at = ?
                WHERE pair_id = ?
                  AND EXISTS (
                      SELECT 1 FROM question_answer_pairs
                      WHERE id = ? AND session_id = ?
                  )
                """,
                (1 if relevant else 0, updated_at, pair_id, pair_id, session_id),
            )
        return self._get_relevance_sync(session_id, pair_id) if result.rowcount else None


def _session_from_row(row: sqlite3.Row) -> Session:
    return Session(
        id=str(row["id"]),
        title=str(row["title"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _report_from_row(row: sqlite3.Row) -> Report:
    return Report(
        session_id=str(row["session_id"]),
        openui_lang=str(row["openui_lang"]),
        incomplete=bool(row["incomplete"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _relevance_from_row(row: sqlite3.Row) -> RelevanceMark:
    return RelevanceMark(
        pair_id=str(row["pair_id"]),
        relevant=bool(row["relevant"]),
        updated_at=str(row["updated_at"]),
    )
