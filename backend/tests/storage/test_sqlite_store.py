import asyncio
import sqlite3
from pathlib import Path

import pytest

from app.connector.storage import QuestionAnswerPair
from app.storage.sqlite import SQLiteQuestionAnswerStore


def _pair(session_id: str = "s1") -> QuestionAnswerPair:
    return QuestionAnswerPair(
        session_id=session_id,
        question="question",
        raw_answer="raw answer",
        openui_lang="root = Card([])",
    )


def test_save_and_list_survive_a_new_store_instance(tmp_path: Path) -> None:
    path = tmp_path / "app.sqlite3"
    pair = _pair()
    asyncio.run(SQLiteQuestionAnswerStore(path).save(pair))

    reopened = SQLiteQuestionAnswerStore(path)
    pairs = asyncio.run(reopened.list_for_session("s1"))
    assert pairs == [pair]
    assert pairs[0].id == pair.id
    assert pairs[0].relevant is True


def test_save_creates_the_session_with_a_default_title(tmp_path: Path) -> None:
    store = SQLiteQuestionAnswerStore(tmp_path / "app.sqlite3")
    asyncio.run(store.save(_pair()))
    with store.database.connect() as connection:
        row = connection.execute("SELECT title FROM sessions WHERE id = 's1'").fetchone()
    assert row is not None
    assert row["title"] == "New Chat"


def test_relevance_can_be_toggled_and_is_returned(tmp_path: Path) -> None:
    store = SQLiteQuestionAnswerStore(tmp_path / "app.sqlite3")
    pair = _pair()
    asyncio.run(store.save(pair))
    with store.database.connect() as connection, connection:
        connection.execute(
            "UPDATE question_answer_relevance SET relevant = 0 WHERE pair_id = ?",
            (pair.id,),
        )
    assert asyncio.run(store.list_for_session("s1"))[0].relevant is False


def test_session_delete_cascades_to_pairs_relevance_and_reports(tmp_path: Path) -> None:
    store = SQLiteQuestionAnswerStore(tmp_path / "app.sqlite3")
    pair = _pair()
    asyncio.run(store.save(pair))
    with store.database.connect() as connection, connection:
        connection.execute(
            """
            INSERT INTO reports
                (session_id, openui_lang, incomplete, created_at, updated_at)
            VALUES ('s1', 'root = Card([])', 0, '2026-11-07T00:00:00Z',
                    '2026-11-07T00:00:00Z')
            """
        )
        connection.execute("DELETE FROM sessions WHERE id = 's1'")
    with store.database.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM question_answer_pairs").fetchone()[0] == 0
        assert (
            connection.execute("SELECT COUNT(*) FROM question_answer_relevance").fetchone()[0] == 0
        )
        assert connection.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 0


def test_only_one_current_report_per_session(tmp_path: Path) -> None:
    store = SQLiteQuestionAnswerStore(tmp_path / "app.sqlite3")
    asyncio.run(store.save(_pair()))
    insert = """
        INSERT INTO reports
            (session_id, openui_lang, incomplete, created_at, updated_at)
        VALUES ('s1', ?, 0, '2026-11-07T00:00:00Z', '2026-11-07T00:00:00Z')
    """
    with store.database.connect() as connection, connection:
        connection.execute(insert, ("root = Card([])",))
    with pytest.raises(sqlite3.IntegrityError):
        with store.database.connect() as connection, connection:
            connection.execute(insert, ("root = Card([])",))
    with store.database.connect() as connection, connection:
        connection.execute(
            """
            INSERT INTO reports
                (session_id, openui_lang, incomplete, created_at, updated_at)
            VALUES ('s1', 'root = Card([])', 1, '2026-11-07T00:00:00Z',
                    '2026-11-07T00:00:00Z')
            ON CONFLICT(session_id) DO UPDATE SET
                openui_lang = excluded.openui_lang,
                incomplete = excluded.incomplete,
                updated_at = excluded.updated_at
            """
        )
    with store.database.connect() as connection:
        row = connection.execute(
            "SELECT COUNT(*), MAX(incomplete) FROM reports WHERE session_id = 's1'"
        ).fetchone()
    assert row[0] == 1
    assert row[1] == 1


def test_sessions_history_and_reports_survive_a_new_store_instance(tmp_path: Path) -> None:
    path = tmp_path / "app.sqlite3"
    pair = _pair()
    store = SQLiteQuestionAnswerStore(path)
    asyncio.run(store.save(pair))
    asyncio.run(store.set_report("s1", "root = Card([])", incomplete=False))

    reopened = SQLiteQuestionAnswerStore(path)

    session = asyncio.run(reopened.get_session("s1"))
    assert session is not None
    assert asyncio.run(reopened.list_for_session("s1")) == [pair]
    report = asyncio.run(reopened.get_report("s1"))
    assert report is not None
    assert report.openui_lang == "root = Card([])"
    assert report.incomplete is False
