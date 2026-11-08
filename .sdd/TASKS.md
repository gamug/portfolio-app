# SDD Tasks

Task register for the hierarchy `FR-001 > WI > Task` defined in [`PLAN.md`](./PLAN.md). Every task has exactly one parent Work Item.

`$SKILL_DIR` is `.sdd-tooling/skills/sdd-init`, a checkout of [gamug/sdd-template](https://github.com/gamug/sdd-template) at the commit pinned in `scripts/sdd-verify.sh` (it is gitignored). `bash scripts/sdd-verify.sh` fetches it and runs the validators; commands run from the project root.

Every Work Item and task carries a checkbox: `[ ]` is the template value and `[x]` means done. A Work Item is checked only when every task under it is checked, in the same change as its last task. Progress is tracked in this file: the checkboxes are the current state, and `backend/app/devtools/check_sdd.py` checks them against `PLAN.md` and `SPEC.md`. Work Items and tasks added to `.sdd/TASKS.md` carry the same boxes and follow the same rule.

## WI-001 — Run the discovery skill and create PRODUCT.md

- [x] **Done** (checked only when every task below is checked)

### TASK-001 — Execute the discovery workflow

- [x] **Done**
- **Work Item:** WI-001
- **Depends on:** none
- **Acceptance criteria:** AC-FR001-01
- **Action:** Run all six phases of `$SKILL_DIR/SKILL.md`, including the Governance & Workflow checklist, except that writing `docs/PRODUCT.md` and seeding `adr.md` are TASK-003, and approving PRODUCT.md and accepting the seeded ADRs are TASK-004. Nothing else in FR-001 may start before this task.

### TASK-002 — Collect discovery outputs

- [x] **Done**
- **Work Item:** WI-001
- **Depends on:** TASK-001
- **Acceptance criteria:** AC-FR001-01
- **Action:** Assemble use cases, requirements, user stories, stack evaluation, ADRs (seeded into the root `adr.md` in TASK-003), environment and governance decisions, risks, and roadmap.

### TASK-003 — Write PRODUCT.md

- [x] **Done**
- **Work Item:** WI-001
- **Depends on:** TASK-002
- **Acceptance criteria:** AC-FR001-01
- **Action:** Write `docs/PRODUCT.md` from `$SKILL_DIR/templates/product-template.md`, filling each numbered section from its phase fragment. Seed the root `adr.md` from the ADRs in section 5 as Phase 4 step 5 of `$SKILL_DIR/SKILL.md` describes, and keep it in sync while iterating. Use three-digit IDs, each defined once and every reference resolving; give each FR an EARS pattern that matches its statement and one MoSCoW priority; score risks as Impact × Probability. Mark every open decision with `UNRESOLVED:`, and run `python "$SKILL_DIR/scripts/validate_discovery.py" --draft docs/PRODUCT.md` until it passes. Draft mode lists the template placeholders still to replace; approval fails while any remain.

### TASK-004 — Resolve open decisions and record approval

- [x] **Done**
- **Work Item:** WI-001
- **Depends on:** TASK-003
- **Acceptance criteria:** AC-FR001-01
- **Action:** Ask the user about every `UNRESOLVED:` item and update `docs/PRODUCT.md`, applying any change to a section 5 ADR to its `adr.md` block in the same step. Present the document for approval and record it in its `## Approval` section (`Approved by:`, `First approved on: YYYY-MM-DD`, `Approved on: YYYY-MM-DD`, and `Approved content:` with the hash printed by `validate_discovery.py --hash docs/PRODUCT.md` once the user has approved). Run the validator without `--draft`; it must pass. Any later edit outside the Approval and Configuration Decisions sections invalidates the approval until the user approves again. This is the entry gate of WI-002, enforced by `validate_config.py`. Then accept the seeded ADRs as Phase 6 step 5 of `$SKILL_DIR/SKILL.md` describes (reconcile with section 5, accept, re-read). `validate_config.py` does not check the ADR acceptance; it is a manual gate. This task is not done, and TASK-005 does not start, until every seeded ADR in `adr.md` is `Accepted` with `Approved by` and `Approved on` filled.

## WI-002 — Create config.yaml

- [x] **Done** (checked only when every task below is checked)

### TASK-005 — Scaffold config.yaml and fill stated values

- [x] **Done**
- **Work Item:** WI-002
- **Depends on:** TASK-004
- **Acceptance criteria:** AC-FR001-02
- **Action:** Run `validate_config.py scaffold`. It writes the `config.yaml` skeleton, with the PRODUCT.md section each key usually comes from, and appends the `Configuration Decisions` table to `docs/PRODUCT.md`. Fill only values that `docs/PRODUCT.md` states explicitly, and record each one in the table with source `PRODUCT.md § <section>`; `check` verifies that the section exists, has no subsections, and contains the value (every item, for lists and maps) as a whole token, so `3.1` is not evidence for "3.12.2". The Approval and Configuration Decisions sections are never evidence. Record lists and maps as compact JSON and escape `|` in values as `\|`.

### TASK-006 — Define domain sections

- [x] **Done**
- **Work Item:** WI-002
- **Depends on:** TASK-005
- **Acceptance criteria:** AC-FR001-02
- **Action:** From the use cases, functional requirements, ADRs, and risks in `docs/PRODUCT.md`, propose the domain-specific constitution sections (for example models, services, storage, AI behavior, evaluation) as `domain_sections` entries with a `title` and `rules`. Confirm them with the user, write them to `config.yaml`, and record the `domain_sections` row as compact JSON with source `user, YYYY-MM-DD` (`check` rejects a `PRODUCT.md §` source here) so `check` detects any later change. An empty list is valid only when the user confirms the project needs none.

### TASK-007 — Ask the user for every remaining value

- [x] **Done**
- **Work Item:** WI-002
- **Depends on:** TASK-006
- **Acceptance criteria:** AC-FR001-02
- **Action:** This task is the only place configuration questions are asked. For every value `docs/PRODUCT.md` does not state, ask a context-rich question. A value the document only implies is proposed to the user and confirmed, never written silently. Record each answer in the table with source `user, YYYY-MM-DD`. Propose `.github/workflows/validators.yml` as `quality.ci_file`: the project's quality gates replace the template's maintenance steps in that workflow, so it stays the single CI file.

### TASK-008 — Validate config.yaml

- [x] **Done**
- **Work Item:** WI-002
- **Depends on:** TASK-007
- **Acceptance criteria:** AC-FR001-02
- **Action:** Run `validate_config.py check`. It fails on missing or empty keys, keys without a valid recorded source, and recorded values that differ from `config.yaml`. Return to TASK-007 for every reported key.

## WI-003 — Render constitution.md and synchronize SDD objects

- [x] **Done** (checked only when every task below is checked)

### TASK-009 — Render constitution.md

- [x] **Done**
- **Work Item:** WI-003
- **Depends on:** TASK-008
- **Acceptance criteria:** AC-FR001-03
- **Action:** Run `validate_config.py render` to create `.sdd/constitution.md` from root `config.yaml` and the immutable `$SKILL_DIR/memory/constitution.md`. Rendering re-runs `check` and fails on any missing value or leftover placeholder. Do not edit the rendered file by hand; re-run `render` after any `config.yaml` change.

### TASK-010 — Synchronize all SDD objects

- [x] **Done**
- **Work Item:** WI-003
- **Depends on:** TASK-009
- **Acceptance criteria:** AC-FR001-03
- **Action:** Create or update `.sdd/SPEC.md`, `.sdd/PLAN.md`, `.sdd/TASKS.md`, and `.sdd/CHANGELOG.md` to match the approved `docs/PRODUCT.md` and preserve traceability. Keep `FR-001` and its Work Items as the initialization requirement and add the product requirements from `docs/PRODUCT.md`, which are numbered from `FR-002`. Carry this task register into `.sdd/TASKS.md` with TASK-001 through TASK-009, WI-001, and WI-002 checked; progress is tracked there from now on. Finish with `validate_config.py render --verify`.

## WI-004 — Create folders and non-programmatic dependencies

- [x] **Done** (checked only when every task below is checked)

### TASK-011 — Create the approved project structure

- [x] **Done**
- **Work Item:** WI-004
- **Depends on:** TASK-010
- **Acceptance criteria:** AC-FR001-04
- **Action:** Create approved folders, configuration locations, documentation paths, environment templates, and other non-programmatic dependencies.

### TASK-012 — Verify non-programmatic dependencies

- [x] **Done**
- **Work Item:** WI-004
- **Depends on:** TASK-011
- **Acceptance criteria:** AC-FR001-04
- **Action:** Check that the structure matches PRODUCT.md and constitution.md without adding application source code.

## WI-005 — Set up the system environment

- [x] **Done** (checked only when every task below is checked)

### TASK-013 — Implement the selected environment setup

- [x] **Done**
- **Work Item:** WI-005
- **Depends on:** TASK-012
- **Acceptance criteria:** AC-FR001-05
- **Action:** Configure the approved devcontainer, Docker, host-only, or explicitly no-container environment.

### TASK-014 — Run baseline environment checks

- [x] **Done**
- **Work Item:** WI-005
- **Depends on:** TASK-013
- **Acceptance criteria:** AC-FR001-05
- **Action:** Create the environment and run the documented baseline checks without committing secrets.

## WI-006 — Automate environment reproduction

- [x] **Done** (checked only when every task below is checked)

### TASK-015 — Create initialization automation

- [x] **Done**
- **Work Item:** WI-006
- **Depends on:** TASK-014
- **Acceptance criteria:** AC-FR001-06
- **Action:** Create `scripts/init.sh` or the approved equivalent to reproduce the environment from a clean checkout. Configure the project's pre-commit hook (the configured `quality.commit_hook`, which also enforces the commit convention) and its CI workflow with the project's own quality gates. The discovery and configuration validators serve initialization only; they are run during WI-001 to WI-003 and are not part of the project's hook or CI.

### TASK-016 — Verify reproducibility and document recovery

- [x] **Done**
- **Work Item:** WI-006
- **Depends on:** TASK-015
- **Acceptance criteria:** AC-FR001-06
- **Action:** Re-run initialization, verify actionable failures, and document the recovery/reproduction procedure for contributors.

---

## Product Work Items

The product Work Items below implement the requirements `FR-002` to `FR-035` of the approved `docs/PRODUCT.md` (section 3) following its roadmap (section 7). `TASK-017`, `TASK-018`, `TASK-019`, `TASK-020`, `TASK-021`, `TASK-022`, `TASK-023`, `TASK-024`, `TASK-025`, `TASK-026`, `TASK-027`, `TASK-028`, `TASK-029`, `TASK-030` and `TASK-031` are done; the remaining product tasks are unchecked. Each task cites only the acceptance criteria it implements. `TASK-035` (a backend health endpoint) was removed on 2026-11-06 by decision of the project owners, because no functional requirement covers it; task IDs are not reused.

## WI-007 — Technical spike

- [x] **Done** (checked only when every task below is checked)

### TASK-017 — Create the read-only GraphDB user and settle the tool source

- [x] **Done**
- **Work Item:** WI-007
- **Depends on:** TASK-016
- **Acceptance criteria:** AC-SPIKE-01
- **Action:** Ask the project owners to create a read-only GraphDB user for the application and set `KG_USER` and `KG_PASSWORD`; configure either a Talk to Your Graph agent or a YAML tool configuration, and verify the tool list through `GET /rest/llm/tool/{configType}/{configId}`.
- **Result (2026-11-06):** Tool source is `ttyg`, using the existing Talk to Your Graph agent `reportes-piloto` (`d832d4d0-5ec3-4953-bd39-cb2f0691b7d7`) on `portfolio_test` (the knowledge graph is not final). GraphDB 11.5.1 answers at `KG_HOST`; `GET /rest/repositories` lists `portfolio_test` as `RUNNING`; `GET /rest/llm/tool/ttyg/d832d4d0-5ec3-4953-bd39-cb2f0691b7d7` returns `/now` and `/sparql_query`. As `KG_USER`, login authorities are `READ_REPO_portfolio_test` and `ROLE_USER`; a SPARQL read succeeds; empty and isolated-graph writes return `403`; without credentials, reads and writes return `401`; the isolated probe graph is absent. No YAML configuration was needed, and neither `config.yaml` nor a dependency was changed.

### TASK-018 — Spike the DeepSeek tool loop on the live tools

- [x] **Done**
- **Work Item:** WI-007
- **Depends on:** TASK-017
- **Acceptance criteria:** AC-SPIKE-02
- **Action:** Prerequisite: `backend/tests/evaluation/questions.json` prepared by gamug and dova (format in its README). Run a DeepSeek tool loop over the GraphDB tools against the curated question set and record accuracy and failure modes (RSK-001).
- **Result (2026-11-07):** Ran the accepted `adr-010` path through the Workbench chat API with the DeepSeek-based agent `reportes-piloto-ds` on the provisional `portfolio_test` KG. All 8 development questions returned an answer; errors 0; median latency 25.808 s; total tokens 1,188,318 (median 136,779.5 per question). The `adr-007` tool loop remains the selectable fallback. Detailed outputs are only in the git-excluded local-results directory under `backend/tests/evaluation/`. Owner grade: pending. The KG and question set are provisional; repeat on the final KG.

### TASK-019 — Spike OpenUI generation, chat layout and report export

- [x] **Done**
- **Work Item:** WI-007
- **Depends on:** TASK-017
- **Acceptance criteria:** AC-SPIKE-03, AC-SPIKE-04, AC-SPIKE-05, AC-SPIKE-06
- **Action:** Verify valid OpenUI Lang from DeepSeek, per-pair controls in the react-ui chat, inlining of the browser bundle into one offline HTML file, and plot quality from answer text (RSK-002, RSK-003, RSK-004, RSK-006).
- **Result (2026-11-07):** Pass.
  - **AC-SPIKE-03 pass:** the locally generated OpenUI chat and report prompts were used for two short DeepSeek calls; 2 of 2 outputs parsed without errors.
  - **AC-SPIKE-04 pass:** the react-ui chat layout accepts custom assistant and user message components, and a relevance toggle and delete action render for each message. Click handlers are wired; no browser-automation dependency was added, so this was verified structurally.
  - **AC-SPIKE-05 pass:** the OpenUI renderer and the report were inlined into one HTML file of 3,702,568 bytes (about 3.7 MB) with 0 external references.
  - **AC-SPIKE-06 pass:** the report contained a bar chart built from the synthetic answer text, with the expected series and values; no ADR for storing structured tool results is needed.
  - **Failure modes:** none for the four checks; AC-SPIKE-04 was verified structurally rather than through browser clicks. Detailed outputs are only in the git-excluded local-results directory under `backend/tests/evaluation/`.

## WI-008 — Chat with the knowledge graph

- [x] **Done** (checked only when every task below is checked)

### TASK-020 — Implement the tool loop and answer streaming

- [x] **Done**
- **Work Item:** WI-008
- **Depends on:** TASK-019
- **Acceptance criteria:** AC-FR002-01
- **Action:** Build the connector tool loop with a bounded iteration count and stream the final answer to the chat.
- **Result (2026-11-07):** Added the production connector under `backend/app/connector/` and the streaming `POST /api/chat` endpoint in `backend/app/main.py`. The default mode is the accepted `adr-010` Workbench chat API; `tool_loop` is the bounded `adr-007` fallback. The connector loads settings from `.env`, checks both chat endpoints at startup, uses a per-question timeout and no retries, and streams the completed answer in chunks. Tests use mocked HTTP and a fake LLM only. One real smoke call returned OK with latency 49.096 s and 148,399 total tokens; it was run once with no retries. Question-answer storage remains TASK-021. No dependency was added.

### TASK-021 — Convert and store question-answer pairs

- [x] **Done**
- **Work Item:** WI-008
- **Depends on:** TASK-020
- **Acceptance criteria:** AC-FR002-01
- **Action:** Convert the final answer to OpenUI Lang with a second DeepSeek call and store the question, the raw answer and the OpenUI Lang after the answer completes.
- **Result (2026-11-07):** Added the second DeepSeek OpenUI conversion and a storage boundary with an in-memory implementation; no database schema was changed, and TASK-023 will replace the in-memory store with SQLite. `POST /api/chat` now converts only after the answer completes, stores the pair only after a successful conversion, and streams the raw answer. Tests use mocked HTTP and LLM only. One real smoke call returned OK with latency 29.03 s; 128,787 answer tokens plus 15,930 conversion tokens, 144,717 total. It ran once with no retries. The OpenUI prompt is committed as a generated local asset; no dependency was added.

### TASK-022 — Handle errors and the analyst's language

- [x] **Done**
- **Work Item:** WI-008
- **Depends on:** TASK-021
- **Acceptance criteria:** AC-FR002-02, AC-FR035-01
- **Action:** Show an error for GraphDB, DeepSeek or tool-loop failures without storing the question; make interface text and answers follow the analyst's language.
- **Result (2026-11-07):** Added a minimal language detector and localized, user-safe error mapping for validation, timeouts, GraphDB, DeepSeek, conversion and storage failures. Raw upstream bodies and internal messages are never returned. The detected language instruction is sent to the GraphDB agent and the tool loop, and to the OpenUI conversion prompt. Failed questions are never stored; tests cover answer, conversion and storage failures. Tests use mocked HTTP and LLM only. The optional one-shot Spanish smoke call failed once with a timeout after 120 s and was not retried; no tokens were reported. The backend returns a localized error JSON; displaying it visibly is left to the chat UI task. No dependency or database schema change.

## WI-009 — Sessions and persistence

- [x] **Done** (checked only when every task below is checked)

### TASK-023 — Create the SQLite schema and migrations

- [x] **Done**
- **Work Item:** WI-009
- **Depends on:** TASK-019
- **Acceptance criteria:** AC-FR005-03
- **Action:** Define the tables for sessions, question-answer pairs, relevance marks and reports with migrations (schema approval applies).
- **Result (2026-11-07):** Added the approved four-table schema in `backend/app/storage/migrations/001_initial.sql` with the agreed indexes, foreign keys and cascade rules, and a stdlib `sqlite3` migration runner using `PRAGMA user_version`. Added the SQLite implementation of the question-answer storage boundary, which replaces the in-memory default; `SQLITE_PATH` is read from `.env`. Tests use temporary databases only and cover migration idempotence, reopen persistence, default relevance, relevance updates, session cascades and one report per session. No dependency was added and no network or API calls are used.

### TASK-024 — Implement the thread REST endpoints

- [x] **Done**
- **Work Item:** WI-009
- **Depends on:** TASK-023
- **Acceptance criteria:** AC-FR005-01, AC-FR005-02
- **Action:** Implement get, create, update and delete thread endpoints over SQLite, plus the report and relevance endpoints.
- **Result (2026-11-07):** Implemented the adr-005 thread endpoints under `/api/threads` (`/get`, `/create`, `/get/{id}`, `/update/{id}`, `/delete/{id}`), the current-report get/set endpoints with the incomplete flag, and per-pair relevance get/set endpoints over the TASK-023 SQLite store. History is returned as user/assistant messages with the stored OpenUI Lang; the report has its own endpoint beside the thread convention. Deleting a session cascades to its history and report. Database failures return a generic user-safe error. Tests use a temporary database through the FastAPI test client, with no network or API calls. No schema change or dependency was added.

### TASK-025 — Build the session list in the frontend

- [x] **Done**
- **Work Item:** WI-009
- **Depends on:** TASK-024
- **Acceptance criteria:** AC-FR005-01, AC-FR005-02, AC-FR005-04
- **Action:** Create, select, rename and delete sessions, create a new empty session after deleting the active one, and show database errors.
- **Result (2026-11-07):** Added the frontend session list over `restStorage({baseUrl: "/api/threads"})` with create, select, inline rename and delete after explicit confirmation. Deleting the active session creates a new empty session and makes it active. Selecting a session loads its history and current report. Failed create, rename, delete or select operations set a visible error and leave the visible session, history and report unchanged. Tests mock the storage and report backend through the controller; no GraphDB or DeepSeek calls are made. `pnpm` lint, Prettier, `tsc --noEmit`, tests and the production build pass. No dependency was added.

## WI-010 — Relevance marking and question-answer deletion

- [x] **Done** (checked only when every task below is checked)

### TASK-026 — Implement the relevance toggle

- [x] **Done**
- **Work Item:** WI-010
- **Depends on:** TASK-025
- **Acceptance criteria:** AC-FR003-01, AC-FR003-02
- **Action:** Store and show the relevance state of each pair; new pairs are marked.
- **Result (2026-11-07):** Added a relevance client and controller state that loads each pair's stored relevance when a session is opened or switched, defaults a new pair to relevant, and toggles it through the existing backend relevance endpoints. The session view renders one relevance checkbox per answer. A failed update shows an error and leaves the visible relevance state unchanged. Tests mock the storage, report and relevance backend; no GraphDB or DeepSeek calls are made. No backend change, dependency or schema change was needed.

### TASK-027 — Implement deletion of a single pair

- [x] **Done**
- **Work Item:** WI-010
- **Depends on:** TASK-026
- **Acceptance criteria:** AC-FR028-03, AC-FR028-04
- **Action:** Delete a pair after confirmation in the active session only, leaving the current report unchanged.
- **Result (2026-11-07):** Added the single-pair delete endpoint under `/api/threads` and the SQLite delete method; the relevance row cascades and the current report is untouched. The session view now exposes a delete action per answer with explicit confirmation. Declining changes nothing; confirming removes only that pair's question/answer messages and relevance mark; failure shows an error and leaves the visible state unchanged. Tests use Vitest with a mocked backend and pytest against a temporary SQLite database. No schema change, dependency, GraphDB or DeepSeek call was needed.

## WI-011 — Report generation

- [x] **Done** (checked only when every task below is checked)

### TASK-028 — Implement the report agent

- [x] **Done**
- **Work Item:** WI-011
- **Depends on:** TASK-027
- **Acceptance criteria:** AC-FR013-01, AC-FR013-04, AC-FR013-05, AC-FR013-06
- **Action:** Implement the two skills as sequential DeepSeek calls producing OpenUI Lang from the relevant pairs, with streaming and cancellation.
- **Result (2026-11-07):** Added skill 1 in `report_skill_1_chart_plan_prompt.txt` (relevant pairs to a validated JSON plan) and skill 2 in `report_skill_2_openui_prompt.txt` (plan to OpenUI Lang, with `openui_chat_prompt.txt` as the component reference). Skill 1 rejects numbers that are not present in the answer text and skips pairs without numeric content. Skill 2 streams one DeepSeek call and validates the complete output with the same `@openuidev/react-lang` parser as the TASK-019 spike through `frontend/scripts/validate-openui-report.mjs`; invalid output is one clear error with no retry. The `ReportAgent` orchestrator adds `POST /api/threads/{thread_id}/report/generate`, which streams SSE progress and OpenUI deltas, rejects no-history and no-relevant requests before streaming, stores the report only when complete, keeps the previous report on cancellation, and stores the partial report flagged incomplete on failure with a user-safe message in the analyst's language. Tests mock the LLM and parser except one parser integration test; the single real smoke run used synthetic answers and reported OK with 5.696 s, 1,378 plan tokens and 15,670 report tokens. The prompt files are a DRAFT pending the teammate's review. No schema change, dependency, GraphDB call or evaluation-question content was used.

### TASK-029 — Build the report panel and the Generate Report flow

- [x] **Done**
- **Work Item:** WI-011
- **Depends on:** TASK-028
- **Acceptance criteria:** AC-FR013-01, AC-FR013-02, AC-FR013-03, AC-FR013-06, AC-FR021-01
- **Action:** Show the report beside the chat with progress, disable the chat during generation, store the result, and handle empty history, nothing marked and failure with a partial report flagged incomplete.
- **Result (2026-11-07):** Added the side-by-side chat and report panels next to the session list. The chat panel sends a question to `POST /api/chat`, streams the raw answer, then reloads and renders the stored OpenUI Lang; a failed request shows the backend's localized error and leaves the failed question out of the history. The report panel consumes the SSE generation endpoint, shows planning/rendering progress, streams the OpenUI Lang progressively, offers Cancel, reloads the current report when a session is selected, keeps the previous report until completion then replaces it, keeps the previous report on cancel, and reloads the partial report flagged incomplete with a localized error on failure. No-history and nothing-marked rejections are shown in the panel. The task list had no frontend chat input task, so this plan gap was filled with a minimal chat panel as FR-002, FR-022 and the "disable the chat" requirement need it. Tests mock fetch and SSE and cover success, cancel, failure, regenerate, both rejections, localized errors and the disabled chat. No dependency or schema change and no real GraphDB or DeepSeek call in the tests.

## WI-012 — Report download

- [x] **Done** (checked only when every task below is checked)

### TASK-030 — Implement the HTML export

- [x] **Done**
- **Work Item:** WI-012
- **Depends on:** TASK-029
- **Acceptance criteria:** AC-FR026-01
- **Action:** Inline the OpenUI browser bundle and the stored OpenUI Lang into one HTML file named from the session and the date.
- **Result (2026-11-08):** Added **Download Report** to the report panel for the active session, shown only when the session has a report. The browser fetches a build-time inlined OpenUI renderer template, injects the stored OpenUI Lang and session metadata, and downloads one self-contained HTML file named from the sanitized session name and the local download date. The template is generated by `frontend/scripts/build-report-template.mjs` before `pnpm dev` and `pnpm build`; it inlines the renderer script and styles, keeps the report data as JSON, and fails if any external reference remains. The export shell follows the system light or dark theme. The report skill 2 prompt now asks for a one-line context subtitle and forbids the literal word "Report". Tests cover filename sanitization, the zero-external-reference check, report content, escaping a closing script sequence and the download trigger. No dependency or schema change and no real LLM or GraphDB call.

### TASK-031 — Handle download with no report

- [x] **Done**
- **Work Item:** WI-012
- **Depends on:** TASK-030
- **Acceptance criteria:** AC-FR026-02
- **Action:** Show a message telling the analyst to generate a report first and download nothing.
- **Result (2026-11-08):** **Download Report** is now always visible in the report panel. When the active session has no report, including while a first report is being generated, pressing it calls no export and shows the dismissible message "No report is stored yet. Generate a report first." The message disappears when a report exists or when the session changes. When a report exists, the TASK-030 download behavior is unchanged. Tests cover no report with no download call and the message, report present with a successful download, the message during a first generation, dismissal, session change and the message being hidden once a report exists. No dependency or schema change and no real LLM or GraphDB call.

## WI-013 — Erase actions

- [ ] **Done** (checked only when every task below is checked)

### TASK-032 — Implement Erase History and Erase Report

- [ ] **Done**
- **Work Item:** WI-013
- **Depends on:** TASK-029
- **Acceptance criteria:** AC-FR028-01, AC-FR028-02, AC-FR028-04, AC-FR028-05
- **Action:** Add both buttons with confirmation, session scoping and disabled states.

## WI-014 — Acceptance testing and fixes

- [ ] **Done** (checked only when every task below is checked)

### TASK-033 — Evaluate the curated question set

- [ ] **Done**
- **Work Item:** WI-014
- **Depends on:** TASK-032
- **Acceptance criteria:** AC-ACC-01
- **Action:** Run the curated question set in `backend/tests/evaluation/questions.json` (prepared by the project owners) and record the result against the 90% target.

### TASK-034 — Run end-to-end verification and fix defects

- [ ] **Done**
- **Work Item:** WI-014
- **Depends on:** TASK-033
- **Acceptance criteria:** AC-FR002-01, AC-FR002-02, AC-FR003-01, AC-FR003-02, AC-FR005-01, AC-FR005-02, AC-FR005-03, AC-FR005-04, AC-FR013-01, AC-FR013-02, AC-FR013-03, AC-FR013-04, AC-FR013-05, AC-FR013-06, AC-FR021-01, AC-FR026-01, AC-FR026-02, AC-FR028-01, AC-FR028-02, AC-FR028-03, AC-FR028-04, AC-FR028-05, AC-FR035-01
- **Action:** Verify the acceptance criteria of every Must Have requirement, run the full quality gates and fix defects.
