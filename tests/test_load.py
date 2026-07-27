"""Tests for etl.load: normalizing the flat dataset into three tables."""

from __future__ import annotations

import pandas as pd

from etl.load import extract_customers, extract_orders, extract_products, normalize


def _flat_fixture() -> pd.DataFrame:
    return pd.DataFrame({
        "Order_ID": ["ORD1", "ORD2"],
        "Order_Date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
        "Ship_Date": pd.to_datetime(["2026-01-03", "2026-01-04"]),
        "Customer_ID": ["C1", "C1"],
        "Customer_Name": ["Alice", "Alice"],
        "Age": [30, 30],
        "Gender": ["Female", "Female"],
        "City": ["Austin", "Austin"],
        "State": ["Texas", "Texas"],
        "Region": ["South", "South"],
        "Country": ["United States", "United States"],
        "Product_ID": ["P1", "P2"],
        "Category": ["Electronics", "Clothing"],
        "Sub_Category": ["Smartphones", "Shirts"],
        "Product_Name": ["Nova Phone", "Ridge Shirt"],
        "Quantity": [1, 2],
        "Unit_Price": [100.0, 50.0],
        "Discount": [0.0, 0.1],
        "Cost": [60.0, 25.0],
        "Revenue": [100.0, 90.0],
        "Profit": [40.0, 40.0],
        "Sales_Channel": ["Online", "Online"],
        "Payment_Method": ["Credit Card", "Credit Card"],
        "Returned": ["No", "No"],
        "Delivery_Time": [2, 2],
        "Rating": [5, 4],
    })


def test_extract_customers_deduplicates() -> None:
    customers = extract_customers(_flat_fixture())
    assert len(customers) == 1  # both rows are the same customer
    assert customers.iloc[0]["customer_id"] == "C1"
    assert list(customers.columns) == [
        "customer_id", "customer_name", "age", "gender", "city", "state", "region", "country",
    ]


def test_extract_products_deduplicates() -> None:
    products = extract_products(_flat_fixture())
    assert len(products) == 2  # two distinct products


def test_extract_orders_keeps_one_row_per_order() -> None:
    orders = extract_orders(_flat_fixture())
    assert len(orders) == 2
    assert orders["order_date"].iloc[0] == "2026-01-01"


def test_normalize_returns_all_three() -> None:
    customers, products, orders = normalize(_flat_fixture())
    assert len(customers) == 1 and len(products) == 2 and len(orders) == 2
