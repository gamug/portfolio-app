"""Runtime settings loaded from the local dotenv file."""

from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

from .models import ChatMode

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_PATH = REPO_ROOT / ".env"
CHAT_MODES = ("chat", "tool_loop")


class SettingsError(ValueError):
    """A missing or invalid connector setting."""


def _required(values: dict[str, str | None], key: str) -> str:
    value = values.get(key)
    if value is None or not value.strip():
        raise SettingsError(f"missing required setting {key} in .env")
    return value.strip()


def _optional_float(values: dict[str, str | None], key: str, default: float) -> float:
    raw = values.get(key)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError as error:
        raise SettingsError(f"{key} must be a number") from error
    if value <= 0:
        raise SettingsError(f"{key} must be greater than zero")
    return value


def _optional_int(values: dict[str, str | None], key: str, default: int) -> int:
    raw = values.get(key)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as error:
        raise SettingsError(f"{key} must be an integer") from error
    if value < 1:
        raise SettingsError(f"{key} must be at least one")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    """Connector configuration; secrets stay in the local environment."""

    kg_host: str
    kg_user: str
    kg_password: str
    kg_agent_id: str
    chat_mode: ChatMode
    llm_api_key: str
    llm_model: str
    llm_url: str
    sqlite_path: str = "backend/data/app.sqlite3"
    chat_timeout_seconds: float = 120.0
    tool_max_iterations: int = 8

    @property
    def kg_base_url(self) -> str:
        return self.kg_host.rstrip("/")

    @classmethod
    def load(cls, env_path: Path | None = None) -> "Settings":
        values = dotenv_values(env_path or DEFAULT_ENV_PATH)
        mode_value = (values.get("KG_CHAT_MODE") or "chat").strip().lower()
        if mode_value not in CHAT_MODES:
            raise SettingsError(
                f"KG_CHAT_MODE must be one of {', '.join(CHAT_MODES)}; got {mode_value}"
            )
        mode: ChatMode = "tool_loop" if mode_value == "tool_loop" else "chat"
        return cls(
            kg_host=_required(values, "KG_HOST"),
            kg_user=_required(values, "KG_USER"),
            kg_password=_required(values, "KG_PASSWORD"),
            kg_agent_id=_required(values, "KG_AGENT_ID"),
            chat_mode=mode,
            llm_api_key=_required(values, "LLM_API_KEY"),
            llm_model=_required(values, "LLM_MODEL"),
            llm_url=_required(values, "LLM_URL"),
            sqlite_path=_required(values, "SQLITE_PATH"),
            chat_timeout_seconds=_optional_float(values, "KG_CHAT_TIMEOUT_SECONDS", 120.0),
            tool_max_iterations=_optional_int(values, "KG_TOOL_MAX_ITERATIONS", 8),
        )
