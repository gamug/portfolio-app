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
- The single real smoke run used synthetic answers, not the evaluation files, and wrote its plan, report and metadata only to `backend/tests/evaluation/local-results/` (git-excluded). Result: OK, 5.696 s, 1,378 plan tokens and 15,670 report tokens. No retry was made.
- Tests mock the LLM and the parser, except one parser integration test against the installed OpenUI library; the suite covers success, cancel keeping the previous report, failure keeping the partial report flagged incomplete, regenerate replacing the previous report, no-history and no-relevant rejections, and invalid skill output.
- No schema change, dependency, GraphDB call or evaluation-question content was used.
- Verification: `ruff`, `mypy`, `pytest`, `check_sdd.py` and `check_consistency.py` pass.
