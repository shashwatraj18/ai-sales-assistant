"""Revenue/profit trends over time, dimensional breakdowns, and Pareto analysis."""

from __future__ import annotations

import pandas as pd


def revenue_profit_trend(df: pd.DataFrame, freq: str = "ME") -> pd.DataFrame:
    """Revenue and profit resampled to `freq` ('D', 'W', 'ME' for daily/weekly/monthly)."""
    trend = (
        df.set_index("order_date")
        .resample(freq)
        .agg(revenue=("revenue", "sum"), profit=("profit", "sum"), orders=("order_id", "nunique"))
        .reset_index()
    )
    trend["margin_pct"] = (trend["profit"] / trend["revenue"] * 100).round(1).where(trend["revenue"] != 0)
    return trend


def revenue_by_dimension(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Revenue, profit, and order count grouped by any column, e.g. 'region', 'state', 'category'."""
    grouped = (
        df.groupby(dimension)
        .agg(revenue=("revenue", "sum"), profit=("profit", "sum"), orders=("order_id", "nunique"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    total = grouped["revenue"].sum()
    grouped["revenue_share_pct"] = (grouped["revenue"] / total * 100).round(1) if total else 0.0
    return grouped


def pareto_analysis(df: pd.DataFrame, dimension: str = "product_name", metric: str = "revenue") -> pd.DataFrame:
    """Cumulative-share table for a Pareto chart: which items account for most of `metric`."""
    grouped = df.groupby(dimension)[metric].sum().sort_values(ascending=False).reset_index()
    total = grouped[metric].sum()
    grouped["cumulative"] = grouped[metric].cumsum()
    grouped["cumulative_pct"] = (grouped["cumulative"] / total * 100).round(1) if total else 0.0
    return grouped
