"""Tests for ai.rule_based_engine and the LLM-provider fallback routing."""

from __future__ import annotations

import pandas as pd

from ai.llm_client import build_provider
from ai.rule_based_engine import answer_question, generate_summary_insights
from analytics.kpi import compute_executive_summary


def test_generate_summary_insights_returns_nonempty_strings(sample_df: pd.DataFrame) -> None:
    summary = compute_executive_summary(sample_df)
    insights = generate_summary_insights(sample_df, summary)
    assert len(insights) >= 2
    assert all(isinstance(line, str) and line.strip() for line in insights)


def test_answer_question_routes_known_patterns(sample_df: pd.DataFrame) -> None:
    summary = compute_executive_summary(sample_df)
    for question in ("Summarize this dashboard.", "Show best-performing products.", "Generate recommendations."):
        answer = answer_question(question, sample_df, summary)
        assert isinstance(answer, str) and answer.strip()


def test_answer_question_falls_back_for_unknown_patterns(sample_df: pd.DataFrame) -> None:
    summary = compute_executive_summary(sample_df)
    answer = answer_question("What's your favorite color?", sample_df, summary)
    assert "connect a real LLM provider" in answer.lower()


def test_build_provider_returns_none_without_a_key() -> None:
    assert build_provider("none", None, "gpt-4o-mini") is None
    assert build_provider("openai", None, "gpt-4o-mini") is None


def test_build_provider_falls_back_when_openai_package_missing() -> None:
    # openai is intentionally not a hard dependency (see ai/llm_client.py);
    # this should degrade gracefully rather than raise.
    assert build_provider("openai", "fake-key", "gpt-4o-mini") is None
