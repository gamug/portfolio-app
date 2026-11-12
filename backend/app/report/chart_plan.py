"""Skill 1: turn relevant question-answer pairs into a validated JSON chart plan."""

import json
import math
import re
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, TypeGuard

from openai import APITimeoutError, AsyncOpenAI

from app.connector.language import Language
from app.connector.models import total_tokens
from app.connector.settings import Settings
from app.storage.models import QuestionAnswerPair

from .language import plan_language_instruction
from .models import (
    ChartColumn,
    ChartPlan,
    ChartSeries,
    ChartSpec,
    ChartType,
    ReportSkillError,
)

DEFAULT_PROMPT_PATH = Path(__file__).with_name("prompts") / "report_skill_1_chart_plan_prompt.txt"
ALLOWED_TYPES: tuple[ChartType, ...] = (
    "bar",
    "horizontal_bar",
    "stacked_bar",
    "line",
    "area",
    "pie",
    "donut",
    "table",
)
CARTESIAN_TYPES: tuple[ChartType, ...] = ("bar", "horizontal_bar", "stacked_bar", "line", "area")
CIRCULAR_TYPES: tuple[ChartType, ...] = ("pie", "donut")
MAX_CHARTS = 8
DEFAULT_MAX_TOKENS = 2500
NUMBER_PATTERN = re.compile(r"(?<![\w.])-?\d+(?:[.,]\d+)*")
THOUSANDS_DOT_PATTERN = re.compile(r"^-?[1-9]\d{0,2}\.\d{3}$")
EMPTY_CELL = "–"
EMPTY_CELL_MARKERS = frozenset({"-", "–", "n/a"})


class _TextOnlyTableError(ReportSkillError):
    """A table with no numeric column; skipped when other charts are valid."""


def strip_fences(text: str) -> str:
    """Remove one surrounding markdown fence, as the TASK-019 spike did."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _parse_number_token(token: str) -> set[float]:
    """Parse one numeric token using Spanish and English separator conventions."""
    if "." not in token and "," not in token:
        return {float(token)}

    if "." in token and "," in token:
        if token.rfind(".") > token.rfind(","):
            return {float(token.replace(",", ""))}
        return {float(token.replace(".", "").replace(",", "."))}

    if "," in token:
        parts = token.split(",")
        if len(parts) > 2:
            return {float(token.replace(",", ""))}
        head, tail = parts
        if head in {"0", "-0"} or len(tail) != 3:
            return {float(token.replace(",", "."))}
        return {float(token.replace(",", ""))}

    parts = token.split(".")
    if len(parts) > 2:
        return {float(token.replace(".", ""))}

    values = {float(token)}
    if THOUSANDS_DOT_PATTERN.fullmatch(token):
        values.add(float(token.replace(".", "")))
    return values


def extract_numbers(text: str) -> set[float]:
    """Return every numeric token in the answer text, keeping the written scale."""
    normalized = text.replace("\u2212", "-")
    numbers: set[float] = set()
    for match in NUMBER_PATTERN.finditer(normalized):
        try:
            numbers.update(_parse_number_token(match.group(0)))
        except ValueError:
            continue
    return numbers


def _is_number(value: object) -> TypeGuard[int | float]:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _require_text(document: dict[str, Any], key: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ReportSkillError(f"The chart plan has no usable {key}.")
    return value.strip()


def _optional_text(document: dict[str, Any], key: str) -> str:
    value = document.get(key)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ReportSkillError(f"The chart plan field {key} must be a string.")
    return value.strip()


def _number_list(value: object, field: str) -> tuple[float, ...]:
    if not isinstance(value, list) or not value:
        raise ReportSkillError(f"The chart plan field {field} must be a non-empty array.")
    numbers: list[float] = []
    for item in value:
        if not _is_number(item):
            raise ReportSkillError(f"The chart plan field {field} must contain only numbers.")
        numbers.append(float(item))
    return tuple(numbers)


def _source_check(values: Sequence[float], source_numbers: set[float], field: str) -> None:
    for value in values:
        if not any(abs(value - source) <= 1e-9 for source in source_numbers):
            raise ReportSkillError(
                f"The chart plan field {field} uses {value:g}, which is not in the answers."
            )


def _labels(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ReportSkillError("The chart plan labels must be a non-empty array.")
    labels: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ReportSkillError("The chart plan labels must contain only non-empty strings.")
        labels.append(item.strip())
    return tuple(labels)


def _series(value: object, label_count: int, source_numbers: set[float]) -> tuple[ChartSeries, ...]:
    if not isinstance(value, list) or not value:
        raise ReportSkillError("A bar or line chart needs at least one series.")
    series: list[ChartSeries] = []
    for item in value:
        if not isinstance(item, dict):
            raise ReportSkillError("Each chart series must be an object.")
        category = item.get("category")
        if not isinstance(category, str) or not category.strip():
            raise ReportSkillError("Each chart series needs a non-empty category.")
        values = _number_list(item.get("values"), "series.values")
        if len(values) != label_count:
            raise ReportSkillError("Each series must have one value per label.")
        _source_check(values, source_numbers, "series.values")
        series.append(ChartSeries(category=category.strip(), values=values))
    return tuple(series)


def _columns(value: object, source_numbers: set[float]) -> tuple[ChartColumn, ...]:
    if not isinstance(value, list) or not value:
        raise ReportSkillError("A table needs at least one column.")
    columns: list[ChartColumn] = []
    length: int | None = None
    has_number = False
    for item in value:
        if not isinstance(item, dict):
            raise ReportSkillError("Each table column must be an object.")
        label = item.get("label")
        if not isinstance(label, str) or not label.strip():
            raise ReportSkillError("Each table column needs a non-empty label.")
        raw_values = item.get("values")
        if not isinstance(raw_values, list) or not raw_values:
            raise ReportSkillError("Each table column needs a non-empty values array.")
        if length is None:
            length = len(raw_values)
        elif len(raw_values) != length:
            raise ReportSkillError("Every table column must have the same number of values.")
        cells: list[str | float] = []
        for cell in raw_values:
            if cell is None or (
                isinstance(cell, str) and cell.strip().casefold() in EMPTY_CELL_MARKERS
            ):
                cells.append(EMPTY_CELL)
            elif isinstance(cell, str):
                cells.append(cell)
            elif _is_number(cell):
                number = float(cell)
                _source_check([number], source_numbers, "table.values")
                has_number = True
                cells.append(number)
            else:
                raise ReportSkillError("Table cells must be strings or numbers.")
        columns.append(ChartColumn(label=label.strip(), values=tuple(cells)))
    if not has_number:
        raise _TextOnlyTableError("A table chart needs at least one numeric column.")
    return tuple(columns)


def _chart(document: object, source_numbers: set[float]) -> ChartSpec:
    if not isinstance(document, dict):
        raise ReportSkillError("Each chart in the plan must be an object.")
    raw_type = document.get("type")
    if raw_type not in ALLOWED_TYPES:
        raise ReportSkillError(
            "Each chart type must be one of bar, line, pie or table "
            "(or horizontal_bar, stacked_bar, area, donut)."
        )
    chart_type: ChartType = raw_type
    title = _require_text(document, "title")
    takeaway = _require_text(document, "takeaway")
    if chart_type in CARTESIAN_TYPES:
        labels = _labels(document.get("labels"))
        series = _series(document.get("series"), len(labels), source_numbers)
        if chart_type in ("line", "area") and len(labels) == 2:
            chart_type = "bar"
        return ChartSpec(
            type=chart_type,
            title=title,
            takeaway=takeaway,
            labels=labels,
            series=series,
            x_label=_optional_text(document, "x_label"),
            y_label=_optional_text(document, "y_label"),
        )
    if chart_type in CIRCULAR_TYPES:
        labels = _labels(document.get("labels"))
        values = _number_list(document.get("values"), "values")
        if len(values) != len(labels):
            raise ReportSkillError("A pie or donut chart needs one value per label.")
        if any(value < 0 for value in values):
            raise ReportSkillError("A pie or donut chart cannot use a negative value.")
        _source_check(values, source_numbers, "values")
        return ChartSpec(
            type=chart_type,
            title=title,
            takeaway=takeaway,
            labels=labels,
            values=values,
        )
    return ChartSpec(
        type="table",
        title=title,
        takeaway=takeaway,
        columns=_columns(document.get("columns"), source_numbers),
    )


def parse_chart_plan(document: object, answers: Sequence[str]) -> ChartPlan:
    """Validate the skill output and enforce that chart numbers come from the answers."""
    if not isinstance(document, dict):
        raise ReportSkillError("The chart plan must be a JSON object.")
    title = _require_text(document, "title")
    summary = _require_text(document, "summary")
    conclusions = _require_text(document, "conclusions")
    raw_charts = document.get("charts")
    if not isinstance(raw_charts, list):
        raise ReportSkillError("The chart plan must contain a charts array.")
    if len(raw_charts) > MAX_CHARTS:
        raise ReportSkillError(f"The chart plan cannot contain more than {MAX_CHARTS} charts.")
    source_numbers = extract_numbers("\n".join(answers))
    parsed_charts: list[ChartSpec] = []
    text_only_error: _TextOnlyTableError | None = None
    for item in raw_charts:
        try:
            parsed_charts.append(_chart(item, source_numbers))
        except _TextOnlyTableError as error:
            text_only_error = error
    if not parsed_charts and text_only_error is not None:
        raise text_only_error
    return ChartPlan(
        title=title,
        summary=summary,
        charts=tuple(parsed_charts),
        conclusions=conclusions,
    )


class ChartPlanSkill:
    """Run skill 1 exactly once with the relevant pairs; never retry."""

    def __init__(
        self,
        settings: Settings,
        llm: Any = None,
        prompt_path: Path | None = None,
    ) -> None:
        self.settings = settings
        self.prompt_path = prompt_path or DEFAULT_PROMPT_PATH
        self.llm: Any = llm or AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_url,
            timeout=settings.chat_timeout_seconds,
            max_retries=0,
        )
        self.last_usage: dict[str, Any] | None = None
        self.last_total_tokens: int | None = None
        self.last_latency_seconds: float | None = None

    def _system_prompt(self, language: Language) -> str:
        try:
            prompt = self.prompt_path.read_text(encoding="utf-8")
        except OSError as error:
            raise ReportSkillError("The chart plan prompt is missing.") from error
        return f"{prompt}\n\n{plan_language_instruction(language)}"

    async def build(
        self, pairs: Sequence[QuestionAnswerPair], language: Language = "en"
    ) -> ChartPlan:
        payload = {
            "language": language,
            "pairs": [{"question": pair.question, "answer": pair.raw_answer} for pair in pairs],
        }
        system_prompt = self._system_prompt(language)
        self.last_usage = None
        self.last_total_tokens = None
        self.last_latency_seconds = None
        started = time.monotonic()
        try:
            response = await self.llm.chat.completions.create(
                model=self.settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(payload, ensure_ascii=False),
                    },
                ],
                temperature=0,
                max_tokens=DEFAULT_MAX_TOKENS,
                timeout=self.settings.chat_timeout_seconds,
            )
        except APITimeoutError as error:
            raise ReportSkillError("The chart plan skill timed out.") from error
        except Exception as error:  # noqa: BLE001 - one clear skill failure, no retry
            raise ReportSkillError("The chart plan skill failed.") from error

        try:
            content = response.choices[0].message.content or ""
        except (AttributeError, IndexError) as error:
            raise ReportSkillError("The chart plan skill returned an invalid response.") from error
        cleaned = strip_fences(content)
        if not cleaned:
            raise ReportSkillError("The chart plan skill returned an empty response.")
        try:
            document = json.loads(cleaned)
        except json.JSONDecodeError as error:
            raise ReportSkillError("The chart plan skill returned invalid JSON.") from error
        plan = parse_chart_plan(document, [pair.raw_answer for pair in pairs])

        usage = response.usage.model_dump() if response.usage else None
        self.last_usage = usage
        self.last_total_tokens = total_tokens(usage)
        self.last_latency_seconds = round(time.monotonic() - started, 3)
        return plan
