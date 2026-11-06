"""Tests for the commit-message hook in scripts/check_commit_msg.py."""

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_commit_msg.py"
_spec = importlib.util.spec_from_file_location("check_commit_msg", _SCRIPT)
assert _spec is not None and _spec.loader is not None
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
check = _module.check


@pytest.mark.parametrize(
    "subject",
    [
        "feat(chat): stream the answer [FR-002][WI-008][TASK-020]",
        "docs: update the plan [FR-001][WI-003][TASK-010]",
        "fix(db)!: keep the session on error [FR-011][WI-009][TASK-025]",
        "Merge branch 'main' into feature",
    ],
)
def test_accepts_valid_subjects(subject: str) -> None:
    assert check(subject)


@pytest.mark.parametrize(
    "subject",
    [
        "update stuff",
        "feat: add chat",
        "feat(chat): stream the answer [FR-2][WI-8][TASK-20]",
        "Feat: add chat [FR-002][WI-008][TASK-020]",
        "",
    ],
)
def test_rejects_invalid_subjects(subject: str) -> None:
    assert not check(subject)
