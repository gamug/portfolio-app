import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.connector.storage import QuestionAnswerPair
from app.main import create_app
from app.storage import SQLiteQuestionAnswerStore, StorageError


@dataclass
class FakeConnector:
    async def check_startup(self) -> None:
        return None

    async def answer_and_store(self, question: str, session_id: str) -> Any:
        raise AssertionError("chat is not used in the thread tests")


def _client(tmp_path: Path) -> tuple[TestClient, SQLiteQuestionAnswerStore]:
    store = SQLiteQuestionAnswerStore(tmp_path / "app.sqlite3")
    app = create_app(connector=FakeConnector(), store=store)  # type: ignore[arg-type]
    return TestClient(app), store


def _pair(session_id: str) -> QuestionAnswerPair:
    return QuestionAnswerPair(
        session_id=session_id,
        question="Synthetic question",
        raw_answer="Synthetic raw answer",
        openui_lang="root = Card([])",
    )


def test_thread_lifecycle_history_report_and_relevance(tmp_path: Path) -> None:
    client, store = _client(tmp_path)
    with client:
        assert client.get("/api/threads/get").json() == {"threads": []}

        created = client.post(
            "/api/threads/create",
            json={"messages": [{"content": "Synthetic first question"}]},
        )
        assert created.status_code == 200
        thread = created.json()
        assert thread["title"] == "Synthetic first question"
        assert set(thread) == {"id", "title", "createdAt"}
        thread_id = thread["id"]

        listed = client.get("/api/threads/get").json()
        assert listed["threads"] == [thread]

        pair = _pair(thread_id)
        asyncio.run(store.save(pair))
        asyncio.run(store.set_report(thread_id, "root = Card([])", True))

        history = client.get(f"/api/threads/get/{thread_id}")
        assert history.status_code == 200
        assert history.json() == [
            {
                "id": f"{pair.id}:question",
                "role": "user",
                "content": "Synthetic question",
            },
            {"id": pair.id, "role": "assistant", "content": "root = Card([])"},
        ]

        report = client.get(f"/api/threads/{thread_id}/report")
        assert report.status_code == 200
        assert report.json()["report"]["openui_lang"] == "root = Card([])"
        assert report.json()["report"]["incomplete"] is True

        updated_report = client.put(
            f"/api/threads/{thread_id}/report",
            json={"openui_lang": "root = Card([])", "incomplete": False},
        )
        assert updated_report.status_code == 200
        assert updated_report.json()["report"]["incomplete"] is False

        relevance = client.get(f"/api/threads/{thread_id}/pairs/{pair.id}/relevance")
        assert relevance.status_code == 200
        assert relevance.json()["relevant"] is True
        toggled = client.put(
            f"/api/threads/{thread_id}/pairs/{pair.id}/relevance",
            json={"relevant": False},
        )
        assert toggled.status_code == 200
        assert toggled.json()["relevant"] is False

        renamed = client.patch(f"/api/threads/update/{thread_id}", json={"title": "Renamed"})
        assert renamed.status_code == 200
        assert renamed.json()["title"] == "Renamed"

        deleted = client.delete(f"/api/threads/delete/{thread_id}")
        assert deleted.status_code == 204
        assert client.get("/api/threads/get").json() == {"threads": []}
        assert client.get(f"/api/threads/get/{thread_id}").status_code == 404
        assert client.get(f"/api/threads/{thread_id}/report").status_code == 404
        assert client.get(f"/api/threads/{thread_id}/pairs/{pair.id}/relevance").status_code == 404
        assert asyncio.run(store.list_for_session(thread_id)) == []
        assert asyncio.run(store.get_report(thread_id)) is None


def test_list_cursor_is_validated(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)
    with client:
        response = client.get("/api/threads/get?cursor=not-a-number")
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid cursor."}


def test_database_failure_is_user_safe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client, store = _client(tmp_path)

    async def broken(*args: Any, **kwargs: Any) -> Any:
        raise StorageError("internal sqlite detail")

    monkeypatch.setattr(store, "list_sessions", broken)
    with client:
        response = client.get("/api/threads/get")
    assert response.status_code == 500
    assert response.json() == {"error": "The database operation failed."}
    assert "sqlite" not in response.text


def test_two_sessions_keep_separate_histories_and_reports(tmp_path: Path) -> None:
    client, store = _client(tmp_path)
    with client:
        first = client.post("/api/threads/create", json={"messages": []}).json()
        second = client.post("/api/threads/create", json={"messages": []}).json()
        first_pair = QuestionAnswerPair(
            session_id=first["id"],
            question="First question",
            raw_answer="First raw answer",
            openui_lang='root = Card([TextContent("First")])',
        )
        second_pair = QuestionAnswerPair(
            session_id=second["id"],
            question="Second question",
            raw_answer="Second raw answer",
            openui_lang='root = Card([TextContent("Second")])',
        )
        asyncio.run(store.save(first_pair))
        asyncio.run(store.save(second_pair))
        asyncio.run(store.set_report(first["id"], "root = Card([])", False))
        asyncio.run(store.set_report(second["id"], "root = Stack([])", True))

        first_history = client.get(f"/api/threads/get/{first['id']}").json()
        second_history = client.get(f"/api/threads/get/{second['id']}").json()
        assert first_history[0]["content"] == "First question"
        assert second_history[0]["content"] == "Second question"
        assert (
            client.get(f"/api/threads/{first['id']}/report").json()["report"]["openui_lang"]
            == "root = Card([])"
        )
        assert (
            client.get(f"/api/threads/{second['id']}/report").json()["report"]["openui_lang"]
            == "root = Stack([])"
        )
