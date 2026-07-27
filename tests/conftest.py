"""Shared pytest fixtures: a small synthetic DataFrame shaped like the real dataset."""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """A tiny (12-row) but structurally realistic joined orders DataFrame.

    Deliberately hand-built (not sampled from etl.generate_data) so these
    tests pin down exact expected numbers rather than re-deriving them.
    """
    dates = pd.to_datetime(
        ["2026-01-01", "2026-01-05", "2026-01-10", "2026-01-15",
         "2026-02-01", "2026-02-05", "2026-02-10", "2026-02-15",
         "2026-03-01", "2026-03-05", "2026-03-10", "2026-03-15"]
    )
    return pd.DataFrame({
        "order_id": [f"ORD{i:03d}" for i in range(1, 13)],
        "order_date": dates,
        "ship_date": dates + pd.Timedelta(days=2),
        "quantity": [1, 2, 1, 3, 2, 1, 1, 2, 3, 1, 2, 1],
        "discount": [0.0, 0.1, 0.35, 0.0, 0.05, 0.4, 0.0, 0.1, 0.0, 0.3, 0.05, 0.0],
        "revenue": [100.0, 180.0, 65.0, 300.0, 200.0, 60.0, 100.0, 180.0, 300.0, 70.0, 190.0, 100.0],
        "profit": [40.0, 70.0, -5.0, 120.0, 80.0, -10.0, 40.0, 70.0, 120.0, -2.0, 76.0, 40.0],
        "sales_channel": ["Online"] * 12,
        "payment_method": ["Credit Card"] * 12,
        "returned": ["No", "No", "Yes", "No", "No", "Yes", "No", "No", "No", "Yes", "No", "No"],
        "delivery_time": [2] * 12,
        "rating": [5, 4, 2, 5, 4, 2, 5, 4, 5, 3, 4, 5],
        "customer_id": ["C1", "C1", "C2", "C3", "C1", "C2", "C3", "C4", "C1", "C2", "C3", "C5"],
        "customer_name": ["Alice", "Alice", "Bob", "Cara", "Alice", "Bob", "Cara", "Dev", "Alice", "Bob", "Cara", "Eve"],
        "age": [30, 30, 40, 25, 30, 40, 25, 50, 30, 40, 25, 22],
        "gender": ["Female", "Female", "Male", "Female", "Female", "Male", "Female", "Male", "Female", "Male", "Female", "Female"],
        "city": ["Austin"] * 12,
        "state": ["Texas"] * 12,
        "region": ["South", "South", "West", "South", "South", "West", "South", "Midwest", "South", "West", "South", "Northeast"],
        "country": ["United States"] * 12,
        "product_id": ["P1", "P2", "P3", "P1", "P2", "P3", "P1", "P2", "P1", "P3", "P2", "P1"],
        "category": ["Electronics", "Clothing", "Electronics", "Electronics", "Clothing", "Electronics",
                     "Electronics", "Clothing", "Electronics", "Electronics", "Clothing", "Electronics"],
        "sub_category": ["Smartphones"] * 12,
        "product_name": ["Nova Phone", "Ridge Shirt", "Ion Phone Lite", "Nova Phone", "Ridge Shirt",
                         "Ion Phone Lite", "Nova Phone", "Ridge Shirt", "Nova Phone", "Ion Phone Lite",
                         "Ridge Shirt", "Nova Phone"],
        "unit_price": [100.0, 90.0, 65.0, 100.0, 90.0, 65.0, 100.0, 90.0, 100.0, 65.0, 90.0, 100.0],
        "cost": [60.0, 55.0, 70.0, 60.0, 55.0, 70.0, 60.0, 55.0, 60.0, 70.0, 55.0, 60.0],
    })
