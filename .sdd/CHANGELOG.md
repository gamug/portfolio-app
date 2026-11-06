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

- Added `scripts/init.sh` (prerequisite checks with actionable errors, `.env` creation without overwriting, locked installs, git hooks, baseline checks), `.pre-commit-config.yaml` (gitleaks, ruff, mypy, ESLint, Prettier, tsc, and a commit-message hook for Conventional Commits with the `[FR][WI][TASK]` suffix), `scripts/check_commit_msg.py` with tests, `.github/workflows/validators.yml` (gitleaks, ruff, mypy, ESLint and Prettier, tsc, pytest, Vitest, in the configured order), `.gitleaks.toml`, gitleaks 8.30.1 in the devcontainer image, and the Setup, Commands, Recovery and commit sections of `README.md`.
- Verification (built image, clean copy in a fresh git repository): `scripts/init.sh` completes and runs 14 backend tests, 2 frontend tests and all static checks; with `uv` missing it stops with `ERROR: uv is not installed or not on PATH` and a fix; the commit hook rejects `bad message` and accepts a conforming subject; `pre-commit run --all-files` passes all hooks; gitleaks passes the clean tree and catches planted secrets. `.gitleaks.toml` allowlists one upstream reference file (an embedded PostHog project key in `packages/lang-core/src/telemetry/shared.ts`). The first run of the CI workflow on PR #1 passed all seven gates.

## 2026-11-06

### PR #1 review remediation (FR-001, WI-004 to WI-006)

- Moved `packages/`, `examples/`, `spec/` and the OpenUI root workspace files to `reference/`; guarded every job of the nine inherited workflows with a repository condition; pinned the `validators` actions by commit SHA; replaced the pull request template; set the executable bit on the scripts; added an erratum for moved and removed paths to `adr.md`.
- Moved the commit-subject check to `backend/app/devtools` (under ruff, mypy and the mirrored tests); added a CI job that checks every commit subject of a pull request; added `check_consistency.py`, run by pytest, for `config.yaml` commands, tool pins, cited paths and the `CLAUDE.md` template; `scripts/init.sh` creates `CLAUDE.md` from a tracked template (`config.yaml` `agent.init_command_if_missing`); added `scripts/sdd-verify.sh` (validators pinned to a `gamug/sdd-template` commit).
- Corrected the acceptance-criteria traceability (WI-007, WI-010, WI-013, WI-014 and per-task criteria), labelled the derived criteria, fixed the blank source in `SPEC.md`, added TASK-035 (health endpoint) and recorded the deviations from the approved `docs/PRODUCT.md` in `PLAN.md`.
- Verification: see the PR conversation.

