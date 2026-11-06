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

