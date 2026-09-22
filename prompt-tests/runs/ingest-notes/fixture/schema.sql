CREATE TABLE IF NOT EXISTS orders (
    order_id    TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    placed_at   TEXT NOT NULL,
    total_cents INTEGER NOT NULL,
    source_file TEXT,
    UNIQUE (order_id)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT NOT NULL,
    email       TEXT,
    source_file TEXT,
    UNIQUE (customer_id)
);

CREATE TABLE IF NOT EXISTS order_lines (
    order_id    TEXT NOT NULL,
    sku         TEXT NOT NULL,
    qty         INTEGER NOT NULL,
    source_file TEXT
);
