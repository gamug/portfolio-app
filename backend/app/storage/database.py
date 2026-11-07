"""SQLite connection handling and forward-only numbered migrations."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = Path(__file__).with_name("migrations")


class SQLiteDatabase:
    """Open short-lived connections with foreign keys and the migration runner."""

    def __init__(self, path: str | Path) -> None:
        self.path = self._resolve_path(path)
        self.migrate()

    @staticmethod
    def _resolve_path(path: str | Path) -> str:
        if str(path) == ":memory:":
            return ":memory:"
        resolved = Path(path)
        if not resolved.is_absolute():
            resolved = REPO_ROOT / resolved
        resolved.parent.mkdir(parents=True, exist_ok=True)
        return str(resolved)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
        finally:
            connection.close()

    def current_version(self) -> int:
        with self.connect() as connection:
            row = connection.execute("PRAGMA user_version").fetchone()
            return int(row[0]) if row is not None else 0

    def migrate(self) -> list[int]:
        """Apply every numbered migration newer than ``PRAGMA user_version``."""
        applied: list[int] = []
        with self.connect() as connection:
            row = connection.execute("PRAGMA user_version").fetchone()
            current = int(row[0]) if row is not None else 0
            for migration in sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql")):
                version = int(migration.name.split("_", 1)[0])
                if version <= current:
                    continue
                script = migration.read_text(encoding="utf-8")
                try:
                    connection.executescript(
                        f"BEGIN IMMEDIATE;\n{script}\nPRAGMA user_version = {version};\nCOMMIT;"
                    )
                except sqlite3.Error:
                    connection.rollback()
                    raise
                applied.append(version)
                current = version
        return applied
