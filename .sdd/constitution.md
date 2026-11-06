# Project Constitution

Governing principles for **portfolio-app-new** under a specification-driven development workflow. Specifications and plans precede implementation and may not silently contradict this constitution.

## Governance framework and rendering

- Project-specific parameters and operational variables are defined exclusively in the root `config.yaml`; informal task notes and prompts cannot replace configuration.
- Initialization created the canonical project artifacts under `.sdd/`, including `.sdd/constitution.md`. It is the generated governance contract and is not an independent source of project decisions.
- Renderers, build scripts, CLI harnesses, and AI context generators must validate the configuration before execution. Missing required configuration keys, mandatory environment variables, or schema parameters must fail immediately with an explicit, actionable error.
- This constitution and its approved SDD artifacts have precedence over informal prompts, ephemeral task notes, or developer preferences.

## Technological foundation

- **Runtime**: Python (backend) and Node.js (frontend) 3.12 and 22.12, managed by `uv and pnpm` using `backend/uv.lock and frontend/pnpm-lock.yaml` and `backend/pyproject.toml and frontend/package.json`.
- The configured runtime, language version, and package manager are locked. Lockfiles must be versioned and enforced by CI for every dependency installation or build.
- **Service type**: Local single-user web application (FastAPI backend, Vite + React frontend). Excluded components: 
  - manual report editing 
  - chart property editing 
  - report tweaks through the chat 
  - report formats other than HTML 
  - multi-user support and authentication 
- Where the project has core business logic, it remains independent from web frameworks, UI libraries, and ORMs. Dependencies point inward toward stable domain abstractions rather than outward toward volatile concrete tools.
- Optional heavy dependency groups must remain isolated from normal package imports.
- New libraries, frameworks, model checkpoints, storage engines, or platform dependencies require a reviewed rationale and a constitution amendment when they alter these guarantees.
- Public API contracts, storage schemas, security boundaries, and architectural layer boundaries are stable guarantees across minor releases unless an approved amendment explicitly changes them.
- Changes to runtime versions, core frameworks, breaking API contracts, or zero-trust security boundaries require constitutional review and a MAJOR version change.
- Where the project has layered domain logic, every Work Item architecture decision must preserve its Clean Architecture boundaries. An exception requires explicit rationale, impact analysis, human approval, and a constitutional amendment.

## Project structure

- Source: `backend/app and frontend/src/`; tests: `backend/tests and frontend/src/`; docs: `docs/`; SDD artifacts: `.sdd/` (fixed template conventions).
- Tests follow this layout and hermetic fixture policy: 
  - backend: backend/tests mirroring backend/app 
  - frontend: tests beside the code in frontend/src 
  - fixtures: backend/tests/fixtures; small, committed, hermetic, with no real graph data or secrets 
  - evaluation: backend/tests/evaluation holds the curated question set prepared by gamug and dova; it is committed to this public repository so it holds only facts the owners approve for publication 
- Each tool has one canonical configuration: 
  - python tools: backend/pyproject.toml (ruff, mypy, pytest) 
  - frontend tools: the ESLint flat config and the Prettier config in frontend/ 
  - git hooks: .pre-commit-config.yaml 
  - environment: .env.example (committed) and .env (local, untracked) 
  - devcontainer: .devcontainer/devcontainer.json 
  - secret scanner: .gitleaks.toml 
- Application settings must be injected through validated environment variables or the configured equivalent; secrets must never be hardcoded or committed to Git history.
- Naming follows these mappings; do not create a new term for an established stage or storage concept: 
  - report generation action: Generate Report 
  - report download action: Download Report 
  - history erase action: Erase History 
  - report erase action: Erase Report 

## Specification-driven development

- `.sdd/SPEC.md` defines required behavior.
- `.sdd/PLAN.md` translates requirements into architecture, risks, verification, rollout, and rollback.
- `.sdd/TASKS.md` contains active, traceable work with stable identifiers.
- The planning hierarchy is strict: functional requirements contain Work Items (WI), and each WI contains implementation tasks.
- Every Work Item in `.sdd/PLAN.md` must reference its parent functional requirement, and every task in `.sdd/TASKS.md` must reference exactly one parent WI. Missing links are invalid and must not be started.
- Product functional requirements define business intent and testable acceptance criteria without technical implementation details. Repository initialization and governance requirements may name the concrete artifacts and workflow steps needed to enforce this constitution. Work Items define architecture, contracts, schemas, and boundaries. Tasks define ordered, dependency-aware execution.
- Every production code commit must reference its Task ID, WI, and FR, in the commit format defined under Code and Git.
- Acceptance criteria use stable identifiers such as `AC-FR001-01`; every task must reference the acceptance-criteria IDs it implements.
- Work Item status and task status must remain synchronized: a Work Item is marked done only when every one of its tasks is.
- Project-specific decisions are collected and approved in `docs/PRODUCT.md` during discovery, normalized into root `config.yaml` with the source of every value recorded in the `Configuration Decisions` table of `docs/PRODUCT.md`, and rendered into `.sdd/constitution.md`. `.sdd/SPEC.md`, `.sdd/PLAN.md`, and `.sdd/TASKS.md` are then derived from `docs/PRODUCT.md`. `FR-001` is the initialization requirement; product requirements are numbered from `FR-002`.
- `docs/PRODUCT.md` is the decision source; `config.yaml` is the authoritative normalized configuration. Any edit to `config.yaml` must update its `Configuration Decisions` row, be synchronized to the affected SDD artifacts and to `.sdd/constitution.md`.
- Missing or ambiguous inputs must be presented as explicit, context-rich questions that identify the decision, explain its impact, and provide concrete options or an expected answer format. Agents must not guess or silently preserve example values.
- Completed work moves to `.sdd/CHANGELOG.md`, and status references are updated in the same change.
- Material ambiguity and scope changes are resolved in the SDD artifacts before implementation relies on them.
- SDD acceptance criteria should use a consistent executable form such as GIVEN-WHEN-THEN where applicable.

## Architecture decisions

- `adr.md` in the project root is the live record of architecture decisions. It was seeded from `docs/PRODUCT.md` section 5, which is a frozen discovery snapshot and is not edited after approval. If `adr.md` does not exist, create it before adding the first ADR: a title, then one `###` block per ADR, headed `adr-001`, `adr-002`, and so on, with `Status`, `Proposed on`, `Approved by`, `Approved on`, `Rejected by`, `Rejected on`, `Rejection reason`, `Deprecated by`, `Deprecated on`, `Deprecation reason`, `Supersedes`, `Superseded By`, `Context`, `Decision`, `Consequences (Positive)`, `Consequences (Trade-offs)`, and `Traceability` (fields that do not apply hold `N/A`).
- An architecture change is adding, upgrading, replacing, or removing a library, framework, model checkpoint, storage engine, or platform dependency, or a change to the runtime or language version, a core framework, a public API contract, a storage schema, a security boundary, an architectural layer boundary, or environment isolation.
- Before implementing an architecture change, add a new ADR to `adr.md` with `Status: Proposed`, present it to the user, and stop until the user decides. Do not implement the change, or work that depends on it, while the ADR is `Proposed`. If a `Proposed` ADR already exists for the same change, resume it instead of adding another. If a `Proposed` ADR's decision content changes after it was presented, present it again before accepting.
- The decision must be an explicit instruction from the user (for example in chat or a review comment). If the user approves, set `Status: Accepted`, record the name or role the user gave in `Approved by` and the date in `Approved on`, and only then implement the change. If the user rejects, set `Status: Rejected` and record `Rejected by`, `Rejected on`, and `Rejection reason`; the change is not implemented. `Approved by` and `Rejected by` never name the agent.
- One explicit user decision may satisfy both this rule and a scope-expansion approval under Coding-agent conduct when it names both.
- ADR statuses move only from `Proposed` to `Accepted` or `Rejected`, and from `Accepted` to `Deprecated` or `Superseded`. Moving an `Accepted` ADR to `Deprecated` also needs an explicit user decision, recorded in `Deprecated by`, `Deprecated on`, and `Deprecation reason`. A `Rejected` ADR is never reopened: revisiting the idea requires a new `Proposed` ADR with a new ID.
- A decision that replaces an earlier one names it in `Supersedes`; once the new ADR is `Accepted`, the earlier ADR becomes `Superseded` and records the new ID in `Superseded By`. Both updates are made in the same change, and an ADR that is already `Superseded` is not superseded again.
- ADR IDs have three digits, continue after the highest existing ID, and are never reused.
- An ADR does not replace a constitution amendment: a change that alters the guarantees under Technological foundation also follows Governance, and its implementation waits for both an `Accepted` ADR and the approved amendment. ADR changes after approval are recorded in `adr.md` only and do not require re-approving `docs/PRODUCT.md`.

## Coding-agent conduct

- Read this constitution and `.sdd/SPEC.md` before planning or editing.
- Match existing placement, naming, imports, and bootstrap conventions before introducing structure.
- Prefer the smallest complete change; avoid unrelated refactors and abstractions.
- `CLAUDE.md` cannot override version-controlled SDD artifacts. Must exist: yes, locally; tracked in Git: no, it is listed in .gitignore; created with `bash scripts/init.sh` when missing. It must reference: 
  - `docs/PRODUCT.md` 
  - `adr.md` 
  - `config.yaml` 
  - `.sdd/constitution.md` 
- Respect this destructive-history boundary before checkout or reset operations: 
  - rebase: needs approval 
  - amend of pushed commits: needs approval 
  - force-push: needs approval 
- Obtain approval for every item below: 
  - adding or upgrading a dependency 
  - changing the database schema 
  - expanding scope beyond the requirements 
- Update all affected product, SDD, configuration, constitution, template, automation, CI, and contributor artifacts when implementation changes their documented state.
- Never fabricate repository state, and never weaken, disable, or delete tests, static-analysis rules, checks, or SDD artifacts to obtain a passing result.

## Interfaces, data, and reliability

- Public contracts define inputs, outputs, errors, versions, compatibility, and ownership.
- Validate external inputs at trust boundaries.
- Schema changes are migration-driven and require explicit scope approval.
- Time, ordering, retries, idempotency, and data provenance are explicit where applicable.
- Failures are observable and are never silently converted to successful results.
- Where the project makes external network calls, database queries, or system-process calls, each uses explicit timeouts, resource limits, circuit breakers, and bounded retries with exponential backoff.
- Where the project exposes external or inter-service interfaces, they use strict, versioned schemas such as OpenAPI, gRPC/Protobuf, or JSON Schema before implementation.
- Where the project has persistence, domain logic accesses it through repositories or gateways; direct SQL or storage calls do not belong in business or presentation layers.
- Failures must be logged with structured context, error codes, and tracing identifiers where available. Silent exception handling and empty catch blocks are prohibited.

## Executable commands

```text
uv sync --locked --directory backend && pnpm --dir frontend install --frozen-lockfile     # base dependencies
uv run --directory backend pytest && pnpm --dir frontend test --run                   # full test suite
uv run --directory backend pytest && pnpm --dir frontend test --run                # CI tests
uv run --directory backend ruff check . && pnpm --dir frontend lint                   # lint
uv run --directory backend ruff format --check . && pnpm --dir frontend exec prettier --check .           # format verification
uv run --directory backend mypy app && pnpm --dir frontend exec tsc --noEmit             # type analysis
uv run --directory backend pre-commit run --all-files             # all local gates
```

- CI configuration: `.github/workflows/validators.yml`; ordered gates: 
  - gitleaks 
  - ruff 
  - mypy 
  - ESLint and Prettier 
  - tsc 
  - pytest 
  - Vitest 
- Commands must use the configured package manager and locked environment.
- All canonical validation commands must run in isolated, deterministic CI before integration.

## Code and Git

- Commit subjects use imperative Conventional Commits syntax with the full FR/WI/Task traceability suffix, enforced by a `commit-msg` hook in the `pre-commit` framework (Python): `type(scope): imperative summary [FR-002][WI-003][TASK-007]`.
- Integration branch: `main`; direct commits allowed: no.
- Verify branch freshness before editing.
- Feature branches are short-lived and pull requests contain isolated, self-contained functional changes.
- Unrelated development on an in-flight PR: not allowed; each concern gets its own branch and pull request.
- Required hooks and CI checks must pass before merge.
- Pre-commit and pre-push hooks must run the configured fast quality checks, including secret scanning with `gitleaks`. CI must reject detected secrets.
- Secrets must not be committed; example environment files contain placeholders only.
- Leave the working tree on the pushed PR branch: yes. Include the complete PR URL in the final handoff.

 
## Chat and knowledge-graph access

- The chat reaches GraphDB only through the backend connector; the browser never holds GraphDB or DeepSeek credentials. - The connector uses a read-only GraphDB user, never a write-enabled or admin user (RSK-007). - The tool loop has a bounded number of iterations; a failed question is shown as an error and never stored (FR-004). 


## Sessions and persistence

- SQLite is the only store; sessions follow the OpenUI thread REST convention (adr-005). - Erase and delete actions ask for confirmation and apply to the active session only (FR-033, FR-034). - A database error is shown and leaves the visible state unchanged (FR-011); schema changes are migration-driven and need approval. 


## Report generation and export

- Only question-answer pairs marked as relevant feed a report; generation streams, can be cancelled, and disables the chat (FR-013 to FR-019). - The report is stored as OpenUI Lang, one current report per session (adr-009). - Download is one self-contained HTML file named <session-name>-<YYYY-MM-DD>.html with no external resources. 


## LLM usage and accuracy

- DeepSeek is the only LLM; its key lives in .env and the OpenUI prompt is generated locally (adr-006). - The interface and reports follow the analyst's language (FR-035). - The curated question set must reach 90% correct answers. 

 
## Project-specific constraints

- The MVP is built in 1 week; the spike runs on days 1-2. - Data leaves the machine only to GraphDB and DeepSeek; secrets live in .env and are never committed. - Out of the MVP: manual report editing, chart property editing, report tweaks through the chat, formats other than HTML, multi-user support and authentication. - Chat per-pair controls, DeepSeek tool calling, OpenUI Lang validity and bundle inlining are verified in the first spike (RSK-001 to RSK-004). 

## Governance

This constitution supersedes ad-hoc convention when the two conflict.

- Amendments identify the affected section, exact change, rationale, and migration impact.
- Amendments that change architecture or governance include an ADR in `adr.md` describing business rationale, technical impact, trade-offs, and migration steps.
- Amendments are reviewed through the normal pull-request path before being relied upon.
- Use semantic versioning: MAJOR for removed or redefined guarantees, MINOR for new or materially expanded principles, PATCH for non-semantic corrections.
- The highest applicable impact wins: MAJOR overrides MINOR, and MINOR overrides PATCH. Runtime, framework, breaking API, and security-boundary changes are MAJOR.
- When an amendment is approved, update every affected artifact together, including `docs/PRODUCT.md` (except ADR changes after approval, which are recorded in `adr.md` only), `.sdd/SPEC.md`, `.sdd/PLAN.md`, `.sdd/TASKS.md`, root `config.yaml`, `.sdd/constitution.md`, templates, `adr.md`, automation, CI workflows, and contributor documentation.
- Reviewers cite the conflicting section when rejecting non-compliant work.
- The rendered constitution records its version, effective date, and governance status from the approved project configuration.

**Version**: 1.0.0  
**Ratified**: 2026-11-05  
**Last Amended**: 2026-11-05  

**Amendment log source**: .sdd/CHANGELOG.md
