"""Types exchanged by the report skills, the orchestrator and the HTTP layer."""

from dataclasses import dataclass
from typing import Literal

from app.connector.language import Language
from app.storage.models import QuestionAnswerPair, Report

ChartType = Literal[
    "bar",
    "horizontal_bar",
    "stacked_bar",
    "line",
    "area",
    "pie",
    "donut",
    "table",
]
ReportStage = Literal["planning", "rendering"]
ReportErrorKind = Literal["not_found", "no_history", "no_relevant"]


class ReportError(RuntimeError):
    """A rejected generation request that the endpoint can answer as JSON."""

    def __init__(
        self,
        kind: ReportErrorKind,
        *,
        status_code: int,
        language: Language = "en",
    ) -> None:
        super().__init__(kind)
        self.kind = kind
        self.status_code = status_code
        self.language = language


class ReportSkillError(RuntimeError):
    """A skill returned invalid output or the LLM call failed; never retried."""


@dataclass(frozen=True, slots=True)
class ChartSeries:
    category: str
    values: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class ChartColumn:
    label: str
    values: tuple[str | float, ...]


@dataclass(frozen=True, slots=True)
class ChartSpec:
    type: ChartType
    title: str
    takeaway: str
    labels: tuple[str, ...] = ()
    series: tuple[ChartSeries, ...] = ()
    values: tuple[float, ...] = ()
    columns: tuple[ChartColumn, ...] = ()
    x_label: str = ""
    y_label: str = ""


@dataclass(frozen=True, slots=True)
class ChartPlan:
    """The validated JSON output of skill 1."""

    title: str
    summary: str
    charts: tuple[ChartSpec, ...]
    conclusions: str
    disclaimers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReportContext:
    """One accepted generation request, prepared before the stream starts."""

    session_id: str
    pairs: tuple[QuestionAnswerPair, ...]
    language: Language


@dataclass(frozen=True, slots=True)
class ReportProgress:
    stage: ReportStage


@dataclass(frozen=True, slots=True)
class ReportDelta:
    text: str


@dataclass(frozen=True, slots=True)
class ReportDone:
    report: Report


@dataclass(frozen=True, slots=True)
class ReportFailed:
    error: str
    incomplete: bool


ReportEvent = ReportProgress | ReportDelta | ReportDone | ReportFailed
