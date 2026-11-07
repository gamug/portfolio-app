"""Thread, report and relevance endpoints over the SQLite store."""

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app.storage import RelevanceMark, Report, Session, SQLiteQuestionAnswerStore

router = APIRouter(prefix="/api/threads", tags=["threads"])


class ThreadCreateRequest(BaseModel):
    messages: list[dict[str, Any]] = []


class ThreadUpdateRequest(BaseModel):
    title: str | None = None


class ThreadResponse(BaseModel):
    id: str
    title: str
    createdAt: str


class MessageResponse(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str


class ReportRequest(BaseModel):
    openui_lang: str
    incomplete: bool = False


class ReportResponse(BaseModel):
    openui_lang: str
    incomplete: bool
    created_at: str
    updated_at: str


class RelevanceRequest(BaseModel):
    relevant: bool


class RelevanceResponse(BaseModel):
    pair_id: str
    relevant: bool
    updated_at: str


def _store(request: Request) -> SQLiteQuestionAnswerStore:
    store = request.app.state.store
    if not isinstance(store, SQLiteQuestionAnswerStore):
        raise HTTPException(status_code=503, detail="The database is not ready.")
    return store


def _thread(session: Session) -> ThreadResponse:
    return ThreadResponse(id=session.id, title=session.title, createdAt=session.created_at)


def _report(report: Report) -> ReportResponse:
    return ReportResponse(
        openui_lang=report.openui_lang,
        incomplete=report.incomplete,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


def _relevance(mark: RelevanceMark) -> RelevanceResponse:
    return RelevanceResponse(
        pair_id=mark.pair_id,
        relevant=mark.relevant,
        updated_at=mark.updated_at,
    )


def _title_from_messages(messages: list[dict[str, Any]]) -> str:
    for message in messages:
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return " ".join(content.split())[:80]
    return "New Chat"


@router.get("/get")
async def list_threads(request: Request, cursor: str | None = None) -> dict[str, Any]:
    offset = 0
    if cursor is not None:
        try:
            offset = int(cursor)
        except ValueError as error:
            raise HTTPException(status_code=400, detail="Invalid cursor.") from error
        if offset < 0:
            raise HTTPException(status_code=400, detail="Invalid cursor.")
    sessions, next_cursor = await _store(request).list_sessions(offset)
    payload: dict[str, Any] = {"threads": [_thread(session) for session in sessions]}
    if next_cursor is not None:
        payload["nextCursor"] = str(next_cursor)
    return payload


@router.post("/create")
async def create_thread(body: ThreadCreateRequest, request: Request) -> ThreadResponse:
    session = await _store(request).create_session(_title_from_messages(body.messages))
    return _thread(session)


@router.get("/get/{thread_id}")
async def get_thread(thread_id: str, request: Request) -> list[MessageResponse]:
    store = _store(request)
    if await store.get_session(thread_id) is None:
        raise HTTPException(status_code=404, detail="Thread not found.")
    messages: list[MessageResponse] = []
    for pair in await store.list_for_session(thread_id):
        messages.append(
            MessageResponse(id=f"{pair.id}:question", role="user", content=pair.question)
        )
        messages.append(MessageResponse(id=pair.id, role="assistant", content=pair.openui_lang))
    return messages


@router.patch("/update/{thread_id}")
async def update_thread(
    thread_id: str, body: ThreadUpdateRequest, request: Request
) -> ThreadResponse:
    store = _store(request)
    session = await store.get_session(thread_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Thread not found.")
    if body.title is not None:
        renamed = await store.rename_session(thread_id, body.title)
        if renamed is None:
            raise HTTPException(status_code=404, detail="Thread not found.")
        session = renamed
    return _thread(session)


@router.delete("/delete/{thread_id}", status_code=204)
async def delete_thread(thread_id: str, request: Request) -> Response:
    if not await _store(request).delete_session(thread_id):
        raise HTTPException(status_code=404, detail="Thread not found.")
    return Response(status_code=204)


@router.get("/{thread_id}/report")
async def get_report(thread_id: str, request: Request) -> dict[str, Any]:
    store = _store(request)
    if await store.get_session(thread_id) is None:
        raise HTTPException(status_code=404, detail="Thread not found.")
    report = await store.get_report(thread_id)
    return {"report": _report(report) if report is not None else None}


@router.put("/{thread_id}/report")
async def set_report(thread_id: str, body: ReportRequest, request: Request) -> dict[str, Any]:
    store = _store(request)
    if await store.get_session(thread_id) is None:
        raise HTTPException(status_code=404, detail="Thread not found.")
    report = await store.set_report(thread_id, body.openui_lang, body.incomplete)
    return {"report": _report(report)}


@router.get("/{thread_id}/pairs/{pair_id}/relevance")
async def get_relevance(thread_id: str, pair_id: str, request: Request) -> RelevanceResponse:
    mark = await _store(request).get_relevance(thread_id, pair_id)
    if mark is None:
        raise HTTPException(status_code=404, detail="Question-answer pair not found.")
    return _relevance(mark)


@router.put("/{thread_id}/pairs/{pair_id}/relevance")
async def set_relevance(
    thread_id: str, pair_id: str, body: RelevanceRequest, request: Request
) -> RelevanceResponse:
    mark = await _store(request).set_relevance(thread_id, pair_id, body.relevant)
    if mark is None:
        raise HTTPException(status_code=404, detail="Question-answer pair not found.")
    return _relevance(mark)
