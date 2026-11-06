#!/usr/bin/env python3
"""Checks that the documents, the configuration and the automation agree with each other.

Development tooling (standard library only); the application never imports it. Run it from
anywhere: `python backend/app/devtools/check_consistency.py`. The same checks run as a pytest
test, so the CI test gate fails when they drift.

Checks:
  commands  every command in config.yaml appears in each file that repeats it
  pins      tool versions agree between the Dockerfile, .nvmrc, package.json, CI and init.sh
  paths     repository paths cited in backticks in the documents exist
  claude    the CLAUDE.md template references every file config.yaml requires
  privacy   telemetry is switched off where dependencies are installed, and the one
            dependency install script that only sends telemetry is not allowed to run
"""

import json
import re
import sys
from collections.abc import Callable
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

# Files that repeat config.yaml commands, and which commands each must contain.
COMMAND_COPIES: dict[str, tuple[str, ...]] = {
    "README.md": ("dependency_install", "test", "lint", "format_check", "type_check", "pre_commit"),
    ".github/workflows/validators.yml": (
        "dependency_install",
        "ci_test",
        "lint",
        "format_check",
        "type_check",
    ),
    "scripts/init.sh": ("dependency_install", "test", "lint", "format_check", "type_check"),
    ".pre-commit-config.yaml": ("lint", "format_check", "type_check"),
}

DOCUMENTS = (
    "docs/PRODUCT.md",
    "adr.md",
    "README.md",
    "reference/README.md",
    "config.yaml",
    ".sdd/SPEC.md",
    ".sdd/PLAN.md",
    ".sdd/TASKS.md",
    ".sdd/CHANGELOG.md",
    ".github/pull_request_template.md",
    "scripts/templates/CLAUDE.md.template",
)
# Files that were renamed or moved; history (the changelog) may still cite the old path.
RENAMED = {
    "scripts/check_commit_msg.py": "backend/app/devtools/check_commit_msg.py",
    "backend/tests/test_commit_msg.py": "backend/tests/devtools/test_check_commit_msg.py",
}
PATH_PREFIXES = (
    "backend/",
    "frontend/",
    "scripts/",
    "docs/",
    ".sdd/",
    ".github/",
    ".devcontainer/",
    "reference/",
    "packages/",
    "examples/",
    "spec/",
    "templates/",
)
# Paths cited as they were before the move into reference/ (see the erratum in adr.md).
MOVED_TO_REFERENCE = ("packages/", "examples/", "spec/")
# `templates/` was removed; the erratum in adr.md must give its upstream location.
REMOVED_UPSTREAM = ("templates/",)
UPSTREAM_TEMPLATES_URL = "https://github.com/thesysdev/openui/tree/main/templates"
# Paths created at runtime, by a later Work Item, or by the owners (the evaluation question set
# is prepared by gamug and dova before TASK-018), or that are examples.
RUNTIME_PATHS = (
    "backend/data/",
    "frontend/src/generated",
    "backend/tests/evaluation/questions.json",
)


def _read(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")


def config_commands(root: Path = REPO) -> dict[str, str]:
    """Read the `commands:` mapping of config.yaml (flat `key: value` lines)."""
    commands: dict[str, str] = {}
    in_commands = False
    for line in _read(root, "config.yaml").splitlines():
        if line.startswith("commands:"):
            in_commands = True
            continue
        if in_commands:
            if line and not line.startswith(" "):
                break
            match = re.match(r"^  (\w+): (.+)$", line)
            if match:
                commands[match.group(1)] = match.group(2).strip()
    return commands


def config_list(root: Path, key: str) -> list[str]:
    """Read a block list (`key:` followed by `- item` lines) from config.yaml."""
    text = _read(root, "config.yaml")
    match = re.search(rf"^\s+{re.escape(key)}:\n((?:\s+- .*\n)+)", text, re.MULTILINE)
    if not match:
        return []
    return [item.strip()[2:].strip() for item in match.group(1).splitlines()]


def check_commands(root: Path = REPO) -> list[str]:
    commands = config_commands(root)
    issues: list[str] = []
    for relative, keys in COMMAND_COPIES.items():
        text = _read(root, relative)
        for key in keys:
            if key not in commands:
                issues.append(f"config.yaml has no commands.{key}")
                continue
            for atom in commands[key].split(" && "):
                if atom not in text:
                    issues.append(f"{relative} does not contain `{atom}` (commands.{key})")
    return issues


def _arg(dockerfile: str, name: str) -> str:
    match = re.search(rf"^ARG {name}=(\S+)", dockerfile, re.MULTILINE)
    return match.group(1) if match else ""


def check_pins(root: Path = REPO) -> list[str]:
    issues: list[str] = []
    dockerfile = _read(root, ".devcontainer/Dockerfile")
    nvmrc = _read(root, ".nvmrc").strip()
    node = _arg(dockerfile, "NODE_VERSION")
    if not (node == nvmrc or node.startswith(nvmrc + ".")):
        issues.append(f".nvmrc ({nvmrc}) and Dockerfile NODE_VERSION ({node}) disagree")

    package = json.loads(_read(root, "frontend/package.json"))
    engines = str(package.get("engines", {}).get("node", ""))
    if engines != f">={node}":
        issues.append(f"frontend/package.json engines.node ({engines}) is not >={node}")

    pnpm = _arg(dockerfile, "PNPM_VERSION")
    manager = str(package.get("packageManager", ""))
    if manager != f"pnpm@{pnpm}":
        issues.append(f"package.json packageManager ({manager}) is not pnpm@{pnpm}")
    workflow = _read(root, ".github/workflows/validators.yml")
    workflow_pnpm = re.search(r'PNPM_VERSION: "([^"]+)"', workflow)
    if not workflow_pnpm or workflow_pnpm.group(1) != pnpm:
        issues.append(f"validators.yml PNPM_VERSION does not match Dockerfile ({pnpm})")
    init = _read(root, "scripts/init.sh")
    if f"pnpm@{pnpm}" not in init:
        issues.append(f"scripts/init.sh does not mention pnpm@{pnpm}")

    uv = _arg(dockerfile, "UV_VERSION")
    if f"uv=={uv}" not in init:
        issues.append(f"scripts/init.sh does not mention uv=={uv}")

    gitleaks = _arg(dockerfile, "GITLEAKS_VERSION")
    workflow_gitleaks = re.search(r'GITLEAKS_VERSION: "([^"]+)"', workflow)
    if not workflow_gitleaks or workflow_gitleaks.group(1) != gitleaks:
        issues.append(f"validators.yml GITLEAKS_VERSION does not match Dockerfile ({gitleaks})")
    if f"gitleaks {gitleaks}" not in init:
        issues.append(f"scripts/init.sh does not mention gitleaks {gitleaks}")

    shellcheck = _arg(dockerfile, "SHELLCHECK_VERSION")
    workflow_shellcheck = re.search(r'SHELLCHECK_VERSION: "([^"]+)"', workflow)
    if not workflow_shellcheck or workflow_shellcheck.group(1) != shellcheck:
        issues.append(f"validators.yml SHELLCHECK_VERSION does not match Dockerfile ({shellcheck})")
    workflow_sha = re.search(r'SHELLCHECK_SHA256: "([0-9a-f]{64})"', workflow)
    if not workflow_sha or workflow_sha.group(1) != _arg(dockerfile, "SHELLCHECK_SHA256_X64"):
        issues.append(
            "validators.yml SHELLCHECK_SHA256 differs from the Dockerfile x86_64 checksum"
        )
    if f"shellcheck {shellcheck}" not in init:
        issues.append(f"scripts/init.sh does not mention shellcheck {shellcheck}")

    python = _read(root, ".python-version").strip()
    if f"python:{python}" not in dockerfile:
        issues.append(f".python-version ({python}) is not the Dockerfile base image")
    if f'requires-python = "=={python}.*"' not in _read(root, "backend/pyproject.toml"):
        issues.append(f"backend/pyproject.toml requires-python is not =={python}.*")
    return issues


def _candidate_paths(text: str) -> set[str]:
    found: set[str] = set()
    for token in re.findall(r"`([^`\s]+)`", text):
        token = token.rstrip(".,;:)")
        if not token.startswith(PATH_PREFIXES):
            continue
        if any(mark in token for mark in "<>{}*|") or "..." in token or "://" in token:
            continue
        if token.startswith(RUNTIME_PATHS):
            continue
        found.add(token)
    return found


def check_paths(root: Path = REPO) -> list[str]:
    issues: list[str] = []
    erratum_ok = UPSTREAM_TEMPLATES_URL in _read(root, "adr.md")
    for document in DOCUMENTS:
        for token in sorted(_candidate_paths(_read(root, document))):
            if token.startswith(REMOVED_UPSTREAM):
                if not erratum_ok:
                    issues.append(f"{document}: `{token}` was removed and adr.md has no erratum")
                continue
            target = RENAMED.get(token, token)
            if target.startswith(MOVED_TO_REFERENCE):
                target = f"reference/{target}"
            if not (root / target).exists():
                issues.append(f"{document}: `{token}` does not exist (looked for {target})")
    return issues


def check_claude_template(root: Path = REPO) -> list[str]:
    template = _read(root, "scripts/templates/CLAUDE.md.template")
    required = config_list(root, "must_reference")
    if not required:
        return ["config.yaml agent.must_reference could not be read"]
    return [
        f"scripts/templates/CLAUDE.md.template does not reference `{item}`"
        for item in required
        if item not in template
    ]


TELEMETRY_OFF = {"DO_NOT_TRACK": "1", "OPENUI_TELEMETRY_DISABLED": "1"}
# Package whose install script only sends installation telemetry; it must not be allowed to run.
TELEMETRY_PACKAGE = "@openuidev/lang-core"


def check_privacy(root: Path = REPO) -> list[str]:
    """The project states that data leaves the machine only to GraphDB and DeepSeek."""
    issues: list[str] = []
    devcontainer = json.loads(_read(root, ".devcontainer/devcontainer.json"))
    container_env = devcontainer.get("containerEnv", {})
    workflow = _read(root, ".github/workflows/validators.yml")
    init = _read(root, "scripts/init.sh")
    for name, value in TELEMETRY_OFF.items():
        if container_env.get(name) != value:
            issues.append(f"devcontainer.json containerEnv does not set {name}={value}")
        if f'{name}: "{value}"' not in workflow:
            issues.append(f".github/workflows/validators.yml does not set {name}={value}")
        if f"export {name}={value}" not in init:
            issues.append(f"scripts/init.sh does not export {name}={value}")
    for relative in ("frontend/pnpm-workspace.yaml", "frontend/package.json"):
        allowed = [
            line
            for line in _read(root, relative).splitlines()
            if TELEMETRY_PACKAGE in line and not line.lstrip().startswith("#")
        ]
        if allowed:
            issues.append(f"{relative} allows the install script of {TELEMETRY_PACKAGE}")
    return issues


CHECKS: dict[str, Callable[[Path], list[str]]] = {
    "commands": check_commands,
    "pins": check_pins,
    "paths": check_paths,
    "claude": check_claude_template,
    "privacy": check_privacy,
}


def run_all(root: Path = REPO) -> list[str]:
    issues: list[str] = []
    for name, check in CHECKS.items():
        issues.extend(f"[{name}] {issue}" for issue in check(root))
    return issues


def main() -> int:
    issues = run_all()
    for issue in issues:
        print(issue, file=sys.stderr)
    if issues:
        print(f"{len(issues)} consistency problem(s) found.", file=sys.stderr)
        return 1
    print("Documents, configuration and automation are consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
