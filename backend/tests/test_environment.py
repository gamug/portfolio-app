"""Baseline checks that the backend toolchain and the approved dependencies are installed."""

import importlib
import sys

import pytest


def test_python_version_is_3_12() -> None:
    assert sys.version_info[:2] == (3, 12)


@pytest.mark.parametrize("module", ["fastapi", "uvicorn", "openai", "dotenv"])
def test_approved_dependencies_import(module: str) -> None:
    assert importlib.import_module(module) is not None
