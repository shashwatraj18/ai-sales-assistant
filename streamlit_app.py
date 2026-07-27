"""
AI Sales Analytics Dashboard - entry point.

Wires the sidebar filters, six tabs, and every module built in
`analytics/`, `forecasting/`, `ai/`, and `visualizations/` into one
Streamlit app. No business logic lives here - this file only loads data,
applies filters, and calls out to those modules.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ai.insights_engine import InsightsEngine
from analytics.customers import (
    churn_risk,
    compute_rfm,
    customer_lifetime_value,
    repeat_customer_rate,
    segment_summary,
)
from analytics.kpi import compute_executive_summary
from analytics.products import (
    category_contribution,
    discount_impact,
    inventory_recommendation,
    top_products,
    worst_products,
)
from analytics.trends import pareto_analysis, revenue_by_dimension, revenue_profit_trend
from database.queries import load_full_dataset
from database.session import get_engine
from forecasting.sales_forecast import forecast_revenue
from utils.config import settings
from utils.logger import get_logger
from visualizations.charts import (
    category_treemap,
    delivery_time_boxplot,
    discount_profit_scatter,
    forecast_chart,
    order_value_histogram,
    pareto_chart,
    region_bar_chart,
    revenue_profit_trend_chart,
    rfm_segment_chart,
    sales_heatmap,
    state_choropleth,
    top_products_bar,
)

logger = get_logger(__name__)

st.set_page_config(
    page_title="AI Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner="Loading sales data...")
def _load_data() -> pd.DataFrame:
    return load_full_dataset(get_engine())


def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    min_date, max_date = df["order_date"].min().date(), df["order_date"].max().date()
    date_range = st.sidebar.date_input(
        "Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
    )
    start, end = date_range if isinstance(date_range, tuple) and len(date_range) == 2 else (min_date, max_date)

    regions = st.sidebar.multiselect("Region", sorted(df["region"].unique()))
    categories = st.sidebar.multiselect("Category", sorted(df["category"].unique()))
    sub_categories = st.sidebar.multiselect("Sub-category", sorted(df["sub_category"].unique()))
    cities = st.sidebar.multiselect("City", sorted(df["city"].unique()))
    channels = st.sidebar.multiselect("Sales channel", sorted(df["sales_channel"].unique()))
    customer_search = st.sidebar.text_input("Customer name contains")

    mask = (df["order_date"].dt.date >= start) & (df["order_date"].dt.date <= end)
    if regions:
        mask &= df["region"].isin(regions)
    if categories:
        mask &= df["category"].isin(categories)
    if sub_categories:
        mask &= df["sub_category"].isin(sub_categories)
    if cities:
        mask &= df["city"].isin(cities)
    if channels:
        mask &= df["sales_channel"].isin(channels)
    if customer_search:
        mask &= df["customer_name"].str.contains(customer_search, case=False, na=False)

    filtered = df.loc[mask]
    st.sidebar.caption(f"{len(filtered):,} of {len(df):,} orders match your filters")
    return filtered


def render_executive_summary(df: pd.DataFrame, engine: InsightsEngine) -> None:
    summary = compute_executive_summary(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Revenue", f"${summary.total_revenue:,.0f}",
        f"{summary.revenue_growth_pct:+.1f}%" if summary.revenue_growth_pct is not None else None,
    )
    c2.metric("Profit", f"${summary.total_profit:,.0f}", f"{summary.profit_margin_pct:.1f}% margin")
    c3.metric("Orders", f"{summary.total_orders:,}", f"AOV ${summary.average_order_value:,.2f}")
    c4.metric("Customers", f"{summary.total_customers:,}", f"{summary.return_rate_pct:.1f}% returned")
    
    st.plotly_chart(
    revenue_profit_trend_chart(revenue_profit_trend(df)),
    width="stretch",
    key="exec_trend",
    )
     
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
    region_bar_chart(revenue_by_dimension(df, "region")),
    width="stretch",
    key="exec_region",
    )
    with col2:
        st.plotly_chart(
    state_choropleth(revenue_by_dimension(df, "state")),
    width="stretch",
    key="exec_state",
    )

    with st.expander("Automated insights", expanded=True):
        for line in engine.generate_summary_insights(df, summary):
            st.markdown(f"- {line}")


def render_revenue_tab(df: pd.DataFrame) -> None:
    freq_label = st.radio("Granularity", ["Daily", "Weekly", "Monthly"], index=2, horizontal=True)
    freq = {"Daily": "D", "Weekly": "W", "Monthly": "ME"}[freq_label]
    st.plotly_chart(revenue_profit_trend_chart(revenue_profit_trend(df, freq=freq)), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(category_treemap(category_contribution(df)), use_container_width=True)
    with col2:
        st.plotly_chart(order_value_histogram(df), use_container_width=True)

    st.plotly_chart(sales_heatmap(df), use_container_width=True)


def render_customers_tab(df: pd.DataFrame) -> None:
    rfm = compute_rfm(df)

    c1, c2, c3 = st.columns(3)
    c1.metric("Repeat customer rate", f"{repeat_customer_rate(df):.1f}%")
    c2.metric("Champions", int((rfm["segment"] == "Champions").sum()))
    c3.metric("At risk", int((rfm["segment"] == "At risk").sum()))

    col1, col2 = st.columns([1, 1])
    with col1:
        st.plotly_chart(rfm_segment_chart(rfm), use_container_width=True)
    with col2:
        st.dataframe(segment_summary(rfm), use_container_width=True, hide_index=True)

    st.subheader("Top customers by lifetime value")
    st.dataframe(customer_lifetime_value(df).head(20), use_container_width=True, hide_index=True)

    with st.expander("Churn risk"):
        risk = churn_risk(df)
        counts = risk["churn_risk"].value_counts().rename_axis("Risk").reset_index(name="Customers")
        st.dataframe(counts, use_container_width=True, hide_index=True)


def render_products_tab(df: pd.DataFrame) -> None:
    metric = st.radio("Rank by", ["revenue", "profit"], horizontal=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(top_products_bar(top_products(df, n=10, by=metric), metric=metric), use_container_width=True)
    with col2:
        st.dataframe(worst_products(df, n=10, by="profit"), use_container_width=True, hide_index=True)

    st.plotly_chart(
        pareto_chart(pareto_analysis(df, "product_name", "revenue"), "product_name", "revenue"),
        use_container_width=True,
    )

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(discount_profit_scatter(df), use_container_width=True)
    with col4:
        st.plotly_chart(delivery_time_boxplot(df), use_container_width=True)

    with st.expander("Discount impact on margin"):
        st.dataframe(discount_impact(df), use_container_width=True, hide_index=True)

    with st.expander("Inventory recommendations"):
        inv = inventory_recommendation(df)
        st.dataframe(
            inv[["product_name", "category", "units_sold", "margin_pct", "recommendation"]],
            use_container_width=True, hide_index=True,
        )


def render_forecasting_tab(df: pd.DataFrame) -> None:
    horizon = st.radio("Horizon", [30, 90], format_func=lambda d: f"Next {d} days", horizontal=True)
    try:
        result = forecast_revenue(df, horizon_days=horizon)
    except ValueError as exc:
        st.warning(str(exc))
        return

    st.plotly_chart(forecast_chart(result.history, result.forecast), use_container_width=True)
    total = result.forecast["forecast"].sum()
    lo, hi = result.forecast["lower"].sum(), result.forecast["upper"].sum()
    st.metric(f"Projected revenue, next {horizon} days", f"${total:,.0f}", f"range ${lo:,.0f} - ${hi:,.0f}")


def render_ai_insights_tab(df: pd.DataFrame, engine: InsightsEngine) -> None:
    st.caption(f"Backend: {'LLM-powered' if engine.backend == 'llm' else 'rule-based (no API key configured)'}")
    summary = compute_executive_summary(df)

    suggestions = [
        "Which region is growing fastest?", "Why is profit falling?",
        "Show best-performing products.", "Which customers should we target?",
        "Summarize this dashboard.", "Generate recommendations.",
    ]
    clicked = None
    cols = st.columns(3)
    for i, suggestion in enumerate(suggestions):
        if cols[i % 3].button(suggestion, use_container_width=True, key=f"suggest_{i}"):
            clicked = suggestion

    question = st.text_input("Or ask your own question", value=clicked or "")
    if question:
        with st.spinner("Thinking..."):
            st.markdown(engine.ask(question, df, summary))


def main() -> None:
    logger.info("App started (env=%s)", settings.app_env)
    st.title("📊 AI Sales Analytics Dashboard")
    st.caption("Revenue, customers, products, and forecasting analytics.")

    if "insights_engine" not in st.session_state:
        st.session_state["insights_engine"] = InsightsEngine()
    engine: InsightsEngine = st.session_state["insights_engine"]

    full_df = _load_data()
    df = _apply_filters(full_df)

    if df.empty:
        st.warning("No orders match the current filters.")
        return

    tabs = st.tabs(["Executive summary", "Revenue", "Customers", "Products", "Forecasting", "AI insights"])
    with tabs[0]:
        render_executive_summary(df, engine)
    with tabs[1]:
        render_revenue_tab(df)
    with tabs[2]:
        render_customers_tab(df)
    with tabs[3]:
        render_products_tab(df)
    with tabs[4]:
        render_forecasting_tab(df)
    with tabs[5]:
        render_ai_insights_tab(df, engine)


if __name__ == "__main__":
    main()
