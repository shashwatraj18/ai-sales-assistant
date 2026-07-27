"""
Insights engine: routes between the LLM provider (if configured) and the
rule-based fallback, so the rest of the app calls one interface regardless
of which backend is active.
"""

from __future__ import annotations

import pandas as pd

from ai.llm_client import build_provider
from ai.rule_based_engine import answer_question as _rule_based_answer
from ai.rule_based_engine import generate_summary_insights as _rule_based_summary
from analytics.kpi import ExecutiveSummary
from utils.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are a sales analytics assistant for an e-commerce dashboard. Answer using only the "
    "summary statistics provided in the prompt. Be concise (3-5 sentences) and concrete - cite "
    "numbers where you have them."
)


class InsightsEngine:
    """The single entry point the UI calls for both bullet insights and Q&A.

    The bulleted "automated insights" panel always uses the rule-based
    engine, by design: it's deterministic and reviewable (same input,
    same output, no API dependency). Free-form questions in the AI
    Insights tab go to the LLM when one is configured, since that's where
    natural-language flexibility actually matters; if the call fails for
    any reason, it falls back to the rule-based answer rather than
    surfacing an error.
    """

    def __init__(self) -> None:
        self._provider = build_provider(settings.llm_provider, settings.llm_api_key, settings.llm_model)
        self.backend = "llm" if self._provider is not None else "rule_based"
        logger.info("Insights engine using backend=%s", self.backend)

    def generate_summary_insights(self, df: pd.DataFrame, summary: ExecutiveSummary) -> list[str]:
        return _rule_based_summary(df, summary)

    def ask(self, question: str, df: pd.DataFrame, summary: ExecutiveSummary) -> str:
        if self._provider is None:
            return _rule_based_answer(question, df, summary)

        context = _rule_based_summary(df, summary)
        prompt = "Dashboard context:\n- " + "\n- ".join(context) + f"\n\nQuestion: {question}"
        try:
            return self._provider.complete(_SYSTEM_PROMPT, prompt)
        except Exception:
            logger.exception("LLM provider call failed; falling back to rule-based answer")
            return _rule_based_answer(question, df, summary)
