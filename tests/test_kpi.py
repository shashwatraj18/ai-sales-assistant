"""Tests for analytics.kpi.compute_executive_summary."""

from __future__ import annotations

import pandas as pd

from analytics.kpi import compute_executive_summary


def test_totals(sample_df: pd.DataFrame) -> None:
    s = compute_executive_summary(sample_df)
    assert s.total_revenue == 1845.0
    assert s.total_profit == 639.0
    assert s.total_orders == 12
    assert s.total_customers == 5


def test_derived_ratios(sample_df: pd.DataFrame) -> None:
    s = compute_executive_summary(sample_df)
    assert s.average_order_value == round(1845.0 / 12, 2)
    assert s.profit_margin_pct == round(639.0 / 1845.0 * 100, 1)
    assert s.return_rate_pct == round(3 / 12 * 100, 1)  # 3 of 12 rows are Returned == "Yes"


def test_empty_dataframe_does_not_raise(sample_df: pd.DataFrame) -> None:
    empty = sample_df.iloc[0:0]
    s = compute_executive_summary(empty)
    assert s.total_orders == 0
    assert s.average_order_value == 0.0
    assert s.revenue_growth_pct is None
