"""Tests for utils.config.Settings."""

import pytest

from utils.config import Settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate tests from whatever is set in the real shell environment."""
    for key in ("APP_ENV", "LOG_LEVEL", "LLM_PROVIDER", "LLM_API_KEY", "DATABASE_URL"):
        monkeypatch.delenv(key, raising=False)


def test_settings_defaults() -> None:
    s = Settings()
    assert s.app_env == "development"
    assert s.log_level == "INFO"
    assert s.llm_provider == "none"
    assert s.ai_enabled is False


def test_ai_enabled_requires_provider_and_key() -> None:
    assert Settings(llm_provider="openai", llm_api_key="test-key").ai_enabled is True
    assert Settings(llm_provider="openai", llm_api_key=None).ai_enabled is False
    assert Settings(llm_provider="none", llm_api_key="test-key").ai_enabled is False


def test_invalid_log_level_raises() -> None:
    with pytest.raises(ValueError):
        Settings(log_level="VERBOSE")


def test_invalid_llm_provider_raises() -> None:
    with pytest.raises(ValueError):
        Settings(llm_provider="anthropic")
