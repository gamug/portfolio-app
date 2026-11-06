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

