
import aiosqlite
import os
import asyncio
import logging

try:
    import asyncpg
except ImportError:
    asyncpg = None

# Point to the existing database in the parent directory
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "retail_supply_chain.db"))
DATABASE_URL = os.getenv("DATABASE_URL") # e.g., postgresql://user:pass@localhost:5432/vyaparmind

_SHARED_CONN = None
_DB_TYPE = "sqlite"

async def get_db_connection():
    """Returns a shared async connection (SQLite or Postgres)."""
    global _SHARED_CONN, _DB_TYPE
    
    if _SHARED_CONN is None:
        if DATABASE_URL and DATABASE_URL.startswith("postgres"):
            if not asyncpg:
                raise ImportError("asyncpg is required for PostgreSQL")
            _SHARED_CONN = await asyncpg.connect(DATABASE_URL)
            _DB_TYPE = "postgres"
            logging.info("Connected to PostgreSQL")
        else:
            _SHARED_CONN = await aiosqlite.connect(DB_PATH, check_same_thread=False)
            _SHARED_CONN.row_factory = aiosqlite.Row
            await _SHARED_CONN.execute("PRAGMA journal_mode=WAL;")
            _DB_TYPE = "sqlite"
            logging.info("Connected to SQLite")
            
    return _SHARED_CONN

def get_placeholder(index=1):
    """Returns '?' for SQLite and '$N' for Postgres."""
    return f"${index}" if _DB_TYPE == "postgres" else "?"

async def execute_query(query, params=(), fetch_one=False, fetch_all=False, commit=False):
    db = await get_db_connection()
    
    # Adjust placeholders for Postgres
    if _DB_TYPE == "postgres":
        # Naive replacement of ? with $1, $2...
        # Only works if query uses ? consistent with param order
        parts = query.split("?")
        if len(parts) > 1:
            query = ""
            for i, part in enumerate(parts[:-1]):
                query += f"{part}${i+1}"
            query += parts[-1]
            
    try:
        if _DB_TYPE == "postgres":
            if fetch_one:
                return await db.fetchrow(query, *params)
            elif fetch_all:
                rows = await db.fetch(query, *params)
                return [dict(r) for r in rows]
            else:
                return await db.execute(query, *params)
        else:
            # SQLite
            async with db.execute(query, params) as cursor:
                if fetch_one:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
                elif fetch_all:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
                
                if commit:
                     await db.commit()
                return True
    except Exception as e:
        print(f"DB Error: {e}")
        raise e

async def fetch_pos_inventory(account_id: str, search_term: str = None, limit: int = 50):
    query = """
        SELECT p.*, COALESCE(SUM(ti.quantity), 0) as total_sold
        FROM products p
        LEFT JOIN transaction_items ti ON p.id = ti.product_id
        WHERE p.account_id = ?
    """
    params = [account_id]
    
    if search_term:
        query += " AND (p.name LIKE ? OR p.category LIKE ?)"
        wildcard = f"%{search_term}%"
        params.extend([wildcard, wildcard])
        
    query += " GROUP BY p.id"
    if not search_term:
        query += " ORDER BY total_sold DESC"
    query += f" LIMIT {limit}"
    
    return await execute_query(query, params, fetch_all=True)

async def add_customer(account_id: str, id: str, name: str, phone: str, email: str = None):
    """
    Async customer creation that handles commits.
    """
    try:
        exists = await execute_query("SELECT id FROM customers WHERE phone = ? AND account_id = ?", (phone, account_id), fetch_one=True)
        if exists:
            return False, "Customer with this phone already exists!"
        
        await execute_query(
            "INSERT INTO customers (id, account_id, name, phone, email) VALUES (?, ?, ?, ?, ?)",
            (id, account_id, name, phone, email),
            commit=True
        )
        return True, "Customer added successfully."
    except Exception as e:
        return False, str(e)

async def add_product_async(account_id, new_id, name, category, price, cost_price, stock_quantity, tax_rate, salt, manuf, schedule, chronic, refill):
    query = """INSERT INTO products (id, account_id, name, category, price, cost_price, stock_quantity, tax_rate, 
            salt_composition, manufacturer, schedule_type, is_chronic, refill_interval) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    params = (new_id, account_id, name, category, price, cost_price, stock_quantity, tax_rate, salt, manuf, schedule, chronic, refill)
    
    try:
        await execute_query(query, params, commit=True)
        return True, "Product added."
    except Exception as e:
        return False, str(e)

async def record_transaction_async(txn_data):
    """
    Complex transaction recording with ACID guarantees.
    """
    db = await get_db_connection()
    import secrets
    import datetime
    
    new_txn_id = secrets.token_hex(8)
    timestamp = datetime.datetime.now()
    
    try:
        if _DB_TYPE == "postgres":
            async with db.transaction():
                # 1. Head
                # Use strict $ placeholders
                await db.execute(
                    """INSERT INTO transactions (id, account_id, customer_id, timestamp, total_amount, total_profit, payment_method, points_redeemed, doctor_name, doctor_reg_no)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
                    new_txn_id, txn_data.account_id, txn_data.customer_id, timestamp, 
                    txn_data.total_amount, txn_data.total_profit, txn_data.payment_method, 
                    txn_data.points_redeemed, txn_data.doctor_name, txn_data.doctor_reg_no
                )
                # 2. Items
                for item in txn_data.items:
                    await db.execute(
                        """INSERT INTO transaction_items (id, transaction_id, product_id, product_name, quantity, price_at_sale, cost_at_sale)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                        secrets.token_hex(8), new_txn_id, item.id, item.name, item.qty, item.price, item.cost
                    )
                    await db.execute(
                        "UPDATE products SET stock_quantity = stock_quantity - $1 WHERE id = $2",
                        item.qty, item.id
                    )
                # 3. Points
                if txn_data.customer_id:
                     points_earned = int(txn_data.total_amount / 100)
                     points_change = points_earned - txn_data.points_redeemed
                     await db.execute(
                        "UPDATE customers SET loyalty_points = loyalty_points + $1 WHERE id = $2",
                        points_change, txn_data.customer_id
                     )
        else:
            # SQLite path
            # 1. Insert Head
            await db.execute(
                """INSERT INTO transactions 
                (id, account_id, customer_id, timestamp, total_amount, total_profit, payment_method, points_redeemed, doctor_name, doctor_reg_no)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (new_txn_id, txn_data.account_id, txn_data.customer_id, timestamp, 
                 txn_data.total_amount, txn_data.total_profit, txn_data.payment_method, 
                 txn_data.points_redeemed, txn_data.doctor_name, txn_data.doctor_reg_no)
            )
            
            # 2. Insert Items & Update Stock
            for item in txn_data.items:
                # Insert Line Item
                await db.execute(
                    """INSERT INTO transaction_items (id, transaction_id, product_id, product_name, quantity, price_at_sale, cost_at_sale)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (secrets.token_hex(8), new_txn_id, item.id, item.name, item.qty, item.price, item.cost)
                )
                
                # Update Stock
                await db.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?",
                    (item.qty, item.id)
                )
            
            # 3. Update Loyalty Points
            if txn_data.customer_id:
                # Add points (1 point per 100 spent? approx logic)
                points_earned = int(txn_data.total_amount / 100)
                points_change = points_earned - txn_data.points_redeemed
                
                await db.execute(
                    "UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ?",
                    (points_change, txn_data.customer_id)
                )
                
            await db.commit()
            
        return new_txn_id
        
    except Exception as e:
        if _DB_TYPE == "sqlite":
             await db.rollback()
        # For postgres, async with transaction() aut-rollbacks on error usually, but manual rollback logic depends on driver usage.
        # asyncpg transaction context handles it.
        print(f"Transaction Error: {e}")
        return None

async def get_setting_async(account_id, key):
    db = await get_db_connection()
    async with db.execute("SELECT value FROM settings WHERE key = ? AND account_id = ?", (key, account_id)) as cursor:
        row = await cursor.fetchone()
        if row:
            return row['value']
        
        # Fallbacks
        if key == 'store_name': return "VyaparMind Store"
        return None

async def set_setting_async(account_id, key, value):
    db = await get_db_connection()
    try:
        await db.execute(
            """INSERT INTO settings (account_id, key, value) VALUES (?, ?, ?) 
               ON CONFLICT(account_id, key) DO UPDATE SET value=excluded.value""",
            (account_id, key, value)
        )
        
        # Sync Subscription logic
        if key == 'subscription_plan':
             await db.execute("UPDATE accounts SET subscription_plan = ? WHERE id = ?", (value, account_id))
             
        await db.commit()
        return True, "Setting updated."
    except Exception as e:
        return False, str(e)
