"""Tests for analytics.trends."""

from __future__ import annotations

import pandas as pd

from analytics.trends import pareto_analysis, revenue_by_dimension, revenue_profit_trend


def test_revenue_by_dimension_shares_sum_to_100(sample_df: pd.DataFrame) -> None:
    by_region = revenue_by_dimension(sample_df, "region")
    assert abs(by_region["revenue_share_pct"].sum() - 100.0) < 0.2
    # South has by far the most orders/revenue in the fixture
    assert by_region.iloc[0]["region"] == "South"


def test_revenue_profit_trend_monthly_bucket_count(sample_df: pd.DataFrame) -> None:
    trend = revenue_profit_trend(sample_df, freq="ME")
    assert len(trend) == 3  # Jan, Feb, Mar
    assert round(trend["revenue"].sum(), 2) == 1845.0


def test_pareto_cumulative_reaches_100(sample_df: pd.DataFrame) -> None:
    pareto = pareto_analysis(sample_df, "product_name", "revenue")
    assert abs(pareto["cumulative_pct"].iloc[-1] - 100.0) < 0.2
    assert pareto["cumulative_pct"].is_monotonic_increasing
