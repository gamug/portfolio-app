# Implementation Plan

## FR-001 — Discover and initialize the project

FR-001 is the initialization requirement. It is fulfilled by completing WI-001 through WI-006 in order. The product requirements `FR-002` to `FR-035` come from the approved `docs/PRODUCT.md` and are implemented by WI-007 through WI-014, which follow the MVP roadmap in its section 7 (spike, build, test).

### Acceptance criteria

The acceptance criteria `AC-FR001-01` through `AC-FR001-06`, and the product criteria derived from the user stories, are defined in [`SPEC.md`](./SPEC.md#acceptance-criteria). Each Work Item below names the criterion it satisfies.

## Work items

### WI-001 — Run the discovery skill and create PRODUCT.md

**Parent:** FR-001  
**Depends on:** none  
**Acceptance criteria:** AC-FR001-01

Run the `sdd-init` skill (`SKILL.md` in [gamug/sdd-template](https://github.com/gamug/sdd-template), pinned in `scripts/sdd-verify.sh`) through all six phases. Collect the user's problem definition, actors, workflows, requirements, user stories, stack evaluation, ADRs, environment and governance decisions, risks, and roadmap in `docs/PRODUCT.md`, built from the skill's `templates/product-template.md`, and seed the root `adr.md` from its ADRs. Discovery runs first: no other FR-001 work starts before it, and `validate_config.py` refuses to run until `docs/PRODUCT.md` is approved; it does not check `adr.md`, so the acceptance of the seeded ADRs is a manual exit criterion below.

The skill must ask focused questions interactively. It must not guess missing inputs. When an answer is required, the question must state what decision is needed, why it affects the project, and what concrete options or examples the user should consider.

**Exit criteria:** Every `UNRESOLVED:` decision has been resolved with the user, `docs/PRODUCT.md` records the user's approval and the hash of the approved content in its `## Approval` section, `validate_discovery.py docs/PRODUCT.md` passes without `--draft`, and every seeded ADR in `adr.md` is `Accepted` with `Approved by` and `Approved on` filled from the approver and first approval date recorded in `docs/PRODUCT.md`.

### WI-002 — Create config.yaml

**Parent:** FR-001  
**Depends on:** WI-001 (approved `docs/PRODUCT.md` and accepted seeded ADRs)  
**Acceptance criteria:** AC-FR001-02

Build root `config.yaml` from scratch with `validate_config.py scaffold`, which lists every key required by the generic `$SKILL_DIR/memory/constitution.md` template and the PRODUCT.md section each one usually comes from.

1. Fill values that `docs/PRODUCT.md` states explicitly, with source `PRODUCT.md § <section>`. The cited section must have no subsections and contain each value (every item, for lists and maps) as a whole token.
2. Define the project's domain sections (`domain_sections`) from the use cases, requirements, ADRs, and risks, and confirm them with the user. The template carries no domain rules of its own. Their source is always `user, YYYY-MM-DD`.
3. Ask the user for every other value. A value PRODUCT.md only implies is proposed and confirmed, never written silently. Record answers with source `user, YYYY-MM-DD`.

Every value and its source is recorded in the `Configuration Decisions` table of `docs/PRODUCT.md`. `validate_config.py check` must pass.

**Exit criteria:** `check` passes: every key is defined and has a recorded source matching its value.

### WI-003 — Render constitution.md and synchronize SDD objects

**Parent:** FR-001  
**Depends on:** WI-002  
**Acceptance criteria:** AC-FR001-03

Render `.sdd/constitution.md` from root `config.yaml` and the immutable `$SKILL_DIR/memory/constitution.md` template with `validate_config.py render`. Rendering re-runs `check` and fails on any missing value or leftover placeholder; no questions are asked in this WI. The rendered file is never edited by hand: any later `config.yaml` change updates its `Configuration Decisions` row and re-runs `render`.

Then create or update all SDD objects under `.sdd/`—`SPEC.md`, `PLAN.md`, `TASKS.md`, and `CHANGELOG.md`—to match the approved `docs/PRODUCT.md` definition while preserving the `FR > WI > Task` hierarchy and traceability. `FR-001` stays the initialization requirement; product requirements are numbered from `FR-002`. Task and Work Item progress starts being tracked in `.sdd/TASKS.md` here, with the tasks completed so far, and the Work Items they complete, checked.

**Exit criteria:** `validate_config.py render --verify` passes, and all SDD objects agree with `docs/PRODUCT.md`.

### WI-004 — Create folders and non-programmatic dependencies

**Parent:** FR-001  
**Depends on:** WI-003  
**Acceptance criteria:** AC-FR001-04

Create the directories, configuration locations, documentation locations, environment templates, container metadata, and other non-programmatic dependencies selected in `docs/PRODUCT.md`. Do not implement application source code in this WI.

**Exit criteria:** Required non-programmatic project structure exists and matches the approved constitution and PRODUCT definition.

### WI-005 — Set up the system environment

**Parent:** FR-001  
**Depends on:** WI-004  
**Acceptance criteria:** AC-FR001-05

Set up the development environment using the approach selected in `docs/PRODUCT.md`: devcontainer, Docker, host tooling, or an explicitly approved no-container setup. Configure runtimes, package managers, services, environment variables, quality tools, and CI prerequisites as applicable.

**Exit criteria:** The selected environment can be created and the documented baseline checks can run without committed secrets.

### WI-006 — Automate environment reproduction

**Parent:** FR-001  
**Depends on:** WI-005  
**Acceptance criteria:** AC-FR001-06

Create the automation needed to reproduce the environment setup from a clean checkout. Prefer `scripts/init.sh` when compatible with the approved environment; otherwise use the project-appropriate equivalent and document why. Configure the fork's pre-commit hook and `.github/workflows/validators.yml` with the project's own quality gates. The discovery and configuration validators serve initialization only and are not part of them.

**Exit criteria:** Re-running the initialization automation produces the documented environment or reports actionable errors, the procedure is documented for contributors, and the pre-commit hook and CI run the project's quality gates.

### WI-007 — Technical spike

**Parent:** FR-002  
**Depends on:** WI-006  
**Acceptance criteria:** AC-SPIKE-01, AC-SPIKE-02, AC-SPIKE-03, AC-SPIKE-04, AC-SPIKE-05, AC-SPIKE-06  
**Related requirements:** FR-002, FR-013, FR-021, FR-026

Resolve the biggest unknowns before building (roadmap phase 0, days 1-2; risks RSK-001 to RSK-004, RSK-006 and RSK-007). Create the read-only GraphDB user and decide the tool source (`ttyg` or `yaml`) from the working one; verify DeepSeek tool calling over GraphDB's `/rest/llm/tool` API, valid OpenUI Lang generation with the locally generated prompt, that the react-ui chat layout can host per-pair controls, the offline inlining of the OpenUI browser bundle, and the report plot quality from stored answer text.

**Exit criteria:** A recorded result for each spike criterion `AC-SPIKE-01` to `AC-SPIKE-06`; any failed item has a proposed ADR in `adr.md` for the project owners.

### WI-008 — Chat with the knowledge graph

**Parent:** FR-002  
**Depends on:** WI-007  
**Acceptance criteria:** AC-FR002-01, AC-FR002-02, AC-FR035-01  
**Related requirements:** FR-002, FR-003, FR-004, FR-035

Implement the FastAPI connector: the DeepSeek tool loop over GraphDB's LLM tool API, the conversion of the final answer to OpenUI Lang, streaming to the chat and storage of the pair (`adr-006`, `adr-007`). The connector and the chat panel for `UC-001`; also covers `FR-003`, `FR-004` and `FR-035`.

**Exit criteria:** A question typed in the chat streams an answer rendered with OpenUI, and the pair is stored once the answer completes; failed questions show an error and are not stored.

### WI-009 — Sessions and persistence

**Parent:** FR-005  
**Depends on:** WI-007  
**Acceptance criteria:** AC-FR005-03, AC-FR005-01, AC-FR005-02, AC-FR005-04  
**Related requirements:** FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011

Implement SQLite persistence and the sessions API that follows the OpenUI thread REST convention (`adr-004`, `adr-005`). The schema, the thread endpoints and the session list for `UC-002`; also covers `FR-006` to `FR-011`.

**Exit criteria:** Sessions can be created, listed, switched, renamed and deleted, all data survives a restart, and database errors are shown without changing the visible state.

### WI-010 — Relevance marking and question-answer deletion

**Parent:** FR-012  
**Depends on:** WI-009  
**Acceptance criteria:** AC-FR003-01, AC-FR003-02, AC-FR028-03, AC-FR028-04  
**Related requirements:** FR-003, FR-012, FR-032, FR-033, FR-034

Implement the relevance toggle and the deletion of a single pair. The per-pair controls for `UC-008` and `UC-009`; also covers `FR-032`, `FR-033` and `FR-034`.

**Exit criteria:** The analyst can mark pairs as relevant and delete a pair after confirmation, and a report is not changed by either action.

### WI-011 — Report generation

**Parent:** FR-013  
**Depends on:** WI-008  
**Acceptance criteria:** AC-FR013-01, AC-FR013-04, AC-FR013-05, AC-FR013-06, AC-FR013-02, AC-FR013-03, AC-FR021-01  
**Related requirements:** FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-021, FR-022

Implement the report agent as two sequential DeepSeek calls and the report panel beside the chat (`adr-008`, `adr-009`). The report agent and report panel for `UC-003`; also covers `FR-014` to `FR-019`, `FR-021` and `FR-022`.

**Exit criteria:** Generate Report builds a streamed, cancellable report from the relevant pairs, replaces the previous report, and handles empty history, nothing marked and agent failure.

### WI-012 — Report download

**Parent:** FR-026  
**Depends on:** WI-011  
**Acceptance criteria:** AC-FR026-01, AC-FR026-02  
**Related requirements:** FR-026, FR-027

Implement the download of the current report as one self-contained HTML file (`adr-009`). The export for `UC-005`; also covers `FR-027`.

**Exit criteria:** Download Report produces `<session-name>-<YYYY-MM-DD>.html` that opens offline, and shows a message when there is no report.

### WI-013 — Erase actions

**Parent:** FR-028  
**Depends on:** WI-011  
**Acceptance criteria:** AC-FR028-01, AC-FR028-02, AC-FR028-04, AC-FR028-05  
**Related requirements:** FR-028, FR-029, FR-030, FR-031

Implement Erase History and Erase Report. The erase actions for `UC-006` and `UC-007`; also covers `FR-029` to `FR-031`.

**Exit criteria:** Both actions ask for confirmation, apply to the active session only, and are disabled when there is nothing to erase.

### WI-014 — Acceptance testing and fixes

**Parent:** FR-002  
**Depends on:** WI-008, WI-009, WI-010, WI-011, WI-012, WI-013  
**Acceptance criteria:** AC-ACC-01, AC-FR002-01, AC-FR002-02, AC-FR003-01, AC-FR003-02, AC-FR005-01, AC-FR005-02, AC-FR005-03, AC-FR005-04, AC-FR013-01, AC-FR013-02, AC-FR013-03, AC-FR013-04, AC-FR013-05, AC-FR013-06, AC-FR021-01, AC-FR026-01, AC-FR026-02, AC-FR028-01, AC-FR028-02, AC-FR028-03, AC-FR028-04, AC-FR028-05, AC-FR035-01  
**Related requirements:** FR-002

Test the MVP against the acceptance criteria and the curated question set (roadmap phase 2, days 6-7). End-to-end verification of every Must Have acceptance criterion and the 90% accuracy target.

**Exit criteria:** All Must Have acceptance criteria pass and the curated question set reaches 90% correct answers.

## Deviations absorbed by the 2026-11-06 re-approval of docs/PRODUCT.md

`docs/PRODUCT.md` was re-approved on 2026-11-06 by Gabriel Múnera (gamug) as version 1.1.0, and its sections now state each difference below, except the ADR blocks of section 5, which stay a frozen snapshot (`adr.md` carries the erratum for moved paths). The table is kept as the record of what changed; nothing is pending. The first approval was on 2026-11-05 (version 1.0.0).

| Where in `docs/PRODUCT.md` | Text approved on 2026-11-05 | Implemented, and stated in version 1.1.0 |
| :--- | :--- | :--- |
| Section 6, Verification command | `uv run pytest`, the frontend suite and a check of `GET /api/health` | `uv run --directory backend pytest` and `pnpm --dir frontend test --run` (see `config.yaml`); the health check is **intentionally not implemented** (owners' decision, 2026-11-06: no functional requirement covers it, so `TASK-035` was removed) |
| Sections 6 and 8, Coding agent | "There is no init command" for `CLAUDE.md` | `scripts/init.sh` creates it from a tracked template (decided by the owners, 2026-11-06) |
| Section 8, Governance | amendments logged in `CHANGELOG.md` | `.sdd/CHANGELOG.md` (`config.yaml`) |
| Section 8, CI | the inherited OpenUI workflows stay in the repository and are disabled | every job is guarded by `github.repository == 'thesysdev/openui'`, and the four that had already run were also disabled in GitHub settings (the other five never registered) |
| Sections 4 to 6 and ADRs | paths `packages/`, `examples/`, `spec/`, `templates/` | `packages/`, `examples/` and `spec/` moved to `reference/`; `templates/` removed (erratum in `adr.md`) |
| Section 3, user stories | acceptance scenarios of `US-001` to `US-007` | derived criteria added in `SPEC.md`: `AC-FR021-01`, `AC-FR035-01`, `AC-ACC-01`, `AC-SPIKE-01` to `AC-SPIKE-06` |
| Section 8, CI | seven ordered gates | the ordered gates are unchanged (`config.yaml` `ci_gate_order`), plus: a `commit-subjects` job on pull requests, a `shellcheck` job for `scripts/*.sh`, and two repository checks inside the pytest gate (`check_consistency.py`: commands, pins, cited paths, `CLAUDE.md` template; `check_sdd.py`: SPEC, PLAN and TASKS traceability) |
| Section 8, Version control | `main` changes only through pull requests, and hooks and CI must pass before merge | the GitHub ruleset `main protection` only blocks deleting `main` and force-pushes; it does not require pull requests or the `validate` and `commit-subjects` checks (accepted by the owners, 2026-11-06); the PR-only rule holds by convention |
| Section 8, Version control | merge method not specified | pull requests are merged with a merge commit (owners' decision, 2026-11-06); squash and rebase merging are disabled in the repository settings, so the PR title is not used as a commit subject |
| Section 3, Security (NFR) | data leaves the machine only to the GraphDB agent endpoint and the LLM | dependency and CLI telemetry is switched off (`DO_NOT_TRACK=1`, `OPENUI_TELEMETRY_DISABLED=1` in the devcontainer, CI and `scripts/init.sh`) and the telemetry-only install script of `@openuidev/lang-core` is not allowed to run; found in review round 3 and enforced by `check_consistency.py` |
| Sections 1 to 8, licensing | no licensing decision | MIT; `LICENSE` keeps the upstream notice and adds `Copyright (c) 2026 gamug and dova` (owners' decision, 2026-11-06) |
| Section 3, Success metric | a curated question set prepared by the owners | it lives in `backend/tests/evaluation/` (public repository, publishable facts only; owners' decision, 2026-11-06); format in its README |

## Planning rules

- `TASKS.md` must contain the tasks for these Work Items, with one explicit parent WI per task.
- Product Work Items (WI-007 to WI-014) follow the roadmap in `docs/PRODUCT.md` section 7: the spike first, then the Must Have build, then testing. Each Work Item's detailed design is written in this plan before its tasks start, and the report-agent skills are specified in the SDD process before WI-011 starts.
- Work Items and tasks must be completed in dependency order.
- Material ambiguity is a question for the user, not an implementation guess.
