"""Product analytics: profitability, discount sensitivity, inventory recommendation."""

from __future__ import annotations

import pandas as pd


def product_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue, profit, margin, units sold, rating, and return rate per product."""
    perf = (
        df.groupby(["product_id", "product_name", "category", "sub_category"])
        .agg(
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
            units_sold=("quantity", "sum"),
            orders=("order_id", "nunique"),
            avg_rating=("rating", "mean"),
            return_rate_pct=("returned", lambda s: (s == "Yes").mean() * 100),
        )
        .reset_index()
    )
    perf["margin_pct"] = (perf["profit"] / perf["revenue"] * 100).round(1).where(perf["revenue"] != 0)
    perf["avg_rating"] = perf["avg_rating"].round(2)
    perf["return_rate_pct"] = perf["return_rate_pct"].round(1)
    return perf.sort_values("revenue", ascending=False).reset_index(drop=True)


def top_products(df: pd.DataFrame, n: int = 10, by: str = "revenue") -> pd.DataFrame:
    return product_performance(df).nlargest(n, by)


def worst_products(df: pd.DataFrame, n: int = 10, by: str = "profit") -> pd.DataFrame:
    return product_performance(df).nsmallest(n, by)


def category_contribution(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue/profit by category and sub-category, for a treemap."""
    grouped = (
        df.groupby(["category", "sub_category"])
        .agg(revenue=("revenue", "sum"), profit=("profit", "sum"))
        .reset_index()
    )
    grouped["margin_pct"] = (grouped["profit"] / grouped["revenue"] * 100).round(1)
    return grouped


def discount_impact(df: pd.DataFrame, bins: list[float] | None = None) -> pd.DataFrame:
    """Revenue and margin at increasing discount bands - shows where discounting stops paying off."""
    bins = bins or [0, 0.10, 0.20, 0.30, 1.0]
    labels = [f"{int(bins[i] * 100)}-{int(bins[i + 1] * 100)}%" for i in range(len(bins) - 1)]
    banded = df.copy()
    banded["discount_band"] = pd.cut(banded["discount"], bins=bins, labels=labels, include_lowest=True)
    summary = (
        banded.groupby("discount_band", observed=True)
        .agg(revenue=("revenue", "sum"), profit=("profit", "sum"), orders=("order_id", "nunique"))
        .reset_index()
    )
    summary["margin_pct"] = (summary["profit"] / summary["revenue"] * 100).round(1)
    return summary


def inventory_recommendation(df: pd.DataFrame) -> pd.DataFrame:
    """Flag each product Restock / Hold / Discontinue from sales velocity and margin
    quantiles within the observed window - a defensible first pass a merchandising
    team could refine, not a real demand-forecasting model.
    """
    perf = product_performance(df)
    velocity_q = perf["units_sold"].quantile([0.33, 0.66]).to_numpy()
    margin_q = perf["margin_pct"].quantile([0.33, 0.66]).to_numpy()

    def _recommend(row: pd.Series) -> str:
        high_velocity = row["units_sold"] >= velocity_q[1]
        low_velocity = row["units_sold"] <= velocity_q[0]
        low_margin = row["margin_pct"] <= margin_q[0]
        if high_velocity and not low_margin:
            return "Restock"
        if low_velocity and low_margin:
            return "Discontinue"
        return "Hold"

    perf["recommendation"] = perf.apply(_recommend, axis=1)
    return perf
