"""
Hand-written, optimized SQL queries for aggregate KPI views.

These run directly against the database rather than in pandas because
they're simple aggregates over the full `orders` table that the database
engine and its indexes already handle well - there's no reason to pull
every row into memory just to compute a handful of numbers.

For the richer, multi-filter interactive analysis in `analytics/`, the
dashboard instead loads the full joined dataset once via
`load_full_dataset` and does the rest in pandas - re-running a fresh SQL
query on every sidebar filter change would be slower than filtering an
in-memory DataFrame at this data volume (~100K rows). See the architecture
note in the README for the reasoning.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

_FULL_JOIN_SQL = """
SELECT
    o.order_id, o.order_date, o.ship_date, o.quantity, o.discount,
    o.revenue, o.profit, o.sales_channel, o.payment_method, o.returned,
    o.delivery_time, o.rating,
    c.customer_id, c.customer_name, c.age, c.gender, c.city, c.state, c.region, c.country,
    p.product_id, p.category, p.sub_category, p.product_name, p.unit_price, p.cost
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products  p ON o.product_id  = p.product_id
"""


def load_full_dataset(engine: Any) -> pd.DataFrame:
    """Run the one join query the whole analytics layer is built on top of.

    Returns every order with its customer and product attributes attached -
    the in-memory equivalent of the original flat CSV, sourced from the
    normalized tables. `engine` accepts a SQLAlchemy Engine/Connection or a
    raw `sqlite3.Connection`.
    """
    df = pd.read_sql(_FULL_JOIN_SQL, engine)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["ship_date"] = pd.to_datetime(df["ship_date"])
    return df


def get_revenue_by_region(engine: Any) -> pd.DataFrame:
    """Total revenue and profit per region, ordered highest revenue first."""
    sql = """
        SELECT c.region,
               ROUND(SUM(o.revenue), 2) AS revenue,
               ROUND(SUM(o.profit), 2)  AS profit,
               COUNT(*)                 AS orders
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY c.region
        ORDER BY revenue DESC
    """
    return pd.read_sql(sql, engine)


def get_top_products(engine: Any, n: int = 10, by: str = "revenue") -> pd.DataFrame:
    """Top `n` products ranked by total revenue or profit."""
    if by not in {"revenue", "profit"}:
        raise ValueError("by must be 'revenue' or 'profit'")
    n = int(n)  # guards the LIMIT clause below against anything but an integer
    sql = f"""
        SELECT p.product_name, p.category,
               ROUND(SUM(o.revenue), 2) AS revenue,
               ROUND(SUM(o.profit), 2)  AS profit,
               SUM(o.quantity)          AS units_sold
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        GROUP BY p.product_id
        ORDER BY {by} DESC
        LIMIT {n}
    """
    return pd.read_sql(sql, engine)


def get_monthly_revenue_trend(engine: Any) -> pd.DataFrame:
    """Monthly revenue and profit using SQLite's built-in date formatting."""
    sql = """
        SELECT strftime('%Y-%m', order_date) AS month,
               ROUND(SUM(revenue), 2) AS revenue,
               ROUND(SUM(profit), 2)  AS profit,
               COUNT(*)               AS orders
        FROM orders
        GROUP BY month
        ORDER BY month
    """
    return pd.read_sql(sql, engine)


def get_return_rate_by_category(engine: Any) -> pd.DataFrame:
    """Return rate (%) per product category, highest first."""
    sql = """
        SELECT p.category,
               ROUND(100.0 * SUM(CASE WHEN o.returned = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 1)
                   AS return_rate_pct,
               COUNT(*) AS orders
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        GROUP BY p.category
        ORDER BY return_rate_pct DESC
    """
    return pd.read_sql(sql, engine)
