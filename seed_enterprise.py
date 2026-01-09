import sqlite3
import random
from datetime import datetime, timedelta
import secrets

DB_NAME = "retail_supply_chain.db"

def get_connection():
    return sqlite3.connect(DB_NAME, timeout=30, check_same_thread=False)

# --- CONSTANTS ---
CITIES = ["Hyderabad", "Warangal", "Karimnagar"]
ROLES = ["Staff", "Manager"]
SUPPLIERS_LIST = [
    ("FreshFarms Ltd", "Rahul Farmer", "9848011111", "Produce"),
    ("DairyBest Co", "Sneha Dairy", "9848022222", "Dairy"),
    ("Global Grains", "Amit Trader", "9848033333", "Grains"),
    ("BevCo Distributors", "Vikram Sales", "9848044444", "Beverages"),
    ("HomeCare Supplies", "Anjali Clean", "9848055555", "Home Care"),
    ("SnackAttack Inc", "Karan Munch", "9848066666", "Snacks")
]
CAMPAIGNS = [
    ("Organic Quinoa", "Supergrain from Andes", 500),
    ("Vegan Cheese", "Plant-based delight", 200),
    ("Smart Water Bottle", "Tracks hydration", 1000),
    ("Biodegradable Bags", "Save the planet", 300)
]

# --- UTILS ---
def random_date(start_date, end_date):
    delta = end_date - start_date
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start_date + timedelta(seconds=random_second)

def generate_transactions(c, customers, products, start_date, n=1000):
    """Generates transactions for existing customers/products"""
    product_keys = list(products.keys())
    batch_data = []
    item_data = []
    
    # Pre-fetch existing products to minimize lookup time
    
    print(f"   > Generating {n} transactions...")
    for _ in range(n):
        txn_date = random_date(start_date, datetime.now())
        cust_id = random.choice(customers)
        txn_hash = secrets.token_hex(8)
        
        # Basket
        basket_size = random.randint(1, 8)
        basket_pids = random.choices(product_keys, k=basket_size)
        
        t_amt = 0
        t_profit = 0
        
        # We need TID first
        c.execute("INSERT INTO transactions (timestamp, total_amount, total_profit, customer_id, transaction_hash) VALUES (?, 0, 0, ?, ?)", (txn_date, cust_id, txn_hash))
        tid = c.lastrowid
        
        for pid in basket_pids:
            p = products[pid]
            qty = random.randint(1, 3)
            # Add noise to price/cost to simulate market fluctuations? No, keep simple.
            price = p['price']
            cost = p['cost']
            
            t_amt += (price * qty)
            t_profit += ((price * qty) - (cost * qty))
            
            item_data.append((tid, pid, p['name'], qty, price, cost))
            
        c.execute("UPDATE transactions SET total_amount = ?, total_profit = ? WHERE id = ?", (t_amt, t_profit, tid))
        
    c.executemany("INSERT INTO transaction_items (transaction_id, product_id, product_name, quantity, price_at_sale, cost_at_sale) VALUES (?, ?, ?, ?, ?, ?)", item_data)



# --- SEEDING FUNCTIONS ---

def seed_suppliers_and_batches():
    print("📍 Seeding Suppliers & Batches (FreshFlow/VendorTrust)...")
    conn = get_connection()
    c = conn.cursor()
    
    # RESET SCHEMA to ensure columns exist
    c.execute("DROP TABLE IF EXISTS suppliers")
    c.execute('''
        CREATE TABLE suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT,
            category_specialty TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute("DROP TABLE IF EXISTS purchase_orders")
    c.execute('''
        CREATE TABLE purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER,
            order_date DATE,
            expected_date DATE,
            received_date DATE,
            status TEXT DEFAULT 'PENDING',
            quality_rating INTEGER DEFAULT 0,
            notes TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
        )
    ''')

    # 1. Suppliers
    c.executemany("INSERT INTO suppliers (name, contact_person, phone, category_specialty) VALUES (?, ?, ?, ?)", SUPPLIERS_LIST)
    
    # 2. Batches (FreshFlow) -> product_batches is usually safe, but check schema? 
    # Existing schema: product_id, batch_code, expiry_date, quantity, cost_price. Matches script.
    
    c.execute("SELECT id, name, price FROM products")
    products = c.fetchall()
    
    batch_data = []
    today = datetime.now()
    
    for p_id, p_name, price in products:
        # Create 3 batches per product
        batch_data.append((p_id, f"BATCH-{secrets.token_hex(3).upper()}", (today - timedelta(days=7)).date(), 0, price * 0.7)) 
        batch_data.append((p_id, f"BATCH-{secrets.token_hex(3).upper()}", (today + timedelta(days=3)).date(), random.randint(5, 20), price * 0.7))
        batch_data.append((p_id, f"BATCH-{secrets.token_hex(3).upper()}", (today + timedelta(days=30)).date(), random.randint(50, 100), price * 0.7))

    c.executemany("INSERT INTO product_batches (product_id, batch_code, expiry_date, quantity, cost_price) VALUES (?, ?, ?, ?, ?)", batch_data)
    
    # Update total stock
    c.execute("UPDATE products SET stock_quantity = (SELECT SUM(quantity) FROM product_batches WHERE product_id = products.id)")
    
    conn.commit()
    conn.close()

def seed_staff_and_shifts():
    print("📍 Seeding Staff & Shifts (ShiftSmart)...")
    conn = get_connection()
    c = conn.cursor()
    
    # RESET SCHEMA
    c.execute("DROP TABLE IF EXISTS staff")
    c.execute('''
        CREATE TABLE staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT,
            hourly_rate REAL
        )
    ''')
    
    c.execute("DROP TABLE IF EXISTS shifts")
    c.execute('''
        CREATE TABLE shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            slot TEXT,
            staff_id INTEGER,
            FOREIGN KEY (staff_id) REFERENCES staff (id)
        )
    ''')

    # 1. Staff
    staff_names = ["Ravi Manager", "Sita Cashier", "Gopal Stock", "Lata Staff"]
    staff_data = []
    for i, name in enumerate(staff_names):
        role = "Manager" if i == 0 else "Staff"
        # No Phone in Staff table schema!
        staff_data.append((name, role, 15 if role == "Staff" else 25))
        
    for s in staff_data:
        c.execute("INSERT INTO staff (name, role, hourly_rate) VALUES (?, ?, ?)", s)
        
    conn.commit()
    
    # 2. Shifts (Past 30 days history)
    c.execute("SELECT id FROM staff")
    staff_ids = [r[0] for r in c.fetchall()]
    
    today = datetime.now()
    shift_data = []
    
    slots = ["Morning", "Evening"]
    
    if staff_ids:
        for day_offset in range(30):
            d = (today - timedelta(days=day_offset)).strftime("%Y-%m-%d")
            for slot in slots:
                assigned = random.sample(staff_ids, min(len(staff_ids), 2))
                for sid in assigned:
                    shift_data.append((d, slot, sid))
                    
        c.executemany("INSERT INTO shifts (date, slot, staff_id) VALUES (?, ?, ?)", shift_data)
    conn.commit()
    conn.close()

def seed_innovations():
    print("📍 Seeding Innovations (StockSwap, CrowdStock)...")
    conn = get_connection()
    c = conn.cursor()
    
    # RESET SCHEMA
    c.execute("DROP TABLE IF EXISTS b2b_deals")
    c.execute('''
        CREATE TABLE b2b_deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT, 
            product_name TEXT,
            quantity INTEGER,
            price_per_unit REAL,
            acc_phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute("DROP TABLE IF EXISTS crowd_campaigns")
    c.execute('''
        CREATE TABLE crowd_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            description TEXT,
            votes_needed INTEGER,
            votes_current INTEGER DEFAULT 0,
            price_est REAL,
            status TEXT DEFAULT 'ACTIVE'
        )
    ''')
    
    # 1. StockSwap Deals
    deals = [
        ("Vyapar Store Hyd", "Excess Rice Bags", 50, 300.0),
        ("Kirana King", "Near Expiry Biscuits", 100, 15.0),
        ("SuperMart", "Surplus Coke Cans", 200, 25.0)
    ]
    
    deal_data = []
    for d in deals:
        # store_name, product_name, quantity, price, phone, created_at
        deal_data.append((d[0], d[1], d[2], d[3], "9876543210", datetime.now()))
        
    c.executemany("INSERT INTO b2b_deals (store_name, product_name, quantity, price_per_unit, acc_phone, created_at) VALUES (?, ?, ?, ?, ?, ?)", deal_data)
    
    # 2. CrowdStock Campaigns
    # table: crowd_campaigns (item_name, description, votes_needed, votes_current, status) (Added price_est to schema above to be safe, but code might not use it?)
    # DB Schema has: item_name, description, votes_needed, votes_current, price_est, status.
    
    camp_data = []
    for camp in CAMPAIGNS:
        current = random.randint(0, camp[2])
        status = "Funded" if current >= camp[2] else "Active"
        # product_name, description, votes_needed, current_votes, price(dummy), status
        camp_data.append((camp[0], camp[1], camp[2], current, 0.0, status))
        
    c.executemany("INSERT INTO crowd_campaigns (item_name, description, votes_needed, votes_current, price_est, status) VALUES (?, ?, ?, ?, ?, ?)", camp_data)
    
    conn.commit()
    conn.close()

def seed_main_history():
    print("📍 Seeding 6-Month Transaction History...")
    conn = get_connection()
    c = conn.cursor()
    
    # Fetch Reference Data
    c.execute("SELECT id FROM customers")
    customers = [r[0] for r in c.fetchall()]
    
    c.execute("SELECT id, name, price, cost_price FROM products")
    products = {r[0]: {'name': r[1], 'price': r[2], 'cost': r[3]} for r in c.fetchall()}
    
    if not customers or not products:
        print("❌ Error: No base data found. Run seed_data.py first.")
        return

    # Generate 6 Months of intense data (High daily volume)
    # Let's say ~30 transactions per day * 180 days = ~5400 transactions
    # This supplements the existing 15k.
    
    start_date = datetime.now() - timedelta(days=180)
    
    # We will generate day by day to ensure "Realtime" feel (up to today)
    for day_offset in range(180):
        current_day = start_date + timedelta(days=day_offset)
        
        # Weekend Spike
        is_weekend = current_day.weekday() >= 5
        daily_txns = random.randint(40, 60) if is_weekend else random.randint(20, 35)
        
        # Call helper (local version slightly modified for performance? No, use loop)
        # We inline the loop for speed here
        pass # Helper function above is better
        
    # Actually, let's use the helper.
    # To simulate "Realtime", we ensure the last few txns are TODAY
    
    print("   > Backfilling history...")
    generate_transactions(c, customers, products, start_date, n=5000)
    
    print("   > Injecting TODAY'S live traffic...")
    today_start = datetime.now().replace(hour=8, minute=0, second=0)
    generate_transactions(c, customers, products, today_start, n=50) # 50 sales today
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("🚀 Starting Enterprise Data Simulation (6 Months)...")
    seed_suppliers_and_batches()
    seed_staff_and_shifts()
    seed_innovations()
    seed_main_history()
    print("✅ Enterprise Simulation Complete!")
