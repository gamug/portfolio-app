"""Tests for app/devtools/check_sdd.py, including a check of the real .sdd/ artifacts."""

import shutil
from pathlib import Path

import pytest

from app.devtools.check_sdd import REPO, check_traceability

FILES = [".sdd/SPEC.md", ".sdd/PLAN.md", ".sdd/TASKS.md"]


def _copy(tmp_path: Path) -> Path:
    for relative in FILES:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / relative, target)
    return tmp_path


def _edit(root: Path, relative: str, old: str, new: str) -> None:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not found in {relative}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _append(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


def test_sdd_artifacts_are_consistent() -> None:
    assert check_traceability(REPO) == []


def test_detects_a_task_citing_an_undefined_criterion(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    _edit(
        root,
        ".sdd/TASKS.md",
        "- **Acceptance criteria:** AC-FR002-01\n",
        "- **Acceptance criteria:** AC-FR002-99\n",
    )
    assert any("AC-FR002-99" in issue for issue in check_traceability(root))


def test_detects_a_work_item_whose_criteria_differ_from_its_tasks(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    _edit(
        root,
        ".sdd/PLAN.md",
        "**Acceptance criteria:** AC-SPIKE-01, AC-SPIKE-02",
        "**Acceptance criteria:** AC-SPIKE-01",
    )
    assert any("WI-007" in issue and "differ" in issue for issue in check_traceability(root))


def test_detects_an_orphan_criterion(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    _append(root, ".sdd/SPEC.md", "\n- **AC-FR002-77:** from nowhere\n")
    issues = check_traceability(root)
    assert any("AC-FR002-77" in issue and "no task cites it" in issue for issue in issues)


def test_detects_a_dependency_that_does_not_exist(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    _edit(root, ".sdd/TASKS.md", "- **Depends on:** TASK-016\n", "- **Depends on:** TASK-999\n")
    assert any("TASK-999" in issue for issue in check_traceability(root))


def test_detects_a_checked_work_item_with_unchecked_tasks(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    _edit(
        root,
        ".sdd/TASKS.md",
        "## WI-007 — Technical spike\n\n- [ ] **Done**",
        "## WI-007 — Technical spike\n\n- [x] **Done**",
    )
    assert any("WI-007" in issue and "checkbox" in issue for issue in check_traceability(root))


@pytest.mark.parametrize("bad", ["from derived from FR-021", "from"])
def test_detects_a_criterion_without_a_proper_source(tmp_path: Path, bad: str) -> None:
    root = _copy(tmp_path)
    _append(root, ".sdd/SPEC.md", f"\n- **AC-FR002-88:** {bad}\n")
    assert any("AC-FR002-88" in issue for issue in check_traceability(root))
