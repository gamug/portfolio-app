#!/usr/bin/env python3
"""TASK-018 spike: ask the eight development questions through GraphDB's Workbench chat API.

This is spike code, not production code. It follows the accepted ``adr-010``: create a
Talk to Your Graph conversation with ``POST /rest/chat/chats``, then ask the question
with ``POST /rest/chat/chats/question`` as the read-only application user. Calls are
sequential and each question has a total deadline. The run stops at the first timeout
or error; it never retries and never sends the remaining questions.

Question text, answers, latency, usage and errors are written only to
``backend/tests/evaluation/local-results/`` (git-excluded). The script prints only
question IDs, status, latency, token counts and error categories.
"""

from __future__ import annotations

import argparse
import base64
import json
import statistics
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QUESTIONS = REPO_ROOT / "backend/tests/evaluation/questions_dev_batch1.json"
DEFAULT_RESULTS_DIR = REPO_ROOT / "backend/tests/evaluation/local-results"
AGENT_ID = "2689c209-4f97-4a07-bfd9-39d3cdd5cf92"
DEFAULT_QUESTION_IDS = (
    "q-001",
    "q-005",
    "q-006",
    "q-012",
    "q-017",
    "q-020",
    "q-023",
    "q-025",
)
PER_QUESTION_TIMEOUT = 120.0
TZ_OFFSET = -300


class ChatAPIError(RuntimeError):
    """A failed chat API call, recorded with a machine-readable category."""

    def __init__(self, kind: str, detail: str = "", status: int | None = None) -> None:
        super().__init__(detail or kind)
        self.kind = kind
        self.detail = detail
        self.status = status


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


def _redact_object(value: Any, secrets: set[str]) -> Any:
    if isinstance(value, str):
        return _redact(value, secrets)
    if isinstance(value, list):
        return [_redact_object(item, secrets) for item in value]
    if isinstance(value, dict):
        return {key: _redact_object(item, secrets) for key, item in value.items()}
    return value


def _extract_answer(payload: dict[str, Any]) -> str | None:
    messages = payload.get("messages")
    if isinstance(messages, list):
        for message in reversed(messages):
            if not isinstance(message, dict):
                continue
            value = message.get("message")
            if isinstance(value, str) and value.strip():
                return value
    for key in ("answer", "message", "response"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _extract_usage(payload: dict[str, Any]) -> dict[str, Any] | None:
    usage = payload.get("usage")
    if isinstance(usage, dict):
        return usage
    messages = payload.get("messages")
    if isinstance(messages, list):
        for message in reversed(messages):
            if isinstance(message, dict) and isinstance(message.get("usage"), dict):
                return message["usage"]
    return None


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


class ChatClient:
    """Minimal client for the two Workbench chat endpoints."""

    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        agent_id: str,
        *,
        per_question_timeout: float,
    ) -> None:
        base_url = host.rstrip("/")
        self.chat_url = f"{base_url}/rest/chat/chats"
        self.question_url = f"{base_url}/rest/chat/chats/question"
        self.agent_id = agent_id
        self.per_question_timeout = per_question_timeout
        credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
        self.auth_header = f"Basic {credentials}"

    def _post_json(
        self,
        url: str,
        payload: dict[str, Any],
        deadline: float,
    ) -> dict[str, Any]:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ChatAPIError("timeout", "per-question deadline exceeded")
        request = urllib.request.Request(
            url,
            method="POST",
            headers={
                "Authorization": self.auth_header,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            data=json.dumps(payload, ensure_ascii=False).encode(),
        )
        try:
            with urllib.request.urlopen(request, timeout=remaining) as response:
                body = response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", "replace")
            raise ChatAPIError("http_error", body[:1000], error.code) from error
        except TimeoutError as error:
            raise ChatAPIError("timeout", "request timed out") from error
        except urllib.error.URLError as error:
            if isinstance(error.reason, TimeoutError):
                raise ChatAPIError("timeout", "request timed out") from error
            raise ChatAPIError("network_error", str(error)) from error
        try:
            document = json.loads(body)
        except json.JSONDecodeError as error:
            raise ChatAPIError("invalid_json", error.msg) from error
        if not isinstance(document, dict):
            raise ChatAPIError("invalid_response", "response is not a JSON object")
        return document

    def create_chat(self, question: str, deadline: float) -> tuple[str, dict[str, Any]]:
        response = self._post_json(
            self.chat_url,
            {"agentId": self.agent_id, "question": question, "tzOffset": TZ_OFFSET},
            deadline,
        )
        conversation_id = response.get("conversationId")
        if not isinstance(conversation_id, str) or not conversation_id:
            raise ChatAPIError("missing_conversation_id", "response has no conversationId")
        return conversation_id, response

    def ask(
        self,
        conversation_id: str,
        question: str,
        deadline: float,
    ) -> tuple[str, dict[str, Any]]:
        response = self._post_json(
            self.question_url,
            {
                "agentId": self.agent_id,
                "conversationId": conversation_id,
                "question": question,
                "tzOffset": TZ_OFFSET,
            },
            deadline,
        )
        answer = _extract_answer(response)
        if answer is None:
            raise ChatAPIError("missing_answer", "response has no answer text")
        return answer, response


def _run_question(
    question: dict[str, Any],
    *,
    client: ChatClient,
    secrets: set[str],
) -> dict[str, Any]:
    started = time.monotonic()
    deadline = started + client.per_question_timeout
    question_text = str(question["question"])
    record: dict[str, Any] = {
        "id": str(question["id"]),
        "question": question_text,
        "owner_grade": "pending",
        "started_at": datetime.now(UTC).isoformat(),
        "latency_seconds": None,
        "completed": False,
        "aborted": False,
        "conversation_id": None,
        "answer": "",
        "usage": None,
        "total_tokens": None,
        "errors": [],
        "responses": [],
    }
    try:
        conversation_id, create_response = client.create_chat(question_text, deadline)
        record["conversation_id"] = conversation_id
        record["responses"].append({"call": "create_chat", "response": create_response})
        print(f"{record['id']}: conversation created", flush=True)
        answer, answer_response = client.ask(conversation_id, question_text, deadline)
        record["responses"].append({"call": "ask", "response": answer_response})
        record["answer"] = _redact(answer, secrets)
        usage = _extract_usage(answer_response)
        record["usage"] = _redact_object(usage, secrets)
        record["total_tokens"] = _total_tokens(usage)
        record["completed"] = True
    except ChatAPIError as error:
        record["errors"].append(
            {
                "type": error.kind,
                "status": error.status,
                "detail": _redact(error.detail, secrets),
            }
        )
        record["aborted"] = True
    except Exception as error:  # noqa: BLE001 - the spike records every failure
        record["errors"].append(
            {"type": "unexpected_error", "detail": _redact(str(error), secrets)}
        )
        record["aborted"] = True
    record["latency_seconds"] = round(time.monotonic() - started, 3)
    return _redact_object(record, secrets)


def _summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    attempted = len(records)
    completed = sum(1 for record in records if record["completed"])
    error_counts: dict[str, int] = {}
    for record in records:
        for error in record["errors"]:
            error_type = str(error["type"])
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
    latencies = [
        float(record["latency_seconds"])
        for record in records
        if isinstance(record["latency_seconds"], (int, float))
    ]
    tokens = [
        int(record["total_tokens"]) for record in records if isinstance(record["total_tokens"], int)
    ]
    return {
        "questions_run": attempted,
        "answered": completed,
        "errors": attempted - completed,
        "error_type_counts": dict(sorted(error_counts.items())),
        "median_latency_seconds": round(statistics.median(latencies), 3) if latencies else None,
        "total_tokens": sum(tokens) if tokens else None,
        "median_tokens_per_question": round(statistics.median(tokens), 1) if tokens else None,
    }


def _write_json(path: Path, run: dict[str, Any]) -> None:
    path.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_markdown(path: Path, run: dict[str, Any]) -> None:
    summary = run["summary"]
    error_types = ", ".join(
        f"{name} x{count}" for name, count in summary["error_type_counts"].items()
    )
    lines = [
        f"# TASK-018 chat API spike — {run['run_id']}",
        "",
        f"- Agent: `{run['agent_id']}`",
        f"- Repository: `{run['repository']}` (provisional knowledge graph)",
        f"- Questions run: {summary['questions_run']}",
        f"- Answered: {summary['answered']}",
        f"- Errors: {summary['errors']}",
        f"- Error types: {error_types or 'none'}",
        f"- Median latency: {summary['median_latency_seconds']} s",
        f"- Total tokens: {summary['total_tokens']}",
        f"- Median tokens per question: {summary['median_tokens_per_question']}",
        "",
        "The knowledge graph and question set are provisional. The evaluation must be "
        "repeated on the final knowledge graph.",
        "",
    ]
    for record in run["questions"]:
        errors = ", ".join(str(error["type"]) for error in record["errors"]) or "none"
        lines.extend(
            [
                f"## {record['id']}",
                "",
                f"**Question:** {record['question']}",
                "",
                f"**Answer:** {record['answer'] or '(empty)'}",
                "",
                f"**Status:** {'answered' if record['completed'] else 'failed'}",
                "",
                f"**Latency:** {record['latency_seconds']} s",
                "",
                f"**Tokens:** {record['total_tokens']}",
                "",
                f"**Usage:** {json.dumps(record['usage'], ensure_ascii=False)}",
                "",
                f"**Errors:** {errors}",
                "",
                "**Owner grade:** pending",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def _load_questions(path: Path, question_ids: tuple[str, ...]) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise RuntimeError("question file is not a list")
    by_id = {str(item["id"]): item for item in data if isinstance(item, dict) and "id" in item}
    missing = [question_id for question_id in question_ids if question_id not in by_id]
    if missing:
        raise RuntimeError(f"missing question IDs: {', '.join(missing)}")
    if len(question_ids) != len(set(question_ids)):
        raise RuntimeError("question IDs contain duplicates")
    return [by_id[question_id] for question_id in question_ids]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--agent-id", default=AGENT_ID)
    parser.add_argument("--timeout", type=float, default=PER_QUESTION_TIMEOUT)
    parser.add_argument(
        "--question-ids",
        default=",".join(DEFAULT_QUESTION_IDS),
        help="Comma-separated IDs; defaults to the eight development questions.",
    )
    args = parser.parse_args()
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than 0 seconds")

    env = dotenv_values(REPO_ROOT / ".env")
    required = ("KG_HOST", "KG_REPOSITORY", "KG_USER", "KG_PASSWORD")
    missing = [key for key in required if not env.get(key)]
    if missing:
        raise SystemExit(f"missing values in .env: {', '.join(missing)}")
    repository = str(env["KG_REPOSITORY"])
    secrets = _secret_values(dict(env))

    question_ids = tuple(item.strip() for item in args.question_ids.split(",") if item.strip())
    questions = _load_questions(args.questions, question_ids)
    client = ChatClient(
        host=str(env["KG_HOST"]),
        user=str(env["KG_USER"]),
        password=str(env["KG_PASSWORD"]),
        agent_id=args.agent_id,
        per_question_timeout=args.timeout,
    )

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run: dict[str, Any] = {
        "task": "TASK-018",
        "mode": "workbench-chat-api",
        "run_id": run_id,
        "started_at": datetime.now(UTC).isoformat(),
        "agent_id": args.agent_id,
        "repository": repository,
        "question_ids": list(question_ids),
        "per_question_timeout_seconds": args.timeout,
        "questions": [],
    }
    args.results_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.results_dir / f"task-018-chat-{run_id}.json"
    markdown_path = args.results_dir / f"task-018-chat-{run_id}.md"
    print(
        f"Running {len(questions)} questions against {repository} through the chat API; "
        f"per-question timeout {args.timeout} s."
    )

    for question in questions:
        record = _run_question(question, client=client, secrets=secrets)
        run["questions"].append(record)
        run["summary"] = _summary(run["questions"])
        run["finished_at"] = datetime.now(UTC).isoformat()
        _write_json(json_path, run)
        _write_markdown(markdown_path, run)
        status = "answered" if record["completed"] else "failed"
        errors = ",".join(str(error["type"]) for error in record["errors"]) or "-"
        print(
            f"{record['id']}: {status}; latency={record['latency_seconds']}s; "
            f"tokens={record['total_tokens']}; errors={errors}"
        )
        if record["aborted"]:
            run["aborted"] = True
            run["abort_reason"] = "chat API call failed; stopped without retrying"
            run["finished_at"] = datetime.now(UTC).isoformat()
            _write_json(json_path, run)
            _write_markdown(markdown_path, run)
            print("Run stopped after an error; no further questions were sent.")
            break

    summary = run["summary"]
    print(
        f"Finished: questions_run={summary['questions_run']}; "
        f"answered={summary['answered']}; errors={summary['errors']}; "
        f"median_latency={summary['median_latency_seconds']}s; "
        f"total_tokens={summary['total_tokens']}"
    )
    print(f"Detailed results: {json_path}")
    print(f"Owner report: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
