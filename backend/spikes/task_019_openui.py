#!/usr/bin/env python3
"""TASK-019 spike: ask DeepSeek for one chat UI and one report UI in OpenUI Lang.

This is spike code, not production code. The prompts are generated locally by the
frontend spike from the installed OpenUI libraries. The script makes exactly two
short DeepSeek calls (chat conversion and report generation), never retries, and
writes the raw outputs only to the git-excluded local-results directory.

The synthetic answer text contains no real knowledge-graph data and no evaluation
questions.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from openai import OpenAI

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "backend/tests/evaluation/local-results"
CHAT_PROMPT = RESULTS / "task-019-chat-prompt.txt"
REPORT_PROMPT = RESULTS / "task-019-report-prompt.txt"
CHAT_OUTPUT = RESULTS / "task-019-chat-output.txt"
REPORT_OUTPUT = RESULTS / "task-019-report-output.txt"
METADATA = RESULTS / "task-019-llm.json"

SYNTHETIC_ANSWER = (
    "Synthetic example: monthly revenue was 100 in January, 120 in February and 150 in "
    "March. March was the strongest month."
)
CHAT_TASK = """Convert the answer text into a short OpenUI Lang chat response using the
chat component library. Keep it to at most 6 statements. Do not invent facts beyond
the answer text. Return only OpenUI Lang, without markdown fences."""
REPORT_TASK = """Build a short report from the answer text using the report component
library. Include a chart that plots the monthly revenue values. Keep it to at most 10
statements. Do not invent facts beyond the answer text. Return only OpenUI Lang,
without markdown fences."""


def _secret_values(env: dict[str, str]) -> set[str]:
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


def _strip_fences(text: str) -> tuple[str, bool]:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped, False
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip(), True


def _total_tokens(usage: dict[str, Any] | None) -> int | None:
    if not isinstance(usage, dict):
        return None
    for key in ("totalTokens", "total_tokens", "total"):
        value = usage.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    prompt = next(
        (
            usage[key]
            for key in ("promptTokens", "prompt_tokens", "inputTokens", "input_tokens")
            if isinstance(usage.get(key), int) and not isinstance(usage.get(key), bool)
        ),
        None,
    )
    completion = next(
        (
            usage[key]
            for key in (
                "completionTokens",
                "completion_tokens",
                "outputTokens",
                "output_tokens",
            )
            if isinstance(usage.get(key), int) and not isinstance(usage.get(key), bool)
        ),
        None,
    )
    if prompt is not None and completion is not None:
        return int(prompt) + int(completion)
    return None


def _call(
    client: OpenAI,
    model: str,
    system_prompt: str,
    task: str,
) -> tuple[str, dict[str, Any]]:
    started = time.monotonic()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": f"{system_prompt}\n\n{task}"},
            {"role": "user", "content": SYNTHETIC_ANSWER},
        ],
        temperature=0,
        max_tokens=2000,
    )
    content = response.choices[0].message.content or ""
    if not content.strip():
        raise RuntimeError("DeepSeek returned an empty response")
    cleaned, stripped_fences = _strip_fences(content)
    usage = response.usage.model_dump() if response.usage else None
    return cleaned, {
        "latency_seconds": round(time.monotonic() - started, 3),
        "finish_reason": response.choices[0].finish_reason,
        "usage": usage,
        "total_tokens": _total_tokens(usage),
        "output_characters": len(cleaned),
        "stripped_markdown_fences": stripped_fences,
    }


def main() -> int:
    env = dotenv_values(REPO_ROOT / ".env")
    required = ("LLM_API_KEY", "LLM_MODEL", "LLM_URL")
    missing = [key for key in required if not env.get(key)]
    if missing:
        raise SystemExit(f"missing values in .env: {', '.join(missing)}")
    for prompt_path in (CHAT_PROMPT, REPORT_PROMPT):
        if not prompt_path.exists():
            raise SystemExit(f"missing {prompt_path}; run the frontend spike prompt test first")

    secrets = _secret_values(dict(env))
    model = str(env["LLM_MODEL"])
    client = OpenAI(
        api_key=str(env["LLM_API_KEY"]),
        base_url=str(env["LLM_URL"]),
        timeout=120,
        max_retries=0,
    )
    RESULTS.mkdir(parents=True, exist_ok=True)
    metadata: dict[str, Any] = {
        "model": model,
        "synthetic_answer_characters": len(SYNTHETIC_ANSWER),
        "calls": [],
    }

    try:
        chat_output, chat_metadata = _call(
            client,
            model,
            CHAT_PROMPT.read_text(encoding="utf-8"),
            CHAT_TASK,
        )
        CHAT_OUTPUT.write_text(f"{chat_output}\n", encoding="utf-8")
        metadata["calls"].append({"name": "chat", **chat_metadata})
        print(
            f"chat: chars={chat_metadata['output_characters']} "
            f"latency={chat_metadata['latency_seconds']}s "
            f"tokens={chat_metadata['total_tokens']}"
        )

        report_output, report_metadata = _call(
            client,
            model,
            REPORT_PROMPT.read_text(encoding="utf-8"),
            REPORT_TASK,
        )
        REPORT_OUTPUT.write_text(f"{report_output}\n", encoding="utf-8")
        metadata["calls"].append({"name": "report", **report_metadata})
        print(
            f"report: chars={report_metadata['output_characters']} "
            f"latency={report_metadata['latency_seconds']}s "
            f"tokens={report_metadata['total_tokens']}"
        )
    except Exception as error:  # noqa: BLE001 - the spike records every failure
        metadata["error"] = _redact(str(error), secrets)
        METADATA.write_text(
            f"{json.dumps(metadata, ensure_ascii=False, indent=2)}\n",
            encoding="utf-8",
        )
        print(f"failed: {type(error).__name__}; no retry")
        return 1

    METADATA.write_text(
        f"{json.dumps(metadata, ensure_ascii=False, indent=2)}\n",
        encoding="utf-8",
    )
    print(f"wrote: {CHAT_OUTPUT}")
    print(f"wrote: {REPORT_OUTPUT}")
    print(f"metadata: {METADATA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
