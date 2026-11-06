"""Checks the format of the curated evaluation question set, when it has been prepared."""

import json
from pathlib import Path

import pytest

QUESTIONS = Path(__file__).resolve().parent / "questions.json"
REQUIRED = ("id", "question", "expected_answer")
OPTIONAL = ("expected_tools", "notes")


@pytest.mark.skipif(not QUESTIONS.exists(), reason="questions.json has not been prepared yet")
def test_questions_file_has_the_documented_format() -> None:
    items = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    assert isinstance(items, list) and items, "questions.json must be a non-empty list"
    ids = [item.get("id") for item in items]
    assert len(ids) == len(set(ids)), "question ids must be unique"
    for item in items:
        assert set(REQUIRED) <= item.keys(), f"missing a required field in {item.get('id')}"
        assert set(item) <= set(REQUIRED) | set(OPTIONAL), f"unknown field in {item['id']}"
        assert all(isinstance(item[field], str) and item[field].strip() for field in REQUIRED)
