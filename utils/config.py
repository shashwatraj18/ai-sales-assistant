"""
Centralized application configuration.

Every environment-dependent value (database URL, log level, AI provider
credentials, etc.) is declared once here as a single `Settings` object.
Other modules import `settings` from this file instead of reading
`os.environ` directly, so configuration has one home, one set of defaults,
and one place to check when something is misconfigured.

Kept dependency-free (standard library only) for now: a `.env` file is
parsed with a small local loader rather than `python-dotenv`, and
validation is a plain `__post_init__` rather than a schema library. If the
config surface grows (nested settings, multiple environments, secrets
management) this is the natural place to swap in `pydantic-settings`
without changing how the rest of the app imports `settings`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

_VALID_APP_ENVS = {"development", "production", "test"}
_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}
_VALID_LLM_PROVIDERS = {"none", "openai"}


def _load_dotenv(path: Path) -> None:
    """Populate os.environ from a simple KEY=VALUE .env file, if present.

    Existing environment variables always win (setdefault), so real env vars
    (e.g. set by a deployment platform) are never overridden by a local
    .env file.
    """
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Typed application settings, populated from environment variables."""

    app_env: str = field(default_factory=lambda: os.environ.get("APP_ENV", "development"))
    log_level: str = field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO"))

    data_raw_dir: Path = PROJECT_ROOT / "data" / "raw"
    data_processed_dir: Path = PROJECT_ROOT / "data" / "processed"

    database_url: str = field(
        default_factory=lambda: os.environ.get(
            "DATABASE_URL",
            f"sqlite:///{PROJECT_ROOT / 'data' / 'processed' / 'sales_analytics.db'}",
        )
    )

    llm_provider: str = field(default_factory=lambda: os.environ.get("LLM_PROVIDER", "none"))
    llm_api_key: str | None = field(default_factory=lambda: os.environ.get("LLM_API_KEY") or None)
    llm_model: str = field(default_factory=lambda: os.environ.get("LLM_MODEL", "gpt-4o-mini"))

    def __post_init__(self) -> None:
        if self.app_env not in _VALID_APP_ENVS:
            raise ValueError(f"APP_ENV must be one of {_VALID_APP_ENVS}, got {self.app_env!r}")
        if self.log_level not in _VALID_LOG_LEVELS:
            raise ValueError(
                f"LOG_LEVEL must be one of {_VALID_LOG_LEVELS}, got {self.log_level!r}"
            )
        if self.llm_provider not in _VALID_LLM_PROVIDERS:
            raise ValueError(
                f"LLM_PROVIDER must be one of {_VALID_LLM_PROVIDERS}, got {self.llm_provider!r}"
            )

    @property
    def ai_enabled(self) -> bool:
        """Whether a real LLM provider is configured (vs. the rule-based fallback)."""
        return self.llm_provider != "none" and bool(self.llm_api_key)


settings = Settings()
