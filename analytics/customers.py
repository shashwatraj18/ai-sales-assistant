"""Customer analytics: RFM segmentation, lifetime value, churn risk, repeat-purchase rate."""

from __future__ import annotations

import pandas as pd


def compute_rfm(df: pd.DataFrame, reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """One row per customer: Recency (days), Frequency (orders), Monetary (revenue),
    each scored 1 (worst) to 5 (best) by quintile, plus a named segment.
    """
    reference_date = reference_date or df["order_date"].max()

    rfm = (
        df.groupby("customer_id")
        .agg(
            customer_name=("customer_name", "first"),
            last_order_date=("order_date", "max"),
            frequency=("order_id", "nunique"),
            monetary=("revenue", "sum"),
        )
        .reset_index()
    )
    rfm["recency_days"] = (reference_date - rfm["last_order_date"]).dt.days

    rfm["r_score"] = _quintile_score(rfm["recency_days"], reverse=True)
    rfm["f_score"] = _quintile_score(rfm["frequency"], reverse=False)
    rfm["m_score"] = _quintile_score(rfm["monetary"], reverse=False)
    rfm["rfm_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]
    rfm["segment"] = rfm.apply(_segment_from_scores, axis=1)
    return rfm


def _quintile_score(series: pd.Series, reverse: bool) -> pd.Series:
    """Bucket a numeric series into 1-5 quintiles; ranking first breaks ties cleanly."""
    ranks = series.rank(method="first")
    scores = pd.qcut(ranks, 5, labels=[1, 2, 3, 4, 5]).astype(int)
    return (6 - scores) if reverse else scores


def _segment_from_scores(row: pd.Series) -> str:
    r, f, m = row["r_score"], row["f_score"], row["m_score"]
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3:
        return "Loyal customers"
    if r >= 4 and f <= 2:
        return "New customers"
    if r <= 2 and f >= 4:
        return "At risk"
    if r <= 2 and f <= 2 and m <= 2:
        return "Lost"
    return "Needs attention"


def churn_risk(df: pd.DataFrame, reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """Flag each customer's churn risk from recency alone: <=30d low, 31-90 medium, >90 high."""
    reference_date = reference_date or df["order_date"].max()
    last_order = df.groupby("customer_id")["order_date"].max().reset_index(name="last_order_date")
    last_order["recency_days"] = (reference_date - last_order["last_order_date"]).dt.days
    last_order["churn_risk"] = pd.cut(
        last_order["recency_days"], bins=[-1, 30, 90, 10_000], labels=["Low", "Medium", "High"]
    )
    return last_order


def customer_lifetime_value(df: pd.DataFrame) -> pd.DataFrame:
    """Historical CLV per customer: total profit contributed to date (a look-back
    measure, not a forward projection of future value)."""
    clv = (
        df.groupby("customer_id")
        .agg(
            customer_name=("customer_name", "first"),
            lifetime_revenue=("revenue", "sum"),
            lifetime_profit=("profit", "sum"),
            orders=("order_id", "nunique"),
        )
        .reset_index()
        .sort_values("lifetime_profit", ascending=False)
    )
    clv["avg_order_value"] = (clv["lifetime_revenue"] / clv["orders"]).round(2)
    return clv


def repeat_customer_rate(df: pd.DataFrame) -> float:
    """Share of customers (%) with more than one distinct order."""
    orders_per_customer = df.groupby("customer_id")["order_id"].nunique()
    if orders_per_customer.empty:
        return 0.0
    return round(float((orders_per_customer > 1).mean() * 100), 1)


def segment_summary(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """Customer count and total monetary value per RFM segment."""
    return (
        rfm_df.groupby("segment")
        .agg(customers=("customer_id", "nunique"), total_monetary=("monetary", "sum"))
        .reset_index()
        .sort_values("total_monetary", ascending=False)
    )
