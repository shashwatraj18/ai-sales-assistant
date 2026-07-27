"""
Reusable Plotly chart-building functions.

Every function takes a pandas DataFrame (already computed by `analytics/`
or `forecasting/`) and returns a `plotly.graph_objects.Figure` - no
Streamlit calls in here, so these are usable from a notebook or a script
as easily as from the dashboard.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

_TEMPLATE = "plotly_white"

_STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO",
    "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}


def revenue_profit_trend_chart(trend_df: pd.DataFrame) -> go.Figure:
    """Line chart of revenue and profit over time (analytics.trends.revenue_profit_trend)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend_df["order_date"], y=trend_df["revenue"], name="Revenue", mode="lines"))
    fig.add_trace(go.Scatter(x=trend_df["order_date"], y=trend_df["profit"], name="Profit", mode="lines"))
    fig.update_layout(template=_TEMPLATE, title="Revenue & profit over time", yaxis_title="USD")
    return fig


def region_bar_chart(region_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of revenue by region (analytics.trends.revenue_by_dimension)."""
    fig = px.bar(
        region_df.sort_values("revenue"), x="revenue", y="region", orientation="h",
        template=_TEMPLATE, title="Revenue by region", text_auto=".2s",
    )
    fig.update_layout(yaxis_title=None, xaxis_title="Revenue (USD)")
    return fig


def state_choropleth(state_df: pd.DataFrame, state_col: str = "state") -> go.Figure:
    """US choropleth of revenue by state. `state_df` needs a `state_col` of full state names."""
    plot_df = state_df.copy()
    plot_df["state_abbr"] = plot_df[state_col].map(_STATE_ABBR)
    fig = px.choropleth(
        plot_df.dropna(subset=["state_abbr"]), locations="state_abbr", locationmode="USA-states",
        color="revenue", scope="usa", template=_TEMPLATE, title="Revenue by state",
        color_continuous_scale="Blues",
    )
    return fig


def top_products_bar(products_df: pd.DataFrame, metric: str = "revenue") -> go.Figure:
    """Horizontal bar chart of the given (already top/worst-filtered) products table."""
    fig = px.bar(
        products_df.sort_values(metric), x=metric, y="product_name", orientation="h",
        template=_TEMPLATE, title=f"Products by {metric}", color="category",
    )
    fig.update_layout(yaxis_title=None)
    return fig


def category_treemap(category_df: pd.DataFrame) -> go.Figure:
    """Treemap of category > sub-category revenue, colored by margin %."""
    fig = px.treemap(
        category_df, path=["category", "sub_category"], values="revenue", color="margin_pct",
        color_continuous_scale="RdYlGn", template=_TEMPLATE, title="Revenue by category (color = margin %)",
    )
    return fig


def pareto_chart(pareto_df: pd.DataFrame, dimension: str, metric: str, top_n: int = 20) -> go.Figure:
    """Bar + cumulative-% line Pareto chart, limited to the top `top_n` items for readability."""
    plot_df = pareto_df.head(top_n)
    fig = go.Figure()
    fig.add_bar(x=plot_df[dimension], y=plot_df[metric], name=metric.title())
    fig.add_trace(go.Scatter(
        x=plot_df[dimension], y=plot_df["cumulative_pct"], name="Cumulative %",
        mode="lines+markers", yaxis="y2",
    ))
    fig.update_layout(
        template=_TEMPLATE, title=f"Pareto: {dimension} by {metric} (top {top_n})",
        yaxis=dict(title=metric.title()),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
        xaxis=dict(tickangle=-45),
    )
    return fig


def sales_heatmap(df: pd.DataFrame) -> go.Figure:
    """Order-volume heatmap: day of week x month."""
    tmp = df.assign(
        weekday=df["order_date"].dt.day_name(),
        month=df["order_date"].dt.strftime("%Y-%m"),
    )
    pivot = tmp.pivot_table(index="weekday", columns="month", values="order_id", aggfunc="nunique", fill_value=0)
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = pivot.reindex([d for d in weekday_order if d in pivot.index])
    fig = px.imshow(pivot, template=_TEMPLATE, title="Order volume: day of week vs. month", aspect="auto")
    return fig


def discount_profit_scatter(df: pd.DataFrame, sample_size: int = 5000, random_state: int = 42) -> go.Figure:
    """Scatter of discount vs. profit, sampled for render performance on large datasets."""
    sample = df.sample(n=min(sample_size, len(df)), random_state=random_state)
    fig = px.scatter(
        sample, x="discount", y="profit", color="category", template=_TEMPLATE,
        title="Discount vs. profit per order", opacity=0.5,
    )
    return fig


def order_value_histogram(df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(df, x="revenue", nbins=60, template=_TEMPLATE, title="Order value distribution")
    fig.update_layout(xaxis_title="Order revenue (USD)")
    return fig


def delivery_time_boxplot(df: pd.DataFrame) -> go.Figure:
    fig = px.box(df, x="category", y="delivery_time", template=_TEMPLATE, title="Delivery time by category")
    fig.update_layout(xaxis_title=None, yaxis_title="Delivery time (days)")
    return fig


def rfm_segment_chart(rfm_df: pd.DataFrame) -> go.Figure:
    """Donut chart of customer counts per RFM segment."""
    counts = rfm_df["segment"].value_counts().reset_index()
    counts.columns = ["segment", "customers"]
    fig = px.pie(
        counts, names="segment", values="customers", template=_TEMPLATE,
        title="Customers by RFM segment", hole=0.4,
    )
    return fig


def forecast_chart(history_df: pd.DataFrame, forecast_df: pd.DataFrame) -> go.Figure:
    """Historical daily revenue plus the forecast line and its confidence band."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=history_df["date"], y=history_df["revenue"], name="Actual", mode="lines"))
    fig.add_trace(go.Scatter(
        x=forecast_df["date"], y=forecast_df["forecast"], name="Forecast",
        mode="lines", line=dict(dash="dash"),
    ))
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast_df["date"], forecast_df["date"][::-1]]),
        y=pd.concat([forecast_df["upper"], forecast_df["lower"][::-1]]),
        fill="toself", fillcolor="rgba(99,110,250,0.15)", line=dict(color="rgba(255,255,255,0)"),
        name="80% interval",
    ))
    fig.update_layout(template=_TEMPLATE, title="Daily revenue forecast", yaxis_title="Revenue (USD)")
    return fig
