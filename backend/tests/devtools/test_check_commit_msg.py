"""Tests for the commit subject check in app/devtools/check_commit_msg.py."""

import io
from pathlib import Path

import pytest

from app.devtools import check_commit_msg
from app.devtools.check_commit_msg import check, first_subject, main

VALID = [
    "feat(chat): stream the answer [FR-002][WI-008][TASK-020]",
    "docs: update the plan [FR-001][WI-003][TASK-010]",
    "fix(db)!: keep the session on error [FR-011][WI-009][TASK-025]",
    "Merge branch 'main' into feature",
]
INVALID = [
    "update stuff",
    "feat: add chat",
    "feat(chat): stream the answer [FR-2][WI-8][TASK-20]",
    "Feat: add chat [FR-002][WI-008][TASK-020]",
    "",
]


@pytest.mark.parametrize("subject", VALID)
def test_accepts_valid_subjects(subject: str) -> None:
    assert check(subject)


@pytest.mark.parametrize("subject", INVALID)
def test_rejects_invalid_subjects(subject: str) -> None:
    assert not check(subject)


def test_first_subject_skips_comments_and_blank_lines() -> None:
    assert first_subject("\n# comment\nfeat: x [FR-002][WI-008][TASK-020]\nbody") == (
        "feat: x [FR-002][WI-008][TASK-020]"
    )


def test_main_checks_a_message_file(tmp_path: Path) -> None:
    good = tmp_path / "good"
    good.write_text(VALID[0] + "\n", encoding="utf-8")
    bad = tmp_path / "bad"
    bad.write_text("bad message\n", encoding="utf-8")
    assert main(["prog", str(good)]) == 0
    assert main(["prog", str(bad)]) == 1


def test_main_stdin_mode_reports_every_invalid_subject(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("\n".join(VALID + ["nope"]) + "\n"))
    assert main(["prog", "--stdin"]) == 1
    assert "nope" in capsys.readouterr().err

    monkeypatch.setattr("sys.stdin", io.StringIO("\n".join(VALID) + "\n"))
    assert main(["prog", "--stdin"]) == 0


def test_main_stdin_mode_fails_on_empty_input(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert main(["prog", "--stdin"]) == 1
    assert "nothing was checked" in capsys.readouterr().err


def test_main_rejects_bad_usage() -> None:
    assert main(["prog"]) == 2
    assert check_commit_msg.PATTERN.pattern
