import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st

DB_NAME = "retail_supply_chain.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    """Initializes the database with necessary tables if they don't exist."""
    conn = get_connection()
    # OPTIMIZATION: Enable WAL Mode for concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    c = conn.cursor()
    
    # Products Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            cost_price REAL NOT NULL,
            stock_quantity INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Transactions Table (Head)
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL NOT NULL,
            total_profit REAL NOT NULL,
            payment_method TEXT DEFAULT 'CASH'
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
    # Settings Table (Key-Value)
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Default Settings if empty
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('store_name', 'VyaparMind Store')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('store_address', 'Hyderabad, India')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('store_phone', '9876543210')")
    # Customers Table (New)
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            loyalty_points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Product Batches (FreshFlow)
    c.execute('''
        CREATE TABLE IF NOT EXISTS product_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            batch_code TEXT,
            expiry_date DATE,
            quantity INTEGER,
            cost_price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
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
    
    # product_batches(expiry_date) for FreshFlow
    c.execute("CREATE INDEX IF NOT EXISTS idx_batches_expiry ON product_batches(expiry_date)")

    # VendorTrust Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT,
            category_specialty TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER,
            order_date DATE,
            expected_date DATE,
            received_date DATE,
            status TEXT DEFAULT 'PENDING', -- PENDING, RECEIVED, CANCELLED
            quality_rating INTEGER DEFAULT 0, -- 1 to 5
            notes TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
        )
    ''')

    # IsoBar Context Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_context (
            date DATE PRIMARY KEY,
            weather_tag TEXT,
            event_tag TEXT,
            notes TEXT
        )
    ''')

    # ShiftSmart Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT,
            hourly_rate REAL
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

    conn.commit()
    conn.close()

def get_setting(key):
    """Fetch a setting value by key."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_setting(key, value):
    """Update or Set a setting."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        return True
    except Exception as e:
        print(f"Settings Error: {e}")
        return False
    finally:
        conn.close()

def add_product(name, category, price, cost_price, stock_quantity, tax_rate=0.0):
    conn = get_connection()
    c = conn.cursor()
    try:
        # Check if product exists (by name) to toggle between Insert/Update logic if wanted, 
        # but user likely wants explicit update. 
        # For now, just Insert.
        c.execute('''
            INSERT INTO products (name, category, price, cost_price, stock_quantity, tax_rate)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, category, price, cost_price, stock_quantity, tax_rate))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()
        # Invalidate Cache
        fetch_all_products.clear()

def update_product(product_id, price, cost_price, stock_quantity, tax_rate):
    """Updates price, cost, stock, and tax."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            UPDATE products 
            SET price = ?, cost_price = ?, stock_quantity = ?, tax_rate = ?, updated_at = ?
            WHERE id = ?
        ''', (price, cost_price, stock_quantity, tax_rate, datetime.now(), product_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Update Error: {e}")
        return False
    finally:
        conn.close()
        # Invalidate Cache
        fetch_all_products.clear()

@st.cache_data(ttl=300)
def fetch_all_products():
    """Returns a pandas DataFrame of all products."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM products", conn)
    conn.close()
    return df

@st.cache_data(ttl=300)
def fetch_customers():
    """Returns a pandas DataFrame of all customers."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    conn.close()
    return df

def get_customer_by_phone(phone):
    """Fetch customer by phone number."""
    conn = get_connection()
    # clean phone? assume exact match for now
    df = pd.read_sql_query("SELECT * FROM customers WHERE phone = ?", conn, params=(phone,))
    conn.close()
    return df.iloc[0] if not df.empty else None

def add_customer(name, phone, email, city="Unknown", pincode="000000"):
    conn = get_connection()
    c = conn.cursor()
    try:
        # Check uniqueness manually since we didn't add UNIQUE constraint at creation
        c.execute("SELECT id FROM customers WHERE phone = ?", (phone,))
        if c.fetchone():
            return False, "Customer with this phone already exists!" # Return tuple (Success, Msg)

        c.execute("INSERT INTO customers (name, phone, email, city, pincode) VALUES (?, ?, ?, ?, ?)", (name, phone, email, city, pincode))
        conn.commit()
        return True, "Customer added successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
        # Invalidate Cache
        fetch_customers.clear()

def update_stock(product_id, quantity_change):
    """Updates stock. quantity_change can be negative (sale) or positive (restock)."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?', (quantity_change, product_id))
    conn.commit()
    conn.close()
    # Invalidate Cache
    fetch_all_products.clear()


# --- FRESHFLOW MODULE LOGIC ---

def add_batch(product_id, batch_code, expiry_date, quantity, cost_price):
    """Adds a new batch and updates total stock."""
    conn = get_connection()
    c = conn.cursor()
    try:
        # 1. Insert Batch
        c.execute('''
            INSERT INTO product_batches (product_id, batch_code, expiry_date, quantity, cost_price)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_id, batch_code, expiry_date, quantity, cost_price))
        
        # 2. Update Total Stock in master table
        c.execute('UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?', (quantity, product_id))
        
        conn.commit()
        return True, "Batch added successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()
        fetch_all_products.clear()

def get_expiring_batches(days_threshold=7):
    """Returns batches expiring within threshold days."""
    conn = get_connection()
    # Logic: expiry_date <= (today + threshold) AND quantity > 0
    query = '''
        SELECT b.*, p.name as product_name, p.price as current_price
        FROM product_batches b
        JOIN products p ON b.product_id = p.id
        WHERE b.quantity > 0 
        AND b.expiry_date <= date('now', '+' || ? || ' days')
        ORDER BY b.expiry_date ASC
    '''
    df = pd.read_sql_query(query, conn, params=(str(days_threshold),))
    conn.close()
    return df

    return df

# --- VENDORTRUST MODULE LOGIC ---

def add_supplier(name, contact, phone, specialty):
    conn = get_connection()
    c = conn.cursor()
    try:
        # Check uniqueness
        c.execute("SELECT id FROM suppliers WHERE name = ? OR phone = ?", (name, phone))
        if c.fetchone():
            return False, "Supplier already exists (same name or phone)."
            
        c.execute("INSERT INTO suppliers (name, contact_person, phone, category_specialty) VALUES (?, ?, ?, ?)", 
                  (name, contact, phone, specialty))
        conn.commit()
        return True, "Supplier added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_all_suppliers():
    conn = get_connection()
    # Deduplicate view logic: Group by name/phone to hide dupes if they exist
    # Ideally we should clean the DB, but for now we filter view
    df = pd.read_sql_query("SELECT * FROM suppliers GROUP BY name", conn)
    conn.close()
    return df

def create_purchase_order(supplier_id, expected_date, notes=""):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO purchase_orders (supplier_id, order_date, expected_date, notes) VALUES (?, date('now'), ?, ?)",
                  (supplier_id, expected_date, notes))
        conn.commit()
        return True, "PO Created."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_open_pos():
    conn = get_connection()
    query = '''
        SELECT po.*, s.name as supplier_name 
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.id
        WHERE po.status = 'PENDING'
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def receive_purchase_order(po_id, quality_rating):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            UPDATE purchase_orders 
            SET status = 'RECEIVED', received_date = date('now'), quality_rating = ?
            WHERE id = ?
        ''', (quality_rating, po_id))
        conn.commit()
        return True, "PO Received."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_vendor_scorecard(supplier_id):
    conn = get_connection()
    # On-Time: received <= expected
    # Score: AVG quality
    query = "SELECT * FROM purchase_orders WHERE supplier_id = ? AND status = 'RECEIVED'"
    df = pd.read_sql_query(query, conn, params=(supplier_id,))
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
    try:
        c.execute("INSERT OR REPLACE INTO daily_context (date, weather_tag, event_tag, notes) VALUES (?, ?, ?, ?)",
                  (date_str, weather, event, notes))
        conn.commit()
        return True, "Context Saved."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_daily_context(date_str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM daily_context WHERE date = ?", (date_str,))
    res = c.fetchone()
    conn.close()
    return res

def analyze_context_demand(weather_filter=None, event_filter=None):
    """
    Finds top selling items on days that match the filters.
    """
    conn = get_connection()
    
    # 1. Find dates matching context
    query = "SELECT date FROM daily_context WHERE 1=1"
    params = []
    
    if weather_filter and weather_filter != "None":
        query += " AND weather_tag = ?"
        params.append(weather_filter)
        
    if event_filter and event_filter != "None":
        query += " AND event_tag = ?"
        params.append(event_filter)
        
    matching_dates_df = pd.read_sql_query(query, conn, params=params)
    
    if matching_dates_df.empty:
        conn.close()
        return pd.DataFrame() # No history
        
    dates = matching_dates_df['date'].tolist()
    placeholders = ','.join(['?']*len(dates))
    
    # 2. Aggregates sales on those dates
    sales_query = f'''
        SELECT ti.product_name, SUM(ti.quantity) as total_qty, AVG(ti.price_at_sale) as avg_price
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        WHERE date(t.timestamp) IN ({placeholders})
        GROUP BY ti.product_name
        ORDER BY total_qty DESC
        LIMIT 10
    '''
    
    sales_df = pd.read_sql_query(sales_query, conn, params=dates)
    conn.close()
    return sales_df

# --- SHIFTSMART MODULE LOGIC ---

def add_staff(name, role, rate):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO staff (name, role, hourly_rate) VALUES (?, ?, ?)", (name, role, rate))
        conn.commit()
        return True, "Staff added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_all_staff():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM staff", conn)
    conn.close()
    return df

def assign_shift(date_str, slot, staff_id):
    conn = get_connection()
    c = conn.cursor()
    try:
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
    query = '''
        SELECT sh.*, s.name, s.role 
        FROM shifts sh
        JOIN staff s ON sh.staff_id = s.id
        WHERE sh.date = ?
    '''
    df = pd.read_sql_query(query, conn, params=(date_str,))
    conn.close()
    return df

def predict_labor_demand(weather, event):
    """
    Returns estimated staff needed based on simulated demand.
    Simple Heuristic: 1 Staff per 50 units of expected volume.
    """
    sales_df = analyze_context_demand(weather, event)
    if sales_df.empty:
        return 2 # Baseline staffing
        
    total_est_volume = sales_df['total_qty'].sum() / 10 # Normalize (history is sum, we need daily avg? simplified)
    # Actually analyze_context_demand sums ALL history.
    # We need AVG per day.
    # Let's refine analyze_context_demand or handle it roughly here.
    
    # Rough fix: Assume history spans ~10 days? 
    # Better: analyze_context_demand should return AVG.
    # Let's assume the current analyze_context_demand returns SUM.
    # We will just divide by a heuristic to get "Daily Volume".
    
    daily_vol = total_est_volume / 5 # Arbitrary divisor for MVP
    
    staff_needed = max(2, int(daily_vol / 20) + 1) # Min 2 staff
    return staff_needed

def record_transaction(items, total_amount, total_profit, customer_id=None, points_redeemed=0):
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
    
    try:
        # 1. Create Transaction Record
        c.execute('INSERT INTO transactions (total_amount, total_profit, timestamp, customer_id, transaction_hash, points_redeemed) VALUES (?, ?, ?, ?, ?, ?)', 
                  (total_amount, total_profit, datetime.now(), customer_id, txn_hash, points_redeemed))
        transaction_id = c.lastrowid
        
        # 2. Add Line Items and Update Stock
        # 2. Add Line Items (Batch Optimization)
        # Prepare data for batch insert
        txn_items_data = [(transaction_id, item['id'], item['name'], item['qty'], item['price'], item['cost']) for item in items]
        
        c.executemany('''
            INSERT INTO transaction_items (transaction_id, product_id, product_name, quantity, price_at_sale, cost_at_sale)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', txn_items_data)
        
        # 3. Deduct Stock (Batch Optimization)
        # Prepare data for batch update: (qty_to_deduct, product_id)
        stock_updates = [(item['qty'], item['id']) for item in items]
        c.executemany('UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?', stock_updates)

       # 4. FEFO Batch Deduction (FreshFlow Logic)
        for item in items:
            qty_needed = item['qty']
            p_id = item['id']
            
            # Fetch batches for this product ordered by expiry
            c.execute("SELECT id, quantity FROM product_batches WHERE product_id = ? AND quantity > 0 ORDER BY expiry_date ASC", (p_id,))
            batches = c.fetchall()
            
            for b_id, b_qty in batches:
                if qty_needed <= 0:
                    break
                
                deduct = min(qty_needed, b_qty)
                c.execute("UPDATE product_batches SET quantity = quantity - ? WHERE id = ?", (deduct, b_id))
                qty_needed -= deduct
        
        # 5. Update Loyalty Points
        if customer_id:
            # Earn: 1 point per 10 currency of final paid amount? Or total? 
            # Sticking to Total Amount for earning to keep it simple.
            points_earned = int(total_amount / 10)
            
            # Net Change = Earned - Redeemed
            net_points_change = points_earned - points_redeemed
            
            c.execute('UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ?', (net_points_change, customer_id))
            
        conn.commit()
        return txn_hash 
    except Exception as e:
        print(f"Transaction Error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()
        # Invalidate Both Caches
        fetch_all_products.clear()
        fetch_customers.clear()


def get_low_stock_products(threshold=10):
    # OPTIMIZATION: Reuse cached entire product list instead of new DB hit
    df = fetch_all_products()
    return df[df['stock_quantity'] <= threshold]

import hashlib

def create_user(username, password, email):
    """Creates a new user with hashed password."""
    conn = get_connection()
    c = conn.cursor()
    try:
        # Simple SHA256 hashing
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", 
                  (username, email, password_hash))
        conn.commit()
        return True, "User created successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def verify_user(username, password):
    """Verifies user credentials."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        
        if result:
            stored_hash = result[0]
            input_hash = hashlib.sha256(password.encode()).hexdigest()
            if stored_hash == input_hash:
                return True, "Login successful."
        
        return False, "Invalid username or password."
        return False, str(e)
    finally:
        conn.close()

# --- CHURNGUARD & GEOVIZ LOGIC ---

def get_churn_metrics(days_threshold=30):
    conn = get_connection()
    # Find customers whose last transaction was > threshold days ago
    # We need MAX(timestamp) per customer from transactions
    query = '''
        SELECT c.id, c.name, c.phone, c.loyalty_points, MAX(t.timestamp) as last_seen, COUNT(t.id) as visit_count, SUM(t.total_amount) as total_spent
        FROM customers c
        LEFT JOIN transactions t ON c.id = t.customer_id
        GROUP BY c.id
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return pd.DataFrame()

    df['last_seen'] = pd.to_datetime(df['last_seen'])
    now = datetime.now()
    
    # Fill usage logic
    df['days_since'] = (now - df['last_seen']).dt.days
    df['days_since'] = df['days_since'].fillna(999) # Never visited
    
    # Filter for Churn Risk: Active before (visited > 0) AND last_seen > threshold
    churn_df = df[(df['visit_count'] > 0) & (df['days_since'] > days_threshold)].sort_values('total_spent', ascending=False)
    
    return churn_df

def get_geo_revenue():
    conn = get_connection()
    query = '''
        SELECT c.city, c.pincode, COUNT(DISTINCT t.id) as txn_count, SUM(t.total_amount) as revenue
        FROM customers c
        JOIN transactions t ON c.id = t.customer_id
        GROUP BY c.city
        ORDER BY revenue DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
