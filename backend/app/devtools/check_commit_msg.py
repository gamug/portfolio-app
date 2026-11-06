#!/usr/bin/env python3
"""Commit subject check: Conventional Commits with the [FR-xxx][WI-xxx][TASK-xxx] suffix.

Development tooling (standard library only); the application never imports it.

Usage:
    check_commit_msg.py <commit message file>   commit-msg hook: checks the first subject line
    check_commit_msg.py --stdin                 CI: checks every line of stdin as a subject;
                                                empty input fails, so a failed `git log` cannot pass

Example subject: feat(chat): stream the answer [FR-002][WI-008][TASK-020]
"""

import re
import sys

TYPES = "feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert"
PATTERN = re.compile(
    rf"^({TYPES})(\([a-z0-9._-]+\))?!?: \S.* \[FR-\d{{3}}\]\[WI-\d{{3}}\]\[TASK-\d{{3}}\]$"
)
EXEMPT_PREFIXES = ("Merge ", 'Revert "', "fixup! ", "squash! ")
EXPECTED = (
    "Expected: type(scope): imperative summary [FR-002][WI-008][TASK-020]\n"
    f"Types: {TYPES.replace('|', ', ')}"
)


def check(subject: str) -> bool:
    """Return True when the subject line is acceptable."""
    if subject.startswith(EXEMPT_PREFIXES):
        return True
    return PATTERN.match(subject) is not None


def first_subject(message: str) -> str:
    """Return the first line that is neither blank nor a git comment."""
    for line in message.splitlines():
        if line.strip() and not line.startswith("#"):
            return line
    return ""


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] == "--stdin":
        subjects = [line for line in sys.stdin.read().splitlines() if line.strip()]
        if not subjects:
            print("No commit subjects received: nothing was checked.", file=sys.stderr)
            return 1
        invalid = [subject for subject in subjects if not check(subject)]
        for subject in invalid:
            print(f"Invalid commit subject: {subject!r}", file=sys.stderr)
        if invalid:
            print(EXPECTED, file=sys.stderr)
            return 1
        print(f"{len(subjects)} commit subject(s) checked.")
        return 0
    if len(argv) != 2:
        print("usage: check_commit_msg.py <commit message file> | --stdin", file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as handle:
        subject = first_subject(handle.read())
    if check(subject):
        return 0
    print(f"Invalid commit subject: {subject!r}", file=sys.stderr)
    print(EXPECTED, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
