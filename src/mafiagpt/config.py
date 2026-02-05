from __future__ import annotations

from dataclasses import dataclass
import os


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    model: str
    api_key: str
    base_url: str
    rate_limit_seconds: float
    temperature: float
    token_limit: int
    debug: bool


def load_settings() -> Settings:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is required.")
    return Settings(
        model=os.getenv("OPENROUTER_MODEL", "gpt5.2"),
        api_key=api_key,
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        rate_limit_seconds=float(os.getenv("RATE_LIMIT_SECONDS", "20")),
        temperature=float(os.getenv("TEMPERATURE", "1.0")),
        token_limit=int(os.getenv("TOKEN_LIMIT", "5000")),
        debug=_get_bool("DEBUG", False),
    )
