# Changelog

## Usage

Record completed Work Items and their associated tasks here after verification. Include the relevant WI/task identifiers, a concise summary of the delivered change, and the verification result. Keep active work in `TASKS.md`; this file is the historical record of completed work.

## 2026-11-05

### WI-001 — Run the discovery skill and create PRODUCT.md (TASK-001 to TASK-004)

- Delivered the six-phase discovery in `docs/PRODUCT.md` (nine use cases, 34 product requirements, nine ADRs, seven risks) and the seeded `adr.md`.
- Verification: `validate_discovery.py docs/PRODUCT.md` passes; approved by Gabriel Munera (gamug) on 2026-11-05; all nine ADRs in `adr.md` are `Accepted`.

### WI-002 — Create config.yaml (TASK-005 to TASK-008)

- Built `config.yaml` with 41 keys; every value and source is recorded in the `Configuration Decisions` table of `docs/PRODUCT.md`.
- Verification: `validate_config.py check` passes.

### WI-003 — Render constitution.md and synchronize SDD objects (TASK-009, TASK-010)

- Rendered `.sdd/constitution.md` and created `.sdd/SPEC.md`, `.sdd/PLAN.md`, `.sdd/TASKS.md` and this file from the approved `docs/PRODUCT.md`.
- Verification: `validate_config.py render --verify` passes.

### WI-004 — Create folders and non-programmatic dependencies (TASK-011, TASK-012)

- Removed OpenUI content the project does not use (`docs/` site, `templates/`, `benchmarks/`, `scripts/`, `shared/`, `assets/`, `.changeset/` and project meta files); kept `packages/`, `examples/`, `spec/`, `LICENSE` and the workspace files as reference. Created `backend/app`, `backend/tests/fixtures`, `frontend/src`, `.env.example`, `.python-version`, `.nvmrc`, `.vscode/`, a project `README.md`, and `.gitignore` and `.gitattributes` rules.
- Verification: the structure matches `docs/PRODUCT.md` section 6 and `config.yaml`; no application source code was added.

### WI-005 — Set up the system environment (TASK-013, TASK-014)

- Added the devcontainer (`.devcontainer/Dockerfile`, `devcontainer.json`: Python 3.12, Node.js 22.12, pnpm 10.33.0, uv 0.12.1, `host.docker.internal` mapped), `backend/pyproject.toml` and `backend/uv.lock`, `frontend/package.json`, `pnpm-lock.yaml`, and the ruff, mypy, pytest, ESLint, Prettier, tsc and Vitest configuration, with one baseline environment test per side.
- Changed the six `config.yaml` commands that used `uv run --project backend` to `--directory backend` (and `ruff check .`, `mypy app`), because the pytest and mypy settings in `backend/pyproject.toml` are only read from that directory; recorded in `docs/PRODUCT.md` and the constitution re-rendered.
- Verification: in the built image, from a clean copy of the project, `uv sync --locked` and `pnpm install --frozen-lockfile` succeed; pytest (5 passed), Vitest (2 passed), ruff, ESLint, `ruff format --check`, Prettier, mypy and tsc all pass; GraphDB answers at `http://host.docker.internal:7200`. The devcontainer CLI parses `devcontainer.json`; opening it in VS Code was not exercised. No secrets are committed.

### WI-006 — Automate environment reproduction (TASK-015, TASK-016)

- Added `scripts/init.sh` (prerequisite checks with actionable errors, `.env` creation without overwriting, locked installs, git hooks, baseline checks), `.pre-commit-config.yaml` (gitleaks, ruff, mypy, ESLint, Prettier, tsc, and a commit-message hook for Conventional Commits with the `[FR][WI][TASK]` suffix), `scripts/check_commit_msg.py` with tests (since moved to `backend/app/devtools/check_commit_msg.py`), `.github/workflows/validators.yml` (gitleaks, ruff, mypy, ESLint and Prettier, tsc, pytest, Vitest, in the configured order), `.gitleaks.toml`, gitleaks 8.30.1 in the devcontainer image, and the Setup, Commands, Recovery and commit sections of `README.md`.
- Verification (built image, clean copy in a fresh git repository): `scripts/init.sh` completes and runs 14 backend tests, 2 frontend tests and all static checks; with `uv` missing it stops with `ERROR: uv is not installed or not on PATH` and a fix; the commit hook rejects `bad message` and accepts a conforming subject; `pre-commit run --all-files` passes all hooks; gitleaks passes the clean tree and catches planted secrets. `.gitleaks.toml` allowlists one upstream reference file (an embedded PostHog project key in `packages/lang-core/src/telemetry/shared.ts`). The first run of the CI workflow on PR #1 passed all seven gates.

## 2026-11-06

### PR #1 review remediation (FR-001, WI-004 to WI-006)

- Moved `packages/`, `examples/`, `spec/` and the OpenUI root workspace files to `reference/`; guarded every job of the nine inherited workflows with a repository condition; pinned the `validators` actions by commit SHA; replaced the pull request template; set the executable bit on the scripts; added an erratum for moved and removed paths to `adr.md`.
- Moved the commit-subject check to `backend/app/devtools` (under ruff, mypy and the mirrored tests); added a CI job that checks every commit subject of a pull request; added `check_consistency.py`, run by pytest, for `config.yaml` commands, tool pins, cited paths and the `CLAUDE.md` template; `scripts/init.sh` creates `CLAUDE.md` from a tracked template (`config.yaml` `agent.init_command_if_missing`); added `scripts/sdd-verify.sh` (validators pinned to a `gamug/sdd-template` commit).
- Corrected the acceptance-criteria traceability (WI-007, WI-010, WI-013, WI-014 and per-task criteria), labelled the derived criteria, fixed the blank source in `SPEC.md`, added TASK-035 (health endpoint) and recorded the deviations from the approved `docs/PRODUCT.md` in `PLAN.md`.
- Verification (built devcontainer image, clean copy of the project, commit `2ff6a405`): `scripts/init.sh` completes and creates `CLAUDE.md`; 23 backend tests and 2 frontend tests pass; ruff, mypy, ESLint, Prettier and tsc pass; the commit-subject command rejects a bad subject and the `commit-msg` hook rejects one; `scripts/sdd-verify.sh` passes. On GitHub, the `validate` and `commit-subjects` jobs passed on that commit and none of the guarded OpenUI workflows ran.

### PR #1 review, round 2 (FR-001, WI-004 to WI-006)

- The commit-subject CI step now runs with `set -euo pipefail`, no longer drops merge commits, and `check_commit_msg.py --stdin` fails on empty input, so a failing `git log` cannot pass (reproduced before the fix). Added `check_sdd.py` (traceability of SPEC, PLAN and TASKS: criteria defined and sourced, no orphans, each Work Item's criteria equal to the union of its tasks, parents, dependencies and checkboxes) and extended `check_consistency.py` to the SDD documents, `config.yaml`, the PR template and the `CLAUDE.md` template, with a map of renamed files and one drift test per version pin. Added ShellCheck (devcontainer image, pre-commit hook, `shellcheck` CI job).
- By decision of the project owners: `TASK-035` (health endpoint) and `AC-ENV-01` were removed because no functional requirement covers them; the GitHub ruleset `main protection` stays as it is (blocks deletion and force-pushes only); pull requests are merged with a merge commit. These and the added CI jobs are recorded in the deviations table of `PLAN.md` and in the README. Fixed "from derived from" in 10 lines of `SPEC.md`.
- Verification (built devcontainer image, clean copy of the project): `scripts/init.sh` completes; 43 backend tests, 2 frontend tests, ruff, mypy, ESLint, Prettier and tsc pass; `pre-commit run --all-files` passes all eight hooks including ShellCheck 0.9.0; `check_sdd.py` and `check_consistency.py` pass; the fixed commit-subject step exits 1 with "No commit subjects received" when `git log` fails; `scripts/sdd-verify.sh` passes. The new traceability check also found a leftover `AC-ENV-01` reference in `TASK-034` right after the removal, which was fixed.

### PR #1 review, round 3 (FR-001, WI-004 to WI-006)

- **Privacy:** the install script of `@openuidev/lang-core` only sends installation telemetry to a third party (reproduced with the package's debug switch). It is no longer allowed to run (`frontend/pnpm-workspace.yaml`, `frontend/package.json`), and `DO_NOT_TRACK=1` and `OPENUI_TELEMETRY_DISABLED=1` are set in the devcontainer, in `validators.yml` and in `scripts/init.sh`. `check_consistency.py` has a `privacy` check with five regression tests. README section "Privacy".
- **ShellCheck** is pinned like the other tools: version 0.11.0 with SHA-256 checksums in the Dockerfile (x86_64 and aarch64) and in CI, and in the pin check (3 new drift tests); CI no longer uses the runner's copy.
- **Owners' decisions:** the evaluation question set lives in `backend/tests/evaluation/` (README with format and the public-repository rule, format test skipped until `questions.json` exists; `config.yaml` `project_structure.tests` updated); squash and rebase merging were disabled in the repository settings (merge commit only); `LICENSE` keeps the upstream notice and adds `Copyright (c) 2026 gamug and dova`. Each is listed in the deviations table of `PLAN.md`.
- Reworded the `TASKS.md` status sentence and the "disabled in GitHub" row (four of nine workflows were disabled; the other five never registered).
- Verification (rebuilt devcontainer image, clean copy of the project): 51 backend tests pass and 1 is skipped (the evaluation format test); `pre-commit run --all-files` passes all eight hooks with ShellCheck 0.11.0; `check_sdd.py`, `check_consistency.py` and `scripts/sdd-verify.sh` pass. Install with the telemetry script allowed printed the payload (before); with the fix, 0 telemetry lines and pnpm reports `Ignored build scripts: @openuidev/lang-core@1.1.0` (after); `scripts/init.sh` leaves no OpenUI state in the home directory.

## 2026-11-06 (re-approval)

### docs/PRODUCT.md 1.1.0 (FR-001, WI-001)

- Re-approved by Gabriel Múnera (gamug) on 2026-11-06 (first approval 2026-11-05, hash `sha256:726da27986300e4a44ceddc9c2dcab7d610aad207fa0f82abb836d58b91deffe`). The sections now state what the implementation and the owners' decisions made true: the verification commands (no health endpoint), `scripts/init.sh` creating `CLAUDE.md`, the `.sdd/CHANGELOG.md` amendment log, the guarded and disabled OpenUI workflows, the additional CI jobs and repository checks, merge commit with squash and rebase disabled, the ruleset that blocks only deletion and force-pushes (accepted), the telemetry switch-off, the MIT license with the project's copyright line, the location of the evaluation question set, the derived acceptance criteria, and the `reference/` path of the FastAPI example in the stack table. The ADR blocks in section 5 were not changed.
- Added `backend/tests/evaluation/GUIDE.md`: a guide for gamug and dova to prepare the evaluation questions, with the question-count estimate (about 100 recommended, 60 minimum) and the decisions they still have to agree.
- Verification: `scripts/sdd-verify.sh` passes (the discovery validator without `--draft`, `validate_config.py check`, `render --verify`).

## 2026-11-06 (spike)

### TASK-017 — Read-only GraphDB user and tool source (WI-007, AC-SPIKE-01)

- Decided the tool source is `ttyg`, using the existing Talk to Your Graph agent `reportes-piloto` (`d832d4d0-5ec3-4953-bd39-cb2f0691b7d7`) on the `portfolio_test` repository (the knowledge graph is not final). No YAML tool configuration was needed, and neither `config.yaml` nor a dependency was changed.
- Verified against GraphDB 11.5.1 at `KG_HOST`: `GET /rest/repositories` lists `portfolio_test` as `RUNNING`; `GET /rest/llm/tool/ttyg/d832d4d0-5ec3-4953-bd39-cb2f0691b7d7` returns `/now` and `/sparql_query`. As `KG_USER`, login authorities are `READ_REPO_portfolio_test` and `ROLE_USER`; a SPARQL read succeeds; empty and isolated-graph writes return `403`; without credentials, reads and writes return `401`; the isolated probe graph is absent.
- Verification: `check_sdd.py` passes after recording the result; WI-007 remains open for TASK-018 and TASK-019.

## 2026-11-07 (follow-up to WI-006)

### TASK-015 — AGENTS.md for OpenCode agents and the delivery rule (WI-006, AC-FR001-06)

- `scripts/init.sh` now also creates a local, untracked `AGENTS.md` from `scripts/templates/CLAUDE.md.template` when it is missing, so OpenCode agents follow the same SDD instructions as `CLAUDE.md`; `.gitignore` lists it and the README documents it.
- The template gains the delivery rule (branch `sdd/<WI>-<TASK-ids>`, traced commit, push, PR to `main`, no merge, stay inside the assigned task files) and the rule to never `source` `.env`. This is a process improvement requested by the project owners; no requirement or acceptance criterion changed.
- Verification: `CLAUDE.md` and `AGENTS.md` are byte-identical to the template; `check_consistency.py` passes.
- `.gitleaks.toml` allowlists the git-ignored local `.env` and `.pnpm-store/`, which the pre-push working-tree scan reads and which blocked every push once `.env` held real credentials. The staged-files scan (pre-commit) is unchanged and still blocks any secret that is staged.

## 2026-11-07 (spike)

### TASK-018 — DeepSeek tool loop (WI-007, AC-SPIKE-02)

- Ran the bounded loop with the 8 development questions on the provisional `portfolio_test` KG. The required `/rest/llm/tool/ttyg/.../sparql_query` endpoint timed out on every call, so the official run produced no final answers and recorded tool-timeout and iteration-limit failures. A local-only diagnostic through the agent's legacy `sparql_query` endpoint completed 7 of 8 questions, confirming the loop and DeepSeek tool calling work; the blocker is the external tool endpoint or the agent configuration.
- Added `backend/spikes/task_018_tool_loop.py` (spike-only, not production code). It reads the tools from `GET /rest/llm/tool/ttyg/{agentId}`, bounds iterations, records timings and failure modes, and writes detailed output only to the git-excluded local-results directory under `backend/tests/evaluation/`.
- Owner grade: pending. The KG and question set are provisional; repeat the evaluation on the final KG after the GraphDB endpoint is fixed.
- Verification: `ruff` passes; `check_sdd.py` and `check_consistency.py` pass; no question text, answers, graph data or local result files are committed.

## 2026-11-07 (spike rerun)

### TASK-018 — DeepSeek tool loop rerun (WI-007, AC-SPIKE-02)

- Re-ran the official loop with the DeepSeek-based agent `reportes-piloto-ds` on the provisional `portfolio_test` KG, using the same 8 development questions. Preflight `/now` and a one-row `sparql_query` succeeded; 1 of the 8 questions then ran and the model-generated `sparql_query` exceeded the 60 s per-tool timeout. The run aborted without sending further queries and produced no final answers. Failure mode: tool timeout.
- Hardened `backend/spikes/task_018_tool_loop.py`: the per-tool timeout is capped at 60 s, an in-flight guard prevents overlapping tool calls, the run aborts on the first tool timeout, and the system prompt forbids unfiltered `?s ?p ?o` scans and requires a small `LIMIT`.
- Owner grade: pending. The KG and question set are provisional; repeat on the final KG after query generation is fixed.
- Verification: `ruff` passes; `check_sdd.py` and `check_consistency.py` pass; no question text, answers, graph data or local results are committed.

## 2026-11-07 (ADR proposal)

### TASK-018 — Proposed `adr-010` after the spike (WI-007, AC-SPIKE-02)

- Added `adr-010` (`Proposed`) to `adr.md`: forward the question to the Talk to Your Graph agent through the Workbench chat API, with the `adr-007` tool loop as a fallback. Nothing is implemented and `adr-007` stays `Accepted` until the project owners accept or reject `adr-010`.
- TASK-018 stays open; the PR #5 branch is not touched by this change.
- Verification: `check_sdd.py` and `check_consistency.py` pass; no question text, answers or graph data are included.

## 2026-11-07 (ADR acceptance)

### TASK-018 — Accept adr-010 and supersede adr-007 (WI-007, AC-SPIKE-02)

- Accepted `adr-010` by dova on 2026-11-07; it supersedes `adr-007`. The `adr-007` tool loop is kept as a selectable fallback.
- TASK-018 stays unchecked. No question text, answers or graph data are included.
- Verification: `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-07 (chat API spike)

### TASK-018 — Chat API spike (WI-007, AC-SPIKE-02)

- Ran the accepted `adr-010` path through the Workbench chat API with the DeepSeek-based agent `reportes-piloto-ds` on the provisional `portfolio_test` KG. All 8 development questions returned an answer; errors 0; median latency 25.808 s; total tokens 1,188,318 (median 136,779.5 per question). The `adr-007` tool loop remains the selectable fallback.
- Added `backend/spikes/task_018_chat_api.py`; the earlier tool-loop script is unchanged as the fallback.
- TASK-018 is marked done. Owner grade: pending. The KG and question set are provisional; repeat on the final KG.
- Verification: `ruff`, `check_sdd.py` and `check_consistency.py` pass; no question text, answers, graph data or local results are committed.

## 2026-11-07 (OpenUI spike)

### TASK-019 — OpenUI generation, chat controls and offline export (WI-007, AC-SPIKE-03..06)

- **AC-SPIKE-03 pass:** the locally generated OpenUI chat and report prompts were used for two short DeepSeek calls; 2 of 2 outputs parsed without errors.
- **AC-SPIKE-04 pass:** the react-ui chat layout accepts custom assistant and user message components, and a relevance toggle and delete action render for each message. Click handlers are wired; no browser-automation dependency was added, so this was verified structurally.
- **AC-SPIKE-05 pass:** the OpenUI renderer and the report were inlined into one HTML file of 3,702,568 bytes (about 3.7 MB) with 0 external references.
- **AC-SPIKE-06 pass:** the report contained a bar chart built from the synthetic answer text, with the expected series and values; no ADR for storing structured tool results is needed.
- Added `backend/spikes/task_019_openui.py` and the prompt/parser, controls and offline-export spikes under `frontend/spikes/`. No product code and no new dependency.
- Failure modes: none for the four checks; AC-SPIKE-04 was verified structurally rather than through browser clicks. Detailed outputs are only in the git-excluded local-results directory under `backend/tests/evaluation/`.
- Verification: `ruff`, `check_sdd.py`, `check_consistency.py`, the frontend spike tests, ESLint and Prettier pass.

## 2026-11-07 (connector)

### TASK-020 — Knowledge-graph connector and answer streaming (WI-008, AC-FR002-01)

- Added the production connector under `backend/app/connector/` and the streaming `POST /api/chat` endpoint in `backend/app/main.py`. The default is the accepted `adr-010` Workbench chat API; `tool_loop` is the bounded `adr-007` fallback behind `KG_CHAT_MODE`.
- Settings load from `.env`; both chat endpoints are checked at startup; each question has a timeout and no retry. The final answer streams in chunks. Tests use mocked HTTP and a fake LLM only.
- One real smoke call returned **OK** with latency **49.096 s** and **148,399 total tokens**. It ran once, with no retries; the answer and usage are only in the git-excluded local-results directory. Question-answer storage remains TASK-021.
- `.env.example` now documents `KG_AGENT_ID`, `KG_CHAT_MODE` and the optional timeout/iteration limits. No dependency was added.
- Verification: `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-07 (question-answer pairs)

### TASK-021 — Convert and store question-answer pairs (WI-008, AC-FR002-01)

- Added the second DeepSeek call that converts a completed answer to OpenUI Lang and a storage boundary with an in-memory implementation. No database schema was changed; TASK-023 will replace the in-memory store with SQLite.
- `POST /api/chat` now converts only after the answer completes, stores the question, raw answer and OpenUI Lang only after a successful conversion, and still streams the raw answer.
- Tests use mocked HTTP and LLM only. One real smoke call returned **OK** with latency **29.03 s**; **128,787** answer tokens plus **15,930** conversion tokens (**144,717** total). It ran once with no retries; the answer and OpenUI output are only in the git-excluded local-results directory.
- The locally generated OpenUI chat prompt is committed as `backend/app/connector/openui_chat_prompt.txt`. No dependency was added.
- Verification: `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-07 (errors and language)

### TASK-022 — Handle errors and follow the analyst's language (WI-008, AC-FR002-02, AC-FR035-01)

- Added a minimal language detector and localized, user-safe error mapping for validation, timeouts, GraphDB, DeepSeek, conversion and storage failures. Raw upstream bodies and internal messages are never returned.
- The detected language instruction is passed to the GraphDB agent, the bounded tool loop and the OpenUI conversion prompt. Failed questions are never stored; tests cover answer, conversion and storage failures.
- Tests use mocked HTTP and LLM only. The optional one-shot Spanish smoke call returned **error** (timeout after **120 s**) and was not retried; no tokens were reported.
- The backend returns a localized error JSON; displaying it visibly remains chat-UI work. No dependency or database schema change.
- Verification: `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-07 (SQLite schema)

### TASK-023 — Create the SQLite schema and migrations (WI-009, AC-FR005-03)

- Added the approved four-table schema for sessions, question-answer pairs, relevance marks and reports in `backend/app/storage/migrations/001_initial.sql`, with the agreed indexes, foreign keys and cascade rules.
- Added a stdlib `sqlite3` migration runner using `PRAGMA user_version`, plus the SQLite implementation of the question-answer storage boundary. It replaces the in-memory default and reads `SQLITE_PATH` from `.env`.
- Tests use temporary databases only and cover migration idempotence, reopen persistence, default relevance, relevance updates, session cascades and one current report per session. No dependency was added and no network or API calls are used.
- Verification: `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-07 (thread endpoints)

### TASK-024 — Thread, report and relevance REST endpoints (WI-009, AC-FR005-01, AC-FR005-02)

- Added the adr-005 thread endpoints under `/api/threads`: list, create, get history, update/rename and delete, plus separate current-report get/set and per-pair relevance get/set endpoints.
- The get-history response contains the stored user question and OpenUI Lang assistant message; the report and relevance endpoints stay separate from the thread convention. Deleting a session cascades to its history and report.
- Database failures return a generic user-safe error. Tests use a temporary database through the FastAPI test client, with no network or API calls.
- No schema change and no dependency was added.
- Verification: `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-07 (session list)

### TASK-025 — Build the session list in the frontend (WI-009, AC-FR005-01, AC-FR005-02, AC-FR005-04)

- Added the frontend session list over `restStorage({baseUrl: "/api/threads"})`: create, select, inline rename and delete after explicit confirmation.
- Deleting the active session creates a new empty session and makes it active. Selecting a session loads its history and current report.
- Failed create, rename, delete or select operations show a visible error and leave the visible session, history and report unchanged.
- Tests mock the storage and report backend through the controller; no GraphDB or DeepSeek calls are made. `pnpm` lint, Prettier, `tsc --noEmit`, tests and the production build pass.
- No dependency was added.
- Verification: `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-07 (relevance toggle)

### TASK-026 — Implement the relevance toggle (WI-010, AC-FR003-01, AC-FR003-02)

- Added a relevance client and controller state that loads each pair's stored relevance when a session is opened or switched, defaults new pairs to relevant, and toggles it through the existing relevance endpoints.
- The session view renders one relevance checkbox per answer. A failed update shows an error and leaves the visible relevance state unchanged.
- Tests mock the storage, report and relevance backend; no GraphDB or DeepSeek calls are made.
- No backend change, dependency or schema change was needed.
- Verification: `pnpm` lint, Prettier, `tsc --noEmit`, tests and build pass; backend `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-07 (single pair delete)

### TASK-027 — Delete a single question-answer pair (WI-010, AC-FR028-03, AC-FR028-04)

- Added the single-pair delete endpoint under `/api/threads` and the SQLite delete method; the relevance row cascades and the current report is untouched.
- The session view exposes a delete action per answer with explicit confirmation. Declining changes nothing; confirming removes only that pair's question/answer messages and relevance mark; failure shows an error and leaves the visible state unchanged.
- Tests use Vitest with a mocked backend and pytest against a temporary SQLite database.
- No schema change, dependency, GraphDB or DeepSeek call was needed.
- Verification: `pnpm` lint, Prettier, `tsc --noEmit`, tests and build pass; backend `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-07 (import fix)

### TASK-023 follow-up — Break the connector and storage import cycle (WI-009, FR-005)

- Moved `QuestionAnswerPair` and `QuestionAnswerStore` to the neutral `app.storage.models`; `app.connector.storage` now re-exports the same public names.
- Added a regression test that imports `app.main`, `app.storage` and `app.connector` each in a fresh Python subprocess.
- Verified `uvicorn app.main:app --port 8000` boots and `GET /api/threads/get` returns `200`.
- No schema change, dependency change or task-checkbox change.
- Verification: `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-07 (local run docs)

### TASK-025 follow-up — Document running the app locally (WI-009, FR-005..FR-010)

- Added the README section "Run the app locally" with prerequisites, the backend and frontend commands, the browser URL and troubleshooting for the IPv6-only Vite binding, the harmless `/health` probes and the fixed circular import.
- Set `server.host: true` in `frontend/vite.config.ts` so `pnpm dev` listens on `0.0.0.0` while keeping port 5173 and the `/api` proxy to `http://localhost:8000`.
- Documented what works today (session create/rename/delete, relevance toggle and single-pair delete pending the chat UI) and what is not built yet (no chat input or report panel; the `POST /api/chat` endpoint exists).
- No task checkbox, dependency or schema change.
- Verification: `ruff`, `check_sdd.py`, `check_consistency.py` and the frontend lint, Prettier, `tsc --noEmit` and tests pass.

## 2026-11-07 (report agent)

### TASK-028 — Implement the report agent (WI-011, AC-FR013-01, AC-FR013-04, AC-FR013-05, AC-FR013-06)

- Added skill 1 (relevant pairs to a validated JSON chart plan) and skill 2 (plan to OpenUI Lang) in separate prompt files, `backend/app/report/prompts/report_skill_1_chart_plan_prompt.txt` and `backend/app/report/prompts/report_skill_2_openui_prompt.txt`. Both are marked DRAFT pending the teammate's review; the owner authorized the draft.
- Skill 1 rejects numbers that do not appear in the answer text and skips pairs without numeric content. Skill 2 reuses `backend/app/connector/openui_chat_prompt.txt` as the component reference and validates the complete output with the same OpenUI parser as the TASK-019 spike through `frontend/scripts/validate-openui-report.mjs`; invalid output is one clear error with no retry.
- Added the `ReportAgent` orchestrator and `POST /api/threads/{thread_id}/report/generate`, which streams SSE progress and OpenUI deltas, rejects no-history and no-relevant requests with a clear message in the analyst's language, stores the report only when complete, keeps the previous report on cancellation, and stores the partial report flagged incomplete on failure.
- The single real smoke run used synthetic answers, not the evaluation files, and wrote its plan, report and metadata only to the git-excluded local-results directory under `backend/tests/evaluation/`. Result: OK, 5.696 s, 1,378 plan tokens and 15,670 report tokens. No retry was made.
- Tests mock the LLM and the parser, except one parser integration test against the installed OpenUI library; the suite covers success, cancel keeping the previous report, failure keeping the partial report flagged incomplete, regenerate replacing the previous report, no-history and no-relevant rejections, and invalid skill output.
- No schema change, dependency, GraphDB call or evaluation-question content was used.
- Verification: `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-07 (chat and report panels)

### TASK-029 — Build the chat and report panels and the Generate Report flow (WI-011, AC-FR013-01, AC-FR013-02, AC-FR013-03, AC-FR013-06, AC-FR021-01)

- Added the side-by-side chat and report panels next to the session list (`FR-022`). The chat panel sends a question to `POST /api/chat`, streams the raw answer, then reloads and renders the stored OpenUI Lang for each pair. A failed request shows the backend's localized error and leaves the failed question out of the history.
- Added the report panel and the **Generate Report** flow. It consumes the SSE `POST /api/threads/{thread_id}/report/generate` endpoint, shows planning and rendering progress, streams the OpenUI Lang progressively, and renders the current report when a session is selected.
- While a report is generated the chat is disabled (`FR-016`). **Cancel** aborts the request, keeps the previous report and re-enables the chat (`FR-017`). A failure shows the localized error, reloads the partial report flagged incomplete and re-enables the chat (`FR-019`). No-history and nothing-marked responses ask the analyst to start exploring or mark at least one pair (`FR-014`, `FR-015`). A successful regeneration replaces the previous report only when complete (`FR-018`).
- The task list had no frontend chat input task; this plan gap was filled with a minimal chat panel because `FR-002`, `FR-022` and the "disable the chat" requirement need it.
- Tests mock fetch and SSE and cover the streamed chat, localized chat errors, success, cancel, failure with a partial report, regeneration, both report rejections, progress, disabled chat and the side-by-side panels.
- No dependency or schema change and no real GraphDB or DeepSeek call in the tests.
- Verification: frontend lint, Prettier, `tsc --noEmit`, tests (49 passed), production build, `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass; `pnpm dev` and `uvicorn` both start and serve their pages.

## 2026-11-07 (chart plan empty cells)

### TASK-028 follow-up — Accept empty table cells and log report failures (WI-011, FR-013, FR-019)

- `ChartPlanSkill` now accepts `null` and the strings `-`, `–` and `n/a` as empty table cells and renders them as `–`; empty cells are not counted as source numbers, and invented numbers are still rejected.
- The chart-plan prompt now tells the model to use the string `–` for a missing table value, never `null`.
- `ReportAgent.stream` now logs the failure type and a truncated, redacted message server-side (at most 300 characters, no API key, no prompt or graph-answer text). The user-facing error is unchanged.
- Tests cover a plan with a null/empty table cell, a plan with an invented table number and the failure log.
- No dependency or schema change and no real LLM call.
- Verification: `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-07 (light, dark and system theme)

### UI polish extension — Light, dark and system theme toggle (user-approved, no FR)

- Added a theme control in the session header with System, Light and Dark choices. System is the default and follows `prefers-color-scheme`; the choice is stored in localStorage inside try/catch.
- Defined the app palette as CSS variables in `frontend/src/styles.css` for both modes. Explicit choices set `data-theme` and `data-openui-theme`, so `@openuidev/react-ui` cards, charts and tables use the same theme and keep readable contrast.
- Added Vitest coverage for the toggle and the theme helpers.
- No dependency or schema change.
- Verification: frontend lint, Prettier, `tsc --noEmit`, tests (53 passed) and production build pass; the backend checks remain green.

## 2026-11-07 (answer text and chat layout)

### TASK-029 follow-up — Show the answer text and improve the chat and report layout (WI-011, FR-002, FR-021, FR-022)

- Each question-answer pair now shows the stored answer as readable text first, with line breaks, bold text, lists and simple markdown tables. The OpenUI card is collapsed behind a **Show chart** toggle below the text; the text stays selectable and uses the normal contrast tokens in both themes.
- The thread endpoint returns the stored OpenUI Lang, so the frontend extracts its narrative text for the text view; no backend change was needed.
- The session list is narrower, the chat and report panels share the remaining width with a minimum of about 420 px each, and each panel scrolls internally instead of the page. Long questions wrap, and wide tables and charts scroll horizontally inside their own container.
- Added contrast fixes for both themes: the OpenUI library follows the app theme, the answer and report containers use the normal text tokens, and leftover chart entry opacity no longer leaves faded content.
- Added Vitest coverage for answer-text extraction and rendering, the **Show chart** toggle and the existing flows.
- No dependency or schema change and no task checkbox change.
- Verification: frontend lint, Prettier, `tsc --noEmit`, tests (60 passed) and production build pass; backend `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-08 (report download)

### TASK-030 — Implement the HTML export (WI-012, AC-FR026-01)

- Added **Download Report** to the report panel for the active session, shown only when the session has a report. The browser builds one self-contained HTML file from the stored OpenUI Lang and downloads it with a filesystem-safe `<session-name>-<YYYY-MM-DD>.html` name.
- Chose a build-time inlined template plus a client-side download: `frontend/scripts/build-report-template.mjs` builds `frontend/report-export/` with Vite, inlines the renderer script and styles, and writes the git-ignored generated report template under the public directory. The template keeps the report data and metadata as JSON placeholders; the browser fills them at download time. The build fails if the template has any external reference.
- The exported page follows the system light or dark theme with the OpenUI theme variables and has no external resources, so it opens offline.
- Changed the report skill 2 prompt to require a one-line context subtitle from the plan's scope (for example the run label and windows, or the main question topic) and never the literal word "Report".
- Tests cover filename sanitization, the zero-external-reference check, report content, escaping a closing script sequence and the download trigger. No dependency or schema change and no real LLM or GraphDB call.
- Verification: frontend lint, Prettier, `tsc --noEmit`, tests (70 passed) and production build pass; backend `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-08 (report export false positives)

### TASK-030 follow-up — Stop flagging bundled documentation text as an external reference (WI-012, FR-026)

- `hasExternalReferences` now removes inline script and style contents before checking. It flags only real external `src`/`href` attributes (http(s):// or //) and CSS `url(...)` inside `<style>` blocks or `style` attributes, with a negative lookbehind so documentation such as `@OpenUrl(...)` and names such as `myurl(...)` do not match. The user-provided report text is inside a script and is no longer scanned.
- The build-time template check in `frontend/scripts/build-report-template.mjs` uses the same strictness, so the build and the download agree.
- Tests cover the false-positive documentation text, a real `<link href>`, a real `<script src>`, real CSS `url(https://...)` in a style block and style attribute, and the real built template plus a sample report through the full download path.
- No dependency or schema change and no task checkbox change.
- Verification: frontend lint, Prettier, `tsc --noEmit`, tests and production build pass; backend `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-08 (download without a report)

### TASK-031 — Tell the analyst to generate a report before downloading (WI-012, AC-FR026-02)

- **Download Report** is now always visible in the report panel. When the active session has no report (including while a first report is being generated and nothing is stored), pressing it downloads nothing and shows the dismissible message "No report is stored yet. Generate a report first."
- The message disappears when a report exists or when the session changes. When a report exists, the TASK-030 download behavior is unchanged.
- Tests cover no report with no download call and the message, report present with a successful download, the message during a first generation, dismissal, session change and hiding the message once a report exists.
- No dependency or schema change and no real LLM or GraphDB call.
- Verification: frontend lint, Prettier, `tsc --noEmit`, tests and production build pass; backend `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-08 (erase actions)

### TASK-032 — Implement Erase History and Erase Report (WI-013, AC-FR028-01, AC-FR028-02, AC-FR028-04, AC-FR028-05)

- Added `DELETE /api/threads/{thread_id}/history` to erase all pairs and the report of one session, and `DELETE /api/threads/{thread_id}/report` to erase only its report. Both are scoped to the given session and use the existing SQLite tables; relevance rows cascade with their pairs. Missing sessions return 404 and erasing a missing report is idempotent.
- Added **Erase History** and **Erase Report** to the report panel with an explicit confirmation for each. Confirming history clears the active session's pairs, relevance and report; confirming report clears only the report and keeps the pairs. Declining changes nothing; failure shows the existing session error and leaves the visible state unchanged.
- Both buttons are disabled when the session has no history and no report; **Erase Report** is also disabled without a report; both are disabled while a report is generated.
- Tests use a temporary SQLite database for other sessions unchanged, report-only keeping pairs, missing sessions and idempotent report erase, and Vitest for confirm, decline, failure and disabled states.
- No dependency or schema change and no real LLM or GraphDB call.
- Verification: frontend lint, Prettier, `tsc --noEmit`, tests and production build pass; backend `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-08 (session switch panel duplication)

### TASK-032 follow-up — Keep one chat and report panel when switching sessions (WI-013, FR-028)

- Fixed the duplicated Chat panel: `ChatPanel` and `ReportPanel` were siblings with the same `key={activeSessionId}`, so React kept stale keyed nodes as the key changed. They now use `chat-<session-id>` and `report-<session-id>`, which keeps the remount on session change and makes the sibling keys distinct.
- Added a regression test that switches the active session through three sessions. For each session it renders `SessionDetail`, asserts exactly one `aria-label="Chat"` and one `aria-label="Report"` element, and asserts that the two panel elements have distinct, session-specific React keys.
- Client rendering with `react-dom/client` is not possible in the current test setup: Vitest runs in the `node` environment and neither `jsdom` nor Testing Library is a dependency. The test inspects the React element tree returned by `SessionDetail` instead; no dependency was added.
- No API call, dependency or schema change.
- Verification: frontend tests, ESLint, Prettier and `tsc --noEmit` pass.

## 2026-11-08 (session list labels)

### TASK-025 follow-up — Give session names a full row in the sidebar (WI-009, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010)

- Session names now take a full-width row and wrap to at most two lines with an ellipsis; the select button has a `title` with the full name so hovering shows it.
- **Rename** and **Delete** moved to a smaller second-row action group, so they no longer compete with the name for horizontal space.
- Widened the sidebar from 220–240 px to 260–280 px. The existing `max-width: 720px` single-column layout is unchanged, and the surface, border, text and active-highlight colours still use the light/dark theme tokens.
- No behaviour, API, dependency or schema change; the active-session highlight, rename form, delete confirmation and every `aria-label` are unchanged. No test change was needed because the session logic is untouched.
- Verification: frontend tests (89 passed), ESLint, Prettier and `tsc --noEmit` pass.

## 2026-11-09 (session lock)

### TASK-025 follow-up — Lock the session controls while an action is in progress (WI-009, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010)

- The session list now disables session selection, **New session**, **Rename**, **Delete**, the rename form controls and both delete-confirmation buttons while `isLoading`, `isSendingChat` or `isGeneratingReport` is true. A visible note says "Wait for the current action to finish."
- `SessionController.selectSession`, `createSession`, `renameSession` and `deleteSession` now no-op in the same three busy states, so the lock cannot be bypassed. The report **Cancel** control is unchanged.
- Added controller tests for all three busy states and a `SessionList` test for the disabled controls and confirmation buttons.
- No API, dependency, schema or backend change. `SPEC.md` describes create, select, rename and delete without a busy precondition (`FR-006` to `FR-010`, `AC-FR005-01`); the lock defers those actions rather than changing their outcome, and the SPEC was not edited.
- Verification: frontend tests, ESLint, Prettier, `tsc --noEmit`, the production build and the SDD/consistency checks pass.

## 2026-11-09 (answer quality and Agent Ap prompts)

### TASK-029 follow-up — Render nested inline markup and tighten Agent Ap prompts (WI-008, WI-011; FR-002, FR-013, FR-019, FR-021, FR-022)

- `AnswerText` now renders inline code and italics inside bold text, so a fragment such as `**Alpha \`:Beta\` Gamma**` shows a code box without literal backticks. Unmatched markers stay as text. Tests use invented fixtures only.
- The chat conversion task now forbids loose labels, bare type names, empty headings and raw query/code metadata. It caps the response at 6 statements, keeps the "do not invent facts" rule, requires exactly one matching chart when the answer has a numeric table over categories, and forbids charts when there is no such table.
- The shared component reference now forbids bare labels and tells the model to use only supplied data instead of plausible/invented data.
- Report skill 1 now uses the most recent pair when two or more relevant pairs answer the same question with different figures, and asks for a short note that an earlier answer with different figures exists. The file remains marked `DRAFT`.
- Live validation: re-ran only the chat conversion on 3 stored answers (2 with a numeric markdown table, 1 without); all 3 parsed and passed the label and chart checks (chart counts 1, 1, 0). Ran the report agent once on the local session with 4 relevant pairs; it completed successfully with 3 plan charts and 2 report charts. Agent G was not called and no answer text, questions or figures were committed.
- No API, dependency, schema or backend-behaviour change.
- Verification: frontend tests (103 passed), ESLint, Prettier, `tsc --noEmit`, the production build, backend `ruff`, `mypy`, `pytest` (155 passed, 1 skipped) and the SDD/consistency checks pass.

## 2026-11-09 (UI and theme refinement)

### TASK-034 progress — Apply the portfolio theme and chart palettes (WI-014; FR-021, FR-022, FR-026)

- Mounted the `@openuidev/react-ui` `ThemeProvider` around the app and around the exported report, with the effective `light` or `dark` mode resolved from the selected theme and the system preference.
- Added `portfolioLightTheme` and `portfolioDarkTheme` with the five-colour categorical palette on every chart palette key and `oklch(...)` semantic tokens for surfaces, borders, accents, positive and negative metrics, and alert callouts.
- `AnswerText` now highlights explicitly signed metrics (`+19.88%`, `-1.24%`, signed currency amounts) as positive or negative badges, while unsigned numbers, dates and code spans stay unchanged.
- Restyled the sidebar, session cards, chat bubbles, composer, report controls and OpenUI cards, tables and charts with the navy/slate dark theme and the clean light theme. The report template still has 0 external references.
- The end-to-end acceptance pass is still in progress, so `TASK-034` remains unchecked.
- No dependency, API, schema or backend change.
- Verification: frontend tests (109 passed), ESLint, Prettier, `tsc --noEmit` and the production build pass; the report template is 4,092,805 bytes with 0 external references. Backend `ruff`, `ruff format --check`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.

## 2026-11-10 (report chart quality)

### TASK-034 progress — Improve portfolio chart selection in the report and chat prompts (WI-014; FR-021, FR-022, FR-025)

- Expanded `ChartType` to `bar`, `horizontal_bar`, `stacked_bar`, `line`, `area`, `pie`, `donut` and `table`, and added optional `x_label`/`y_label` fields to `ChartSpec`.
- `parse_chart_plan` now validates the new cartesian and circular types, parses optional axis labels, rejects non-string labels and negative donut values, and keeps the strict `extract_numbers` / `_source_check` rule that every chart or table number must appear verbatim in the answer text. `plan_payload` serializes non-empty axis labels.
- Report skill 1 now documents the portfolio chart catalogue, axis labels, donut allocations, horizontal rankings, smooth time series and explicit `+`/`-` signs on supported returns and changes.
- Report skill 2 now maps every plan type to its OpenUI component with `"natural"` lines and areas, grouped or stacked bars, grouped horizontal rankings, donut pies and real axis labels instead of literal `"Category"` / `"Value"`.
- The chat conversion now allows `AreaChart` and `PieChart`, selects chart types by portfolio data shape, passes real axis labels, keeps a concise 1-2 sentence takeaway and preserves the 6-statement limit.
- Tests cover the new chart types, axis-label parsing and serialization, negative donut values, invented values in area/horizontal/stacked charts, and the Node parser accepts `AreaChart`, `HorizontalBarChart` and `PieChart(..., "donut")`.
- `TASK-034` remains unchecked because the end-to-end acceptance pass is still in progress.
- No dependency, SQLite schema, HTTP endpoint or API change.
- Verification: backend `pytest` (168 passed, 1 skipped), `ruff check`, `ruff format --check` and `mypy app` pass; frontend tests (110 passed), SDD/consistency checks and `pre-commit run --all-files` pass.

## 2026-11-10 (chart theme context and report stream)

### TASK-034 progress — Unify the OpenUI theme context and harden report streaming (WI-014; FR-013, FR-021, FR-022, FR-026)

- Imported `ThemeProvider`, `openuiLibrary` and `openuiChatLibrary` from the same `@openuidev/react-ui` entrypoint in the app and the report export, so chart components read the mounted theme instead of the isolated `genui-lib` context and use the portfolio chart palettes.
- Refined report skill 1: `line` requires at least 3 time points and never replaces a 2-point start/end comparison; `area` is preferred over `bar` for single-series periodic counts, activity, alerts or cumulative volume; mixed start/end and summary-metric tables must use `table` so every numeric column is preserved.
- Added an SSE `: keep-alive` comment every 5 seconds while the report agent waits for its next event, using a pending `anext` task that is reused across heartbeats, then cancelled and closed in `finally`.
- `SessionController.errorText` now returns the user-safe fallback for raw browser `TypeError`s such as `Error in input stream` and `Failed to fetch`, for both chat streaming and report generation.
- Added the missing `format:check` and `typecheck` frontend script aliases used by the verification commands.
- The report template still builds with 0 external references. No dependency, SQLite schema, HTTP endpoint or API change; `TASK-034` remains unchecked.
- Verification: frontend tests (113 passed), ESLint, Prettier, `tsc --noEmit` and the production build pass; report template 3,810,422 bytes with 0 external references; backend `pytest` (169 passed, 1 skipped), `ruff check`, `ruff format --check` and `mypy app` pass; SDD/consistency checks and `pre-commit run --all-files` pass.

## 2026-11-11 (report visual precision)

### TASK-034 progress — Highlight report metrics and scale financial charts (WI-014; FR-015, FR-021, FR-022)

- Exported `renderMetrics` and `renderInline` from `AnswerText` and added `portfolioReportLibrary` / `portfolioChatLibrary`, which override `TextContent`, `InlineHeader` and `Table` so report paragraphs, chart takeaways and table cells reuse the emerald/coral signed-metric badges from the chat.
- Replaced the built-in OpenUI line and area charts with a responsive SVG `PortfolioChart`: tight positive domains no longer anchor at zero, Y ticks are generated from the data range, the context strip explains the Y unit and range plus the X axis, and the legend shows each series colour, name and start → end values. Data points, hover/focus tooltips and legend visibility toggles are also included.
- Wired `portfolioReportLibrary` into `ReportPanel` and the exported report, `portfolioChatLibrary` into `PairAnswer`, and kept the report validation script on the same schema through the root `@openuidev/react-ui` entrypoint.
- Added chart, legend, tooltip and pagination styles for the app and the exported report, with `--app-*` aliases mapped to the OpenUI tokens in the export so the same signed-metric badges work offline.
- Skill 1 now requires non-empty `x_label` and `y_label` on every cartesian chart, and `_chart()` coerces any 2-point `line` or `area` plan to `bar` while preserving 3+ point lines.
- `TASK-034` remains unchecked because the end-to-end acceptance pass is still in progress. No dependency, SQLite schema, HTTP endpoint or API change.
- Verification: frontend tests (119 passed), ESLint, Prettier, `tsc --noEmit` and the production build pass; backend `pytest` (172 passed, 1 skipped), `ruff check`, `ruff format --check` and `mypy app` pass; SDD/consistency checks and `pre-commit run --all-files` pass.

## 2026-11-11 (integer chart axes)

### TASK-034 progress — Format integer Y-axis ticks and avoid crowded X labels (WI-014; FR-015)

- `buildYAxis()` now computes the tick step before choosing label precision and uses both `dataDecimals` and `stepDecimals`. When every data point and the tick step are integers, the axis renders `0`, `50`, `100`, `150` without trailing decimals; fractional NAV series keep clean three-decimal ticks such as `0.850`, `0.900`, `0.950`, `1.000`.
- X-axis tick selection drops the penultimate label when adding the final label would place two ticks next to each other, so a 10-month `2022-01`..`2022-10` series ends with `2022-07` and `2022-10`.
- Added an integer `AreaChart` regression test alongside the existing NAV `LineChart` precision test.
- `TASK-034` remains unchecked. No dependency, SQLite schema, HTTP endpoint or API change.
- Verification: frontend tests (120 passed), ESLint, Prettier, `tsc --noEmit` and the production build pass; report template 3,830,780 bytes with 0 external references.

## 2026-11-11 (UI polish)

### TASK-034 progress — Polish report cards, chat footer and empty states (WI-014; FR-015, FR-021, FR-022)

- Styled the top-level report card as an executive canvas with a subtle accent rule, generous spacing and a refined header, and made nested section cards distinct elevated cards in both the app and the exported report.
- `PortfolioTable` now detects numeric and signed-metric columns and adds `data-col-align` plus `portfolio-table__col--numeric` to headers and cells, with right alignment, tabular numerals, zebra rows and hover highlighting.
- Replaced the stacked chat controls with a single `.message__footer` containing the chart toggle, relevance pill chip and right-aligned delete action; the expanded chart sits directly above the footer and the delete confirmation remains a separate alert dialog.
- Streamed chat answers now render through `AnswerText`, so markdown, tables and signed metrics format as tokens arrive. Chat and report progress use animated status pills, and empty chat/report/session panels use intentional dashed empty-state cards.
- Grouped primary report actions apart from destructive erase actions with a divider, and compacted session cards with actions that strengthen on hover, focus-within or active state.
- Tests cover numeric column alignment, the compact answer footer and live formatted chat streaming.
- `TASK-034` remains unchecked. No dependency, SQLite schema, HTTP endpoint or API change.
- Verification: frontend tests (124 passed), ESLint, Prettier, `tsc --noEmit` and the production build pass; report template 3,833,197 bytes with 0 external references.

## 2026-11-12 (localized metrics and report recovery)

### TASK-034 progress — Handle Unicode minus, decimal commas and text-only tables (WI-014; FR-015)

- `AnswerText` now matches ASCII `-`, Unicode minus `−`, plus signs, dot or comma decimals and an optional space before `%`, so `−10.14 %`, `−18.94 %.`, `-0,1229` and `+19.88 %` receive the correct red/green badges while dates and code spans stay plain.
- `PortfolioTable` uses the same localized numeric grammar, so Unicode-minus percentages and comma decimals right-align as numeric columns.
- `extract_numbers()` normalizes Unicode minus before matching and parses localized numbers: comma decimals (`-0,1229`, `0,0108`, `0,5`), thousands commas (`1,200`), mixed separators, multiple dots and Spanish thousands dots (`4.958` also yields `4958.0`) without changing `0.999` or four-decimal NAVs.
- `parse_chart_plan()` now skips a text-only table when at least one valid numeric chart exists, and still raises the `numeric column` error when the plan contains only text-only tables.
- Skill 1 explicitly forbids qualitative-only tables in Rules 2 and 5.
- Tests cover the new localized metric badges, table alignment, number extraction and mixed text-only/numeric chart plans.
- `TASK-034` remains unchecked. No dependency, SQLite schema, HTTP endpoint or API change.
- Verification: frontend tests (127 passed), ESLint, Prettier, `tsc --noEmit` and the production build pass; report template 3,833,217 bytes with 0 external references; backend `pytest` (176 passed, 1 skipped), `ruff check`, `ruff format --check` and `mypy app` pass.

## 2026-11-12 (SPARQL viewer and distinct bar charts)

### TASK-034 progress — Add a lazy SPARQL viewer and portfolio-colored bar charts (WI-014; FR-015)

- Added `SQLiteQuestionAnswerStore.get_raw_answer()` and `GET /api/threads/{thread_id}/pairs/{pair_id}/sparql`, which returns `{pair_id, queries}` extracted from fenced `sparql` blocks in the stored raw answer. Missing pairs or pairs from another thread return 404; the history response shape is unchanged.
- Added `createSparqlClient()` and wired an optional loader through `App`, `SessionDetail`, `ChatPanel` and `PairAnswer`.
- Chat answers now expose `Show SPARQL query` / `Hide SPARQL query` next to the chart toggle. Queries load lazily on first open, stay cached per pair, reset when the message changes, and render in `.message__sparql` panels inside `.message__card` with per-query Copy/Copied feedback, loading, error and empty states.
- Added `PortfolioBarChart` overrides for both `BarChart` and `HorizontalBarChart` in the report and chat libraries. Single-series charts color every category from the emerald-first dark/light palette, multi-series charts color by series and keep legend toggles, grouped/stacked layouts and negative values around a zero baseline are supported, and the header pills swap value/category axis labels for horizontal bars.
- Added bar-specific zero-line styling to the app and exported report, plus SPARQL panel styles in the app stylesheet. The exported report still builds as one inline file with zero external references.
- Tests cover SPARQL block extraction, 404s, client requests, lazy/cached viewer state, multiple queries, empty/error/loading states, distinct bar colors, series legends, stacked bars and negative values.
- `TASK-034` remains unchecked. No dependency, SQLite schema, REST/SSE contract or API response-shape change.
- Verification: frontend tests (141 passed), ESLint, Prettier, `tsc --noEmit` and the production build pass; report template 3,840,578 bytes with 0 external references; backend `pytest` (180 passed, 1 skipped), `ruff check`, `ruff format --check` and `mypy app` pass.

## 2026-11-12 (stacked bar axis extent)

### TASK-034 progress — Scale stacked bars to category totals (WI-014; FR-015)

- `PortfolioBarChart` now derives its axis values from per-category stacked positive and negative totals when the chart is multi-series and uses the `"stacked"` variant, rather than individual series values.
- `buildBarAxis()` now extends the bar domain and ticks when the raw stacked extent falls outside the last nice tick, so tall stacked bars stay inside the SVG plot.
- The `Rango` header pill follows the stacked extent, and the value-axis label inference uses the same totals.
- Added a regression test with stacked series `[60]` and `[50]` asserting ticks reach at least `110`, the range shows `0 – 110`, and both bar rectangles stay within the plot height.
- `TASK-034` remains unchecked. No dependency, SQLite schema, HTTP endpoint or API change.
- Verification: frontend tests (142 passed), ESLint, Prettier, `tsc --noEmit` and the production build pass; report template remains a single inline file with 0 external references.

## 2026-11-13 (verbatim disclaimers and caveats)

### TASK-034 progress — Preserve mandatory generated-text and provenance notes (WI-014; FR-015)

- Added shared `app.disclaimers` helpers that ignore fenced code/SPARQL blocks, extract generated-text disclaimers, in-sample caveats and provenance/source lines, deduplicate notes, and append missing notes as valid `TextContent(..., "small")` statements referenced from `root = Card([...])` with quote-aware balanced bracket matching.
- The chat OpenUI converter prompt now requires verbatim preservation and exempts mandatory notes from the takeaway, statement and process-note limits. `OpenUIConverter.convert()` deterministically appends any missing note after fence stripping.
- Added optional `ChartPlan.disclaimers`, Skill 1 prompt and parsing support, automatic extraction from answers, and `plan_payload` serialization only when notes exist.
- Skill 2 now requires every plan disclaimer, caveat and provenance note to be rendered verbatim after Conclusions. `ReportAgent` appends any missing note before validation and storage, including partial reports when a plan exists.
- Added backend tests for Spanish/English disclaimers, in-sample caveats, provenance lines, duplicate suppression, last-line root cards, report-plan extraction, payload serialization, prompt rules, agent injection and optional Node parser validation. Added a frontend answer-text extraction test for small disclaimers.
- `TASK-034` remains unchecked. No dependency, SQLite schema, REST/SSE contract or API response-shape change.
- Verification: backend `pytest` (190 passed, 1 skipped), `ruff check`, `ruff format --check` and `mypy app` pass; frontend tests (143 passed), ESLint, Prettier, `tsc --noEmit` and the production build pass; report template 3,841,103 bytes with 0 external references.

## 2026-11-13 (disclaimer deduplication)

### TASK-034 progress — Avoid duplicate disclaimers and provenance notes (WI-014; FR-015)

- Strengthened the shared note presence check: it decodes OpenUI string literals, normalizes whitespace and Markdown emphasis, and checks multi-sentence notes sentence by sentence.
- A note split across several `TextContent` statements, or rendered with Markdown formatting, is now recognized as already present, so the app no longer appends a second copy.
- Added regression tests for a Spanish disclaimer and provenance line split across separate `TextContent` statements in both the chat converter and the report agent.
- Both the chat converter and report Skill 2 prompts now explicitly say to keep an already-visible mandatory note only once.
- `TASK-034` remains unchecked. No dependency, SQLite schema, HTTP endpoint or API change.
- Verification: backend `pytest` (192 passed, 1 skipped), `ruff check`, `ruff format --check` and `mypy app` pass; frontend tests (143 passed), ESLint, Prettier and `tsc --noEmit` pass.
