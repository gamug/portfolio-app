from pathlib import Path

from app.storage.database import SQLiteDatabase


def test_migrations_create_the_schema_and_are_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "app.sqlite3"
    database = SQLiteDatabase(path)
    assert database.current_version() == 1
    assert database.migrate() == []

    with database.connect() as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        indexes = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
        }
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1

    assert {
        "sessions",
        "question_answer_pairs",
        "question_answer_relevance",
        "reports",
    } <= tables
    assert {"idx_sessions_created_at", "idx_qap_session_created"} <= indexes


def test_reopening_an_existing_database_does_not_reapply_migrations(tmp_path: Path) -> None:
    path = tmp_path / "app.sqlite3"
    SQLiteDatabase(path)
    reopened = SQLiteDatabase(path)
    assert reopened.current_version() == 1
    assert reopened.migrate() == []
