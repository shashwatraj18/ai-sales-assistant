"""Tests for analytics.customers."""

from __future__ import annotations

import pandas as pd

from analytics.customers import churn_risk, compute_rfm, customer_lifetime_value, repeat_customer_rate


def test_repeat_customer_rate(sample_df: pd.DataFrame) -> None:
    # C1, C2, C3 each have 3 orders; C4 and C5 have 1 each -> 3 of 5 repeat.
    assert repeat_customer_rate(sample_df) == 60.0


def test_rfm_has_one_row_per_customer_with_valid_scores(sample_df: pd.DataFrame) -> None:
    rfm = compute_rfm(sample_df, reference_date=pd.Timestamp("2026-03-16"))
    assert len(rfm) == sample_df["customer_id"].nunique()
    assert rfm["customer_id"].is_unique
    for col in ("r_score", "f_score", "m_score"):
        assert set(rfm[col].unique()) <= {1, 2, 3, 4, 5}
    assert rfm["segment"].notna().all()


def test_churn_risk_buckets(sample_df: pd.DataFrame) -> None:
    risk = churn_risk(sample_df, reference_date=pd.Timestamp("2026-03-16"))
    # C4's last order was 2026-01-15 -> 60 days recency -> Medium (31-90 day band)
    c4_risk = risk.loc[risk["customer_id"] == "C4", "churn_risk"].iloc[0]
    assert c4_risk == "Medium"


def test_clv_ranks_by_lifetime_profit(sample_df: pd.DataFrame) -> None:
    clv = customer_lifetime_value(sample_df)
    assert clv["lifetime_profit"].is_monotonic_decreasing
    assert clv.iloc[0]["customer_id"] == "C1"  # highest cumulative profit in the fixture
