"""FastAPI entry point and streaming chat endpoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.connector import ConnectorError, KnowledgeGraphConnector, Settings
from app.connector.service import STREAM_CHUNK_SIZE


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)


def create_app(connector: KnowledgeGraphConnector | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        active = app.state.connector or KnowledgeGraphConnector(Settings.load())
        app.state.connector = active
        await active.check_startup()
        yield

    app = FastAPI(lifespan=lifespan)
    app.state.connector = connector

    @app.post("/api/chat", response_model=None)
    async def chat(request: ChatRequest) -> JSONResponse | StreamingResponse:
        active: KnowledgeGraphConnector | None = app.state.connector
        if active is None:
            return JSONResponse(
                {"error": "The knowledge-graph connector is not ready."}, status_code=503
            )
        try:
            result = await active.answer(request.question)
        except ConnectorError as error:
            return JSONResponse({"error": str(error)}, status_code=error.status_code)

        async def body() -> AsyncIterator[bytes]:
            for index in range(0, len(result.text), STREAM_CHUNK_SIZE):
                yield result.text[index : index + STREAM_CHUNK_SIZE].encode()

        return StreamingResponse(body(), media_type="text/plain")

    return app


app = create_app()
