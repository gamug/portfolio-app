#!/usr/bin/env bash
# Verifies the SDD artifacts with the validators of gamug/sdd-template, pinned to the commit used
# to initialize this project. It checks docs/PRODUCT.md and its approval hash, config.yaml and its
# recorded sources, and that .sdd/constitution.md is up to date with config.yaml.
#
# Run it after any change to docs/PRODUCT.md or config.yaml (and re-render first with `render`
# when config.yaml changed: bash scripts/sdd-verify.sh render). These validators serve the SDD
# process; they are not part of the project's hooks or CI.
set -euo pipefail
cd "$(dirname "$0")/.."

TEMPLATE_REPO="https://github.com/gamug/sdd-template.git"
TEMPLATE_COMMIT="5baae825c4ec7dbe525c6d338cd848705e008e12"
TOOLING=".sdd-tooling"   # a checkout of the template; listed in .gitignore

fail() {
  echo "ERROR: $1" >&2
  echo "  Fix: $2" >&2
  exit 1
}

command -v git >/dev/null 2>&1 || fail "git is not installed." "install git."
command -v uv >/dev/null 2>&1 || fail "uv is not installed." "install uv 0.12.1, for example: pip install uv==0.12.1"
PY="$(command -v python3 || command -v python || true)"
[ -n "$PY" ] || fail "python is not installed." "install Python 3."

if [ ! -d "$TOOLING/.git" ]; then
  git clone --quiet "$TEMPLATE_REPO" "$TOOLING" || fail "could not clone $TEMPLATE_REPO." "check network access."
fi
git -C "$TOOLING" fetch --quiet origin "$TEMPLATE_COMMIT" 2>/dev/null || true
git -C "$TOOLING" checkout --quiet "$TEMPLATE_COMMIT" || fail "could not check out $TEMPLATE_COMMIT." "delete $TOOLING and re-run."

SKILL_DIR="$TOOLING/skills/sdd-init"
config() {
  uv run --with-requirements "$SKILL_DIR/scripts/requirements.txt" python "$SKILL_DIR/scripts/validate_config.py" "$@"
}

if [ "${1:-}" = "render" ]; then
  config render
fi
echo "==> validate_discovery.py docs/PRODUCT.md"
"$PY" "$SKILL_DIR/scripts/validate_discovery.py" docs/PRODUCT.md
echo "==> validate_config.py check"
config check
echo "==> validate_config.py render --verify"
config render --verify
echo "SDD artifacts verified."
