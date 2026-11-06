"""Tests for app/devtools/check_consistency.py, including a check of the real repository."""

import shutil
from pathlib import Path

from app.devtools import check_consistency
from app.devtools.check_consistency import REPO, run_all

COPIED = [
    "config.yaml",
    "README.md",
    "adr.md",
    "docs/PRODUCT.md",
    "reference/README.md",
    ".nvmrc",
    ".python-version",
    ".devcontainer/Dockerfile",
    ".github/workflows/validators.yml",
    ".pre-commit-config.yaml",
    "scripts/init.sh",
    "scripts/templates/CLAUDE.md.template",
    "backend/pyproject.toml",
    "frontend/package.json",
]


def _copy(tmp_path: Path) -> Path:
    for relative in COPIED:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / relative, target)
    for directory in ("backend", "frontend", "scripts", ".sdd", ".github", ".devcontainer"):
        (tmp_path / directory).mkdir(exist_ok=True)
    (tmp_path / "docs").mkdir(exist_ok=True)
    return tmp_path


def test_repository_is_consistent() -> None:
    assert run_all(REPO) == []


def test_detects_a_version_pin_that_drifted(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    (root / ".nvmrc").write_text("20.19\n", encoding="utf-8")
    assert any("NODE_VERSION" in issue for issue in check_consistency.check_pins(root))


def test_detects_a_command_missing_from_a_copy(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    readme = (root / "README.md").read_text(encoding="utf-8")
    (root / "README.md").write_text(
        readme.replace("ruff check .", "ruff check src"), encoding="utf-8"
    )
    assert any("ruff check ." in issue for issue in check_consistency.check_commands(root))


def test_detects_a_cited_path_that_does_not_exist(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    (root / "README.md").write_text(
        "See `backend/missing.py` and `docs/PRODUCT.md`.\n", encoding="utf-8"
    )
    issues = check_consistency.check_paths(root)
    assert any("backend/missing.py" in issue for issue in issues)


def test_detects_a_claude_template_missing_a_required_reference(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    (root / "scripts/templates/CLAUDE.md.template").write_text("nothing here\n", encoding="utf-8")
    assert len(check_consistency.check_claude_template(root)) == 4
