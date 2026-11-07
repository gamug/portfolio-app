"""Streamed report generation endpoint over the report agent."""

import json
from collections.abc import AsyncIterator
from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

from app.report.agent import ReportAgent, report_payload
from app.report.language import report_error_message
from app.report.models import (
    ReportDelta,
    ReportDone,
    ReportError,
    ReportEvent,
    ReportProgress,
)

router = APIRouter(prefix="/api/threads", tags=["reports"])


class ReportGenerateRequest(BaseModel):
    language: Literal["en", "es"] | None = None


def _sse(event: str, payload: dict[str, object]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n".encode()


def _encode(event: ReportEvent) -> bytes:
    if isinstance(event, ReportProgress):
        return _sse("progress", {"stage": event.stage})
    if isinstance(event, ReportDelta):
        return _sse("delta", {"text": event.text})
    if isinstance(event, ReportDone):
        return _sse("done", {"report": report_payload(event.report)})
    return _sse("error", {"error": event.error, "incomplete": event.incomplete})


@router.post("/{thread_id}/report/generate")
async def generate_report(
    thread_id: str,
    request: Request,
    body: ReportGenerateRequest | None = None,
) -> Response:
    language = body.language if body is not None else None
    agent = request.app.state.report_agent
    if not isinstance(agent, ReportAgent):
        return JSONResponse(
            {"error": report_error_message("unavailable", language or "en")},
            status_code=503,
        )
    try:
        context = await agent.prepare(thread_id, language)
    except ReportError as error:
        return JSONResponse(
            {"error": report_error_message(error.kind, error.language)},
            status_code=error.status_code,
        )

    async def events() -> AsyncIterator[bytes]:
        try:
            async for event in agent.stream(context):
                yield _encode(event)
        except ReportError as error:
            yield _sse(
                "error",
                {
                    "error": report_error_message(error.kind, context.language),
                    "incomplete": False,
                },
            )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
