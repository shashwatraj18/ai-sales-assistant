"""
Load the flat synthetic dataset into the normalized SQLite database.

Splits the flat, one-row-per-order CSV into the three normalized tables
(`customers`, `products`, `orders`). The extraction functions are pure
pandas - no SQLAlchemy import - so they're testable on their own and
reusable regardless of which engine ultimately receives the data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

_CUSTOMER_COLUMNS = ["Customer_ID", "Customer_Name", "Age", "Gender", "City", "State", "Region", "Country"]
_PRODUCT_COLUMNS = ["Product_ID", "Category", "Sub_Category", "Product_Name", "Unit_Price", "Cost"]
_ORDER_COLUMNS = [
    "Order_ID", "Order_Date", "Ship_Date", "Customer_ID", "Product_ID", "Quantity",
    "Discount", "Revenue", "Profit", "Sales_Channel", "Payment_Method", "Returned",
    "Delivery_Time", "Rating",
]

_RENAME_TO_SNAKE_CASE = {
    "Order_ID": "order_id", "Order_Date": "order_date", "Ship_Date": "ship_date",
    "Customer_ID": "customer_id", "Customer_Name": "customer_name", "Age": "age",
    "Gender": "gender", "City": "city", "State": "state", "Region": "region",
    "Country": "country", "Product_ID": "product_id", "Category": "category",
    "Sub_Category": "sub_category", "Product_Name": "product_name", "Unit_Price": "unit_price",
    "Discount": "discount", "Cost": "cost", "Revenue": "revenue", "Profit": "profit",
    "Sales_Channel": "sales_channel", "Payment_Method": "payment_method", "Returned": "returned",
    "Delivery_Time": "delivery_time", "Rating": "rating",
}


def extract_customers(flat_df: pd.DataFrame) -> pd.DataFrame:
    """De-duplicate customer attributes out of the flat order-level dataset."""
    customers = flat_df[_CUSTOMER_COLUMNS].drop_duplicates(subset="Customer_ID").reset_index(drop=True)
    return customers.rename(columns=_RENAME_TO_SNAKE_CASE)


def extract_products(flat_df: pd.DataFrame) -> pd.DataFrame:
    """De-duplicate product attributes out of the flat order-level dataset."""
    products = flat_df[_PRODUCT_COLUMNS].drop_duplicates(subset="Product_ID").reset_index(drop=True)
    return products.rename(columns=_RENAME_TO_SNAKE_CASE)


def extract_orders(flat_df: pd.DataFrame) -> pd.DataFrame:
    """Project the flat dataset down to the orders table's own columns."""
    orders = flat_df[_ORDER_COLUMNS].copy()
    orders["Order_Date"] = pd.to_datetime(orders["Order_Date"]).dt.strftime("%Y-%m-%d")
    orders["Ship_Date"] = pd.to_datetime(orders["Ship_Date"]).dt.strftime("%Y-%m-%d")
    return orders.rename(columns=_RENAME_TO_SNAKE_CASE)


def normalize(flat_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split the flat dataset into (customers, products, orders) tables."""
    return extract_customers(flat_df), extract_products(flat_df), extract_orders(flat_df)


def load_dataframe_to_db(flat_df: pd.DataFrame, engine: Any) -> None:
    """Write the normalized tables to the database behind `engine`.

    `engine` can be a SQLAlchemy `Engine`/`Connection`, or (useful for
    testing without the SQLAlchemy dependency installed) a raw
    `sqlite3.Connection` - pandas' `to_sql` accepts either for SQLite.
    """
    customers, products, orders = normalize(flat_df)
    customers.to_sql("customers", engine, if_exists="append", index=False)
    products.to_sql("products", engine, if_exists="append", index=False)
    orders.to_sql("orders", engine, if_exists="append", index=False)
    logger.info(
        "Loaded %d customers, %d products, %d orders", len(customers), len(products), len(orders)
    )


def load_csv_to_db(csv_path: Path, engine: Any) -> None:
    """Read the flat CSV and load it into the database behind `engine`."""
    flat_df = pd.read_csv(csv_path, parse_dates=["Order_Date", "Ship_Date"])
    load_dataframe_to_db(flat_df, engine)


if __name__ == "__main__":
    from database.session import get_engine, init_db
    from utils.config import settings

    init_db()
    load_csv_to_db(settings.data_raw_dir / "sales_data.csv", get_engine())
