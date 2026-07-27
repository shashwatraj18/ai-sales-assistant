"""
SQLAlchemy ORM models for the normalized database.

Written in SQLAlchemy 2.0's typed declarative style (`Mapped` /
`mapped_column`). These models are the source of truth for anything that
goes through the ORM; `schema.sql` expresses the same three tables as raw
DDL for tooling that wants to create the database without importing
SQLAlchemy at all (see `etl/load.py`, which uses the raw DDL directly so
data loading has no hard dependency on the ORM layer).
"""

from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models in this project."""


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(primary_key=True)
    customer_name: Mapped[str]
    age: Mapped[int]
    gender: Mapped[str]
    city: Mapped[str]
    state: Mapped[str]
    region: Mapped[str] = mapped_column(index=True)
    country: Mapped[str]

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")

    def __repr__(self) -> str:
        return f"Customer({self.customer_id!r}, {self.customer_name!r})"


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(index=True)
    sub_category: Mapped[str]
    product_name: Mapped[str]
    unit_price: Mapped[float]
    cost: Mapped[float]

    orders: Mapped[list["Order"]] = relationship(back_populates="product")

    def __repr__(self) -> str:
        return f"Product({self.product_id!r}, {self.product_name!r})"


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(primary_key=True)
    order_date: Mapped[str] = mapped_column(index=True)
    ship_date: Mapped[str]
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), index=True)
    quantity: Mapped[int]
    discount: Mapped[float]
    revenue: Mapped[float]
    profit: Mapped[float]
    sales_channel: Mapped[str]
    payment_method: Mapped[str]
    returned: Mapped[str]
    delivery_time: Mapped[int]
    rating: Mapped[int]

    customer: Mapped[Customer] = relationship(back_populates="orders")
    product: Mapped[Product] = relationship(back_populates="orders")

    def __repr__(self) -> str:
        return f"Order({self.order_id!r}, revenue={self.revenue})"
