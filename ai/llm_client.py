"""
LLM provider abstraction for AI-powered insights.

Defines a minimal `LLMProvider` protocol so a real provider can be plugged
in without touching any calling code, plus an `OpenAIProvider`
implementation. The `openai` package is imported lazily inside
`OpenAIProvider.__init__` (not at module load time), so this module - and
everything that imports it - works even when `openai` isn't installed,
which is the common case for anyone running this project without an API
key (see `ai/rule_based_engine.py` for the default fallback).
"""

from __future__ import annotations

from typing import Protocol

from utils.logger import get_logger

logger = get_logger(__name__)


class LLMProvider(Protocol):
    """Anything that can turn a prompt into a text completion."""

    def complete(self, system_prompt: str, user_prompt: str) -> str: ...


class OpenAIProvider:
    """LLMProvider backed by an OpenAI-compatible chat completions API."""

    def __init__(self, api_key: str, model: str) -> None:
        try:
            import openai
        except ImportError as exc:
            raise ImportError(
                "The 'openai' package is required to use OpenAIProvider. "
                "Install it with: pip install openai"
            ) from exc
        self._client = openai.OpenAI(api_key=api_key)
        self._model = model

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=400,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""


def build_provider(provider_name: str, api_key: str | None, model: str) -> LLMProvider | None:
    """Construct the configured provider, or None if none is configured (or it fails)."""
    if provider_name == "none" or not api_key:
        return None
    if provider_name == "openai":
        try:
            return OpenAIProvider(api_key=api_key, model=model)
        except ImportError:
            logger.warning(
                "LLM_PROVIDER=openai but the openai package isn't installed; "
                "falling back to rule-based insights"
            )
            return None
    logger.warning("Unknown LLM_PROVIDER=%r; falling back to rule-based insights", provider_name)
    return None
