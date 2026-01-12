import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st
import secrets
import string
import hashlib
import json
import config

# Try to import psycopg2 for Postgres support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_values
except ImportError:
    psycopg2 = None

def get_connection():
    """Returns a database connection based on the configured engine."""
    if config.DB_TYPE == "POSTGRES":
        if psycopg2 is None:
            raise ImportError("psycopg2 is required for PostgreSQL support. Run 'pip install psycopg2-binary'")
        
        return psycopg2.connect(
            host=config.PG_HOST,
            port=config.PG_PORT,
            database=config.PG_NAME,
            user=config.PG_USER,
            password=config.PG_PASS
        )
    else:
        # Default to SQLite
        return sqlite3.connect(config.SQLITE_DB, timeout=30, check_same_thread=False)

# Global SQL Placeholder
PLACEHOLDER = "%s" if config.DB_TYPE == "POSTGRES" else "?"

def generate_unique_id(length=16, numeric_only=False, prefix=''):
    """Generates a secure 16-character unique ID."""
    if numeric_only:
        # Generate 16 digit number string
        # Ensure first digit is not 0 for cleanliness if needed, but string doesn't care.
        chars = string.digits
    else:
        # Alphanumeric (uppercase + digits for readability)
        chars = string.ascii_uppercase + string.digits
    
    # Calculate length needed excluding prefix
    gen_len = max(1, length - len(prefix))
    random_str = ''.join(secrets.choice(chars) for _ in range(gen_len))
    return f"{prefix}{random_str}"

def get_current_account_id():
    """
    Retrieves the logged-in user's Account ID from Session State.
    Returns None if not logged in.
    """
    if 'account_id' in st.session_state:
        return st.session_state['account_id']
    return None

def init_db():
    """Initializes the database with necessary tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    if config.DB_TYPE == "SQLITE":
        # OPTIMIZATION: Enable WAL Mode for concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;") 
    
    # helper for insert ignore
    insert_ignore = "INSERT INTO accounts (id, company_name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING" if config.DB_TYPE == "POSTGRES" else "INSERT OR IGNORE INTO accounts (id, company_name) VALUES (?, ?)"
    place = "%s" if config.DB_TYPE == "POSTGRES" else "?"

    # 1. Accounts Table (Tenants)
    c.execute(f'''
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            subscription_plan TEXT DEFAULT 'Starter',
            status TEXT DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Ensure Default Demo Account Exists
    demo_id = config.DEFAULT_ACCOUNT_ID
    c.execute(insert_ignore, (demo_id, 'VyaparMind Demo Store'))

    # 2. Products Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            account_id TEXT DEFAULT '1111222233334444',
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            cost_price REAL NOT NULL,
            stock_quantity INTEGER DEFAULT 0,
            tax_rate REAL DEFAULT 0.0,
            updated_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')
    
    # 3. Transactions Table (Head)
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            account_id TEXT DEFAULT '1111222233334444',
            customer_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL NOT NULL,
            total_profit REAL NOT NULL,
            payment_method TEXT DEFAULT 'CASH',
            transaction_hash TEXT,
            points_redeemed INTEGER DEFAULT 0,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')
    
    # 4. Transaction Items (Line Items)
    c.execute('''
        CREATE TABLE IF NOT EXISTS transaction_items (
            id TEXT PRIMARY KEY,
            transaction_id TEXT,
            product_id TEXT,
            product_name TEXT,
            quantity INTEGER,
            price_at_sale REAL,
            cost_at_sale REAL,
            FOREIGN KEY (transaction_id) REFERENCES transactions (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    # 5. Settings Table (Multi-Tenant)
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            account_id TEXT,
            key TEXT,
            value TEXT,
            UNIQUE(account_id, key),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')
    
    # Demo Defaults
    insert_settings = "INSERT INTO settings (account_id, key, value) VALUES (%s, %s, %s) ON CONFLICT (account_id, key) DO NOTHING" if config.DB_TYPE == "POSTGRES" else "INSERT OR IGNORE INTO settings (account_id, key, value) VALUES (?, ?, ?)"
    c.execute(insert_settings, (demo_id, 'store_name', 'VyaparMind Store'))
    c.execute(insert_settings, (demo_id, 'store_address', 'Hyderabad, India'))
    c.execute(insert_settings, (demo_id, 'store_phone', '9876543210'))
    c.execute(insert_settings, (demo_id, 'subscription_plan', 'Starter'))

    # 6. Customers Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            account_id TEXT DEFAULT '1111222233334444',
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            city TEXT DEFAULT 'Unknown',
            pincode TEXT DEFAULT '000000',
            loyalty_points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')
    
    # 7. Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            account_id TEXT DEFAULT '1111222233334444',
            username TEXT NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'admin', -- admin, manager, staff, super_admin
            permissions TEXT, -- Comma separated list of allowed modules
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            UNIQUE(account_id, username)
        )
    ''')

    # Ensure Default SuperAdmin User Exists for Demo Account
    admin_user = "superadmin"
    admin_pass = "admin123" # Default password
    admin_hash = hashlib.sha256(admin_pass.encode()).hexdigest()
    
    insert_user = f"INSERT INTO users (id, account_id, username, email, password_hash, role) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}) ON CONFLICT (account_id, username) DO NOTHING" if config.DB_TYPE == "POSTGRES" else "INSERT OR IGNORE INTO users (id, account_id, username, email, password_hash, role) VALUES (?, ?, ?, ?, ?, ?)"
    
    # Using 'super_admin' role for dashboard access
    c.execute(insert_user, (generate_unique_id(16), demo_id, admin_user, 'admin@vyaparmind.com', admin_hash, 'super_admin'))
    
    # 8. Product Batches (FreshFlow)
    c.execute('''
        CREATE TABLE IF NOT EXISTS product_batches (
            id TEXT PRIMARY KEY,
            account_id TEXT DEFAULT '1111222233334444',
            product_id TEXT,
            batch_code TEXT,
            expiry_date DATE,
            quantity INTEGER,
            cost_price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
    ''')

    # --- OPTIMIZATION: INDEXES ---
    # Global Account Isolation Indexes
    c.execute("CREATE INDEX IF NOT EXISTS idx_products_aid ON products(account_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_customers_aid ON customers(account_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_transactions_aid ON transactions(account_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_suppliers_aid ON suppliers(account_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_staff_aid ON staff(account_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_batches_aid ON product_batches(account_id)")
    
    # Search & Join Indexes
    c.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_txn_items_txn_id ON transaction_items(transaction_id)")


    # 9. Suppliers (VendorTrust)
    c.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id TEXT PRIMARY KEY,
            account_id TEXT DEFAULT '1111222233334444',
            name TEXT,
            contact_person TEXT,
            phone TEXT,
            category_specialty TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')

    # 10. Purchase Orders (VendorTrust)
    c.execute('''
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id TEXT PRIMARY KEY,
            account_id TEXT DEFAULT '1111222233334444',
            supplier_id TEXT,
            order_date DATE,
            expected_date DATE,
            received_date DATE,
            status TEXT DEFAULT 'PENDING', -- PENDING, RECEIVED, CANCELLED
            quality_rating REAL,
            notes TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')

    # 11. Staff (ShiftSmart)
    c.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id TEXT PRIMARY KEY,
            account_id TEXT DEFAULT '1111222233334444',
            name TEXT,
            role TEXT,
            hourly_rate REAL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')

    # 12. Shifts (ShiftSmart)
    c.execute('''
        CREATE TABLE IF NOT EXISTS shifts (
            id TEXT PRIMARY KEY,
            staff_id TEXT,
            date DATE,
            slot TEXT, -- Morning, Evening
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (staff_id) REFERENCES staff(id)
        )
    ''')
    
    # 13. Daily Context (IsoBar) - Uses Composite PK usually, but let's standardize simple ID for simplicity?
    # Context is usually unique per date per account.
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_context (
            account_id TEXT,
            date DATE,
            weather_tag TEXT,
            event_tag TEXT,
            notes TEXT,
            PRIMARY KEY (account_id, date),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')

    # 14. B2B Deals (StockSwap)
    c.execute('''
        CREATE TABLE IF NOT EXISTS b2b_deals (
            id TEXT PRIMARY KEY,
            account_id TEXT DEFAULT '1111222233334444',
            store_name TEXT,
            product_name TEXT,
            quantity INTEGER,
            price_per_unit REAL,
            acc_phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')

    # 15. Crowd Campaigns (CrowdStock)
    c.execute('''
        CREATE TABLE IF NOT EXISTS crowd_campaigns (
            id TEXT PRIMARY KEY,
            account_id TEXT DEFAULT '1111222233334444',
            item_name TEXT,
            description TEXT,
            votes_needed INTEGER,
            votes_current INTEGER DEFAULT 0,
            price_est REAL,
            status TEXT DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')
    
    # 16. Restaurant Tables (TableLink) is handled by create_table_management_tables, 
    # but we can initialize it here for consistency if we update that function to do nothing if exists.
    # Let's leave it to that module logic but update that function later.

    # Leave connection open for migrations below
    # conn.commit() 
    # conn.close()
    
    # Check for new columns in customers (Migration)
    try:
        c.execute("SELECT city FROM customers LIMIT 1")
    except:
        c.execute("ALTER TABLE customers ADD COLUMN city TEXT DEFAULT 'Unknown'")
        c.execute("ALTER TABLE customers ADD COLUMN pincode TEXT DEFAULT '000000'")

    # Check for science_tags in products (Migration Phase 3)
    try:
        c.execute("SELECT science_tags FROM products LIMIT 1")
    except:
        c.execute("ALTER TABLE products ADD COLUMN science_tags TEXT")

    
    # product_batches(expiry_date) for FreshFlow
    c.execute("CREATE INDEX IF NOT EXISTS idx_batches_expiry ON product_batches(expiry_date)")

    # 9. Subscription Plans Table (Super Admin)
    # Postgres uses SERIAL for autoincrement
    pk_auto = "SERIAL PRIMARY KEY" if config.DB_TYPE == "POSTGRES" else "INTEGER PRIMARY KEY AUTOINCREMENT"
    c.execute(f'''
        CREATE TABLE IF NOT EXISTS subscription_plans (
            id {pk_auto},
            name TEXT UNIQUE,
            price REAL,
            modules TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Default Plans
    insert_plan = f"INSERT INTO subscription_plans (name, price) VALUES ({PLACEHOLDER}, {PLACEHOLDER}) ON CONFLICT (name) DO NOTHING" if config.DB_TYPE == "POSTGRES" else "INSERT OR IGNORE INTO subscription_plans (name, price) VALUES (?, ?)"
    c.execute(insert_plan, ('Professional', 2999))
    c.execute(insert_plan, ('Enterprise', 9999))

    # Migration: Accounts Status
    try:
        c.execute("SELECT status FROM accounts LIMIT 1")
    except:
        c.execute("ALTER TABLE accounts ADD COLUMN status TEXT DEFAULT 'ACTIVE'")

    # Migration: User Permissions
    try:
        c.execute("SELECT permissions FROM users LIMIT 1")
    except:
        c.execute("ALTER TABLE users ADD COLUMN permissions TEXT")

    # Ensure Restaurant Tables are created/migrated
    create_table_management_tables(conn)
    create_online_integration_tables(conn)

    conn.commit()
    conn.close()



def get_setting(key):
    """Fetch a setting value by key (Scoped)."""
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    # Check Account Specific Setting
    c.execute(f"SELECT value FROM settings WHERE key = {PLACEHOLDER} AND account_id = {PLACEHOLDER}", (key, aid))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    return "VyaparMind Store" if key == 'store_name' else None # Fallback

def update_setting(key, value):
    """Update or Set a setting (Scoped)."""
    return set_setting(key, value)

def set_setting(key, value):
    """Update or Set a setting (Scoped). Returns (bool, msg)."""
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        # Check if exists for this account
        c.execute(f"SELECT value FROM settings WHERE key = {PLACEHOLDER} AND account_id = {PLACEHOLDER}", (key, aid))
        if c.fetchone():
            c.execute(f"UPDATE settings SET value = {PLACEHOLDER} WHERE key = {PLACEHOLDER} AND account_id = {PLACEHOLDER}", (value, key, aid))
        else:
            c.execute(f"INSERT INTO settings (account_id, key, value) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})", (aid, key, value))
            
        # SYNC: If updating subscription_plan, also update accounts table
        if key == 'subscription_plan':
            c.execute("UPDATE accounts SET subscription_plan = ? WHERE id = ?", (value, aid))
            
        conn.commit()
        return True, "Success"
    except Exception as e:
        err_msg = f"DB Error: {e}"
        print(err_msg)
        return False, err_msg
    finally:
        conn.close()

def add_product(name, category, price, cost_price, stock_quantity, tax_rate=0.0, override_account_id=None):
    conn = get_connection()
    c = conn.cursor()
    account_id = override_account_id if override_account_id is not None else get_current_account_id()
    new_id = generate_unique_id(16)
    try:
        c.execute(f"INSERT INTO products (id, account_id, name, category, price, cost_price, stock_quantity, tax_rate) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
                  (new_id, account_id, name, category, price, cost_price, stock_quantity, tax_rate))
        conn.commit()
        return True, "Product added successfully."
    except Exception as e:
        print(e)
        return False, str(e)
    finally:
        conn.close()
        # Invalidate Cache
        _fetch_all_products_impl.clear()
        _fetch_pos_inventory_impl.clear()

def update_product(product_id, price, cost_price, stock_quantity, tax_rate):
    """Updates price, cost, stock, and tax (Scoped)."""
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        c.execute(f"UPDATE products SET price = {PLACEHOLDER}, cost_price = {PLACEHOLDER}, stock_quantity = {PLACEHOLDER}, tax_rate = {PLACEHOLDER}, updated_at = {PLACEHOLDER} WHERE id = {PLACEHOLDER} AND account_id = {PLACEHOLDER}",
                  (price, cost_price, stock_quantity, tax_rate, datetime.now(), product_id, aid))
        conn.commit()
        return True
    except Exception as e:
        print(f"Update Error: {e}")
        return False
    finally:
        conn.close()
        # Invalidate Cache
        _fetch_all_products_impl.clear()

@st.cache_data(ttl=300)
def _fetch_all_products_impl(account_id):
    """Internal cached fetcher."""
    conn = get_connection()
    # RLS: Filter by account_id
    df = pd.read_sql_query(f"SELECT * FROM products WHERE account_id = {PLACEHOLDER}", conn, params=(account_id,))
    conn.close()
    return df

def fetch_all_products(search_term=None, override_account_id=None):
    """
    Optimized fetcher with server-side searching.
    search_term: Optional string to filter by name or category.
    """
    conn = get_connection()
    aid = override_account_id if override_account_id else get_current_account_id()
    query = f"SELECT * FROM products WHERE account_id = {PLACEHOLDER}"
    params = [aid]
    
    if search_term:
        query += f" AND (name ILIKE {PLACEHOLDER} OR category ILIKE {PLACEHOLDER})" if config.DB_TYPE=="POSTGRES" else f" AND (name LIKE {PLACEHOLDER} OR category LIKE {PLACEHOLDER})"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
        
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

@st.cache_data(ttl=60)
def _fetch_pos_inventory_impl(account_id):
    conn = get_connection()
    # Left join to include products even with 0 sales
    # RLS: Only products for this account
    query = """
        SELECT p.*, COALESCE(SUM(ti.quantity), 0) as total_sold
        FROM products p
        LEFT JOIN transaction_items ti ON p.id = ti.product_id
        WHERE p.account_id = ?
        GROUP BY p.id
    """
    df = pd.read_sql_query(query, conn, params=(account_id,))
    conn.close()
    return df

def fetch_pos_inventory(search_term=None, limit=50, override_account_id=None):
    """
    Optimized POS fetcher. 
    - search_term: Filter by name/category
    - limit: Max rows to return (default 50 for speed)
    """
    conn = get_connection()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    
    query = """
        SELECT p.*, COALESCE(SUM(ti.quantity), 0) as total_sold
        FROM products p
        LEFT JOIN transaction_items ti ON p.id = ti.product_id
        WHERE p.account_id = ?
    """
    params = [aid]
    
    if search_term:
        query += f" AND (p.name ILIKE {PLACEHOLDER} OR p.category ILIKE {PLACEHOLDER})" if config.DB_TYPE=="POSTGRES" else f" AND (p.name LIKE {PLACEHOLDER} OR p.category LIKE {PLACEHOLDER})"
        wildcard = f"%{search_term}%"
        params.extend([wildcard, wildcard])
        
    query += " GROUP BY p.id"
    
    if not search_term:
        # If no search, sort by popularity to show best items first
        query += " ORDER BY total_sold DESC"
    
    query += f" LIMIT {limit}"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

@st.cache_data(ttl=300)
def _fetch_customers_impl(account_id):
    """Internal cached fetcher."""
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM customers WHERE account_id = {PLACEHOLDER}", conn, params=(account_id,))
    conn.close()
    return df

def fetch_customers():
    """Public Wrapper."""
    aid = get_current_account_id()
    return _fetch_customers_impl(aid)

def get_customer_by_phone(phone):
    """Fetch customer by phone number (Scoped)."""
    conn = get_connection()
    aid = get_current_account_id()
    # clean phone? assume exact match for now
    df = pd.read_sql_query("SELECT * FROM customers WHERE phone = ? AND account_id = ?", conn, params=(phone, aid))
    conn.close()
    return df.iloc[0].to_dict() if not df.empty else None

def add_customer(name, phone, email, city="Unknown", pincode="000000"):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    new_id = generate_unique_id(16, numeric_only=True) # Customers get numeric IDs often
    try:
        # Check uniqueness manually since we didn't add UNIQUE constraint at creation
        c.execute(f"SELECT id FROM customers WHERE phone = {PLACEHOLDER} AND account_id = {PLACEHOLDER}", (phone, aid))
        if c.fetchone():
            return False, "Customer with this phone already exists!" # Return tuple (Success, Msg)

        c.execute(f"INSERT INTO customers (id, account_id, name, phone, email, city, pincode) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})", (new_id, aid, name, phone, email, city, pincode))
        conn.commit()
        return True, "Customer added successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
        # Invalidate Cache
        _fetch_customers_impl.clear()

def update_stock(product_id, quantity_change):
    """Updates stock (Scoped). quantity_change can be negative (sale) or positive (restock)."""
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    c.execute(f'UPDATE products SET stock_quantity = stock_quantity + {PLACEHOLDER} WHERE id = {PLACEHOLDER} AND account_id = {PLACEHOLDER}', (quantity_change, product_id, aid))
    conn.commit()
    conn.close()
    # Invalidate Cache
    _fetch_all_products_impl.clear(), _fetch_pos_inventory_impl.clear()


# --- FRESHFLOW MODULE LOGIC ---

def add_batch(product_id, batch_code, expiry_date, quantity, cost_price, override_account_id=None):
    """Adds a new batch and updates total stock."""
    conn = get_connection()
    c = conn.cursor()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    new_id = generate_unique_id(16)
    try:
        # 1. Insert Batch (With Account ID)
        c.execute(f'''
            INSERT INTO product_batches (id, account_id, product_id, batch_code, expiry_date, quantity, cost_price)
            VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})
        ''', (new_id, aid, product_id, batch_code, expiry_date, quantity, cost_price))
        
        # 2. Update Total Stock in master table (Scoped)
        c.execute(f'UPDATE products SET stock_quantity = stock_quantity + {PLACEHOLDER} WHERE id = {PLACEHOLDER} AND account_id = {PLACEHOLDER}', (quantity, product_id, aid))
        
        conn.commit()
        return True, "Batch added successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()
        _fetch_all_products_impl.clear()
        _fetch_pos_inventory_impl.clear()

def get_expiring_batches(days_threshold=7, override_account_id=None):
    """Returns batches expiring within threshold days (Scoped)."""
    conn = get_connection()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    # Logic: expiry_date <= (today + threshold) AND quantity > 0
    if config.DB_TYPE == "POSTGRES":
        query = f'''
            SELECT b.*, p.name as product_name, p.price as current_price
            FROM product_batches b
            JOIN products p ON b.product_id = p.id
            WHERE b.account_id = {PLACEHOLDER} 
            AND b.quantity > 0 
            AND b.expiry_date <= CURRENT_DATE + (interval '1 day' * {PLACEHOLDER})
            ORDER BY b.expiry_date ASC
        '''
    else:
        query = f'''
            SELECT b.*, p.name as product_name, p.price as current_price
            FROM product_batches b
            JOIN products p ON b.product_id = p.id
            WHERE b.account_id = {PLACEHOLDER} 
            AND b.quantity > 0 
            AND b.expiry_date <= date('now', '+' || {PLACEHOLDER} || ' days')
            ORDER BY b.expiry_date ASC
        '''
    df = pd.read_sql_query(query, conn, params=(aid, str(days_threshold)))
    conn.close()
    return df

# --- VENDORTRUST MODULE LOGIC ---

def add_supplier(name, contact, phone, specialty, override_account_id=None):
    conn = get_connection()
    c = conn.cursor()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    new_id = generate_unique_id(16)
    try:
        # Check uniqueness (Scoped)
        c.execute(f"SELECT id FROM suppliers WHERE (name = {PLACEHOLDER} OR phone = {PLACEHOLDER}) AND account_id = {PLACEHOLDER}", (name, phone, aid))
        if c.fetchone():
            return False, "Supplier already exists (same name or phone)."
            
        c.execute(f"INSERT INTO suppliers (id, account_id, name, contact_person, phone, category_specialty) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})", 
                  (new_id, aid, name, contact, phone, specialty))
        conn.commit()
        return True, "Supplier added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

@st.cache_data(ttl=300)
def get_all_suppliers(override_account_id=None):
    conn = get_connection()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    # Deduplicate view logic: Group by name/phone to hide dupes if they exist
    df = pd.read_sql_query(f"SELECT * FROM suppliers WHERE account_id = {PLACEHOLDER} GROUP BY name", conn, params=(aid,))
    conn.close()
    return df

def create_purchase_order(supplier_id, expected_date, notes="", override_account_id=None):
    conn = get_connection()
    c = conn.cursor()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    new_id = generate_unique_id(16)
    try:
        c.execute(f"INSERT INTO purchase_orders (id, account_id, supplier_id, order_date, expected_date, notes) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, CURRENT_DATE, {PLACEHOLDER}, {PLACEHOLDER})",
                  (new_id, aid, supplier_id, expected_date, notes))
        conn.commit()
        return True, "PO Created."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_open_pos():
    conn = get_connection()
    aid = get_current_account_id()
    query = f'''
        SELECT po.*, s.name as supplier_name 
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.id
        WHERE po.status = 'PENDING' AND po.account_id = {PLACEHOLDER}
    '''
    df = pd.read_sql_query(query, conn, params=(aid,))
    conn.close()
    return df

def receive_purchase_order(po_id, quality_rating):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        c.execute(f'''
            UPDATE purchase_orders 
            SET status = 'RECEIVED', received_date = CURRENT_DATE, quality_rating = {PLACEHOLDER}
            WHERE id = {PLACEHOLDER} AND account_id = {PLACEHOLDER}
        ''', (quality_rating, po_id, aid))
        conn.commit()
        return True, "PO Received."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_vendor_scorecard(supplier_id):
    conn = get_connection()
    aid = get_current_account_id()
    # Scoped to Account
    query = f"SELECT * FROM purchase_orders WHERE supplier_id = {PLACEHOLDER} AND account_id = {PLACEHOLDER} AND status = 'RECEIVED'"
    df = pd.read_sql_query(query, conn, params=(supplier_id, aid))
    conn.close()
    
    if df.empty:
        return {'on_time_rate': 100, 'avg_quality': 5.0, 'risk': 'Unknown (New)'}
    
    df['expected_date'] = pd.to_datetime(df['expected_date'])
    df['received_date'] = pd.to_datetime(df['received_date'])
    
    on_time_count = len(df[df['received_date'] <= df['expected_date']])
    total = len(df)
    on_time_rate = (on_time_count / total) * 100
    avg_quality = df['quality_rating'].mean()
    
    risk = "Low"
    if on_time_rate < 70 or avg_quality < 3.0:
        risk = "High"
    elif on_time_rate < 90 or avg_quality < 4.0:
        risk = "Medium"
        
    return {'on_time_rate': on_time_rate, 'avg_quality': avg_quality, 'risk': risk}

# --- ISOBAR MODULE LOGIC ---

def set_daily_context(date_str, weather, event, notes=""):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        # Postgres ON CONFLICT, SQLite INSERT OR IGNORE
        if config.DB_TYPE == "POSTGRES":
            c.execute(f"INSERT INTO daily_context (account_id, date, weather_tag, event_tag, notes) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}) ON CONFLICT (account_id, date) DO UPDATE SET weather_tag = EXCLUDED.weather_tag, event_tag = EXCLUDED.event_tag, notes = EXCLUDED.notes",
                      (aid, date_str, weather, event, notes))
        else:
            # SQLite's INSERT OR REPLACE handles upsert
            c.execute(f"INSERT OR REPLACE INTO daily_context (account_id, date, weather_tag, event_tag, notes) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
                      (aid, date_str, weather, event, notes))
        conn.commit()
        return True, "Context Saved."
    except Exception as e:
        print(f"ISO Error: {e}")
        return False, str(e)
    finally:
        conn.close()

def get_daily_context(date_str):
    conn = get_connection()
    aid = get_current_account_id()
    df = pd.read_sql_query(f"SELECT * FROM daily_context WHERE date = {PLACEHOLDER} AND account_id = {PLACEHOLDER}", conn, params=(date_str, aid))
    conn.close()
    return df.iloc[0].to_dict() if not df.empty else None

def analyze_context_demand(weather_filter=None, event_filter=None):
    """
    Finds top selling items on days that match the filters (Scoped).
    """
    conn = get_connection()
    aid = get_current_account_id()
    
    # 1. Find dates matching context for this account
    query = "SELECT date FROM daily_context WHERE account_id = ?"
    params = [aid]
    
    if weather_filter and weather_filter != "None":
        query += " AND weather_tag = ?"
        params.append(weather_filter)
        
    if event_filter and event_filter != "None":
        query += " AND event_tag = ?"
        params.append(event_filter)

# --- TABLELINK (RESTAURANT) MODULE LOGIC ---

def create_table_management_tables(conn):
    c = conn.cursor()
    # Restaurant Tables (Already added to init_db, but logic here for safety or redundancy? 
    # Actually, init_db now handles it. Let's make this idempotent or just skip if exists)
    # But table_orders IS NOT in init_db yet (my mistake in previous thought). Let's add it here properly or move to init_db.
    # Moving to init_db is cleaner, but to save edits, I'll update it here.
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS restaurant_tables (
            id TEXT PRIMARY KEY,
            account_id TEXT DEFAULT '1111222233334444',
            label TEXT,
            capacity INTEGER DEFAULT 4,
            status TEXT DEFAULT 'Available', -- Available, Occupied, Reserved, Bill Requested
            current_order_id TEXT,
            waiter_id TEXT, -- Assigned Waiter
            pos_x INTEGER DEFAULT 0, -- Grid X
            pos_y INTEGER DEFAULT 0, -- Grid Y
            merged_with TEXT, -- ID of parent table if merged
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')

    # MIGRATION: Attempt to add columns to existing tables
    try:
        c.execute("ALTER TABLE restaurant_tables ADD COLUMN waiter_id TEXT")
    except: pass
    try:
        c.execute("ALTER TABLE restaurant_tables ADD COLUMN pos_x INTEGER DEFAULT 0")
    except: pass
    try:
        c.execute("ALTER TABLE restaurant_tables ADD COLUMN pos_y INTEGER DEFAULT 0")
    except: pass
    try:
        c.execute("ALTER TABLE restaurant_tables ADD COLUMN merged_with TEXT")
    except: pass

    
    # Active Table Orders (Temporary holding before Transaction)
    c.execute('''
        CREATE TABLE IF NOT EXISTS table_orders (
            id TEXT PRIMARY KEY,
            account_id TEXT DEFAULT '1111222233334444',
            table_id TEXT,
            items_json TEXT, -- JSON string of items
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (table_id) REFERENCES restaurant_tables(id),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')
    
    # See if we need to seed
    # With TEXT IDs, seeding 1..6 is standard '1', '2' etc? No, use GUIDs?
    # For demo, maybe standardized Text IDs like 'TABLE-01', 'TABLE-02' are better for readability?
    # Or just GUIDs. Let's use GUIDs.
    
    conn.commit()

@st.cache_data(ttl=60)
def get_tables():
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    # Ensure tables exist for this account
    df = pd.read_sql_query(f"SELECT * FROM restaurant_tables WHERE account_id = {PLACEHOLDER}", conn, params=(aid,))
    conn.close()
    return df

def occupy_table(table_id):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    new_order_id = generate_unique_id(16)
    try:
        # Create new order
        c.execute("INSERT INTO table_orders (id, account_id, table_id, items_json) VALUES (?, ?, ?, '[]')", (new_order_id, aid, table_id))
        
        # Update Table
        c.execute("UPDATE restaurant_tables SET status = 'Occupied', current_order_id = ? WHERE id = ?", (new_order_id, table_id))
        conn.commit()
        # Invalidate Cache
        get_tables.clear()
        get_enriched_tables.clear()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()

def get_table_order(table_id):
    conn = get_connection()
    c = conn.cursor()
    query = """
        SELECT o.id, o.items_json 
        FROM restaurant_tables t
        JOIN table_orders o ON t.current_order_id = o.id
        WHERE t.id = ?
    """
    c.execute(query, (table_id,))
    res = c.fetchone()
    conn.close()
    
    if res:
        import json
        return res[0], json.loads(res[1])
    return None, []

def _get_kot_section(category):
    """Helper to route items to sections based on category"""
    if not category: return "Kitchen"
    cat = category.lower()
    if any(k in cat for k in ['bar', 'cocktail', 'wine', 'beer', 'drink', 'beverage', 'alcohol']):
        return "Bar"
    if any(k in cat for k in ['dessert', 'ice cream', 'cake', 'sweet']):
        return "Dessert"
    return "Kitchen"

def add_item_to_table(table_id, item_dict):
    conn = get_connection()
    c = conn.cursor()
    try:
        # Get current items
        order_id, current_items = get_table_order(table_id)
        if order_id is None: return False
        
        # Route item to section if not already set
        if 'section' not in item_dict:
            item_dict['section'] = _get_kot_section(item_dict.get('category'))
            
        # Check if item exists to merge (only merge if status is pending)
        found = False
        for i in current_items:
            if i['id'] == item_dict['id'] and i.get('status', 'pending') == 'pending':
                i['qty'] += item_dict['qty']
                i['total'] += item_dict['total']
                found = True
                break
        
        if not found:
            # Ensure new item has pending status
            if 'status' not in item_dict:
                item_dict['status'] = 'pending'
            current_items.append(item_dict)
            
        import json
        new_json = json.dumps(current_items)
        
        c.execute("UPDATE table_orders SET items_json = ? WHERE id = ?", (new_json, order_id))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()

def free_table(table_id):
    """Clears table without saving transaction (Cancel)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"UPDATE restaurant_tables SET status = 'Available', current_order_id = NULL WHERE id = {PLACEHOLDER}", (table_id,))
    conn.commit()
    conn.close()

def add_restaurant_table(label, capacity):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    new_id = generate_unique_id(16)
    try:
        c.execute(f"INSERT INTO restaurant_tables (id, account_id, label, capacity, status) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, 'Available')", (new_id, aid, label, capacity))
        conn.commit()
        return True, "Table Added"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_restaurant_table(table_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        # Check if occupied
        c.execute(f"SELECT status FROM restaurant_tables WHERE id = {PLACEHOLDER}", (table_id,))
        res = c.fetchone()
        if res and res[0] != 'Available':
            return False, "Cannot delete occupied table"
            
        c.execute(f"DELETE FROM restaurant_tables WHERE id = {PLACEHOLDER}", (table_id,))
        conn.commit()
        return True, "Table Deleted"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_table_status(table_id, status):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(f"UPDATE restaurant_tables SET status = {PLACEHOLDER} WHERE id = {PLACEHOLDER}", (status, table_id))
        conn.commit()
        return True
    finally:
        conn.close()

def transfer_table(table_id, waiter_name):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE restaurant_tables SET waiter_id = ? WHERE id = ?", (waiter_name, table_id))
        conn.commit()
        return True
    finally:
        conn.close()

def merge_tables(parent_id, child_ids):
    conn = get_connection()
    c = conn.cursor()
    try:
        for child in child_ids:
            c.execute(f"UPDATE restaurant_tables SET merged_with = {PLACEHOLDER} WHERE id = {PLACEHOLDER}", (parent_id, child))
        conn.commit()
        return True
    finally:
        conn.close()

def unmerge_table(table_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        # If this is a child, unmerge it
        c.execute(f"UPDATE restaurant_tables SET merged_with = NULL WHERE id = {PLACEHOLDER}", (table_id,))
        # If this is a parent, unmerge all children
        c.execute(f"UPDATE restaurant_tables SET merged_with = NULL WHERE merged_with = {PLACEHOLDER}", (table_id,))
        conn.commit()
        return True
    finally:
        conn.close()

def update_table_position(table_id, x, y):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(f"UPDATE restaurant_tables SET pos_x = {PLACEHOLDER}, pos_y = {PLACEHOLDER} WHERE id = {PLACEHOLDER}", (x, y, table_id))
        conn.commit()
        return True
    finally:
        conn.close()

@st.cache_data(ttl=30)
def get_enriched_tables():
    """Replacment for fetch_floor_status to include new columns"""
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    
    # Left Join to get active order details
    query = f"""
        SELECT t.id, t.label, t.capacity, t.status, t.current_order_id, t.waiter_id, t.pos_x, t.pos_y, t.merged_with,
               o.start_time, o.items_json
        FROM restaurant_tables t
        LEFT JOIN table_orders o ON t.current_order_id = o.id
        WHERE t.account_id = {PLACEHOLDER}
    """
    df = pd.read_sql_query(query, conn, params=(aid,))
    conn.close()
    
    # Process JSON
    import json
    results = []
    for _, row in df.iterrows():
        items = []
        if row['items_json']:
            try:
                items = json.loads(row['items_json'])
            except: pass
            
        results.append({
            'id': row['id'],
            'label': row['label'],
            'capacity': row['capacity'],
            'status': row['status'],
            'waiter_id': row['waiter_id'],
            'pos_x': row['pos_x'],
            'pos_y': row['pos_y'],
            'merged_with': row['merged_with'],
            'start_time': row['start_time'],
            'items': items
        })
    return results




def update_restaurant_table_capacity(table_id, new_capacity):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(f"UPDATE restaurant_tables SET capacity = {PLACEHOLDER} WHERE id = {PLACEHOLDER}", (new_capacity, table_id))
        conn.commit()
        return True, "Updated"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def mark_items_kot_printed(table_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        aid = get_current_account_id()
        # Get current items
        query = """
            SELECT o.id, o.items_json 
            FROM restaurant_tables t
            JOIN table_orders o ON t.current_order_id = o.id
            WHERE t.id = {PLACEHOLDER}
        """
        c.execute(query, (table_id,))
        res = c.fetchone()
        
        if not res: return False, "No active order", None
        
        order_id = res[0]
        import json
        items = json.loads(res[1])
        
        modified = False
        for i in items:
            if i.get('status', 'pending') == 'pending':
                i['status'] = 'ordered' # Sent to kitchen
                # Add timestamp for KDS tracking
                i['ordered_at'] = datetime.utcnow().isoformat()
                modified = True
                
        if modified:
            new_json = json.dumps(items)
            c.execute(f"UPDATE table_orders SET items_json = {PLACEHOLDER} WHERE id = {PLACEHOLDER}", (new_json, order_id))
            conn.commit()
            return True, "KOT Sent", order_id
        return False, "No new items", order_id
    except Exception as e:
        return False, str(e), None
    finally:
        conn.close()

def cancel_table_item(table_id, item_idx):
    """Marks an item as Cancelled instead of deleting it (for audit)"""
    conn = get_connection()
    c = conn.cursor()
    try:
        order_id, items = get_table_order(table_id)
        if not order_id or item_idx >= len(items): return False
        
        # Items already sent to kitchen? Mark as cancelled.
        # Pending items? Just remove or mark? 
        # User wants "Cancel KOT" which usually means already sent.
        items[item_idx]['status'] = 'cancelled'
        items[item_idx]['cancelled_at'] = datetime.utcnow().isoformat()
        
        import json
        c.execute(f"UPDATE table_orders SET items_json = {PLACEHOLDER} WHERE id = {PLACEHOLDER}", (json.dumps(items), order_id))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()

def get_table_kot_history(table_id):
    """Fetches all items that have been sent to kitchen for reprinting"""
    _, items = get_table_order(table_id)
    # Filter for anything not pending
    sent_items = [i for i in items if i.get('status') not in ['pending', 'cancelled']]
    return sent_items

def update_item_kds_status(table_id, item_idx, new_status):
    conn = get_connection()
    c = conn.cursor()
    try:
        query = """
            SELECT o.id, o.items_json 
            FROM restaurant_tables t
            JOIN table_orders o ON t.current_order_id = o.id
            WHERE t.id = ?
        """
        c.execute(query, (table_id,))
        res = c.fetchone()
        
        if not res: return False
        order_id = res[0]
        import json
        items = json.loads(res[1])
        
        if 0 <= item_idx < len(items):
            items[item_idx]['status'] = new_status
            c.execute("UPDATE table_orders SET items_json = ? WHERE id = ?", (json.dumps(items), order_id))
            conn.commit()
            return True
        return False
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()


        

# --- ONLINE ORDERING INTEGRATION (SWIGGY/ZOMATO) ---

def create_online_integration_tables(conn):
    c = conn.cursor()
    
    # 1. Online Menu Mapping
    c.execute('''
        CREATE TABLE IF NOT EXISTS online_menu_mapping (
            id TEXT PRIMARY KEY,
            account_id TEXT DEFAULT '1111222233334444',
            platform TEXT, -- SWIGGY, ZOMATO
            external_item_name TEXT,
            internal_product_id TEXT,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (internal_product_id) REFERENCES products(id)
        )
    ''')

    # 2. Online Orders Sync
    c.execute('''
        CREATE TABLE IF NOT EXISTS online_orders_sync (
            id TEXT PRIMARY KEY,
            account_id TEXT DEFAULT '1111222233334444',
            platform TEXT,
            external_order_id TEXT,
            items_json TEXT,
            status TEXT DEFAULT 'PENDING', -- PENDING, ACCEPTED, REJECTED
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')
    conn.commit()

def map_online_item(platform, ext_name, int_prod_id):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        mapping_id = generate_unique_id(16)
        # Check if exists (upsert)
        c.execute(f"DELETE FROM online_menu_mapping WHERE platform = {PLACEHOLDER} AND external_item_name = {PLACEHOLDER} AND account_id = {PLACEHOLDER}", (platform, ext_name, aid))
        c.execute(f"INSERT INTO online_menu_mapping (id, account_id, platform, external_item_name, internal_product_id) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
                  (mapping_id, aid, platform, ext_name, int_prod_id))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()

def get_online_mappings(platform=None):
    conn = get_connection()
    aid = get_current_account_id()
    query = f"SELECT m.*, p.name as internal_name FROM online_menu_mapping m JOIN products p ON m.internal_product_id = p.id WHERE m.account_id = {PLACEHOLDER}"
    params = [aid]
    if platform:
        query += f" AND m.platform = {PLACEHOLDER}"
        params.append(platform)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def sync_online_order(platform, ext_order_id, items_list):
    """
    Ingests an online order. 
    items_list: list of dicts {'name': external_name, 'qty': qty}
    """
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        import json
        order_id = generate_unique_id(16)
        c.execute(f"INSERT INTO online_orders_sync (id, account_id, platform, external_order_id, items_json) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
                  (order_id, aid, platform, ext_order_id, json.dumps(items_list)))
        conn.commit()
        return order_id
    except Exception as e:
        print(e)
        return None
    finally:
        conn.close()

def get_pending_online_orders():
    conn = get_connection()
    aid = get_current_account_id()
    try:
        df = pd.read_sql_query(f"SELECT * FROM online_orders_sync WHERE account_id = {PLACEHOLDER} AND status = 'PENDING' ORDER BY created_at DESC", conn, params=(aid,))
        conn.close()
        return df
    except:
        # Table might be missing if just added
        create_online_integration_tables(conn)
        conn = get_connection() # Re-open
        df = pd.read_sql_query(f"SELECT * FROM online_orders_sync WHERE account_id = {PLACEHOLDER} AND status = 'PENDING' ORDER BY created_at DESC", conn, params=(aid,))
        conn.close()
        return df

def get_accepted_online_orders():
    conn = get_connection()
    aid = get_current_account_id()
    try:
        df = pd.read_sql_query(f"SELECT * FROM online_orders_sync WHERE account_id = {PLACEHOLDER} AND status = 'ACCEPTED' ORDER BY created_at DESC", conn, params=(aid,))
        conn.close()
        return df
    except:
        # Table might be missing
        create_online_integration_tables(conn)
        conn = get_connection() # Re-open
        df = pd.read_sql_query(f"SELECT * FROM online_orders_sync WHERE account_id = {PLACEHOLDER} AND status = 'ACCEPTED' ORDER BY created_at DESC", conn, params=(aid,))
        conn.close()
        return df

def update_online_order_status(sync_id, new_status):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(f"UPDATE online_orders_sync SET status = {PLACEHOLDER} WHERE id = {PLACEHOLDER}", (new_status, sync_id))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()

def update_online_item_kds_status(sync_id, item_idx, new_status):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(f"SELECT items_json FROM online_orders_sync WHERE id = {PLACEHOLDER}", (sync_id,))
        res = c.fetchone()
        if not res: return False
        
        import json
        items = json.loads(res[0])
        if 0 <= item_idx < len(items):
            items[item_idx]['status'] = new_status
            c.execute(f"UPDATE online_orders_sync SET items_json = {PLACEHOLDER} WHERE id = {PLACEHOLDER}", (json.dumps(items), sync_id))
            conn.commit()
            return True
        return False
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()
    matching_dates_df = pd.read_sql_query(query, conn, params=params)
    
    if matching_dates_df.empty:
        conn.close()
        return pd.DataFrame() # No history
        
    dates = matching_dates_df['date'].tolist()
    placeholders = ','.join([PLACEHOLDER]*len(dates))
    
    # 2. Aggregates sales on those dates (Scoped)
    sales_query = f'''
        SELECT ti.product_name, SUM(ti.quantity) as total_qty, AVG(ti.price_at_sale) as avg_price
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        WHERE t.account_id = {PLACEHOLDER} AND date(t.timestamp) IN ({placeholders})
        GROUP BY ti.product_name
        ORDER BY total_qty DESC
        LIMIT 10
    '''
    
    sales_params = [aid] + dates
    sales_df = pd.read_sql_query(sales_query, conn, params=sales_params)
    conn.close()
    return sales_df

# --- SHIFTSMART MODULE LOGIC ---

def create_b2b_deal(store, product, qty, price, phone):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    new_id = generate_unique_id(16)
    try:
        c.execute(f"INSERT INTO b2b_deals (id, account_id, store_name, product_name, quantity, price_per_unit, acc_phone) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})", 
                  (new_id, aid, store, product, qty, price, phone))
        conn.commit()
        return True, "Deal Broadcasted!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def create_campaign(item, desc, votes, price):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    new_id = generate_unique_id(16)
    try:
        c.execute(f"INSERT INTO crowd_campaigns (id, account_id, item_name, description, votes_needed, price_est) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})", 
                  (new_id, aid, item, desc, votes, price))
        conn.commit()
        return True, "Campaign Started!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
def add_staff(name, role, rate):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        c.execute(f"INSERT INTO staff (account_id, name, role, hourly_rate) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})", (aid, name, role, rate))
        conn.commit()
        return True, "Staff added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

@st.cache_data(ttl=300)
def get_all_staff(override_account_id=None):
    conn = get_connection()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    df = pd.read_sql_query(f"SELECT * FROM staff WHERE account_id = {PLACEHOLDER}", conn, params=(aid,))
    conn.close()
    return df

def assign_shift(date_str, slot, staff_id):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        # Check Staff Ownership
        c.execute(f"SELECT id FROM staff WHERE id = {PLACEHOLDER} AND account_id = {PLACEHOLDER}", (staff_id, aid))
        if not c.fetchone():
            return False, "Unauthorized shift assignment."

        # Check if already assigned
        c.execute(f"SELECT id FROM shifts WHERE date = {PLACEHOLDER} AND slot = {PLACEHOLDER} AND staff_id = {PLACEHOLDER}", (date_str, slot, staff_id))
        if c.fetchone():
            return True, "Already assigned."
            
        c.execute(f"INSERT INTO shifts (date, slot, staff_id) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})", (date_str, slot, staff_id))
        conn.commit()
        return True, "Shift assigned."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_shifts(date_str):
    conn = get_connection()
    aid = get_current_account_id()
    # Join with Staff to filter by Account via Staff
    query = f'''
        SELECT sh.*, s.name, s.role 
        FROM shifts sh
        JOIN staff s ON sh.staff_id = s.id
        WHERE sh.date = {PLACEHOLDER} AND s.account_id = {PLACEHOLDER}
    '''
    df = pd.read_sql_query(query, conn, params=(date_str, aid))
    conn.close()
    return df

def update_setting(key, value):
    # Already handled in scoped set_setting above
    return set_setting(key, value)

def predict_labor_demand(weather, event):
    # Uses analyze_context_demand which is now scoped
    sales_df = analyze_context_demand(weather, event)
    if sales_df.empty:
        return 2 # Baseline staffing
        
    total_est_volume = sales_df['total_qty'].sum() / 10 
    
    daily_vol = total_est_volume / 5 
    
    staff_needed = max(2, int(daily_vol / 20) + 1)
    return staff_needed

def record_transaction(items, total_amount, total_profit, customer_id=None, points_redeemed=0, payment_method='CASH', override_account_id=None):
    """
    items: list of dicts {'id': prod_id, 'name': name, 'qty': qty, 'price': price, 'cost': cost}
    customer_id: Optional ID of the customer
    points_redeemed: Amount of loyalty points used (1 point = 1 unit currency)
    """
    conn = get_connection()
    c = conn.cursor()
    
    import secrets
    # Generate 16-char unique hash for display/lookup
    txn_hash = secrets.token_hex(8) 
    
    # Generate TEXT ID for Primary Key
    new_txn_id = generate_unique_id(16, numeric_only=True)

    aid = override_account_id if override_account_id is not None else get_current_account_id()
    print(f"DEBUG: record_transaction for account_id={aid}, method={payment_method}")
    
    try:
        # 1. Create Transaction Record (With Account ID)
        c.execute(f'INSERT INTO transactions (id, account_id, total_amount, total_profit, timestamp, customer_id, transaction_hash, points_redeemed, payment_method) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})', 
                  (new_txn_id, aid, total_amount, total_profit, datetime.now(), customer_id, txn_hash, points_redeemed, payment_method))
        
        transaction_id = new_txn_id # Use our generated ID
        
        # 2. Add Line Items (Batch Optimization)
        # Prepare data for batch insert
        # Need to generate IDs for items too!
        txn_items_data = []
        for item in items:
             item_id = generate_unique_id(16)
             txn_items_data.append((item_id, transaction_id, item['id'], item['name'], item['qty'], item['price'], item['cost']))
        
        c.executemany(f'''
            INSERT INTO transaction_items (id, transaction_id, product_id, product_name, quantity, price_at_sale, cost_at_sale)
            VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})
        ''', txn_items_data)
        
        # 3. Deduct Stock (Batch Optimization - Scoped)
        # Prepare data for batch update: (qty_to_deduct, product_id, account_id)
        stock_updates = [(item['qty'], item['id'], aid) for item in items]
        c.executemany(f'UPDATE products SET stock_quantity = stock_quantity - {PLACEHOLDER} WHERE id = {PLACEHOLDER} AND account_id = {PLACEHOLDER}', stock_updates)

       # 4. FEFO Batch Deduction (FreshFlow Logic - Scoped)
        for item in items:
            qty_needed = item['qty']
            p_id = item['id']
            
            # Fetch batches for this product ordered by expiry (Scoped to Account)
            c.execute(f"SELECT id, quantity FROM product_batches WHERE product_id = {PLACEHOLDER} AND account_id = {PLACEHOLDER} AND quantity > 0 ORDER BY expiry_date ASC", (p_id, aid))
            batches = c.fetchall()
            
            for b_id, b_qty in batches:
                if qty_needed <= 0:
                    break
                
                deduct = min(qty_needed, b_qty)
                c.execute(f"UPDATE product_batches SET quantity = quantity - {PLACEHOLDER} WHERE id = {PLACEHOLDER} AND account_id = {PLACEHOLDER}", (deduct, b_id, aid))
                qty_needed -= deduct
        
        # 5. Update Loyalty Points
        if customer_id:
            # Earn: 1 point per 10 currency
            points_earned = int(total_amount / 10)
            
            # Net Change = Earned - Redeemed
            net_points_change = points_earned - points_redeemed
            
            c.execute(f'UPDATE customers SET loyalty_points = loyalty_points + {PLACEHOLDER} WHERE id = {PLACEHOLDER} AND account_id = {PLACEHOLDER}', (net_points_change, customer_id, aid))
            
        conn.commit()
        return txn_hash 
    except Exception as e:
        print(f"Transaction Error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()
        # Invalidate All Product Caches
        _fetch_all_products_impl.clear()
        _fetch_customers_impl.clear()
        _fetch_pos_inventory_impl.clear()

def create_company_account(company_name, username, password, email):
    """
    Creates a new Account (Tenant) AND an Admin User for that account.
    Returns (Success, Msg)
    """
    conn = get_connection()
    c = conn.cursor()
    new_acc_id = generate_unique_id(16)
    try:
        # Check if COMPANY NAME exists globally
        c.execute(f"SELECT id, status FROM accounts WHERE company_name = {PLACEHOLDER}", (company_name,))
        result = c.fetchone()
        if result:
            acc_id, status = result[0], result[1]
            if status != 'ACTIVE':
                return False, "Account is Suspended. Contact Support."
            return False, "Company Name already exists. Please login."

        # 1. Create Account
        c.execute(f"INSERT INTO accounts (id, company_name, subscription_plan, status) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, 'Starter', 'PENDING')", (new_acc_id, company_name))
        account_id = new_acc_id
        
        # 2. Create User (Admin)
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        new_user_id = generate_unique_id(16)
        
        c.execute(f"INSERT INTO users (id, account_id, username, email, password_hash, role) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})", 
                  (new_user_id, account_id, username, email, pwd_hash, 'admin'))
        
        conn.commit()
        conn.commit()
        return True, "Account created! ⏳ Request sent to Superadmin for approval."
    except sqlite3.IntegrityError:
        return False, "Duplicate user in this account (Should not happen for new account)."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def create_user(username, password, email, role='staff', override_account_id=None):
    """
    Creates a new user for the CURRENT account.
    Enforced uniqueness via (account_id, username) index.
    """
    conn = get_connection()
    c = conn.cursor()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    new_id = generate_unique_id(16)
    try:
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        c.execute(f"INSERT INTO users (id, account_id, username, email, password_hash, role) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})", 
                  (new_id, aid, username, email, pwd_hash, role))
        conn.commit()
        return True, "User created successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists in your account."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def verify_user(username, password, company_name_check):
    """
    Verifies credentials requiring Company Name.
    """
    conn = get_connection()
    c = conn.cursor()
    
    if not company_name_check:
        return False, "Company Name is mandatory."

    try:
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Strict Login: Match Username + Password + Company Name AND Check Status
        # Added permissions to SELECT
        query = f"""
            SELECT u.role, u.account_id, a.company_name, a.status, u.permissions
            FROM users u 
            JOIN accounts a ON u.account_id = a.id
            WHERE u.username = {PLACEHOLDER} AND u.password_hash = {PLACEHOLDER} AND a.company_name = {PLACEHOLDER}
        """
        c.execute(query, (username, pwd_hash, company_name_check))
        result = c.fetchone()
        
        if result:
            role, aid, company, status, perms = result[0], result[1], result[2], result[3], result[4]
            
            # STRICT CHECK
            # STRICT CHECK
            if status == 'PENDING':
                return False, "Account pending approval. Please wait for email confirmation."
            if status != 'ACTIVE':
                return False, "Account is Suspended. Contact Support."
                
            return True, role, aid, company, perms
        
        return False, "Invalid credentials or company name."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def initiate_password_reset(contact):
    """
    Simulates sending a password reset link to Email or Phone.
    """
    conn = get_connection()
    c = conn.cursor()
    try:
        # Search in users (username or email matching contact)
        c.execute(f"SELECT id, email FROM users WHERE username = {PLACEHOLDER} OR email = {PLACEHOLDER}", (contact, contact))
        user = c.fetchone()
        
        if user:
            # Found User
            email = user[1]
            # MOCK SENDING EMAIL
            print(f"[MOCK EMAIL] Sending Password Reset Link to {email} for User {contact}")
            return True, f"Reset link sent to registered email for '{contact}'."
        else:
             # Security Best Practice: Don't reveal if user exists, but for this internal app, let's be helpful?
             # No, stick to generic "If account exists..." but user user asked for "send email to email or phone"
             return True, f"If an account exists for '{contact}', a reset link has been sent."
    except Exception as e:
        return False, str(e)
    finally:
         conn.close()

def get_all_account_users():
    """Returns all users for the current account."""
    conn = get_connection()
    aid = get_current_account_id()
    try:
        df = pd.read_sql_query(f"SELECT username, email, role, created_at, permissions FROM users WHERE account_id = {PLACEHOLDER} ORDER BY created_at DESC", conn, params=(aid,))
        return df
    except:
        return pd.DataFrame()
    finally:
        conn.close()

def delete_user(username):
    """Deletes a user from the current account."""
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        # Prevent deleting yourself (basic check, though UI should handle)
        current_user = st.session_state.get('username')
        if username == current_user:
             return False, "Cannot delete your own account."

        c.execute(f"DELETE FROM users WHERE username = {PLACEHOLDER} AND account_id = {PLACEHOLDER}", (username, aid))
        if c.rowcount > 0:
            conn.commit()
            return True, "User deleted."
        return False, "User not found."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def admin_reset_password(username, new_password):
    """Resets a user's password (Admin Action)."""
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        pwd_hash = hashlib.sha256(new_password.encode()).hexdigest()
        c.execute(f"UPDATE users SET password_hash = {PLACEHOLDER} WHERE username = {PLACEHOLDER} AND account_id = {PLACEHOLDER}", (pwd_hash, username, aid))
        if c.rowcount > 0:
            conn.commit()
            return True, "Password reset successfully."
        return False, "User not found."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_user_permissions(username, permissions_list):
    """Updates the allowed modules for a user."""
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        perm_str = ",".join(permissions_list) if permissions_list else None
        
        c.execute(f"UPDATE users SET permissions = {PLACEHOLDER} WHERE username = {PLACEHOLDER} AND account_id = {PLACEHOLDER}", (perm_str, username, aid))
        if c.rowcount > 0:
            conn.commit()
            return True, "Permissions updated."
        return False, "User not found."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def create_purchase_order(supplier_id, expected_date, notes="", override_account_id=None):
    conn = get_connection()
    c = conn.cursor()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    new_id = generate_unique_id(16)
    try:
        now_sql = "CURRENT_DATE" if config.DB_TYPE == "POSTGRES" else "date('now')"
        c.execute(f"INSERT INTO purchase_orders (id, account_id, supplier_id, order_date, expected_date, notes) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {now_sql}, {PLACEHOLDER}, {PLACEHOLDER})",
                  (new_id, aid, supplier_id, expected_date, notes))
        conn.commit()
        return True, "PO Created."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def add_staff(name, role, rate, override_account_id=None):
    conn = get_connection()
    c = conn.cursor()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    new_id = generate_unique_id(16)
    try:
        c.execute(f"INSERT INTO staff (id, account_id, name, role, hourly_rate) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})", (new_id, aid, name, role, rate))
        conn.commit()
        return True, "Staff added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def assign_shift(date_str, slot, staff_id, override_account_id=None):
    conn = get_connection()
    c = conn.cursor()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    new_id = generate_unique_id(16)
    try:
        # Verify staff belongs to account
        c.execute(f"SELECT id FROM staff WHERE id = {PLACEHOLDER} AND account_id = {PLACEHOLDER}", (staff_id, aid))
        if not c.fetchone():
            return False, "Staff member not found or unauthorized."

        # Check if already assigned
        c.execute(f"SELECT id FROM shifts WHERE date = {PLACEHOLDER} AND slot = {PLACEHOLDER} AND staff_id = {PLACEHOLDER}", (date_str, slot, staff_id))
        if c.fetchone():
            return True, "Already assigned."
            
        c.execute(f"INSERT INTO shifts (id, date, slot, staff_id) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})", (new_id, date_str, slot, staff_id))
        conn.commit()
        return True, "Shift assigned."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_shifts(date_str):
    conn = get_connection()
    aid = get_current_account_id()
    # Join with Staff to filter by Account via Staff
    query = f'''
        SELECT sh.*, s.name, s.role 
        FROM shifts sh
        JOIN staff s ON sh.staff_id = s.id
        WHERE sh.date = {PLACEHOLDER} AND s.account_id = {PLACEHOLDER}
    '''
    df = pd.read_sql_query(query, conn, params=(date_str, aid))
    conn.close()
    return df

def update_setting(key, value):
    # Already handled in scoped set_setting above
    return set_setting(key, value)

def predict_labor_demand(weather, event):
    # Uses analyze_context_demand which is now scoped
    sales_df = analyze_context_demand(weather, event)
    if sales_df.empty:
        return 2 # Baseline staffing
        
    total_est_volume = sales_df['total_qty'].sum() / 10 
    
    daily_vol = total_est_volume / 5 
    
    staff_needed = max(2, int(daily_vol / 20) + 1)
    return staff_needed

# End of database.py

# --- SUPER ADMIN MODULE LOGIC ---

def fetch_all_accounts():
    """Returns all accounts (System Level)."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM accounts ORDER BY created_at DESC", conn)
    conn.close()
    return df

def create_tenant(company_name, plan="Starter"):
    """Creates a new tenant account."""
    conn = get_connection()
    c = conn.cursor()
    new_id = generate_unique_id(16, numeric_only=True)
    try:
        c.execute(f"INSERT INTO accounts (id, company_name, subscription_plan, status) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, 'ACTIVE')", 
                  (new_id, company_name, plan))
        
        # Initialize Default Settings for this Account
        c.execute(f"INSERT INTO settings (account_id, key, value) VALUES ({PLACEHOLDER}, 'store_name', {PLACEHOLDER})", (new_id, company_name))
        c.execute(f"INSERT INTO settings (account_id, key, value) VALUES ({PLACEHOLDER}, 'subscription_plan', {PLACEHOLDER})", (new_id, plan))
        
        conn.commit()
        return True, f"Tenant Created. ID: {new_id}"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_tenant_status(account_id, status):
    """Updates tenant status (System Level)."""
    # GUARD: Protect System Account
    if account_id == 'SYS_001':
        return False, "Cannot suspend the System Account."
        
    conn = get_connection()
    c = conn.cursor()
    try:
        # Also check company name just in case ID varies
        msg = "Status Updated."
        if status == 'SUSPENDED':
             c.execute(f"SELECT company_name FROM accounts WHERE id={PLACEHOLDER}", (account_id,))
             res = c.fetchone()
             if res and (res[0] == 'VyaparMind System' or res[0] == 'admin'):
                 return False, "Cannot suspend Critical System Account."
                 
        c.execute(f"UPDATE accounts SET status = {PLACEHOLDER} WHERE id = {PLACEHOLDER}", (status, account_id))
        conn.commit()
        return True, msg
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_tenant_plan(account_id, new_plan):
    """Updates tenant subscription plan (System Level)."""
    conn = get_connection()
    c = conn.cursor()
    try:
        # Update Account Table
        c.execute(f"UPDATE accounts SET subscription_plan = {PLACEHOLDER} WHERE id = {PLACEHOLDER}", (new_plan, account_id))
        # Update Settings Table
        if config.DB_TYPE == "POSTGRES":
            c.execute(f"INSERT INTO settings (account_id, key, value) VALUES ({PLACEHOLDER}, 'subscription_plan', {PLACEHOLDER}) ON CONFLICT (account_id, key) DO UPDATE SET value = EXCLUDED.value", (account_id, new_plan))
        else:
            c.execute(f"INSERT OR REPLACE INTO settings (account_id, key, value) VALUES ({PLACEHOLDER}, 'subscription_plan', {PLACEHOLDER})", (account_id, new_plan))
        conn.commit()
        return True, "Plan Updated."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def fetch_floor_status():
    """
    Returns enriched table data for KDS-style display.
    List of dicts: {id, label, capacity, status, start_time, order_id, items_count, items_summary}
    """
    conn = get_connection()
    # Left join to get all tables even if empty
    # We also need to calculate elapsed time in python or sql. Python is easier for formatting.
    q = f"""
        SELECT 
            t.id, t.label, t.capacity, t.status, 
            o.start_time, o.items_json
        FROM restaurant_tables t
        LEFT JOIN table_orders o ON t.current_order_id = o.id
        WHERE t.account_id = {PLACEHOLDER}
    """
    aid = get_current_account_id()
    
    data = []
    try:
        df = pd.read_sql_query(q, conn, params=(aid,))
        
        # Enriched processing
        for _, row in df.iterrows():
            item = {
                "id": row['id'],
                "label": row['label'],
                "capacity": row['capacity'],
                "status": row['status'],
                "start_time": row['start_time'],
                "items": []
            }
            
            if row['items_json']:
                try:
                    import json
                    items_list = json.loads(row['items_json'])
                    item['items'] = items_list
                except:
                    item['items'] = []
            
            data.append(item)
            
        return data
    except Exception as e:
        print(f"Error fetching floor: {e}")
        return []
    finally:
        conn.close()

def remove_item_from_table(table_id, item_index):
    """Removes an item from a table's active order by index."""
    conn = get_connection()
    c = conn.cursor()
    try:
        # Get Current Items
        c.execute(f"""
            SELECT o.items_json, o.id 
            FROM restaurant_tables t
            JOIN table_orders o ON t.current_order_id = o.id
            WHERE t.id = {PLACEHOLDER}
        """, (table_id,))
        row = c.fetchone()
        
        if row:
            items_json, order_id = row
            try:
                import json
                items = json.loads(items_json) if items_json else []
                
                # Check bounds
                if 0 <= item_index < len(items):
                    popped = items.pop(item_index)
                    
                    # Update DB
                    new_json = json.dumps(items)
                    c.execute(f"UPDATE table_orders SET items_json = {PLACEHOLDER} WHERE id = {PLACEHOLDER}", (new_json, order_id))
                    conn.commit()
                    return True, f"Removed {popped.get('name', 'Item')}"
                else:
                    return False, "Item not found."
            except Exception as e:
                return False, f"JSON Error: {e}"
        return False, "Order not active."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def mark_items_kot_printed(table_id):
    """Marks all pending items in a table's order as 'sent' (Printed KOT)."""
    conn = get_connection()
    c = conn.cursor()
    try:
        # Get Current Items
        c.execute(f"""
            SELECT o.items_json, o.id 
            FROM restaurant_tables t
            JOIN table_orders o ON t.current_order_id = o.id
            WHERE t.id = {PLACEHOLDER}
        """, (table_id,))
        row = c.fetchone()
        
        if row:
            items_json, order_id = row
            try:
                import json
                items = json.loads(items_json) if items_json else []
                
                updated = False
                for i in items:
                    if i.get('status') != 'sent':
                         i['status'] = 'sent'
                         updated = True
                
                if updated:
                    new_json = json.dumps(items)
                    c.execute(f"UPDATE table_orders SET items_json = {PLACEHOLDER} WHERE id = {PLACEHOLDER}", (new_json, order_id))
                    conn.commit()
                    return True, "KOT Marked Printed", order_id
                return True, "No new items", order_id
            except Exception as e:
                return False, f"JSON Error: {e}", None
        return False, "Order not active", None
    except Exception as e:
        return False, str(e), None
    finally:
        conn.close()

def get_plan_features(plan_name):
    """Returns a list of feature strings for a given plan."""
    conn = get_connection()
    try:
        # Check standard hardcoded tiers first (Optional, but DB is source of truth for custom)
        # We'll just check DB.
        c = conn.cursor()
        c.execute(f"SELECT modules FROM subscription_plans WHERE name = {PLACEHOLDER}", (plan_name,))
        row = c.fetchone()
        if row and row[0]:
            return [f.strip() for f in row[0].split(',') if f.strip()]
        return []
    except:
        return []
    finally:
        conn.close()

def get_system_overview():
    """Aggregate stats for Super Admin."""
    conn = get_connection()
    
    # Total Tenants
    total_tenants = pd.read_sql_query("SELECT COUNT(*) as count FROM accounts", conn).iloc[0]['count']
    
    # Active Tenants
    active_tenants = pd.read_sql_query("SELECT COUNT(*) as count FROM accounts WHERE status='ACTIVE'", conn).iloc[0]['count']
    
    # Total Transactions (Global) - indicative of activity
    total_txns = pd.read_sql_query("SELECT COUNT(*) as count FROM transactions", conn).iloc[0]['count']
    
    conn.close()
    return {
        "Total Tenants": total_tenants,
        "Active Tenants": active_tenants,
        "Total Transactions": total_txns
    }

# --- SUB PLANS MANAGEMENT ---

def get_all_plans():
    """Returns all subscription plans as a dataframe."""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM subscription_plans ORDER BY price ASC", conn)
        return df
    except:
        return pd.DataFrame() # Fallback
    finally:
        conn.close()

def add_plan(name, price, modules=""):
    """Adds a new subscription plan."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(f"INSERT INTO subscription_plans (name, price, modules) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})", (name, price, modules))
        conn.commit()
        return True, "Plan Added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_plan(old_name, new_name, new_price, new_modules):
    """Updates an existing subscription plan."""
    conn = get_connection()
    c = conn.cursor()
    try:
        # Check if new name exists and is not the old name (collision check)
        if old_name != new_name:
            c.execute(f"SELECT id FROM subscription_plans WHERE name = {PLACEHOLDER}", (new_name,))
            if c.fetchone():
                return False, "Plan name already exists."

        c.execute(f"""
            UPDATE subscription_plans 
            SET name = {PLACEHOLDER}, price = {PLACEHOLDER}, modules = {PLACEHOLDER} 
            WHERE name = {PLACEHOLDER}
        """, (new_name, new_price, new_modules, old_name))
        
        conn.commit()
        return True, "Plan Updated."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_plan(plan_name):
    """Deletes a plan by name."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(f"DELETE FROM subscription_plans WHERE name = {PLACEHOLDER}", (plan_name,))
        conn.commit()
        return True, "Plan Deleted."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# --- CHURN GUARD OPTIMIZATION ---

def get_churn_metrics(days_threshold=30):
    """
    Identifies at-risk customers who haven't purchased in > days_threshold.
    Optimized to do heavy lifting in SQL.
    """
    conn = get_connection()
    aid = get_current_account_id()
    
    # Logic: 
    # 1. Get max timestamp per customer (Last Seen)
    # 2. Filter where Last Seen < (Now - Threshold)
    if config.DB_TYPE == "POSTGRES":
        days_diff_sql = "EXTRACT(DAY FROM (CURRENT_TIMESTAMP - MAX(t.timestamp)))"
    else:
        days_diff_sql = "(julianday('now') - julianday(MAX(t.timestamp)))"

    query = f"""
        SELECT 
            c.id, c.name, c.phone, c.email, 
            MAX(t.timestamp) as last_seen, 
            SUM(t.total_amount) as total_spent,
            {days_diff_sql} as days_since
        FROM transactions t
        JOIN customers c ON t.customer_id = c.id
        WHERE t.account_id = {PLACEHOLDER}
        GROUP BY c.id
        HAVING {days_diff_sql} > {PLACEHOLDER}
        ORDER BY total_spent DESC
    """
    
    try:
        df = pd.read_sql_query(query, conn, params=(aid, days_threshold))
        return df
    except Exception as e:
        print(f"Churn Metric Error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# --- GEO ANALYSIS ---
def get_geo_revenue():
    """
    Returns total revenue grouped by City.
    Used for GeoViz catchment analysis.
    """
    conn = get_connection()
    aid = get_current_account_id()
    
    query = f"""
        SELECT c.city, SUM(t.total_amount) as revenue
        FROM transactions t
        JOIN customers c ON t.customer_id = c.id
        WHERE t.account_id = {PLACEHOLDER} AND c.city IS NOT NULL
        GROUP BY c.city
        ORDER BY revenue DESC
    """
    try:
        df = pd.read_sql_query(query, conn, params=(aid,))
        return df
    except Exception as e:
        raise e
    finally:
        conn.close()

# --- STOCKSWAP NETWORK ---

def get_b2b_deals():
    """
    Fetches active B2B deals from the Marketplace Feed.
    In a real mesh, this would fetch from ALL accounts (with location filter).
    For now, we fetch all deals EXCEPT the current account's own deals (to buy from others).
    """
    conn = get_connection()
    aid = get_current_account_id()
    
    # Logic: Show me deals from OTHER stores
    query = f"""
        SELECT * FROM b2b_deals 
        WHERE account_id != {PLACEHOLDER} 
        ORDER BY created_at DESC
    """
    try:
        df = pd.read_sql_query(query, conn, params=(aid,))
        return df
    except Exception as e:
        print(f"StockSwap Fetch Error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def create_b2b_deal(store_name, product_name, quantity, price_per_unit, phone):
    """Broadcasts a new deal to the network."""
    conn = get_connection()
    aid = get_current_account_id()
    new_id = generate_unique_id(16)
    
    try:
        c = conn.cursor()
        c.execute(f"""
            INSERT INTO b2b_deals (id, account_id, store_name, product_name, quantity, price_per_unit, acc_phone)
            VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})
        """, (new_id, aid, store_name, product_name, quantity, price_per_unit, phone))
        conn.commit()
        return True, "Deal Broadcasted."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# --- CROWDSTOCK (KICKSTARTER) ---

def get_campaigns():
    """Fetches all active crowd campaigns for the store."""
    conn = get_connection()
    aid = get_current_account_id()
    try:
        df = pd.read_sql_query(f"SELECT * FROM crowd_campaigns WHERE account_id = {PLACEHOLDER} ORDER BY created_at DESC", conn, params=(aid,))
        return df
    except Exception as e:
        return pd.DataFrame()
    finally:
        conn.close()

def create_campaign(item_name, description, votes_needed, price_est):
    """Creates a new crowd testing campaign."""
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    new_id = generate_unique_id(16)
    
    try:
        c.execute(f"""
            INSERT INTO crowd_campaigns (id, account_id, item_name, description, votes_needed, price_est)
            VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})
        """, (new_id, aid, item_name, description, votes_needed, price_est))
        conn.commit()
        return True, "Campaign Launched."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def vote_campaign(campaign_id):
    """Adds a vote to a campaign."""
    conn = get_connection()
    c = conn.cursor()
    try:
        # Check current status first
        c.execute(f"SELECT votes_current, votes_needed, item_name FROM crowd_campaigns WHERE id = {PLACEHOLDER}", (campaign_id,))
        row = c.fetchone()
        if not row:
            return False, "Campaign not found."
            
        current, needed, name = row
        new_votes = current + 1
        
        msg = "Vote Recorded!"
        if new_votes >= needed:
            msg = f"🎉 '{name}' is FULLY FUNDED! Time to order stock."
            c.execute(f"UPDATE crowd_campaigns SET status = 'FUNDED' WHERE id = {PLACEHOLDER}", (campaign_id,))
            
        c.execute(f"UPDATE crowd_campaigns SET votes_current = {PLACEHOLDER} WHERE id = {PLACEHOLDER}", (new_votes, campaign_id))
        conn.commit()
        return True, msg
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# --- APPROVAL WORKFLOW ---
def get_pending_accounts():
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM accounts WHERE status='PENDING' ORDER BY created_at DESC", conn)
        return df
    except:
        return pd.DataFrame()
    finally:
        conn.close()

def approve_account(account_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        # 1. Update Status
        c.execute(f"UPDATE accounts SET status='ACTIVE' WHERE id={PLACEHOLDER}", (account_id,))
        if c.rowcount == 0:
            return False, "Account not found"
            
        # 2. Get Account & Admin Details for Email
        c.execute(f"SELECT company_name, subscription_plan, created_at FROM accounts WHERE id={PLACEHOLDER}", (account_id,))
        acc_row = c.fetchone()
        
        c.execute(f"SELECT email, username FROM users WHERE account_id={PLACEHOLDER} AND role='admin' LIMIT 1", (account_id,))
        user_row = c.fetchone()
        
        conn.commit()
        
        if acc_row and user_row:
            details = {
                "company": acc_row[0],
                "plan": acc_row[1],
                "date": str(acc_row[2]),
                "email": user_row[0],
                "username": user_row[1]
            }
            # Send Email
            send_approval_email(details)
            return True, "Account Approved & Email Sent!"
            
        return True, "Approved, but email details missing."
        
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def send_approval_email(details):
    """
    Mock Email Sender.
    """
    print("="*60)
    print(f"📧 SENDING APPROVAL EMAIL TO: {details['email']}")
    print(f"Subject: Welcome to VyaparMind - {details['company']} Approved!")
    print("-" * 60)
    print(f"Dear {details['username']},")
    print(f"Your account for '{details['company']}' has been approved.")
    print(f"Plan: {details['plan']}")
    print(f"Start Date: {details['date']}")
    # Mock End Date logic
    from datetime import datetime, timedelta
    end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    print(f"End Date: {end_date} (Renews Yearly)")
    
    # Get Modules
    mods = get_plan_features(details['plan'])
    mod_str = ", ".join(mods) if mods else "Standard Suite"
    print(f"Subscribed Modules: {mod_str}")
    print("\nYou can now login at: https://app.vyaparmind.com")
    print("="*60)
