-- AI Sales Analytics Dashboard - database schema
--
-- Normalized into three tables so customer and product attributes are
-- stored once each, rather than repeated on every order row as they are
-- in the flat CSV export. Foreign keys point from orders -> customers and
-- orders -> products.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    customer_id   TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    age           INTEGER NOT NULL,
    gender        TEXT NOT NULL,
    city          TEXT NOT NULL,
    state         TEXT NOT NULL,
    region        TEXT NOT NULL,
    country       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id    TEXT PRIMARY KEY,
    category      TEXT NOT NULL,
    sub_category  TEXT NOT NULL,
    product_name  TEXT NOT NULL,
    unit_price    REAL NOT NULL,
    cost          REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id       TEXT PRIMARY KEY,
    order_date     TEXT NOT NULL,   -- ISO 8601 date
    ship_date      TEXT NOT NULL,   -- ISO 8601 date
    customer_id    TEXT NOT NULL REFERENCES customers (customer_id),
    product_id     TEXT NOT NULL REFERENCES products (product_id),
    quantity       INTEGER NOT NULL,
    discount       REAL NOT NULL,   -- fraction, e.g. 0.20 == 20% off
    revenue        REAL NOT NULL,
    profit         REAL NOT NULL,
    sales_channel  TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    returned       TEXT NOT NULL,   -- 'Yes' / 'No'
    delivery_time  INTEGER NOT NULL,  -- days between order_date and ship_date
    rating         INTEGER NOT NULL
);

-- Query patterns this dashboard runs constantly: filter/aggregate orders by
-- date, by customer, by product, and join out to region/category. Index the
-- FKs and the date column
-- the dimension tables are small enough (thousands
-- of rows) that scans on them are cheap without extra indexes.
CREATE INDEX IF NOT EXISTS idx_orders_order_date  ON orders (order_date);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders (customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_product_id  ON orders (product_id);
CREATE INDEX IF NOT EXISTS idx_customers_region   ON customers (region);
CREATE INDEX IF NOT EXISTS idx_products_category  ON products (category);
