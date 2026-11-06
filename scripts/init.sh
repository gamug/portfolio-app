#!/usr/bin/env bash
# Reproduces the development environment from a clean checkout (see README.md, "Setup").
# Safe to re-run: it never overwrites .env and fails with an actionable message when a
# prerequisite is missing.
set -euo pipefail
cd "$(dirname "$0")/.."

fail() {
  echo "ERROR: $1" >&2
  echo "  Fix: $2" >&2
  exit 1
}

need() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is not installed or not on PATH." "$2"
}

need git "install git."
need python3 "install Python 3 (it runs the commit-message hook); the project itself uses Python $(cat .python-version), which uv installs."
need uv "install uv 0.12.1, for example: pip install uv==0.12.1"
need node "install Node.js $(cat .nvmrc) or newer, for example with fnm or nvm (the version is pinned in .nvmrc)."
need pnpm "install pnpm 10.33.0, for example: npm install -g pnpm@10.33.0"
need gitleaks "install gitleaks 8.30.1 (the devcontainer image includes it): https://github.com/gitleaks/gitleaks/releases"

node_version="$(node -p 'process.versions.node')"
required_node="22.12.0"
if [ "$(printf '%s\n%s\n' "$required_node" "$node_version" | sort -V | head -n1)" != "$required_node" ]; then
  fail "Node.js $node_version is older than $required_node." "switch to the version in .nvmrc (for example: fnm use, or nvm use)."
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Fill LLM_API_KEY, KG_USER and KG_PASSWORD (a read-only GraphDB user)."
fi

if [ ! -f CLAUDE.md ]; then
  cp scripts/templates/CLAUDE.md.template CLAUDE.md
  echo "Created CLAUDE.md (local, not tracked in Git) from scripts/templates/CLAUDE.md.template."
fi

echo "==> Installing dependencies"
uv sync --locked --directory backend || fail "the backend dependencies could not be installed." "check network access, and that backend/uv.lock is in sync (uv lock --directory backend)."
pnpm --dir frontend install --frozen-lockfile || fail "the frontend dependencies could not be installed." "check network access, and that frontend/pnpm-lock.yaml is in sync (pnpm --dir frontend install)."

echo "==> Installing git hooks"
if git rev-parse --git-dir >/dev/null 2>&1; then
  uv run --project backend pre-commit install
else
  echo "Not a git checkout; skipping git hooks."
fi

echo "==> Running baseline checks"
uv run --directory backend pytest
pnpm --dir frontend test --run
uv run --directory backend ruff check .
pnpm --dir frontend lint
uv run --directory backend ruff format --check .
pnpm --dir frontend exec prettier --check .
uv run --directory backend mypy app
pnpm --dir frontend exec tsc --noEmit

echo "Environment ready."
for key in LLM_API_KEY KG_USER KG_PASSWORD; do
  if ! grep -Eq "^${key}=.+" .env; then
    echo "Reminder: ${key} is empty in .env."
  fi
done
