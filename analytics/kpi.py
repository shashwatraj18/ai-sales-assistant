"""Executive summary KPIs: the headline numbers for the dashboard's top row."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ExecutiveSummary:
    total_revenue: float
    total_profit: float
    total_orders: int
    total_customers: int
    average_order_value: float
    profit_margin_pct: float
    return_rate_pct: float
    revenue_growth_pct: float | None  # None if there's no prior period to compare against


def compute_executive_summary(df: pd.DataFrame) -> ExecutiveSummary:
    """Compute headline KPIs over every row in `df` (already filtered by the caller).

    Growth % compares the second half of `df`'s date range to the first
    half of equal length, so it adapts to whatever date range is currently
    selected rather than assuming a fixed "vs. last month" comparison.
    """
    total_revenue = float(df["revenue"].sum())
    total_profit = float(df["profit"].sum())
    total_orders = int(df["order_id"].nunique())
    total_customers = int(df["customer_id"].nunique())
    average_order_value = total_revenue / total_orders if total_orders else 0.0
    profit_margin_pct = (total_profit / total_revenue * 100) if total_revenue else 0.0
    return_rate_pct = float((df["returned"] == "Yes").mean() * 100) if len(df) else 0.0
    revenue_growth_pct = _period_over_period_growth(df)

    return ExecutiveSummary(
        total_revenue=round(total_revenue, 2),
        total_profit=round(total_profit, 2),
        total_orders=total_orders,
        total_customers=total_customers,
        average_order_value=round(average_order_value, 2),
        profit_margin_pct=round(profit_margin_pct, 1),
        return_rate_pct=round(return_rate_pct, 1),
        revenue_growth_pct=round(revenue_growth_pct, 1) if revenue_growth_pct is not None else None,
    )


def _period_over_period_growth(df: pd.DataFrame) -> float | None:
    """Revenue growth of the second half of the date range vs. the first half."""
    if df.empty:
        return None
    start, end = df["order_date"].min(), df["order_date"].max()
    if start == end:
        return None
    midpoint = start + (end - start) / 2
    first_half = df.loc[df["order_date"] < midpoint, "revenue"].sum()
    second_half = df.loc[df["order_date"] >= midpoint, "revenue"].sum()
    if first_half == 0:
        return None
    return (second_half - first_half) / first_half * 100
