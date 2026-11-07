"""Regression tests for the connector/storage import cycle."""

import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("module", ["app.main", "app.storage", "app.connector"])
def test_module_imports_in_a_fresh_process(module: str) -> None:
    result = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
