from pathlib import Path

import pytest

from app.connector.settings import Settings, SettingsError

BASE = {
    "KG_HOST": "http://graphdb:7200",
    "KG_USER": "reader",
    "KG_PASSWORD": "secret",
    "KG_AGENT_ID": "agent-1",
    "LLM_API_KEY": "llm-secret",
    "LLM_MODEL": "deepseek-chat",
    "LLM_URL": "https://api.deepseek.com",
}


def _env(tmp_path: Path, extra: dict[str, str] | None = None) -> Path:
    values = {**BASE, **(extra or {})}
    path = tmp_path / ".env"
    path.write_text("\n".join(f"{key}={value}" for key, value in values.items()) + "\n")
    return path


def test_default_mode_is_chat(tmp_path: Path) -> None:
    settings = Settings.load(_env(tmp_path))
    assert settings.chat_mode == "chat"
    assert settings.kg_agent_id == "agent-1"
    assert settings.chat_timeout_seconds == 120.0
    assert settings.tool_max_iterations == 8


def test_tool_loop_mode_and_limits(tmp_path: Path) -> None:
    settings = Settings.load(
        _env(
            tmp_path,
            {
                "KG_CHAT_MODE": "tool_loop",
                "KG_CHAT_TIMEOUT_SECONDS": "30",
                "KG_TOOL_MAX_ITERATIONS": "4",
            },
        )
    )
    assert settings.chat_mode == "tool_loop"
    assert settings.chat_timeout_seconds == 30.0
    assert settings.tool_max_iterations == 4


def test_missing_required_setting(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text("KG_HOST=http://graphdb:7200\n")
    with pytest.raises(SettingsError, match="KG_USER"):
        Settings.load(path)


def test_invalid_mode(tmp_path: Path) -> None:
    with pytest.raises(SettingsError, match="KG_CHAT_MODE"):
        Settings.load(_env(tmp_path, {"KG_CHAT_MODE": "other"}))
