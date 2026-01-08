import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "retail_supply_chain.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    """Initializes the database with necessary tables if they don't exist."""
    conn = get_connection()
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

def fetch_all_products():
    """Returns a pandas DataFrame of all products."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM products", conn)
    conn.close()
    return df

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

def add_customer(name, phone, email):
    conn = get_connection()
    c = conn.cursor()
    try:
        # Check uniqueness manually since we didn't add UNIQUE constraint at creation
        c.execute("SELECT id FROM customers WHERE phone = ?", (phone,))
        if c.fetchone():
            return False, "Customer with this phone already exists!" # Return tuple (Success, Msg)

        c.execute("INSERT INTO customers (name, phone, email) VALUES (?, ?, ?)", (name, phone, email))
        conn.commit()
        return True, "Customer added successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_stock(product_id, quantity_change):
    """Updates stock. quantity_change can be negative (sale) or positive (restock)."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?', (quantity_change, product_id))
    conn.commit()
    conn.close()

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
        for item in items:
            c.execute('''
                INSERT INTO transaction_items (transaction_id, product_id, product_name, quantity, price_at_sale, cost_at_sale)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (transaction_id, item['id'], item['name'], item['qty'], item['price'], item['cost']))
            
            # Deduct stock
            c.execute('UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?', (item['qty'], item['id']))
        
        # 3. Update Loyalty Points
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


def get_low_stock_products(threshold=10):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM products WHERE stock_quantity <= ?", conn, params=(threshold,))
    conn.close()
    return df

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
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
