#!/usr/bin/env python3
"""TASK-018 spike: run a bounded DeepSeek tool loop over GraphDB's LLM tools.

This is spike code, not production code. It reads the tool definitions from
``GET /rest/llm/tool/ttyg/<agent>``, gives them to DeepSeek as function definitions,
forwards tool calls to GraphDB as the read-only application user, stops after a
bounded number of iterations, and aborts the run if a tool call times out so that a
stuck GraphDB query is not followed by more queries.

Question text, answers, tool calls, tool results, errors and timings are written only
to ``backend/tests/evaluation/local-results/`` (git-excluded). The script prints only
question IDs, statuses, iteration counts, failure categories and timings.
"""

from __future__ import annotations

import argparse
import base64
import json
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values
from openai import OpenAI

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
MAX_ITERATIONS = 8
MAX_MODEL_TOOL_CHARS = 20_000
MAX_RECORDED_TOOL_CHARS = 200_000
SYSTEM_PROMPT = """You answer questions about a knowledge graph stored in GraphDB.

Use the provided tools before answering factual questions. Never invent values, names,
dates or causes. For sparql_query, send a complete SPARQL SELECT, CONSTRUCT or DESCRIBE
query in the query field.

Never run an unfiltered full scan over ?s ?p ?o. Do not use text filters such as
FILTER(CONTAINS(STR(?s), ...)) or FILTER(REGEX(STR(?s), ...)) over ?s ?p ?o. Start from a
specific named graph, class or predicate, add selective filters, and always use a small
LIMIT (for example 50) for lists. Use COUNT, SUM or other aggregations for totals.

If the graph does not contain the requested data, say so explicitly. Answer in the
language of the question and keep the final answer concise."""


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


class ToolTimeoutError(RuntimeError):
    """Raised when a GraphDB tool call does not return within the configured timeout."""


class GraphDBTools:
    """Minimal read-only client for the GraphDB LLM tool API."""

    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        agent_id: str,
        *,
        tool_timeout: float = 120,
    ) -> None:
        self.base_url = host.rstrip("/")
        self.tool_url = f"{self.base_url}/rest/llm/tool/ttyg/{agent_id}"
        self.tool_timeout = tool_timeout
        self._call_in_flight = False
        credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
        self.auth_header = f"Basic {credentials}"

    def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        data: bytes | None = None,
        timeout: float = 60,
    ) -> tuple[int, str]:
        request_headers = {"Authorization": self.auth_header}
        if headers:
            request_headers.update(headers)
        request = urllib.request.Request(url, method=method, headers=request_headers, data=data)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.status, response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", "replace")
            return error.code, body

    def openapi_document(self) -> str:
        status, body = self._request(
            "GET",
            self.tool_url,
            headers={"Accept": "application/yaml"},
            timeout=30,
        )
        if status != 200:
            raise RuntimeError(f"tool list request failed with HTTP {status}")
        return body

    def call_tool(self, path: str, arguments: dict[str, Any]) -> tuple[int, str]:
        if self._call_in_flight:
            raise RuntimeError("a GraphDB tool call is already in flight")
        self._call_in_flight = True
        try:
            status, body = self._request(
                "POST",
                f"{self.tool_url}/{path.lstrip('/')}",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/plain;q=0.9, */*;q=0.8",
                },
                data=json.dumps(arguments, ensure_ascii=False).encode(),
                timeout=self.tool_timeout,
            )
            return status, body
        except TimeoutError as error:
            raise ToolTimeoutError("GraphDB tool call timed out") from error
        except urllib.error.URLError as error:
            if isinstance(error.reason, TimeoutError):
                raise ToolTimeoutError("GraphDB tool call timed out") from error
            raise
        finally:
            self._call_in_flight = False


def _openapi_tools(document: str) -> tuple[list[dict[str, Any]], dict[str, str]]:
    specification = yaml.safe_load(document)
    if not isinstance(specification, dict):
        raise RuntimeError("tool list is not an OpenAPI document")
    paths = specification.get("paths")
    if not isinstance(paths, dict) or not paths:
        raise RuntimeError("tool list has no paths")

    tools: list[dict[str, Any]] = []
    tool_paths: dict[str, str] = {}
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        operation = methods.get("post")
        if not isinstance(operation, dict):
            continue
        name = str(operation.get("operationId") or str(path).strip("/").replace("/", "_"))
        request_body = operation.get("requestBody", {})
        content = request_body.get("content", {}) if isinstance(request_body, dict) else {}
        media_type = content.get("application/json", {}) if isinstance(content, dict) else {}
        parameters = media_type.get("schema", {}) if isinstance(media_type, dict) else {}
        if not isinstance(parameters, dict):
            parameters = {"type": "object", "properties": {}}
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": str(operation.get("description") or f"Call {name}"),
                    "parameters": parameters,
                },
            }
        )
        tool_paths[name] = str(path)
    if not tools:
        raise RuntimeError("tool list has no POST operations")
    return tools, tool_paths


def _looks_like_sparql_error(body: str) -> bool:
    lowered = body.lower()
    markers = (
        "malformed query",
        "parse error",
        "lexical error",
        "syntax error",
        "query is not valid",
    )
    return any(marker in lowered for marker in markers)


def _truncate(value: str, limit: int) -> tuple[str, bool]:
    if len(value) <= limit:
        return value, False
    return value[:limit] + "\n...[truncated]", True


def _run_question(
    question: dict[str, Any],
    *,
    client: OpenAI,
    graph: GraphDBTools,
    tools: list[dict[str, Any]],
    tool_paths: dict[str, str],
    model: str,
    max_iterations: int,
    secrets: set[str],
) -> dict[str, Any]:
    started = time.monotonic()
    question_text = str(question["question"])
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question_text},
    ]
    record: dict[str, Any] = {
        "id": str(question["id"]),
        "question": question_text,
        "owner_grade": "pending",
        "started_at": datetime.now(UTC).isoformat(),
        "duration_seconds": 0.0,
        "iterations": 0,
        "completed": False,
        "aborted": False,
        "answer": "",
        "tool_calls": [],
        "failure_modes": [],
        "llm_calls": [],
        "messages": messages,
    }
    seen_calls: dict[tuple[str, str], int] = {}

    for iteration in range(1, max_iterations + 1):
        record["iterations"] = iteration
        print(f"{record['id']}: llm call {iteration}", flush=True)
        call_started = time.monotonic()
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0,
                max_tokens=2000,
            )
        except Exception as error:  # noqa: BLE001 - the spike records every failure
            record["failure_modes"].append(
                {"type": "llm_error", "detail": _redact(str(error), secrets)}
            )
            break

        choice = response.choices[0]
        message = choice.message
        content = message.content or ""
        tool_calls = list(message.tool_calls or [])
        print(
            f"{record['id']}: llm response {iteration}: finish={choice.finish_reason}; "
            f"tool_calls={len(tool_calls)}",
            flush=True,
        )
        record["llm_calls"].append(
            {
                "iteration": iteration,
                "duration_seconds": round(time.monotonic() - call_started, 3),
                "finish_reason": choice.finish_reason,
                "content": _redact(content, secrets),
                "tool_call_names": [call.function.name for call in tool_calls],
                "usage": response.usage.model_dump() if response.usage else None,
            }
        )

        if not tool_calls:
            answer = content.strip()
            record["answer"] = _redact(answer, secrets)
            record["completed"] = bool(answer)
            if not answer:
                record["failure_modes"].append({"type": "empty_answer"})
            if choice.finish_reason == "length":
                record["failure_modes"].append({"type": "llm_length"})
            break

        messages.append(
            {
                "role": "assistant",
                "content": content or None,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in tool_calls
                ],
            }
        )

        stop_loop = False
        abort_question = False
        for call in tool_calls:
            name = call.function.name
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError as error:
                record["failure_modes"].append(
                    {"type": "invalid_tool_arguments", "detail": error.msg}
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps({"error": "invalid tool arguments"}),
                    }
                )
                continue
            if not isinstance(arguments, dict):
                record["failure_modes"].append(
                    {"type": "invalid_tool_arguments", "detail": "arguments are not an object"}
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps({"error": "invalid tool arguments"}),
                    }
                )
                continue

            signature = (name, json.dumps(arguments, sort_keys=True, ensure_ascii=False))
            seen_calls[signature] = seen_calls.get(signature, 0) + 1
            if seen_calls[signature] >= 3:
                record["failure_modes"].append(
                    {
                        "type": "loop",
                        "detail": f"{name} called with identical arguments "
                        f"{seen_calls[signature]} times",
                    }
                )
                stop_loop = True
                break

            path = tool_paths.get(name)
            if path is None:
                record["failure_modes"].append(
                    {"type": "unknown_tool", "detail": f"unknown tool {name}"}
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps({"error": "unknown tool"}),
                    }
                )
                continue

            print(f"{record['id']}: tool {name}", flush=True)
            tool_started = time.monotonic()
            timed_out = False
            try:
                status, body = graph.call_tool(path, arguments)
            except ToolTimeoutError:
                status, body = 0, "tool request timed out"
                timed_out = True
            except Exception as error:  # noqa: BLE001 - the spike records every failure
                status, body = 0, f"tool request failed: {type(error).__name__}"
            tool_duration = round(time.monotonic() - tool_started, 3)
            print(
                f"{record['id']}: tool {name} -> HTTP {status} ({tool_duration}s)",
                flush=True,
            )
            recorded_result, recorded_truncated = _truncate(body, MAX_RECORDED_TOOL_CHARS)
            record["tool_calls"].append(
                {
                    "name": name,
                    "arguments": arguments,
                    "status": status,
                    "duration_seconds": tool_duration,
                    "result_characters": len(body),
                    "result_truncated": recorded_truncated,
                    "result": _redact(recorded_result, secrets),
                }
            )
            if timed_out:
                record["failure_modes"].append(
                    {
                        "type": "tool_timeout",
                        "detail": f"{name} did not return within {graph.tool_timeout}s",
                    }
                )
                record["aborted"] = True
                abort_question = True
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps({"error": "tool call timed out"}),
                    }
                )
                break
            if status != 200:
                failure_type = (
                    "invalid_sparql"
                    if name == "sparql_query" and _looks_like_sparql_error(body)
                    else "tool_error"
                )
                record["failure_modes"].append(
                    {"type": failure_type, "detail": f"{name} returned HTTP {status}"}
                )
            model_result, _ = _truncate(body, MAX_MODEL_TOOL_CHARS)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": _redact(model_result, secrets),
                }
            )

        if stop_loop or abort_question:
            break
        if iteration == max_iterations:
            record["failure_modes"].append(
                {
                    "type": "iteration_limit",
                    "detail": f"no final answer after {max_iterations} iterations",
                }
            )

    record["duration_seconds"] = round(time.monotonic() - started, 3)
    return _redact_object(record, secrets)


def _summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    failure_counts: dict[str, int] = {}
    for record in records:
        for failure in record["failure_modes"]:
            failure_type = str(failure["type"])
            failure_counts[failure_type] = failure_counts.get(failure_type, 0) + 1
    completed = sum(1 for record in records if record["completed"])
    return {
        "questions_run": len(records),
        "completed": completed,
        "failed": len(records) - completed,
        "aborted": sum(1 for record in records if record.get("aborted")),
        "failure_mode_counts": dict(sorted(failure_counts.items())),
    }


def _write_json(path: Path, run: dict[str, Any]) -> None:
    path.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_markdown(path: Path, run: dict[str, Any]) -> None:
    summary = run["summary"]
    modes = ", ".join(f"{name} x{count}" for name, count in summary["failure_mode_counts"].items())
    lines = [
        f"# TASK-018 spike run — {run['run_id']}",
        "",
        f"- Agent: `{run['agent_id']}`",
        f"- Repository: `{run['repository']}` (provisional knowledge graph)",
        f"- Model: `{run['model']}`",
        f"- Iteration bound: {run['max_iterations']}",
        f"- Tool timeout: {run['tool_timeout_seconds']} s",
        f"- Questions run: {summary['questions_run']}",
        f"- Completed: {summary['completed']}",
        f"- Failed: {summary['failed']}",
        f"- Aborted: {summary['aborted']}",
        f"- Failure modes: {modes or 'none'}",
        "",
        "The knowledge graph and question set are provisional. The evaluation must be "
        "repeated on the final knowledge graph.",
        "",
    ]
    for record in run["questions"]:
        modes = ", ".join(sorted({str(failure["type"]) for failure in record["failure_modes"]}))
        lines.extend(
            [
                f"## {record['id']}",
                "",
                f"**Question:** {record['question']}",
                "",
                f"**Answer:** {record['answer'] or '(empty)'}",
                "",
                f"**Status:** {'completed' if record['completed'] else 'failed'}",
                "",
                f"**Iterations:** {record['iterations']}",
                "",
                f"**Tool calls:** {len(record['tool_calls'])}",
                "",
                f"**Failure modes:** {modes or 'none'}",
                "",
                f"**Duration:** {record['duration_seconds']} s",
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
    parser.add_argument("--max-iterations", type=int, default=MAX_ITERATIONS)
    parser.add_argument("--tool-timeout", type=float, default=60)
    parser.add_argument("--agent-id", default=AGENT_ID)
    parser.add_argument(
        "--question-ids",
        default=",".join(DEFAULT_QUESTION_IDS),
        help="Comma-separated IDs; defaults to the eight development questions.",
    )
    args = parser.parse_args()
    if not 0 < args.tool_timeout <= 60:
        raise SystemExit("--tool-timeout must be greater than 0 and at most 60 seconds")
    if args.max_iterations < 1:
        raise SystemExit("--max-iterations must be at least 1")

    env = dotenv_values(REPO_ROOT / ".env")
    required = (
        "LLM_API_KEY",
        "LLM_MODEL",
        "LLM_URL",
        "KG_HOST",
        "KG_REPOSITORY",
        "KG_USER",
        "KG_PASSWORD",
    )
    missing = [key for key in required if not env.get(key)]
    if missing:
        raise SystemExit(f"missing values in .env: {', '.join(missing)}")
    repository = str(env["KG_REPOSITORY"])
    model = str(env["LLM_MODEL"])
    secrets = _secret_values(dict(env))

    question_ids = tuple(item.strip() for item in args.question_ids.split(",") if item.strip())
    questions = _load_questions(args.questions, question_ids)
    graph = GraphDBTools(
        host=str(env["KG_HOST"]),
        user=str(env["KG_USER"]),
        password=str(env["KG_PASSWORD"]),
        agent_id=args.agent_id,
        tool_timeout=args.tool_timeout,
    )
    tools, tool_paths = _openapi_tools(graph.openapi_document())
    client = OpenAI(
        api_key=str(env["LLM_API_KEY"]),
        base_url=str(env["LLM_URL"]),
        timeout=120,
        max_retries=0,
    )

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run: dict[str, Any] = {
        "task": "TASK-018",
        "run_id": run_id,
        "started_at": datetime.now(UTC).isoformat(),
        "agent_id": args.agent_id,
        "repository": repository,
        "model": model,
        "question_ids": list(question_ids),
        "max_iterations": args.max_iterations,
        "tool_timeout_seconds": args.tool_timeout,
        "tool_names": sorted(tool_paths),
        "questions": [],
    }
    args.results_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.results_dir / f"task-018-{run_id}.json"
    markdown_path = args.results_dir / f"task-018-{run_id}.md"
    print(
        f"Running {len(questions)} questions against {repository} "
        f"with {len(tools)} GraphDB tools; max {args.max_iterations} iterations."
    )

    for question in questions:
        record = _run_question(
            question,
            client=client,
            graph=graph,
            tools=tools,
            tool_paths=tool_paths,
            model=model,
            max_iterations=args.max_iterations,
            secrets=secrets,
        )
        run["questions"].append(record)
        run["summary"] = _summary(run["questions"])
        run["finished_at"] = datetime.now(UTC).isoformat()
        _write_json(json_path, run)
        _write_markdown(markdown_path, run)
        status = "completed" if record["completed"] else "failed"
        modes = ",".join(sorted({str(item["type"]) for item in record["failure_modes"]}))
        print(
            f"{record['id']}: {status}; iterations={record['iterations']}; "
            f"tool_calls={len(record['tool_calls'])}; failures={modes or '-'}; "
            f"seconds={record['duration_seconds']}"
        )
        if record.get("aborted"):
            run["aborted"] = True
            run["abort_reason"] = "GraphDB tool call timed out; no further queries sent"
            run["finished_at"] = datetime.now(UTC).isoformat()
            _write_json(json_path, run)
            _write_markdown(markdown_path, run)
            print("Run aborted: GraphDB tool call timed out; no further queries sent.")
            break

    summary = run["summary"]
    modes = ", ".join(f"{name} x{count}" for name, count in summary["failure_mode_counts"].items())
    print(
        f"Finished: {summary['questions_run']} questions; completed={summary['completed']}; "
        f"failed={summary['failed']}; failure modes={modes or 'none'}"
    )
    print(f"Detailed results: {json_path}")
    print(f"Owner report: {markdown_path}")
    return 2 if run.get("aborted") else 0


if __name__ == "__main__":
    raise SystemExit(main())
