"""
Rule-based insights engine: the default "AI" backend when no LLM provider
is configured. Deterministic and needs no API key - every insight is a
plain-language read-out of numbers already computed by `analytics/`.
"""

from __future__ import annotations

import pandas as pd

from analytics.customers import compute_rfm
from analytics.kpi import ExecutiveSummary
from analytics.products import discount_impact, inventory_recommendation, product_performance
from analytics.trends import revenue_by_dimension


def generate_summary_insights(df: pd.DataFrame, summary: ExecutiveSummary) -> list[str]:
    """A handful of headline, plain-language observations about `df`."""
    insights: list[str] = []

    if summary.revenue_growth_pct is not None:
        direction = "increased" if summary.revenue_growth_pct >= 0 else "decreased"
        insights.append(
            f"Revenue {direction} {abs(summary.revenue_growth_pct):.0f}% comparing the second half "
            f"of the selected period to the first half."
        )

    by_region = revenue_by_dimension(df, "region")
    if not by_region.empty:
        top = by_region.iloc[0]
        insights.append(
            f"The {top['region']} region contributes {top['revenue_share_pct']:.0f}% of total revenue, "
            f"the largest share of any region."
        )

    perf = product_performance(df)
    priced = perf[perf["revenue"] > 0]
    if not priced.empty:
        median_margin = priced["margin_pct"].median()
        candidates = priced[
            (priced["revenue"] >= priced["revenue"].quantile(0.75)) & (priced["margin_pct"] < median_margin)
        ]
        if not candidates.empty:
            worst = candidates.sort_values("margin_pct").iloc[0]
            insights.append(
                f"{worst['product_name']} has high revenue (${worst['revenue']:,.0f}) but a "
                f"below-median profit margin ({worst['margin_pct']:.0f}%) - a candidate for repricing."
            )

    d_impact = discount_impact(df)
    if len(d_impact) >= 2:
        low_band, high_band = d_impact.iloc[0], d_impact.iloc[-1]
        if pd.notna(high_band["margin_pct"]) and pd.notna(low_band["margin_pct"]):
            if high_band["margin_pct"] < low_band["margin_pct"] - 5:
                insights.append(
                    f"Margin falls from {low_band['margin_pct']:.0f}% on orders discounted "
                    f"{low_band['discount_band']} to {high_band['margin_pct']:.0f}% on orders discounted "
                    f"{high_band['discount_band']} - discounting past that point costs more than it "
                    f"earns back in volume."
                )

    insights.append(
        f"Average order value is ${summary.average_order_value:,.2f} across {summary.total_orders:,} "
        f"orders and {summary.total_customers:,} customers, with a {summary.return_rate_pct:.1f}% "
        f"return rate."
    )
    return insights


def answer_question(question: str, df: pd.DataFrame, summary: ExecutiveSummary) -> str:
    """Best-effort answer to a free-text question using keyword matching.

    Intentionally simple - it exists so the AI Insights tab works with zero
    configuration. Once a real provider is configured, `ai.insights_engine`
    routes questions here instead, which can handle open-ended phrasing.
    """
    q = question.lower()

    if any(w in q for w in ("summarize", "summary", "overview")):
        return " ".join(generate_summary_insights(df, summary))
    if "region" in q and any(w in q for w in ("grow", "fastest", "best", "top")):
        return _fastest_growing_region(df)
    if any(w in q for w in ("profit fall", "profit drop", "why is profit", "losing money", "margin")):
        return _profit_drivers(df)
    if any(w in q for w in ("best product", "top product", "best-performing", "best performing")):
        return _top_products_answer(df)
    if any(w in q for w in ("worst product", "underperform", "low performing", "low-performing")):
        return _worst_products_answer(df)
    if any(w in q for w in ("target", "which customers", "best customers", "loyal")):
        return _customers_to_target(df)
    if any(w in q for w in ("recommend", "suggestion", "what should we do")):
        return _recommendations(df, summary)

    return (
        "I can answer questions about revenue and profit trends, regional performance, top or "
        "underperforming products, customer segments, and recommendations. Try asking one of "
        "those, or connect a real LLM provider in Settings for open-ended questions."
    )


def _fastest_growing_region(df: pd.DataFrame) -> str:
    trend = df.groupby([df["order_date"].dt.to_period("M"), "region"])["revenue"].sum().reset_index()
    trend.columns = ["month", "region", "revenue"]
    pivot = trend.pivot(index="month", columns="region", values="revenue").fillna(0.0)
    if len(pivot) < 2:
        return "Not enough monthly history to compare regional growth rates yet."
    growth = ((pivot.iloc[-1] - pivot.iloc[0]) / pivot.iloc[0].replace(0, pd.NA) * 100).dropna()
    if growth.empty:
        return "Not enough data to compute regional growth."
    fastest = growth.sort_values(ascending=False).index[0]
    return (
        f"{fastest} grew revenue {growth[fastest]:.0f}% from the first to the last month in the "
        f"selected range, the fastest of any region."
    )


def _profit_drivers(df: pd.DataFrame) -> str:
    cat = df.groupby("category").agg(revenue=("revenue", "sum"), profit=("profit", "sum"))
    cat = cat[cat["revenue"] > 0]
    cat["margin_pct"] = cat["profit"] / cat["revenue"] * 100
    cat = cat.sort_values("margin_pct")

    d_impact = discount_impact(df)
    perf = product_performance(df)

    parts = []
    if not cat.empty:
        thin = cat.iloc[0]
        parts.append(f"{cat.index[0]} has the thinnest margin of any category ({thin['margin_pct']:.0f}%).")
    if len(d_impact) >= 2 and pd.notna(d_impact.iloc[-1]["margin_pct"]):
        parts.append(
            f"Orders discounted {d_impact.iloc[-1]['discount_band']} run a "
            f"{d_impact.iloc[-1]['margin_pct']:.0f}% margin, the lowest of any discount band."
        )
    negative = perf[perf["profit"] < 0]
    if not negative.empty:
        parts.append(f"{len(negative)} product(s) are net-unprofitable overall in this selection.")
    return " ".join(parts) if parts else "No clear profit-erosion pattern found in the current selection."


def _top_products_answer(df: pd.DataFrame) -> str:
    top = product_performance(df).head(5)
    lines = [f"{r.product_name} (${r.revenue:,.0f} revenue, {r.margin_pct:.0f}% margin)" for r in top.itertuples()]
    return "Top 5 products by revenue: " + "; ".join(lines) + "."


def _worst_products_answer(df: pd.DataFrame) -> str:
    worst = product_performance(df).nsmallest(5, "profit")
    lines = [f"{r.product_name} (${r.profit:,.0f} profit)" for r in worst.itertuples()]
    return "Lowest-profit products: " + "; ".join(lines) + "."


def _customers_to_target(df: pd.DataFrame) -> str:
    rfm = compute_rfm(df)
    champions = int((rfm["segment"] == "Champions").sum())
    at_risk = int((rfm["segment"] == "At risk").sum())
    return (
        f"{champions} customers are current Champions (high recency, frequency, and spend) - a "
        f"natural audience for a loyalty or early-access offer. {at_risk} customers are flagged "
        f"At risk (they used to order frequently but haven't recently) - worth a targeted "
        f"win-back campaign before they lapse further."
    )


def _recommendations(df: pd.DataFrame, summary: ExecutiveSummary) -> str:
    inv = inventory_recommendation(df)
    discontinue = inv[inv["recommendation"] == "Discontinue"]
    restock = inv[inv["recommendation"] == "Restock"]
    recs = []
    if not restock.empty:
        recs.append(
            f"Prioritize inventory for the {len(restock)} products flagged Restock "
            f"(high sales velocity, healthy margin)."
        )
    if not discontinue.empty:
        recs.append(
            f"Reconsider the {len(discontinue)} products flagged Discontinue (low velocity, thin margin)."
        )
    if summary.return_rate_pct > 8:
        recs.append(
            f"The {summary.return_rate_pct:.1f}% overall return rate is worth investigating, "
            f"particularly in categories with above-average returns."
        )
    return " ".join(recs) if recs else "No high-confidence recommendations for the current selection."
