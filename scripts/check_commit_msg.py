#!/usr/bin/env python3
"""Commit-message hook: Conventional Commits with the [FR-xxx][WI-xxx][TASK-xxx] suffix.

Usage: check_commit_msg.py <commit message file>
Example subject: feat(chat): stream the answer [FR-002][WI-008][TASK-020]
"""

import re
import sys

TYPES = "feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert"
PATTERN = re.compile(
    rf"^({TYPES})(\([a-z0-9._-]+\))?!?: \S.* \[FR-\d{{3}}\]\[WI-\d{{3}}\]\[TASK-\d{{3}}\]$"
)


def check(subject: str) -> bool:
    """Return True when the subject line is acceptable."""
    if subject.startswith(("Merge ", "Revert \"", "fixup! ", "squash! ")):
        return True
    return PATTERN.match(subject) is not None


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_commit_msg.py <commit message file>", file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    subject = next((line for line in lines if line.strip() and not line.startswith("#")), "")
    if check(subject):
        return 0
    print(f"Invalid commit subject: {subject!r}", file=sys.stderr)
    print(
        "Expected: type(scope): imperative summary [FR-002][WI-008][TASK-020]\n"
        f"Types: {TYPES.replace('|', ', ')}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
