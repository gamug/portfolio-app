import asyncio
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from app.connector.models import ConnectorError
from app.connector.openui import DEFAULT_PROMPT_PATH, OpenUIConverter
from app.connector.settings import Settings


class FakeCompletions:
    def __init__(self, content: str = "", error: Exception | None = None) -> None:
        self.content = content
        self.error = error
        self.calls = 0
        self.calls_args: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls += 1
        self.calls_args.append(kwargs)
        if self.error is not None:
            raise self.error
        message = SimpleNamespace(content=self.content)
        choice = SimpleNamespace(message=message)
        usage = SimpleNamespace(model_dump=lambda: {"totalTokens": 7})
        return SimpleNamespace(choices=[choice], usage=usage)


@dataclass
class FakeLLM:
    completions: FakeCompletions

    @property
    def chat(self) -> Any:
        return SimpleNamespace(completions=self.completions)


def _settings() -> Settings:
    return Settings(
        kg_host="http://graphdb:7200",
        kg_user="reader",
        kg_password="secret",
        kg_agent_id="agent-1",
        chat_mode="chat",
        llm_api_key="llm-secret",
        llm_model="deepseek-chat",
        llm_url="https://api.deepseek.com",
        chat_timeout_seconds=30,
        tool_max_iterations=4,
    )


def _converter(tmp_path: Path, completions: FakeCompletions) -> OpenUIConverter:
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("SYSTEM PROMPT", encoding="utf-8")
    return OpenUIConverter(_settings(), llm=FakeLLM(completions), prompt_path=prompt)


def test_default_openui_prompt_is_committed() -> None:
    assert DEFAULT_PROMPT_PATH.is_file()
    assert DEFAULT_PROMPT_PATH.stat().st_size > 1000


def test_converts_and_strips_fences(tmp_path: Path) -> None:
    completions = FakeCompletions("```\nroot = Card([])\n```")
    result = asyncio.run(_converter(tmp_path, completions).convert("answer"))
    assert result.text == "root = Card([])"
    assert result.total_tokens == 7
    assert completions.calls == 1


def test_spanish_conversion_instruction_is_passed(tmp_path: Path) -> None:
    completions = FakeCompletions("root = Card([])")
    asyncio.run(_converter(tmp_path, completions).convert("respuesta", "es"))
    system = str(completions.calls_args[0]["messages"][0]["content"])
    assert "español" in system


def test_empty_conversion_is_an_error(tmp_path: Path) -> None:
    completions = FakeCompletions("   ")
    with pytest.raises(ConnectorError, match="empty"):
        asyncio.run(_converter(tmp_path, completions).convert("answer"))
    assert completions.calls == 1


def test_conversion_error_is_not_retried(tmp_path: Path) -> None:
    completions = FakeCompletions(error=RuntimeError("provider failed"))
    with pytest.raises(ConnectorError, match="conversion failed"):
        asyncio.run(_converter(tmp_path, completions).convert("answer"))
    assert completions.calls == 1
