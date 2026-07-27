"""Tests for analytics.products."""

from __future__ import annotations

import pandas as pd

from analytics.products import discount_impact, inventory_recommendation, product_performance


def test_product_performance_totals(sample_df: pd.DataFrame) -> None:
    perf = product_performance(sample_df)
    assert len(perf) == 3  # P1, P2, P3
    assert round(perf["revenue"].sum(), 2) == 1845.0
    nova = perf.loc[perf["product_id"] == "P1"].iloc[0]
    assert nova["units_sold"] == 9  # 1 + 3 + 1 + 3 + 1 = 9 across the 5 rows for P1


def test_discount_impact_shows_margin_declining(sample_df: pd.DataFrame) -> None:
    impact = discount_impact(sample_df)
    non_null = impact.dropna(subset=["margin_pct"])
    # Highest-discount band should have a lower margin than the lowest-discount band.
    assert non_null.iloc[-1]["margin_pct"] < non_null.iloc[0]["margin_pct"]


def test_inventory_recommendation_assigns_a_label_to_every_product(sample_df: pd.DataFrame) -> None:
    inv = inventory_recommendation(sample_df)
    assert set(inv["recommendation"].unique()) <= {"Restock", "Hold", "Discontinue"}
    assert inv["recommendation"].notna().all()
