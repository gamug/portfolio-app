"""Tests for app/devtools/check_consistency.py, including a check of the real repository."""

import shutil
from pathlib import Path

import pytest

from app.devtools import check_consistency
from app.devtools.check_consistency import DOCUMENTS, REPO, run_all

COPIED = sorted(
    {
        *DOCUMENTS,
        ".nvmrc",
        ".python-version",
        ".devcontainer/Dockerfile",
        ".devcontainer/devcontainer.json",
        "frontend/pnpm-workspace.yaml",
        ".github/workflows/validators.yml",
        ".pre-commit-config.yaml",
        "scripts/init.sh",
        "backend/pyproject.toml",
        "frontend/package.json",
    }
)

# (file, text to replace, replacement, text expected in an issue)
PIN_DRIFTS = [
    (".nvmrc", "22.12", "20.19", "NODE_VERSION"),
    ("frontend/package.json", '">=22.12.0"', '">=20.19.0"', "engines.node"),
    ("frontend/package.json", '"pnpm@10.33.0"', '"pnpm@9.0.0"', "packageManager"),
    (
        ".github/workflows/validators.yml",
        'PNPM_VERSION: "10.33.0"',
        'PNPM_VERSION: "9.0.0"',
        "PNPM_VERSION",
    ),
    (
        ".github/workflows/validators.yml",
        'GITLEAKS_VERSION: "8.30.1"',
        'GITLEAKS_VERSION: "8.0.0"',
        "GITLEAKS_VERSION",
    ),
    ("scripts/init.sh", "pnpm@10.33.0", "pnpm@9.0.0", "pnpm@"),
    ("scripts/init.sh", "uv==0.12.1", "uv==0.0.1", "uv=="),
    ("scripts/init.sh", "gitleaks 8.30.1", "gitleaks 8.0.0", "gitleaks 8.30.1"),
    (
        ".github/workflows/validators.yml",
        'SHELLCHECK_VERSION: "0.11.0"',
        'SHELLCHECK_VERSION: "0.9.0"',
        "SHELLCHECK_VERSION",
    ),
    (
        ".github/workflows/validators.yml",
        'SHELLCHECK_SHA256: "8c3be12b',
        'SHELLCHECK_SHA256: "00000000',
        "SHELLCHECK_SHA256",
    ),
    ("scripts/init.sh", "shellcheck 0.11.0", "shellcheck 0.9.0", "shellcheck 0.11.0"),
    (".python-version", "3.12", "3.13", ".python-version"),
    (
        "backend/pyproject.toml",
        'requires-python = "==3.12.*"',
        'requires-python = ">=3.12"',
        "requires-python",
    ),
]


def _copy(tmp_path: Path) -> Path:
    for relative in COPIED:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / relative, target)
    return tmp_path


def _edit(root: Path, relative: str, old: str, new: str) -> None:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not found in {relative}"
    path.write_text(text.replace(old, new), encoding="utf-8")


def test_repository_is_consistent() -> None:
    assert run_all(REPO) == []


@pytest.mark.parametrize(("relative", "old", "new", "expected"), PIN_DRIFTS)
def test_detects_each_version_pin_that_drifted(
    tmp_path: Path, relative: str, old: str, new: str, expected: str
) -> None:
    root = _copy(tmp_path)
    _edit(root, relative, old, new)
    issues = check_consistency.check_pins(root)
    assert any(expected in issue for issue in issues), issues


def test_detects_a_command_missing_from_a_copy(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    _edit(root, "README.md", "ruff check .", "ruff check src")
    assert any("ruff check ." in issue for issue in check_consistency.check_commands(root))


def test_detects_a_cited_path_that_does_not_exist(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    (root / "README.md").write_text(
        "See `backend/missing.py` and `docs/PRODUCT.md`.\n", encoding="utf-8"
    )
    issues = check_consistency.check_paths(root)
    assert any("backend/missing.py" in issue for issue in issues)


def test_path_check_covers_the_sdd_documents(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    (root / ".sdd/CHANGELOG.md").write_text("Uses `backend/gone.py`.\n", encoding="utf-8")
    issues = check_consistency.check_paths(root)
    assert any(".sdd/CHANGELOG.md" in issue and "backend/gone.py" in issue for issue in issues)


def test_a_renamed_file_cited_by_history_resolves_to_its_new_path() -> None:
    for old, new in check_consistency.RENAMED.items():
        assert not (REPO / old).exists()
        assert (REPO / new).exists()


PRIVACY_BREAKS = [
    (
        ".devcontainer/devcontainer.json",
        '"DO_NOT_TRACK": "1"',
        '"DO_NOT_TRACK": "0"',
        "containerEnv",
    ),
    (
        ".devcontainer/devcontainer.json",
        '"OPENUI_TELEMETRY_DISABLED": "1"',
        '"OPENUI_TELEMETRY_DISABLED": "0"',
        "containerEnv",
    ),
    (
        ".github/workflows/validators.yml",
        'DO_NOT_TRACK: "1"',
        'DO_NOT_TRACK: "0"',
        "validators.yml",
    ),
    ("scripts/init.sh", "export OPENUI_TELEMETRY_DISABLED=1", "echo skipped", "init.sh"),
    (
        "frontend/pnpm-workspace.yaml",
        "allowBuilds:\n",
        'allowBuilds:\n  "@openuidev/lang-core": true\n',
        "pnpm-workspace.yaml allows",
    ),
]


@pytest.mark.parametrize(("relative", "old", "new", "expected"), PRIVACY_BREAKS)
def test_detects_a_privacy_regression(
    tmp_path: Path, relative: str, old: str, new: str, expected: str
) -> None:
    root = _copy(tmp_path)
    _edit(root, relative, old, new)
    issues = check_consistency.check_privacy(root)
    assert any(expected in issue for issue in issues), issues


def test_detects_a_claude_template_missing_a_required_reference(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    (root / "scripts/templates/CLAUDE.md.template").write_text("nothing here\n", encoding="utf-8")
    assert len(check_consistency.check_claude_template(root)) == 4
