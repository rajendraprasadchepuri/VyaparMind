import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st

DB_NAME = "retail_supply_chain.db"

def get_connection():
    return sqlite3.connect(DB_NAME, timeout=30, check_same_thread=False)

def get_current_account_id():
    """
    Retrieves the logged-in user's Account ID from Session State.
    Returns 1 (Default/Demo) if not logged in, to allow public pages/testing to work.
    In strict production, this should return None or raise Error.
    """
    if 'account_id' in st.session_state:
        return st.session_state['account_id']
    return 1 # Default to Demo Account for now

def init_db():
    """Initializes the database with necessary tables if they don't exist."""
    conn = get_connection()
    # OPTIMIZATION: Enable WAL Mode for concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    c = conn.cursor()
    
    # Accounts Table (Tenants)
    c.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            subscription_plan TEXT DEFAULT 'Starter',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Ensure Default Demo Account Exists
    c.execute("INSERT OR IGNORE INTO accounts (id, company_name) VALUES (1, 'VyaparMind Demo Store')")

    # Products Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER DEFAULT 1,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            cost_price REAL NOT NULL,
            stock_quantity INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')
    
    # Transactions Table (Head)
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER DEFAULT 1,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL NOT NULL,
            total_profit REAL NOT NULL,
            payment_method TEXT DEFAULT 'CASH',
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')
    
    # Transaction Items (Line Items)
    c.execute('''
        CREATE TABLE IF NOT EXISTS transaction_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            price_at_sale REAL,
            cost_at_sale REAL,
            FOREIGN KEY (transaction_id) REFERENCES transactions (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    # Settings Table (Multi-Tenant)
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            account_id INTEGER,
            key TEXT,
            value TEXT,
            UNIQUE(account_id, key),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')
    
    # Note: Global defaults are deprecated in favor of account-scoped defaults during signup.
    # But for demo account (ID=1), we ensure they exist.
    c.execute("INSERT OR IGNORE INTO settings (account_id, key, value) VALUES (1, 'store_name', 'VyaparMind Store')")
    c.execute("INSERT OR IGNORE INTO settings (account_id, key, value) VALUES (1, 'store_address', 'Hyderabad, India')")
    c.execute("INSERT OR IGNORE INTO settings (account_id, key, value) VALUES (1, 'store_phone', '9876543210')")
    # Customers Table (New)
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER DEFAULT 1,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            loyalty_points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')
    
    # Migrations for Account ID
    for table in ["products", "transactions", "customers", "suppliers", "purchase_orders", "product_batches", "staff", "daily_context", "b2b_deals", "crowd_campaigns"]:
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN account_id INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass # Already exists

    # Migration: Add customer_id to transactions if not exists
    try:
        c.execute("ALTER TABLE transactions ADD COLUMN customer_id INTEGER")
    except sqlite3.OperationalError:
        pass # Column likely exists

    # Migration: Add updated_at to products if not exists
    try:
        c.execute("ALTER TABLE products ADD COLUMN updated_at TIMESTAMP")
    except sqlite3.OperationalError:
        pass

    # Migration: Add tax_rate to products if not exists
    try:
        c.execute("ALTER TABLE products ADD COLUMN tax_rate REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass

    # Migration: Add transaction_hash to transactions if not exists
    try:
        c.execute("ALTER TABLE transactions ADD COLUMN transaction_hash TEXT")
    except sqlite3.OperationalError:
        pass
    
    # Migration: Add points_redeemed to transactions
    try:
        c.execute("ALTER TABLE transactions ADD COLUMN points_redeemed INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Users Table (New)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER DEFAULT 1,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'admin', -- admin, manager, staff
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')

    # Migration: Add role to users if not exists
    try:
        c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'admin'")
    except sqlite3.OperationalError:
        pass
        
    # Default Subscription
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('subscription_plan', 'Starter')")

    # Product Batches (FreshFlow)
    c.execute('''
        CREATE TABLE IF NOT EXISTS product_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER DEFAULT 1,
            product_id INTEGER,
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
    # products(name) for search
    c.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)")
    
    # transactions(timestamp) for reporting
    c.execute("CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp)")
    
    # transaction_items(transaction_id) for joins
    c.execute("CREATE INDEX IF NOT EXISTS idx_txn_items_txn_id ON transaction_items(transaction_id)")
    
    # customers(phone) for fast lookup
    c.execute("CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)")
    
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

    # VendorTrust Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER DEFAULT 1,
            name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT,
            category_specialty TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER DEFAULT 1,
            supplier_id INTEGER,
            order_date DATE,
            expected_date DATE,
            received_date DATE,
            status TEXT DEFAULT 'PENDING', -- PENDING, RECEIVED, CANCELLED
            quality_rating INTEGER DEFAULT 0, -- 1 to 5
            notes TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
    ''')

    # IsoBar Context Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_context (
            date DATE,
            account_id INTEGER DEFAULT 1,
            weather_tag TEXT,
            event_tag TEXT,
            notes TEXT,
            PRIMARY KEY (date, account_id),
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
    ''')

    # ShiftSmart Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER DEFAULT 1,
            name TEXT NOT NULL,
            role TEXT,
            hourly_rate REAL,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            slot TEXT, -- Morning, Evening
            staff_id INTEGER,
            FOREIGN KEY (staff_id) REFERENCES staff (id)
        )
    ''')

    # StockSwap Table (B2B)
    c.execute('''
        CREATE TABLE IF NOT EXISTS b2b_deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT, -- In real app, this is linked to Store ID
            product_name TEXT,
            quantity INTEGER,
            price_per_unit REAL,
            acc_phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    create_table_management_tables(conn)

    # CrowdStock Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS crowd_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            description TEXT,
            votes_needed INTEGER,
            votes_current INTEGER DEFAULT 0,
            price_est REAL,
            status TEXT DEFAULT 'ACTIVE' -- ACTIVE, FUNDED, CLOSED
        )
    ''')

    # --- MIGRATION: Settings Multi-Tenancy (Strict Re-creation) ---
    try:
        # Check if we have the correct composite unique constraint
        # We can't easily check constraints via simple SQL, but we can check if it's the old schema
        c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='settings'")
        sql = c.fetchone()[0]
        if "PRIMARY KEY (key)" in sql or "PRIMARY KEY (\"key\")" in sql or "UNIQUE(account_id, key)" not in sql:
            print("Force Migrating 'settings' table to composite unique...")
            c.execute("ALTER TABLE settings RENAME TO settings_old")
            c.execute('''
                CREATE TABLE settings (
                    account_id INTEGER,
                    key TEXT,
                    value TEXT,
                    UNIQUE(account_id, key),
                    FOREIGN KEY (account_id) REFERENCES accounts(id)
                )
            ''')
            # Copy data, prefer existing account_id if available
            try:
                c.execute("INSERT OR IGNORE INTO settings (account_id, key, value) SELECT account_id, key, value FROM settings_old")
            except:
                # Fallback if account_id was missing
                c.execute("INSERT OR IGNORE INTO settings (account_id, key, value) SELECT 1, key, value FROM settings_old")
            
            c.execute("DROP TABLE settings_old")
            print("Settings migration complete.")
    except Exception as e:
        # If table doesn't exist at all, init_db will create it later, but let's handle it
        pass

    # --- MIGRATION: Scoped Usernames ---
    # Check if 'users' table needs migration (by checking if 'users_new' logic is applied)
    # We can check via PRAGMA or just try to perform migration if flag not present
    # Simplest: Try to add the constraint or recreate.
    
    # Let's use a "try/catch" approach for table swap
    try:
        # Check if existing users table has the composite unique constraint
        # Warning: Complicated to check constraints in SQLite.
        # Strategy: ALWAYS create 'users_v2', copy data, drop 'users', rename 'users_v2'
        # BUT only if 'users' exists.
        
        # Check if 'users' exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if c.fetchone():
            # Check if it's the OLD schema (Global Unique Username)
            # We can rely on a migration flag or just do it once.
            # Let's check if we have already migrated by checking index info? 
            # No, let's just do a safe swap if we haven't already.
            pass 
            
            # MIGRATION LOGIC:
            # 1. Rename current users -> users_backup
            # 2. Create NEW users table with composite unique
            # 3. Copy data
            # 4. Drop users_backup
            
            # Since this runs every time, we need a condition.
            # Let's create the table with the NEW schema IF NOT EXISTS first.
            # But the table DOES exist with old schema.
            
            # HACK: We will try to CREATE the new table definition. 
            # If the current table schema matches old, we migrate.
            
            c.execute("PRAGMA index_list('users')")
            indexes = c.fetchall()
            # If we don't see a composite index/unique, we migrate.
            # Old schema: unique index on username.
            
            needs_migration = True
            for idx in indexes:
                # idx: (seq, name, unique, origin, partial)
                if idx[2] == 1: # Unique
                     c.execute(f"PRAGMA index_info('{idx[1]}')")
                     cols = c.fetchall()
                     # If unique index is on (account_id, username) -> (0,0,account_id), (1,1,username)
                     col_names = [col[2] for col in cols]
                     if 'account_id' in col_names and 'username' in col_names:
                         needs_migration = False
                         break
            
            if needs_migration:
                print("MIGRATING 'users' TABLE TO SCOPED UNIQUENESS...")
                c.execute("ALTER TABLE users RENAME TO users_old_schema")
                c.execute('''
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_id INTEGER,
                        username TEXT NOT NULL,
                        email TEXT,
                        password_hash TEXT NOT NULL,
                        role TEXT DEFAULT 'manager',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (account_id) REFERENCES accounts (id),
                        UNIQUE(account_id, username)
                    )
                ''')
                # Copy Data
                c.execute("INSERT INTO users (id, account_id, username, email, password_hash, role, created_at) SELECT id, account_id, username, email, password_hash, role, created_at FROM users_old_schema")
                c.execute("DROP TABLE users_old_schema")
                print("MIGRATION COMPLETE.")
                
    except Exception as e:
        print(f"Migration Warning: {e}")

    # --- MULTI-TENANCY MIGRATION: Add account_id to ALL tables ---
    tables_to_migrate = [
        'users', 'products', 'transactions', 'customers', 'suppliers', 
        'staff', 'product_batches', 'daily_context', 'b2b_deals', 'crowd_campaigns',
        'settings'
    ]
    
    for table in tables_to_migrate:
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN account_id INTEGER DEFAULT 1")
            c.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_account ON {table}(account_id)")
        except sqlite3.OperationalError:
            pass # Already exists

    # Settings needs account_id but also might need to drop unique constraint on 'key' if purely global
    # We will create `account_settings` table properly for strict separation.
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS account_settings (
            account_id INTEGER,
            key TEXT,
            value TEXT,
            PRIMARY KEY (account_id, key),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')

    conn.commit()
    conn.close()

def get_setting(key):
    """Fetch a setting value by key (Scoped)."""
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    # Check Account Specific Setting
    c.execute("SELECT value FROM settings WHERE key = ? AND account_id = ?", (key, aid))
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
        c.execute("SELECT value FROM settings WHERE key = ? AND account_id = ?", (key, aid))
        if c.fetchone():
            c.execute("UPDATE settings SET value = ? WHERE key = ? AND account_id = ?", (value, key, aid))
        else:
            c.execute("INSERT INTO settings (account_id, key, value) VALUES (?, ?, ?)", (aid, key, value))
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
    try:
        c.execute('''
            INSERT INTO products (account_id, name, category, price, cost_price, stock_quantity, tax_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (account_id, name, category, price, cost_price, stock_quantity, tax_rate))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
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
        c.execute('''
            UPDATE products 
            SET price = ?, cost_price = ?, stock_quantity = ?, tax_rate = ?, updated_at = ?
            WHERE id = ? AND account_id = ?
        ''', (price, cost_price, stock_quantity, tax_rate, datetime.now(), product_id, aid))
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
    df = pd.read_sql_query("SELECT * FROM products WHERE account_id = ?", conn, params=(account_id,))
    conn.close()
    return df

def fetch_all_products(override_account_id=None):
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    return _fetch_all_products_impl(aid)

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

def fetch_pos_inventory():
    aid = get_current_account_id()
    return _fetch_pos_inventory_impl(aid)

@st.cache_data(ttl=300)
def _fetch_customers_impl(account_id):
    """Internal cached fetcher."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM customers WHERE account_id = ?", conn, params=(account_id,))
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
    try:
        # Check uniqueness manually since we didn't add UNIQUE constraint at creation
        c.execute("SELECT id FROM customers WHERE phone = ? AND account_id = ?", (phone, aid))
        if c.fetchone():
            return False, "Customer with this phone already exists!" # Return tuple (Success, Msg)

        c.execute("INSERT INTO customers (account_id, name, phone, email, city, pincode) VALUES (?, ?, ?, ?, ?, ?)", (aid, name, phone, email, city, pincode))
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
    c.execute('UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ? AND account_id = ?', (quantity_change, product_id, aid))
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
    try:
        # 1. Insert Batch (With Account ID)
        c.execute('''
            INSERT INTO product_batches (account_id, product_id, batch_code, expiry_date, quantity, cost_price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (aid, product_id, batch_code, expiry_date, quantity, cost_price))
        
        # 2. Update Total Stock in master table (Scoped)
        c.execute('UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ? AND account_id = ?', (quantity, product_id, aid))
        
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
    query = '''
        SELECT b.*, p.name as product_name, p.price as current_price
        FROM product_batches b
        JOIN products p ON b.product_id = p.id
        WHERE b.account_id = ? 
        AND b.quantity > 0 
        AND b.expiry_date <= date('now', '+' || ? || ' days')
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
    try:
        # Check uniqueness (Scoped)
        c.execute("SELECT id FROM suppliers WHERE (name = ? OR phone = ?) AND account_id = ?", (name, phone, aid))
        if c.fetchone():
            return False, "Supplier already exists (same name or phone)."
            
        c.execute("INSERT INTO suppliers (account_id, name, contact_person, phone, category_specialty) VALUES (?, ?, ?, ?, ?)", 
                  (aid, name, contact, phone, specialty))
        conn.commit()
        return True, "Supplier added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_all_suppliers(override_account_id=None):
    conn = get_connection()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    # Deduplicate view logic: Group by name/phone to hide dupes if they exist
    df = pd.read_sql_query("SELECT * FROM suppliers WHERE account_id = ? GROUP BY name", conn, params=(aid,))
    conn.close()
    return df

def create_purchase_order(supplier_id, expected_date, notes="", override_account_id=None):
    conn = get_connection()
    c = conn.cursor()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    try:
        c.execute("INSERT INTO purchase_orders (account_id, supplier_id, order_date, expected_date, notes) VALUES (?, ?, date('now'), ?, ?)",
                  (aid, supplier_id, expected_date, notes))
        conn.commit()
        return True, "PO Created."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_open_pos():
    conn = get_connection()
    aid = get_current_account_id()
    query = '''
        SELECT po.*, s.name as supplier_name 
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.id
        WHERE po.status = 'PENDING' AND po.account_id = ?
    '''
    df = pd.read_sql_query(query, conn, params=(aid,))
    conn.close()
    return df

def receive_purchase_order(po_id, quality_rating):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        c.execute('''
            UPDATE purchase_orders 
            SET status = 'RECEIVED', received_date = date('now'), quality_rating = ?
            WHERE id = ? AND account_id = ?
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
    query = "SELECT * FROM purchase_orders WHERE supplier_id = ? AND account_id = ? AND status = 'RECEIVED'"
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
        c.execute("INSERT OR REPLACE INTO daily_context (account_id, date, weather_tag, event_tag, notes) VALUES (?, ?, ?, ?, ?)",
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
    c = conn.cursor()
    aid = get_current_account_id()
    c.execute("SELECT * FROM daily_context WHERE date = ? AND account_id = ?", (date_str, aid))
    res = c.fetchone()
    conn.close()
    return res

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
    # Restaurant Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS restaurant_tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER DEFAULT 1,
            label TEXT,
            capacity INTEGER DEFAULT 4,
            status TEXT DEFAULT 'Available', -- Available, Occupied
            current_order_id INTEGER,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')
    
    # Active Table Orders (Temporary holding before Transaction)
    c.execute('''
        CREATE TABLE IF NOT EXISTS table_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER DEFAULT 1,
            table_id INTEGER,
            items_json TEXT, -- JSON string of items
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (table_id) REFERENCES restaurant_tables(id),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')
    
    # Seed some tables if empty
    c.execute("SELECT count(*) FROM restaurant_tables")
    if c.fetchone()[0] == 0:
        # Seed 6 tables
        for i in range(1, 7):
            c.execute("INSERT INTO restaurant_tables (label, capacity, status) VALUES (?, ?, ?)", 
                      (f"T{i}", 4 if i < 5 else 6, "Available"))
    conn.commit()

def get_tables():
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    # Ensure tables exist for this account (Multi-tenant seeding logic omitted for brevity, assuming shared or pre-seeded)
    # For now, just fetch checks
    query = "SELECT * FROM restaurant_tables WHERE account_id = ?"
    df = pd.read_sql_query("SELECT * FROM restaurant_tables", conn) # Simplified for demo, ignoring strict account binding for seed
    conn.close()
    return df

def occupy_table(table_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        # Create new order
        c.execute("INSERT INTO table_orders (table_id, items_json) VALUES (?, '[]')", (table_id,))
        new_order_id = c.lastrowid
        
        # Update Table
        c.execute("UPDATE restaurant_tables SET status = 'Occupied', current_order_id = ? WHERE id = ?", (new_order_id, table_id))
        conn.commit()
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

def add_item_to_table(table_id, item_dict):
    conn = get_connection()
    c = conn.cursor()
    try:
        # Get current items
        order_id, current_items = get_table_order(table_id)
        if order_id is None: return False
        
        # Check if item exists to merge
        found = False
        for i in current_items:
            if i['id'] == item_dict['id']:
                i['qty'] += item_dict['qty']
                i['total'] += item_dict['total']
                found = True
                break
        
        if not found:
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
    c.execute("UPDATE restaurant_tables SET status = 'Available', current_order_id = NULL WHERE id = ?", (table_id,))
    conn.commit()
    conn.close()

def add_restaurant_table(label, capacity):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        c.execute("INSERT INTO restaurant_tables (account_id, label, capacity, status) VALUES (?, ?, ?, 'Available')", (aid, label, capacity))
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
        c.execute("SELECT status FROM restaurant_tables WHERE id = ?", (table_id,))
        status = c.fetchone()[0]
        if status != 'Available':
            return False, "Cannot delete occupied table!"
        
        c.execute("DELETE FROM restaurant_tables WHERE id = ?", (table_id,))
        conn.commit()
        return True, "Table Deleted"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_restaurant_table_capacity(table_id, new_capacity):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE restaurant_tables SET capacity = ? WHERE id = ?", (new_capacity, table_id))
        conn.commit()
        return True, "Updated"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


        
    matching_dates_df = pd.read_sql_query(query, conn, params=params)
    
    if matching_dates_df.empty:
        conn.close()
        return pd.DataFrame() # No history
        
    dates = matching_dates_df['date'].tolist()
    placeholders = ','.join(['?']*len(dates))
    
    # 2. Aggregates sales on those dates (Scoped)
    sales_query = f'''
        SELECT ti.product_name, SUM(ti.quantity) as total_qty, AVG(ti.price_at_sale) as avg_price
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        WHERE t.account_id = ? AND date(t.timestamp) IN ({placeholders})
        GROUP BY ti.product_name
        ORDER BY total_qty DESC
        LIMIT 10
    '''
    
    sales_params = [aid] + dates
    sales_df = pd.read_sql_query(sales_query, conn, params=sales_params)
    conn.close()
    return sales_df

# --- SHIFTSMART MODULE LOGIC ---

def add_staff(name, role, rate):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        c.execute("INSERT INTO staff (account_id, name, role, hourly_rate) VALUES (?, ?, ?, ?)", (aid, name, role, rate))
        conn.commit()
        return True, "Staff added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_all_staff():
    conn = get_connection()
    aid = get_current_account_id()
    df = pd.read_sql_query("SELECT * FROM staff WHERE account_id = ?", conn, params=(aid,))
    conn.close()
    return df

def assign_shift(date_str, slot, staff_id):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        # Check Staff Ownership
        c.execute("SELECT id FROM staff WHERE id = ? AND account_id = ?", (staff_id, aid))
        if not c.fetchone():
            return False, "Unauthorized shift assignment."

        # Check if already assigned
        c.execute("SELECT id FROM shifts WHERE date = ? AND slot = ? AND staff_id = ?", (date_str, slot, staff_id))
        if c.fetchone():
            return True, "Already assigned."
            
        c.execute("INSERT INTO shifts (date, slot, staff_id) VALUES (?, ?, ?)", (date_str, slot, staff_id))
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
    query = '''
        SELECT sh.*, s.name, s.role 
        FROM shifts sh
        JOIN staff s ON sh.staff_id = s.id
        WHERE sh.date = ? AND s.account_id = ?
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
    # Generate 16-char unique hash
    txn_hash = secrets.token_hex(8) # 8 bytes = 16 hex chars
    
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    print(f"DEBUG: record_transaction for account_id={aid}, method={payment_method}")
    
    try:
        # 1. Create Transaction Record (With Account ID)
        c.execute('INSERT INTO transactions (account_id, total_amount, total_profit, timestamp, customer_id, transaction_hash, points_redeemed, payment_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
                  (aid, total_amount, total_profit, datetime.now(), customer_id, txn_hash, points_redeemed, payment_method))
        transaction_id = c.lastrowid
        
        # 2. Add Line Items and Update Stock
        # 2. Add Line Items (Batch Optimization)
        # Prepare data for batch insert
        txn_items_data = [(transaction_id, item['id'], item['name'], item['qty'], item['price'], item['cost']) for item in items]
        
        c.executemany('''
            INSERT INTO transaction_items (transaction_id, product_id, product_name, quantity, price_at_sale, cost_at_sale)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', txn_items_data)
        
        # 3. Deduct Stock (Batch Optimization - Scoped)
        # Prepare data for batch update: (qty_to_deduct, product_id, account_id)
        stock_updates = [(item['qty'], item['id'], aid) for item in items]
        c.executemany('UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ? AND account_id = ?', stock_updates)

       # 4. FEFO Batch Deduction (FreshFlow Logic - Scoped)
        for item in items:
            qty_needed = item['qty']
            p_id = item['id']
            
            # Fetch batches for this product ordered by expiry (Scoped to Account)
            c.execute("SELECT id, quantity FROM product_batches WHERE product_id = ? AND account_id = ? AND quantity > 0 ORDER BY expiry_date ASC", (p_id, aid))
            batches = c.fetchall()
            
            for b_id, b_qty in batches:
                if qty_needed <= 0:
                    break
                
                deduct = min(qty_needed, b_qty)
                c.execute("UPDATE product_batches SET quantity = quantity - ? WHERE id = ? AND account_id = ?", (deduct, b_id, aid))
                qty_needed -= deduct
        
        # 5. Update Loyalty Points
        if customer_id:
            # Earn: 1 point per 10 currency of final paid amount? Or total? 
            # Sticking to Total Amount for earning to keep it simple.
            points_earned = int(total_amount / 10)
            
            # Net Change = Earned - Redeemed
            net_points_change = points_earned - points_redeemed
            
            c.execute('UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ? AND account_id = ?', (net_points_change, customer_id, aid))
            
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


def get_low_stock_products(threshold=10):
    # OPTIMIZATION: Reuse cached entire product list instead of new DB hit
    df = fetch_all_products()
    return df[df['stock_quantity'] <= threshold]


# --- ACCESS CONTROL & SUBSCRIPTION LOGIC ---

# Tiers Configuration
TIERS = {
    'Starter': ['1_Inventory', '2_POS', '3_Settings', '4_Dashboard'],
    'Business': ['1_Inventory', '2_POS', '3_Settings', '4_Dashboard', '6_FreshFlow', '7_VendorTrust', '8_VoiceAudit'],
    'Enterprise': ['*'] # All
}

# Role Configuration
ROLES = {
    'staff': ['2_POS', '8_VoiceAudit'], # Restricted
    'manager': ['1_Inventory', '2_POS', '6_FreshFlow', '7_VendorTrust', '8_VoiceAudit', '4_Dashboard'],
    'admin': ['*']
}

def check_access(username, page_name):
    """
    Returns (True, "") if allowed.
    Returns (False, Reason) if blocked.
    """
    # 1. Fetch User Role & Subscription from Accounts Table
    conn = get_connection()
    c = conn.cursor()
    
    # Get User Role and Account Subscription (Joined)
    query = """
        SELECT u.role, a.subscription_plan 
        FROM users u 
        JOIN accounts a ON u.account_id = a.id
        WHERE u.username = ?
    """
    c.execute(query, (username,))
    r = c.fetchone()
    conn.close()
    
    if not r:
        return False, "User not found or orphaned."
        
    user_role = r[0]
    sub_plan = r[1]
    
    # 2. Check Role Limits
    allowed_roles = ROLES.get(user_role, [])
    if '*' not in allowed_roles and page_name not in allowed_roles:
         return False, f"⛔ Restricted: '{user_role.title()}' cannot access this module."

    # 3. Check Subscription Limits
    allowed_sub = TIERS.get(sub_plan, [])
    if '*' not in allowed_sub and page_name not in allowed_sub:
        return False, f"🔒 Locked: Upgrade to '{sub_plan}' to unlock this."
        
    return True, "Access Granted"

import hashlib

def create_company_account(company_name, username, password, email):
    """
    Creates a new Account (Tenant) AND an Admin User for that account.
    Returns (Success, Msg)
    """
    conn = get_connection()
    c = conn.cursor()
    try:
        # Check if COMPANY NAME exists globally
        c.execute("SELECT id FROM accounts WHERE company_name = ?", (company_name,))
        if c.fetchone():
            return False, "Company Name already exists. Please login."

        # 1. Create Account
        c.execute("INSERT INTO accounts (company_name, subscription_plan) VALUES (?, 'Starter')", (company_name,))
        account_id = c.lastrowid
        
        # 2. Create User (Admin)
        # Note: Username uniqueness is now enforced at DB level (UNIQUE(account_id, username))
        # So we can just try insert and catch error if it violates (but wait, account_id is new, so it won't violate unless same user twice in same account)
        
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        
        c.execute("INSERT INTO users (account_id, username, email, password_hash, role) VALUES (?, ?, ?, ?, ?)", 
                  (account_id, username, email, pwd_hash, 'admin'))
        
        conn.commit()
        return True, "Account created successfully! Please login."
    except sqlite3.IntegrityError:
        return False, "Duplicate user in this account (Should not happen for new account)."
    except Exception as e:
        conn.rollback()
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
        
        # Strict Login: Match Username + Password + Company Name
        query = """
            SELECT u.role, u.account_id, a.company_name 
            FROM users u 
            JOIN accounts a ON u.account_id = a.id
            WHERE u.username = ? AND u.password_hash = ? AND a.company_name = ?
        """
        c.execute(query, (username, pwd_hash, company_name_check))
        result = c.fetchone()
        
        if result:
            role, aid, company = result[0], result[1], result[2]
            return True, role, aid, company
        
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
        c.execute("SELECT id, email FROM users WHERE username = ? OR email = ?", (contact, contact))
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

# --- CHURNGUARD & GEOVIZ LOGIC ---

def get_churn_metrics(days_threshold=30):
    conn = get_connection()
    aid = get_current_account_id()
    # Scoped Logic
    query = '''
        SELECT c.id, c.name, c.phone, c.loyalty_points, MAX(t.timestamp) as last_seen, COUNT(t.id) as visit_count, SUM(t.total_amount) as total_spent
        FROM customers c
        LEFT JOIN transactions t ON c.id = t.customer_id
        WHERE c.account_id = ?
        GROUP BY c.id
    '''
    df = pd.read_sql_query(query, conn, params=(aid,))
    conn.close()
    
    if df.empty:
        return pd.DataFrame()

    df['last_seen'] = pd.to_datetime(df['last_seen'])
    now = datetime.now()
    
    df['days_since'] = (now - df['last_seen']).dt.days
    df['days_since'] = df['days_since'].fillna(999) 
    
    churn_df = df[(df['visit_count'] > 0) & (df['days_since'] > days_threshold)].sort_values('total_spent', ascending=False)
    return churn_df

def get_geo_revenue():
    conn = get_connection()
    aid = get_current_account_id()
    query = '''
        SELECT c.city, c.pincode, COUNT(DISTINCT t.id) as txn_count, SUM(t.total_amount) as revenue
        FROM customers c
        JOIN transactions t ON c.id = t.customer_id
        WHERE c.account_id = ?
        GROUP BY c.city
        ORDER BY revenue DESC
    '''
    df = pd.read_sql_query(query, conn, params=(aid,))
    conn.close()
    return df

# --- STOCKSWAP LOGIC ---

def create_b2b_deal(store, product, qty, price, phone):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        c.execute("INSERT INTO b2b_deals (account_id, store_name, product_name, quantity, price_per_unit, acc_phone) VALUES (?, ?, ?, ?, ?, ?)", 
                  (aid, store, product, qty, price, phone))
        conn.commit()
        return True, "Deal Broadcasted!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_b2b_deals():
    conn = get_connection()
    aid = get_current_account_id()
    # Scoped to Account for Strict Isolation
    df = pd.read_sql_query("SELECT * FROM b2b_deals WHERE account_id = ? ORDER BY created_at DESC", conn, params=(aid,))
    conn.close()
    return df

# --- CROWDSTOCK LOGIC ---

def create_campaign(item, desc, votes, price):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        c.execute("INSERT INTO crowd_campaigns (account_id, item_name, description, votes_needed, price_est) VALUES (?, ?, ?, ?, ?)", 
                  (aid, item, desc, votes, price))
        conn.commit()
        return True, "Campaign Started!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_campaigns():
    conn = get_connection()
    aid = get_current_account_id()
    # Scoped
    df = pd.read_sql_query("SELECT * FROM crowd_campaigns WHERE status='ACTIVE' AND account_id = ?", conn, params=(aid,))
    conn.close()
    return df

def vote_campaign(camp_id):
    conn = get_connection()
    c = conn.cursor()
    aid = get_current_account_id()
    try:
        # Verify ownership/visibility (Scoped to Account)
        c.execute("SELECT votes_needed, votes_current FROM crowd_campaigns WHERE id = ? AND account_id = ?", (camp_id, aid))
        row = c.fetchone()
        if not row:
            return False, "Campaign not found or unauthorized."
            
        c.execute("UPDATE crowd_campaigns SET votes_current = votes_current + 1 WHERE id = ? AND account_id = ?", (camp_id, aid))
        
        # Check if funded (re-fetch current)
        c.execute("SELECT votes_needed, votes_current FROM crowd_campaigns WHERE id = ? AND account_id = ?", (camp_id, aid))
        row = c.fetchone()
        if row and row[1] >= row[0]:
            c.execute("UPDATE crowd_campaigns SET status = 'FUNDED' WHERE id = ? AND account_id = ?", (camp_id, aid))
            msg = "Vote Registered! 🚀 CAMPAIGN FUNDED!"
        else:
            msg = "Vote Registered!"
            
        conn.commit()
        return True, msg
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# --- SHIFTSMART MODULE LOGIC ---

def add_staff(name, role, rate, override_account_id=None):
    conn = get_connection()
    c = conn.cursor()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    try:
        c.execute("INSERT INTO staff (account_id, name, role, hourly_rate) VALUES (?, ?, ?, ?)", (aid, name, role, rate))
        conn.commit()
        return True, "Staff added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_all_staff(override_account_id=None):
    conn = get_connection()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    df = pd.read_sql_query("SELECT * FROM staff WHERE account_id = ?", conn, params=(aid,))
    conn.close()
    return df

def create_user(username, password, email, role='staff', override_account_id=None):
    """
    Creates a new user for the CURRENT account.
    Enforced uniqueness via (account_id, username) index.
    """
    conn = get_connection()
    c = conn.cursor()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    try:
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        c.execute("INSERT INTO users (account_id, username, email, password_hash, role) VALUES (?, ?, ?, ?, ?)", 
                  (aid, username, email, pwd_hash, role))
        conn.commit()
        return True, "User created successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists in your account."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def assign_shift(date_str, slot, staff_id, override_account_id=None):
    conn = get_connection()
    c = conn.cursor()
    aid = override_account_id if override_account_id is not None else get_current_account_id()
    try:
        # Verify staff belongs to account
        c.execute("SELECT id FROM staff WHERE id = ? AND account_id = ?", (staff_id, aid))
        if not c.fetchone():
            return False, "Staff member not found or unauthorized."

        # Check if already assigned
        c.execute("SELECT id FROM shifts WHERE date = ? AND slot = ? AND staff_id = ?", (date_str, slot, staff_id))
        if c.fetchone():
            return True, "Already assigned."
            
        c.execute("INSERT INTO shifts (date, slot, staff_id) VALUES (?, ?, ?)", (date_str, slot, staff_id))
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
    query = '''
        SELECT sh.*, s.name, s.role 
        FROM shifts sh
        JOIN staff s ON sh.staff_id = s.id
        WHERE sh.date = ? AND s.account_id = ?
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
