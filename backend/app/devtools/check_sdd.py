#!/usr/bin/env python3
"""Checks the traceability of the SDD artifacts in .sdd/ (SPEC.md, PLAN.md, TASKS.md).

Development tooling (standard library only); the application never imports it. Run it with
`python backend/app/devtools/check_sdd.py`. The same checks run as a pytest test, so the CI test
gate fails when the artifacts drift apart.

Rules (the constitution's FR > WI > Task hierarchy):
  * every acceptance criterion in SPEC.md has a source, and is cited by at least one task;
  * every task has exactly one existing Work Item, existing dependencies and defined criteria;
  * a Work Item's criteria in PLAN.md equal the union of the criteria of its tasks;
  * every Work Item has an existing parent requirement and existing related requirements;
  * a Work Item is checked in TASKS.md exactly when all of its tasks are checked.
"""

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
AC = r"AC-[A-Z0-9]+-\d+"
FR = r"FR-\d{3}"
WI = r"WI-\d{3}"
TASK = r"TASK-\d{3}"


@dataclass
class WorkItem:
    parent: str = ""
    depends: list[str] = field(default_factory=list)
    criteria: set[str] = field(default_factory=set)
    related: list[str] = field(default_factory=list)


@dataclass
class Task:
    work_item: str
    depends: list[str]
    criteria: set[str]
    done: bool


def _read(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")


def spec_criteria(spec: str) -> tuple[dict[str, str], list[str]]:
    """Return ({criterion: source text}, issues). A source is the text after `**AC-x:**`."""
    found: dict[str, str] = {}
    issues: list[str] = []
    for match in re.finditer(rf"^- \*\*({AC}):\*\*(.*)$", spec, re.MULTILINE):
        criterion, source = match.group(1), match.group(2).strip()
        found[criterion] = source
        if "from derived from" in source:
            issues.append(f"SPEC.md: {criterion} reads 'from derived from'")
        if source in ("from", ""):
            if not criterion.startswith("AC-FR001-"):
                issues.append(f"SPEC.md: {criterion} has no source")
    return found, issues


def spec_requirements(spec: str) -> set[str]:
    return set(re.findall(rf"^#{{3,4}} ({FR})\b", spec, re.MULTILINE))


def plan_work_items(plan: str) -> dict[str, WorkItem]:
    items: dict[str, WorkItem] = {}
    for match in re.finditer(
        rf"^### ({WI}) — .*?(?=^### |^## |\Z)", plan, re.MULTILINE | re.DOTALL
    ):
        block = match.group(0)
        item = WorkItem()
        parent = re.search(rf"\*\*Parent:\*\* ({FR})", block)
        item.parent = parent.group(1) if parent else ""
        depends = re.search(r"\*\*Depends on:\*\* (.*)", block)
        item.depends = re.findall(WI, depends.group(1)) if depends else []
        criteria = re.search(r"\*\*Acceptance criteria:\*\* (.*)", block)
        item.criteria = set(re.findall(AC, criteria.group(1))) if criteria else set()
        related = re.search(r"\*\*Related requirements:\*\* (.*)", block)
        item.related = re.findall(FR, related.group(1)) if related else []
        items[match.group(1)] = item
    return items


def tasks_register(tasks_text: str) -> tuple[dict[str, bool], dict[str, Task], list[str]]:
    """Return ({Work Item: done}, {task id: Task}, issues)."""
    issues: list[str] = []
    work_items: dict[str, bool] = {}
    for match in re.finditer(
        rf"^## ({WI}) — .*?\n\n- \[([ x])\] \*\*Done\*\*", tasks_text, re.MULTILINE
    ):
        if match.group(1) in work_items:
            issues.append(f"TASKS.md: {match.group(1)} appears twice")
        work_items[match.group(1)] = match.group(2) == "x"
    tasks: dict[str, Task] = {}
    pattern = (
        rf"^### ({TASK}) — .*?\n\n- \[([ x])\] \*\*Done\*\*\n- \*\*Work Item:\*\* (.*)\n"
        r"- \*\*Depends on:\*\* (.*)\n- \*\*Acceptance criteria:\*\* (.*)\n"
    )
    for match in re.finditer(pattern, tasks_text, re.MULTILINE):
        task_id = match.group(1)
        if task_id in tasks:
            issues.append(f"TASKS.md: {task_id} appears twice")
        tasks[task_id] = Task(
            work_item=match.group(3).strip(),
            depends=re.findall(TASK, match.group(4)),
            criteria=set(re.findall(AC, match.group(5))),
            done=match.group(2) == "x",
        )
    return work_items, tasks, issues


def check_traceability(root: Path = REPO) -> list[str]:
    spec = _read(root, ".sdd/SPEC.md")
    criteria, issues = spec_criteria(spec)
    requirements = spec_requirements(spec)
    items = plan_work_items(_read(root, ".sdd/PLAN.md"))
    work_items, tasks, register_issues = tasks_register(_read(root, ".sdd/TASKS.md"))
    issues += register_issues

    for task_id, task in tasks.items():
        if task.work_item not in items:
            issues.append(f"{task_id}: Work Item {task.work_item!r} is not in PLAN.md")
        if task.work_item not in work_items:
            issues.append(f"{task_id}: Work Item {task.work_item!r} is not in TASKS.md")
        if not task.criteria:
            issues.append(f"{task_id}: cites no acceptance criterion")
        for criterion in sorted(task.criteria - criteria.keys()):
            issues.append(f"{task_id}: cites {criterion}, which SPEC.md does not define")
        for dependency in task.depends:
            if dependency not in tasks:
                issues.append(f"{task_id}: depends on {dependency}, which does not exist")

    by_work_item: dict[str, list[Task]] = {}
    for task in tasks.values():
        by_work_item.setdefault(task.work_item, []).append(task)
    for wid, item in items.items():
        own = by_work_item.get(wid, [])
        if not own:
            issues.append(f"{wid}: has no tasks in TASKS.md")
            continue
        union = set().union(*(task.criteria for task in own))
        if union != item.criteria:
            issues.append(
                f"{wid}: PLAN.md criteria {sorted(item.criteria)} differ from the union of its "
                f"tasks {sorted(union)}"
            )
        if item.parent not in requirements:
            issues.append(f"{wid}: parent requirement {item.parent!r} is not in SPEC.md")
        for related in item.related:
            if related not in requirements:
                issues.append(f"{wid}: related requirement {related} is not in SPEC.md")
        for dependency in item.depends:
            if dependency not in items:
                issues.append(f"{wid}: depends on {dependency}, which is not in PLAN.md")
        if wid in work_items and work_items[wid] != all(task.done for task in own):
            issues.append(f"{wid}: its checkbox does not match the state of its tasks")
    for wid in work_items:
        if wid not in items:
            issues.append(f"{wid}: is in TASKS.md but not in PLAN.md")

    cited = set().union(*(task.criteria for task in tasks.values())) if tasks else set()
    for criterion in sorted(criteria.keys() - cited):
        issues.append(f"{criterion}: is defined in SPEC.md but no task cites it")
    return issues


def main() -> int:
    issues = check_traceability()
    for issue in issues:
        print(issue, file=sys.stderr)
    if issues:
        print(f"{len(issues)} traceability problem(s) found.", file=sys.stderr)
        return 1
    print("SPEC, PLAN and TASKS are consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
