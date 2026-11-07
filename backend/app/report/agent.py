"""Orchestrate the two report skills behind one streamed generation."""

import asyncio
import logging
from collections.abc import AsyncIterator

from app.connector.language import Language, detect_language
from app.connector.settings import Settings
from app.storage import Report, SQLiteQuestionAnswerStore

from .chart_plan import ChartPlanSkill
from .language import report_error_message
from .models import (
    ReportContext,
    ReportDelta,
    ReportDone,
    ReportError,
    ReportEvent,
    ReportFailed,
    ReportProgress,
)
from .openui import OpenUIReportSkill, strip_code_fences

logger = logging.getLogger(__name__)


class ReportAgent:
    """Run skill 1 and skill 2 in order; store only complete or partial results."""

    def __init__(
        self,
        settings: Settings,
        store: SQLiteQuestionAnswerStore,
        plan_skill: ChartPlanSkill | None = None,
        render_skill: OpenUIReportSkill | None = None,
    ) -> None:
        self.settings = settings
        self.store = store
        self.plan_skill = plan_skill or ChartPlanSkill(settings)
        self.render_skill = render_skill or OpenUIReportSkill(settings)

    async def prepare(self, session_id: str, language: Language | None = None) -> ReportContext:
        session = await self.store.get_session(session_id)
        if session is None:
            raise ReportError("not_found", status_code=404, language=language or "en")
        pairs = await self.store.list_for_session(session_id)
        if not pairs:
            raise ReportError("no_history", status_code=400, language=language or "en")
        selected = language or detect_language(" ".join(pair.question for pair in pairs))
        relevant = [pair for pair in pairs if pair.relevant]
        if not relevant:
            raise ReportError("no_relevant", status_code=400, language=selected)
        return ReportContext(
            session_id=session_id,
            pairs=tuple(relevant),
            language=selected,
        )

    async def stream(self, context: ReportContext) -> AsyncIterator[ReportEvent]:
        yield ReportProgress(stage="planning")
        partial: list[str] = []
        try:
            plan = await self.plan_skill.build(context.pairs, context.language)
            yield ReportProgress(stage="rendering")
            chunks = self.render_skill.stream(plan, context.language)
            try:
                async for chunk in chunks:
                    partial.append(chunk)
                    yield ReportDelta(text=chunk)
            finally:
                close = getattr(chunks, "aclose", None)
                if callable(close):
                    await close()
            text = strip_code_fences("".join(partial))
            if not text:
                raise RuntimeError("the report is empty")
            await self.render_skill.validate(text)
            stored = await self.store.set_report(context.session_id, text, incomplete=False)
            yield ReportDone(report=stored)
        except asyncio.CancelledError:
            raise
        except Exception as error:  # noqa: BLE001 - one user-safe failure, partial kept if any
            # exc_info is off on purpose: a chained provider error can include request
            # details. The type and truncated, redacted message are enough to diagnose it.
            logger.exception(
                "Report generation failed (%s): %s",
                type(error).__name__,
                self._safe_error_message(error),
                exc_info=False,
            )
            text = strip_code_fences("".join(partial))
            stored_partial = await self._store_partial(context.session_id, text)
            yield ReportFailed(
                error=report_error_message("generation", context.language, partial=stored_partial),
                incomplete=stored_partial,
            )

    def _safe_error_message(self, error: BaseException) -> str:
        message = " ".join(str(error).split())
        for secret in (self.settings.llm_api_key, self.settings.kg_password):
            if secret:
                message = message.replace(secret, "<redacted>")
        return message[:300]

    async def _store_partial(self, session_id: str, text: str) -> bool:
        if not text.strip():
            return False
        try:
            await self.store.set_report(session_id, text, incomplete=True)
        except Exception:  # noqa: BLE001 - the original failure is the user-facing one
            return False
        return True


def report_payload(report: Report) -> dict[str, object]:
    """The same shape the GET report endpoint returns."""
    return {
        "openui_lang": report.openui_lang,
        "incomplete": report.incomplete,
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }
