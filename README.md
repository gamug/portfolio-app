# portfolio-app-new

A chat interface to a GraphDB knowledge graph, with a report panel beside it. The analyst chats with the graph, marks the useful question-answer pairs, presses **Generate Report**, and downloads the result as one self-contained HTML file. The report view is built on [OpenUI](https://github.com/thesysdev/openui); this repository is a fork of `thesysdev/openui` (MIT, see `LICENSE`).

The project follows specification-driven development:

| Path | Content |
| :--- | :--- |
| `docs/PRODUCT.md` | Approved discovery: use cases, requirements, stack, risks and roadmap |
| `adr.md` | Architecture decision records (live) |
| `config.yaml` | Project configuration, with sources in `docs/PRODUCT.md` |
| `.sdd/` | Constitution, specification, plan, tasks and changelog |
| `backend/` | FastAPI backend (`app/`, `tests/`) |
| `frontend/` | Vite + React frontend |
| `packages/`, `examples/`, `spec/` | OpenUI source, examples and language specification, kept for reference |

## Setup

The supported environment is the VS Code devcontainer (`.devcontainer/`): Python 3.12, Node.js 22.12, pnpm 10.33.0, uv 0.12.1 and gitleaks 8.30.1. Opening the folder in the container runs `scripts/init.sh`.

Without the container, install the prerequisites listed below and run the script from the repository root:

```bash
bash scripts/init.sh
```

The script is safe to re-run. It checks the prerequisites, creates `.env` from `.env.example` if it is missing (it never overwrites it), installs the locked dependencies, installs the git hooks, and runs the baseline checks. Then fill `.env`: `LLM_API_KEY` (DeepSeek) and a **read-only** GraphDB user in `KG_USER` and `KG_PASSWORD`. `.env` is never committed.

Prerequisites outside the container: git, python3, uv 0.12.1, Node.js 22.12 or newer (`.nvmrc`), pnpm 10.33.0, gitleaks 8.30.1. GraphDB 11.5 runs separately; the container reaches it at `KG_HOST` (default `http://host.docker.internal:7200`).

## Commands

Run from the repository root (they are fixed in `config.yaml`):

| Purpose | Command |
| :--- | :--- |
| Install | `uv sync --locked --directory backend && pnpm --dir frontend install --frozen-lockfile` |
| Test | `uv run --directory backend pytest && pnpm --dir frontend test --run` |
| Lint | `uv run --directory backend ruff check . && pnpm --dir frontend lint` |
| Format check | `uv run --directory backend ruff format --check . && pnpm --dir frontend exec prettier --check .` |
| Type check | `uv run --directory backend mypy app && pnpm --dir frontend exec tsc --noEmit` |
| All local gates | `uv run --directory backend pre-commit run --all-files` |

## Commits and pull requests

`main` changes only through pull requests. Commit subjects follow Conventional Commits with the traceability suffix, enforced by the `commit-msg` hook:

```text
feat(chat): stream the answer [FR-002][WI-008][TASK-020]
```

CI (`.github/workflows/validators.yml`) runs gitleaks, ruff, mypy, ESLint and Prettier, tsc, pytest and Vitest, in that order.

## Recovery

| Symptom | Fix |
| :--- | :--- |
| `ERROR: <tool> is not installed or not on PATH` | Install the tool named in the message, then re-run `bash scripts/init.sh`. |
| Node.js is older than 22.12.0 | Switch to the version in `.nvmrc` (`fnm use` or `nvm use`). |
| Dependency install fails | Check network access; if a lockfile is out of sync, run `uv lock --directory backend` or `pnpm --dir frontend install` and commit the result. |
| A hook blocks a commit | Fix the reported problem (never bypass hooks). A gitleaks finding means a secret is staged: remove it, and rotate it if it was ever pushed. |
| GraphDB is unreachable from the container | Check that GraphDB runs on the host and that `KG_HOST` is correct; the container maps `host.docker.internal` to the host. |
| Broken environment | Re-run `bash scripts/init.sh`; if that fails, rebuild the devcontainer image and run it again. |
