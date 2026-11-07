"""SQLite implementation of the connector's question-answer storage boundary."""

import asyncio
from pathlib import Path

from app.connector.storage import QuestionAnswerPair

from .database import SQLiteDatabase

DEFAULT_SESSION_TITLE = "New Chat"


class SQLiteQuestionAnswerStore:
    """Persist completed pairs and their default relevance mark in one transaction."""

    def __init__(self, path: str | Path) -> None:
        self.database = SQLiteDatabase(path)

    async def save(self, pair: QuestionAnswerPair) -> None:
        await asyncio.to_thread(self._save_sync, pair)

    async def list_for_session(self, session_id: str) -> list[QuestionAnswerPair]:
        return await asyncio.to_thread(self._list_sync, session_id)

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
