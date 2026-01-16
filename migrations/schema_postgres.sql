
-- Accounts
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    name TEXT,
    email TEXT,
    phone TEXT,
    subscription_plan TEXT DEFAULT 'Starter',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    price DOUBLE PRECISION,
    cost_price DOUBLE PRECISION,
    stock_quantity INTEGER,
    tax_rate DOUBLE PRECISION DEFAULT 0.0,
    salt_composition TEXT,
    manufacturer TEXT,
    schedule_type TEXT,
    is_chronic INTEGER DEFAULT 0,
    refill_interval INTEGER DEFAULT 30,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_products_account ON products(account_id);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);

-- Customers
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    name TEXT,
    phone TEXT,
    email TEXT,
    loyalty_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone, account_id);

-- Transactions
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    customer_id TEXT,
    timestamp TIMESTAMP,
    total_amount DOUBLE PRECISION,
    total_profit DOUBLE PRECISION,
    payment_method TEXT,
    points_redeemed INTEGER DEFAULT 0,
    doctor_name TEXT,
    doctor_reg_no TEXT
);
CREATE INDEX IF NOT EXISTS idx_txn_account ON transactions(account_id);

-- Transaction Items
CREATE TABLE IF NOT EXISTS transaction_items (
    id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    product_id TEXT,
    product_name TEXT,
    quantity INTEGER,
    price_at_sale DOUBLE PRECISION,
    cost_at_sale DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS idx_txn_items_txn_id ON transaction_items(transaction_id);

-- Settings
CREATE TABLE IF NOT EXISTS settings (
    account_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    PRIMARY KEY (account_id, key)
);
