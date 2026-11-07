# portfolio-app-new

A chat interface to a GraphDB knowledge graph, with a report panel beside it. The analyst chats with the graph, marks the useful question-answer pairs, presses **Generate Report**, and downloads the result as one self-contained HTML file. The report view is built on [OpenUI](https://github.com/thesysdev/openui); this repository is a fork of `thesysdev/openui` (MIT: `LICENSE` keeps the upstream notice and adds this project's copyright).

The project follows specification-driven development:

| Path | Content |
| :--- | :--- |
| `docs/PRODUCT.md` | Approved discovery: use cases, requirements, stack, risks and roadmap |
| `adr.md` | Architecture decision records (live) |
| `config.yaml` | Project configuration, with sources in `docs/PRODUCT.md` |
| `.sdd/` | Constitution, specification, plan, tasks and changelog |
| `backend/` | FastAPI backend (`app/`, `tests/`) |
| `frontend/` | Vite + React frontend |
| `reference/` | OpenUI source, examples and language specification, for reading only (see `reference/README.md`) |

## Setup

The supported environment is the VS Code devcontainer (`.devcontainer/`): Python 3.12, Node.js 22.12, pnpm 10.33.0, uv 0.12.1 and gitleaks 8.30.1. Opening the folder in the container runs `scripts/init.sh`.

Without the container, install the prerequisites listed below and run the script from the repository root:

```bash
bash scripts/init.sh
```

The script is safe to re-run. It checks the prerequisites, creates `.env` from `.env.example` if it is missing (it never overwrites it), installs the locked dependencies, installs the git hooks, and runs the baseline checks. Then fill `.env`: `LLM_API_KEY` (DeepSeek) and a **read-only** GraphDB user in `KG_USER` and `KG_PASSWORD`. `.env` is never committed.

Prerequisites outside the container: git, python3, uv 0.12.1, Node.js 22.12 or newer (`.nvmrc`), pnpm 10.33.0, gitleaks 8.30.1, shellcheck 0.11.0. GraphDB 11.5 runs separately; the container reaches it at `KG_HOST` (default `http://host.docker.internal:7200`).

## Run the app locally

Prerequisites: GraphDB 11.5 is reachable at `KG_HOST`, and `.env` exists with the DeepSeek key and the read-only GraphDB user. `scripts/init.sh` creates `.env` from `.env.example` when it is missing. Fill it in and never `source` it in a shell; parse it as a dotenv file.

Terminal 1, backend:

```bash
cd backend
uv run uvicorn app.main:app --port 8000
```

Terminal 2, frontend:

```bash
cd frontend
pnpm dev
```

Open <http://localhost:5173>. In VS Code, if the browser cannot reach the page, open the **Ports** tab and use **Open in Browser** for port 5173.

### Troubleshooting

- **Blank page or "Waiting for localhost":** Vite was listening on IPv6 only. `server.host: true` in `frontend/vite.config.ts` makes it listen on `0.0.0.0`; restart `pnpm dev`.
- **Repeated `GET /health 404` lines in the backend log:** harmless. VS Code probes the port, and the backend has no `/health` endpoint by the TASK-035 removal.
- **`ImportError ... circular import`:** fixed in PR #18; update `main`.

### What works today

Sessions can be created, renamed and deleted with confirmation. The chat panel asks a question, streams the raw answer, then reloads and renders the stored OpenUI Lang for each pair. Each pair has a relevance toggle and a single-pair delete action. The report panel sits beside the chat: **Generate Report** streams progress and the report, **Cancel** stops the request and keeps the previous report, and a failed generation keeps the partial report flagged incomplete. The report is shown again when the session is selected. A theme control in the header switches between system, light and dark, follows the system setting by default and remembers the choice.

### What is not built yet

There is no report download or erase action yet, and manual report editing is out of the MVP. The report download is TASK-030 and the erase actions are WI-013.

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

CI (`.github/workflows/validators.yml`) runs gitleaks, ruff, mypy, ESLint and Prettier, tsc, pytest and Vitest, in that order. A separate job checks every commit subject of the pull request with the same rule as the hook, because the hook only runs where `scripts/init.sh` installed it. Pull requests are merged with a merge commit (squash and rebase merging are disabled in the repository settings), so the PR title is not used as a commit subject. The pytest gate also runs two repository checks from `backend/app/devtools/`: `check_consistency.py` (fails when `config.yaml` commands, tool versions, cited repository paths or the `CLAUDE.md` template drift apart) and `check_sdd.py` (traceability of `.sdd/SPEC.md`, `PLAN.md` and `TASKS.md`). A `shellcheck` job lints `scripts/*.sh`.

The GitHub ruleset `main protection` blocks deleting `main` and force-pushes; it does not require pull requests or the CI checks (accepted by the owners), so the pull-request-only rule holds by convention.

## Privacy

The project states that data leaves the machine only to GraphDB and DeepSeek. The OpenUI packages and CLI can send telemetry to a third party, so `DO_NOT_TRACK=1` and `OPENUI_TELEMETRY_DISABLED=1` are set in the devcontainer, in CI and in `scripts/init.sh`, and the install script of `@openuidev/lang-core` (it only sends installation telemetry) is not allowed to run. Set the same variables in your shell if you run `pnpm install` or the `openui` CLI outside the container. `check_consistency.py` fails if any of this is removed.

## Evaluation question set

The curated question set behind the 90% accuracy target lives in `backend/tests/evaluation/` (format and rules in its README). The repository is public, so it may contain only facts the owners approve for publication.

## SDD artifacts

`docs/PRODUCT.md`, `config.yaml` and `.sdd/constitution.md` are checked by the validators of [gamug/sdd-template](https://github.com/gamug/sdd-template), pinned to a commit in `scripts/sdd-verify.sh`:

```bash
bash scripts/sdd-verify.sh          # discovery approval hash, config sources, constitution up to date
bash scripts/sdd-verify.sh render   # after editing config.yaml: re-render the constitution, then verify
```

These validators serve the SDD process and are not part of the hooks or CI. The script keeps a gitignored checkout in `.sdd-tooling/`. `.sdd/constitution.md` is generated: change `config.yaml` (and its row in `docs/PRODUCT.md`), then render.

`CLAUDE.md` is local and not tracked; `scripts/init.sh` creates it from `scripts/templates/CLAUDE.md.template` when it is missing. `AGENTS.md` (read by OpenCode agents) is the same file, local and not tracked, created from the same template.

## Recovery

| Symptom | Fix |
| :--- | :--- |
| `ERROR: <tool> is not installed or not on PATH` | Install the tool named in the message, then re-run `bash scripts/init.sh`. |
| Node.js is older than 22.12.0 | Switch to the version in `.nvmrc` (`fnm use` or `nvm use`). |
| Dependency install fails | Check network access; if a lockfile is out of sync, run `uv lock --directory backend` or `pnpm --dir frontend install` and commit the result. |
| A hook blocks a commit | Fix the reported problem (never bypass hooks). A gitleaks finding means a secret is staged: remove it, and rotate it if it was ever pushed. |
| GraphDB is unreachable from the container | Check that GraphDB runs on the host and that `KG_HOST` is correct; the container maps `host.docker.internal` to the host. |
| Broken environment | Re-run `bash scripts/init.sh`; if that fails, rebuild the devcontainer image and run it again. |
