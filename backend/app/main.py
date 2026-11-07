"""FastAPI entry point and streaming chat endpoint."""

import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from app.api.threads import router as threads_router
from app.connector import ConnectorError, KnowledgeGraphConnector, Settings
from app.connector.language import detect_language, error_message
from app.connector.service import STREAM_CHUNK_SIZE
from app.storage import SQLiteQuestionAnswerStore, StorageError


class ChatRequest(BaseModel):
    question: str = ""
    session_id: str = "default"


def create_app(
    connector: KnowledgeGraphConnector | None = None,
    store: SQLiteQuestionAnswerStore | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        active = app.state.connector or KnowledgeGraphConnector(Settings.load())
        app.state.connector = active
        if app.state.store is None:
            app.state.store = getattr(active, "store", None)
        await active.check_startup()
        yield

    app = FastAPI(lifespan=lifespan)
    app.state.connector = connector
    app.state.store = store

    @app.exception_handler(StorageError)
    async def storage_error_handler(request: Request, error: StorageError) -> JSONResponse:
        return JSONResponse({"error": "The database operation failed."}, status_code=500)

    @app.exception_handler(sqlite3.Error)
    async def sqlite_error_handler(request: Request, error: sqlite3.Error) -> JSONResponse:
        return JSONResponse({"error": "The database operation failed."}, status_code=500)

    app.include_router(threads_router)

    @app.post("/api/chat", response_model=None)
    async def chat(request: ChatRequest) -> JSONResponse | StreamingResponse:
        language = detect_language(request.question)
        if not request.question.strip():
            return JSONResponse({"error": error_message("validation", language)}, status_code=400)
        active: KnowledgeGraphConnector | None = app.state.connector
        if active is None:
            return JSONResponse({"error": error_message("unknown", language)}, status_code=503)
        try:
            result = await active.answer_and_store(request.question, request.session_id)
        except ConnectorError as error:
            return JSONResponse(
                {"error": error_message(error.kind, language)},
                status_code=error.status_code,
            )

        async def body() -> AsyncIterator[bytes]:
            for index in range(0, len(result.raw.text), STREAM_CHUNK_SIZE):
                yield result.raw.text[index : index + STREAM_CHUNK_SIZE].encode()

        return StreamingResponse(body(), media_type="text/plain")

    return app


app = create_app()
