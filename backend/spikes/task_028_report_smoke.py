#!/usr/bin/env python3
"""TASK-028 smoke: one report generation from synthetic answers.

This is a smoke script, not a test. It makes one smoke run of the two report skills (skill 1,
then skill 2), never retries, and writes the plan, the OpenUI Lang and the metadata only to the
git-excluded local-results directory. The synthetic text is not taken from the evaluation files.

The console prints only OK or ERROR, the latency and the token counts. Secret values from
``.env`` are redacted from every error written to disk.

Run from ``backend/`` as ``PYTHONPATH=. uv run python spikes/task_028_report_smoke.py``.
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from app.connector.settings import Settings
from app.report.chart_plan import ChartPlanSkill
from app.report.openui import OpenUIReportSkill, plan_payload, strip_code_fences
from app.storage import QuestionAnswerPair

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "backend/tests/evaluation/local-results"

SYNTHETIC_PAIRS = [
    QuestionAnswerPair(
        session_id="synthetic-smoke",
        question="How did revenue and cost change from January to March?",
        raw_answer=(
            "Synthetic example: revenue was 100 in January, 120 in February and 150 in March. "
            "Cost was 40 in January, 50 in February and 60 in March."
        ),
        openui_lang="root = Card([])",
    ),
    QuestionAnswerPair(
        session_id="synthetic-smoke",
        question="Which product earned more in March?",
        raw_answer=("Synthetic example: in March, Product A earned 90 and Product B earned 60."),
        openui_lang="root = Card([])",
    ),
]


def _secret_values(env: dict[str, str | None]) -> set[str]:
    markers = ("KEY", "PASSWORD", "SECRET", "TOKEN", "USER")
    return {
        value
        for key, value in env.items()
        if value and any(marker in key.upper() for marker in markers)
    }


def _redact(text: str, secrets: set[str]) -> str:
    for secret in secrets:
        text = text.replace(secret, "<redacted>")
    return text


async def _run(
    plan_skill: ChartPlanSkill,
    render_skill: OpenUIReportSkill,
    plan_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    plan = await plan_skill.build(SYNTHETIC_PAIRS, "en")
    plan_path.write_text(
        f"{json.dumps(plan_payload(plan), ensure_ascii=False, indent=2)}\n",
        encoding="utf-8",
    )
    chunks = [chunk async for chunk in render_skill.stream(plan, "en")]
    text = strip_code_fences("".join(chunks))
    await render_skill.validate(text)
    report_path.write_text(f"{text}\n", encoding="utf-8")
    return {
        "plan": {
            "latency_seconds": plan_skill.last_latency_seconds,
            "total_tokens": plan_skill.last_total_tokens,
            "usage": plan_skill.last_usage,
            "charts": len(plan.charts),
        },
        "report": {
            "latency_seconds": render_skill.last_latency_seconds,
            "total_tokens": render_skill.last_total_tokens,
            "usage": render_skill.last_usage,
            "characters": len(text),
        },
    }


def main() -> int:
    env = dotenv_values(REPO_ROOT / ".env")
    settings = Settings.load()
    secrets = _secret_values(env)
    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    metadata_path = RESULTS / f"task-028-smoke-{stamp}.json"
    plan_path = RESULTS / f"task-028-plan-{stamp}.json"
    report_path = RESULTS / f"task-028-report-{stamp}.openui"

    plan_skill = ChartPlanSkill(settings)
    render_skill = OpenUIReportSkill(settings)
    metadata: dict[str, Any] = {
        "model": settings.llm_model,
        "synthetic_pairs": len(SYNTHETIC_PAIRS),
        "status": "error",
    }
    started = time.monotonic()
    try:
        result = asyncio.run(_run(plan_skill, render_skill, plan_path, report_path))
        metadata.update(
            {
                "status": "ok",
                "total_latency_seconds": round(time.monotonic() - started, 3),
                **result,
            }
        )
    except Exception as error:  # noqa: BLE001 - the smoke records every failure once
        metadata.update(
            {
                "total_latency_seconds": round(time.monotonic() - started, 3),
                "error_type": type(error).__name__,
                "error": _redact(str(error), secrets),
            }
        )
        metadata_path.write_text(
            f"{json.dumps(metadata, ensure_ascii=False, indent=2)}\n",
            encoding="utf-8",
        )
        print(f"report smoke: ERROR ({type(error).__name__})")
        print(
            f"latency={metadata['total_latency_seconds']}s "
            f"plan_tokens={plan_skill.last_total_tokens} "
            f"report_tokens={render_skill.last_total_tokens}"
        )
        return 1

    metadata_path.write_text(
        f"{json.dumps(metadata, ensure_ascii=False, indent=2)}\n",
        encoding="utf-8",
    )
    print("report smoke: OK")
    print(
        f"latency={metadata['total_latency_seconds']}s "
        f"plan_tokens={plan_skill.last_total_tokens} "
        f"report_tokens={render_skill.last_total_tokens}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
