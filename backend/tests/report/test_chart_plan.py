import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from app.connector.settings import Settings
from app.report.chart_plan import ChartPlanSkill, extract_numbers, parse_chart_plan
from app.report.models import ReportSkillError
from app.storage import QuestionAnswerPair

ANSWERS = (
    "In January revenue was 100 and cost was 40. "
    "In February revenue was 120 and cost was 50. "
    "In March revenue was 150 and cost was 60."
)


def _pair(question: str = "Synthetic question", answer: str = ANSWERS) -> QuestionAnswerPair:
    return QuestionAnswerPair(
        session_id="s1",
        question=question,
        raw_answer=answer,
        openui_lang="root = Card([])",
    )


def _document() -> dict[str, Any]:
    return {
        "title": "Quarter",
        "summary": "Revenue rose from January to March.",
        "charts": [
            {
                "type": "line",
                "title": "Revenue by month",
                "labels": ["January", "February", "March"],
                "series": [{"category": "Revenue", "values": [100, 120, 150]}],
                "takeaway": "Revenue rose each month.",
            }
        ],
        "conclusions": "The quarter improved.",
    }


def test_validates_a_plan_and_keeps_only_answer_numbers() -> None:
    plan = parse_chart_plan(_document(), [ANSWERS])
    assert plan.title == "Quarter"
    assert len(plan.charts) == 1
    assert plan.charts[0].series[0].values == (100.0, 120.0, 150.0)


def test_matches_numbers_written_with_thousands_separators() -> None:
    document = _document()
    document["charts"][0]["labels"] = ["January", "February"]
    document["charts"][0]["series"][0]["values"] = [1200, 1500]
    plan = parse_chart_plan(
        document,
        ["In January revenue was 1,200 and in February revenue was 1,500."],
    )
    assert plan.charts[0].series[0].values == (1200.0, 1500.0)


def test_extract_numbers_handles_unicode_minus_and_localized_separators() -> None:
    numbers = extract_numbers(
        "Returns were −10.55 %, −18.94 %, -0,1229, 0,0108, 0,5 and 0,0. "
        "Assets were 4.958 and 1.289; the ratio was 0.999 and 0.8945."
    )
    assert -10.55 in numbers
    assert -18.94 in numbers
    assert -0.1229 in numbers
    assert 0.0108 in numbers
    assert 0.5 in numbers
    assert 0.0 in numbers
    assert 4.958 in numbers
    assert 4958.0 in numbers
    assert 1.289 in numbers
    assert 1289.0 in numbers
    assert 0.999 in numbers
    assert 0.8945 in numbers


def test_parse_plan_accepts_unicode_minus_and_localized_numbers() -> None:
    document = _document()
    document["charts"] = [
        {
            "type": "bar",
            "title": "Returns",
            "labels": ["A", "B", "C"],
            "series": [{"category": "Return", "values": [-10.55, -18.94, -0.1229]}],
            "takeaway": "Returns were negative.",
        },
        {
            "type": "table",
            "title": "Ratios",
            "columns": [
                {"label": "Ratio", "values": [0.0108, 0.5, 4958.0, 1289.0, 0.999]},
            ],
            "takeaway": "Ratios are shown.",
        },
    ]
    plan = parse_chart_plan(
        document,
        ["−10.55 %, −18.94 %, -0,1229, 0,0108, 0,5, 4.958, 1.289 and 0.999"],
    )
    assert plan.charts[0].series[0].values == (-10.55, -18.94, -0.1229)
    assert plan.charts[1].columns[0].values == (0.0108, 0.5, 4958.0, 1289.0, 0.999)


@pytest.mark.parametrize("text_table_first", [True, False])
def test_skips_text_only_table_when_other_numeric_charts_exist(
    text_table_first: bool,
) -> None:
    document = _document()
    text_table = {
        "type": "table",
        "title": "Rules",
        "columns": [
            {"label": "Rule", "values": ["Maximum weight", "Minimum weight"]},
            {"label": "Objective", "values": ["Minimize risk", "Maximize return"]},
        ],
        "takeaway": "Rules are qualitative.",
    }
    numeric_chart = document["charts"][0]
    document["charts"] = (
        [text_table, numeric_chart] if text_table_first else [numeric_chart, text_table]
    )
    plan = parse_chart_plan(document, [ANSWERS])
    assert [chart.type for chart in plan.charts] == ["line"]


def test_accepts_a_pie_and_a_table() -> None:
    document = _document()
    document["charts"] = [
        {
            "type": "pie",
            "title": "March mix",
            "labels": ["Product", "Service"],
            "values": [90, 60],
            "takeaway": "Product is larger.",
        },
        {
            "type": "table",
            "title": "Monthly detail",
            "columns": [
                {"label": "Month", "values": ["January", "February"]},
                {"label": "Revenue", "values": [100, 120]},
            ],
            "takeaway": "Revenue rose.",
        },
    ]
    plan = parse_chart_plan(document, ["Product 90, Service 60, January 100, February 120."])
    assert [chart.type for chart in plan.charts] == ["pie", "table"]


@pytest.mark.parametrize("chart_type", ["line", "area"])
def test_coerces_two_point_line_and_area_charts_to_bar(chart_type: str) -> None:
    document = _document()
    document["charts"][0]["type"] = chart_type
    document["charts"][0]["labels"] = ["January", "February"]
    document["charts"][0]["series"][0]["values"] = [100, 120]
    plan = parse_chart_plan(document, [ANSWERS])
    assert plan.charts[0].type == "bar"
    assert plan.charts[0].labels == ("January", "February")


def test_keeps_a_three_point_line_chart() -> None:
    plan = parse_chart_plan(_document(), [ANSWERS])
    assert plan.charts[0].type == "line"
    assert len(plan.charts[0].labels) == 3


@pytest.mark.parametrize("chart_type", ["bar", "horizontal_bar", "stacked_bar", "line", "area"])
def test_accepts_cartesian_types_and_axis_labels(chart_type: str) -> None:
    document = _document()
    document["charts"][0]["type"] = chart_type
    document["charts"][0]["x_label"] = "Month"
    document["charts"][0]["y_label"] = "Revenue"
    plan = parse_chart_plan(document, [ANSWERS])
    chart = plan.charts[0]
    assert chart.type == chart_type
    assert chart.x_label == "Month"
    assert chart.y_label == "Revenue"


def test_accepts_a_donut_chart() -> None:
    document = _document()
    document["charts"] = [
        {
            "type": "donut",
            "title": "March mix",
            "labels": ["Product", "Service"],
            "values": [90, 60],
            "takeaway": "Product is larger.",
        }
    ]
    plan = parse_chart_plan(document, ["Product 90, Service 60."])
    chart = plan.charts[0]
    assert chart.type == "donut"
    assert chart.values == (90.0, 60.0)
    assert chart.x_label == ""
    assert chart.y_label == ""


def test_optional_axis_labels_default_to_empty_and_reject_non_strings() -> None:
    document = _document()
    document["charts"][0]["x_label"] = None
    document["charts"][0]["y_label"] = "  Revenue  "
    plan = parse_chart_plan(document, [ANSWERS])
    assert plan.charts[0].x_label == ""
    assert plan.charts[0].y_label == "Revenue"

    document["charts"][0]["x_label"] = 5
    with pytest.raises(ReportSkillError, match="x_label"):
        parse_chart_plan(document, [ANSWERS])


def test_rejects_negative_values_in_a_donut() -> None:
    document = _document()
    document["charts"] = [
        {
            "type": "donut",
            "title": "Mix",
            "labels": ["A", "B"],
            "values": [-1, 2],
            "takeaway": "Invalid.",
        }
    ]
    with pytest.raises(ReportSkillError, match="negative"):
        parse_chart_plan(document, ["A -1, B 2"])


@pytest.mark.parametrize("chart_type", ["area", "horizontal_bar", "stacked_bar"])
def test_rejects_invented_numbers_in_new_cartesian_types(chart_type: str) -> None:
    document = _document()
    document["charts"][0]["type"] = chart_type
    document["charts"][0]["series"][0]["values"] = [100, 120, 999]
    with pytest.raises(ReportSkillError, match="not in the answers"):
        parse_chart_plan(document, [ANSWERS])


def test_accepts_empty_table_cells_without_counting_them_as_numbers() -> None:
    document = _document()
    document["charts"] = [
        {
            "type": "table",
            "title": "Monthly detail",
            "columns": [
                {"label": "Month", "values": ["January", "February", "March"]},
                {"label": "Revenue", "values": [100, None, 150]},
                {"label": "Cost", "values": ["-", "N/A", "–"]},
            ],
            "takeaway": "Some values are missing.",
        }
    ]
    plan = parse_chart_plan(document, [ANSWERS])
    table = plan.charts[0]
    assert table.columns[1].values == (100.0, "–", 150.0)
    assert table.columns[2].values == ("–", "–", "–")


def test_rejects_an_invented_number_in_a_table() -> None:
    document = _document()
    document["charts"] = [
        {
            "type": "table",
            "title": "Monthly detail",
            "columns": [
                {"label": "Month", "values": ["January", "February"]},
                {"label": "Revenue", "values": [100, 999]},
            ],
            "takeaway": "Invalid.",
        }
    ]
    with pytest.raises(ReportSkillError, match="not in the answers"):
        parse_chart_plan(document, [ANSWERS])


def test_allows_an_empty_chart_list() -> None:
    document = {
        "title": "No numbers",
        "summary": "The marked answers contain no numeric data.",
        "charts": [],
        "conclusions": "No chart is possible.",
    }
    assert parse_chart_plan(document, ["Text without figures."]).charts == ()


def test_rejects_a_number_that_is_not_in_the_answers() -> None:
    document = _document()
    document["charts"][0]["series"][0]["values"] = [100, 120, 999]
    with pytest.raises(ReportSkillError, match="not in the answers"):
        parse_chart_plan(document, [ANSWERS])


def test_rejects_an_unknown_chart_type() -> None:
    document = _document()
    document["charts"][0]["type"] = "radar"
    with pytest.raises(ReportSkillError, match="bar, line, pie or table"):
        parse_chart_plan(document, [ANSWERS])


def test_rejects_a_negative_pie_value() -> None:
    document = _document()
    document["charts"] = [
        {
            "type": "pie",
            "title": "Mix",
            "labels": ["A", "B"],
            "values": [-1, 2],
            "takeaway": "Invalid.",
        }
    ]
    with pytest.raises(ReportSkillError, match="negative"):
        parse_chart_plan(document, ["A -1, B 2"])


def test_rejects_mismatched_series_and_labels() -> None:
    document = _document()
    document["charts"][0]["series"][0]["values"] = [100, 120]
    with pytest.raises(ReportSkillError, match="one value per label"):
        parse_chart_plan(document, [ANSWERS])


def test_rejects_mismatched_table_columns() -> None:
    document = _document()
    document["charts"] = [
        {
            "type": "table",
            "title": "Detail",
            "columns": [
                {"label": "Month", "values": ["January", "February"]},
                {"label": "Revenue", "values": [100]},
            ],
            "takeaway": "Invalid.",
        }
    ]
    with pytest.raises(ReportSkillError, match="same number of values"):
        parse_chart_plan(document, ["January 100, February 120"])


def test_rejects_a_text_only_table() -> None:
    document = _document()
    document["charts"] = [
        {
            "type": "table",
            "title": "Detail",
            "columns": [{"label": "Month", "values": ["January", "February"]}],
            "takeaway": "Invalid.",
        }
    ]
    with pytest.raises(ReportSkillError, match="numeric column"):
        parse_chart_plan(document, ["January 100, February 120"])


def test_rejects_missing_text_fields() -> None:
    document = _document()
    del document["summary"]
    with pytest.raises(ReportSkillError, match="summary"):
        parse_chart_plan(document, [ANSWERS])


def test_rejects_too_many_charts() -> None:
    document = _document()
    document["charts"] = [document["charts"][0]] * 9
    with pytest.raises(ReportSkillError, match="more than 8"):
        parse_chart_plan(document, [ANSWERS])


class FakeCompletions:
    def __init__(self, content: str = "", error: Exception | None = None) -> None:
        self.content = content
        self.error = error
        self.calls = 0
        self.calls_args: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls += 1
        self.calls_args.append(kwargs)
        if self.error is not None:
            raise self.error
        message = SimpleNamespace(content=self.content)
        choice = SimpleNamespace(message=message)
        usage = SimpleNamespace(model_dump=lambda: {"totalTokens": 11})
        return SimpleNamespace(choices=[choice], usage=usage)


@dataclass
class FakeLLM:
    completions: FakeCompletions

    @property
    def chat(self) -> Any:
        return SimpleNamespace(completions=self.completions)


def _settings() -> Settings:
    return Settings(
        kg_host="http://graphdb:7200",
        kg_user="reader",
        kg_password="secret",
        kg_agent_id="agent-1",
        chat_mode="chat",
        llm_api_key="llm-secret",
        llm_model="deepseek-chat",
        llm_url="https://api.deepseek.com",
        chat_timeout_seconds=30,
    )


def _skill(tmp_path: Path, completions: FakeCompletions) -> ChartPlanSkill:
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("CHART PLAN PROMPT", encoding="utf-8")
    return ChartPlanSkill(_settings(), llm=FakeLLM(completions), prompt_path=prompt)


def test_skill_calls_once_and_parses_fenced_json(tmp_path: Path) -> None:
    content = f"```json\n{json.dumps(_document())}\n```"
    completions = FakeCompletions(content)
    result = asyncio.run(_skill(tmp_path, completions).build([_pair()], "en"))
    assert result.title == "Quarter"
    assert completions.calls == 1
    assert completions.calls_args[0]["temperature"] == 0
    system = str(completions.calls_args[0]["messages"][0]["content"])
    payload = json.loads(completions.calls_args[0]["messages"][1]["content"])
    assert "CHART PLAN PROMPT" in system
    assert "English" in system
    assert payload["pairs"][0]["question"] == "Synthetic question"
    assert payload["pairs"][0]["answer"] == ANSWERS


def test_skill_writes_spanish_instructions(tmp_path: Path) -> None:
    completions = FakeCompletions(json.dumps(_document()))
    asyncio.run(_skill(tmp_path, completions).build([_pair()], "es"))
    system = str(completions.calls_args[0]["messages"][0]["content"])
    assert "español" in system


def test_skill_rejects_invalid_json_with_one_call(tmp_path: Path) -> None:
    completions = FakeCompletions("not json")
    with pytest.raises(ReportSkillError, match="invalid JSON"):
        asyncio.run(_skill(tmp_path, completions).build([_pair()]))
    assert completions.calls == 1


def test_skill_failure_is_not_retried(tmp_path: Path) -> None:
    completions = FakeCompletions(error=RuntimeError("provider failed"))
    with pytest.raises(ReportSkillError, match="failed"):
        asyncio.run(_skill(tmp_path, completions).build([_pair()]))
    assert completions.calls == 1


def test_missing_prompt_is_a_clear_error(tmp_path: Path) -> None:
    completions = FakeCompletions(json.dumps(_document()))
    skill = ChartPlanSkill(
        _settings(),
        llm=FakeLLM(completions),
        prompt_path=tmp_path / "missing.txt",
    )
    with pytest.raises(ReportSkillError, match="prompt is missing"):
        asyncio.run(skill.build([_pair()]))
    assert completions.calls == 0
