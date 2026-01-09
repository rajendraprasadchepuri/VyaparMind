import sqlite3
import random
from datetime import datetime, timedelta
import secrets

DB_NAME = "retail_supply_chain.db"

def get_connection():
    return sqlite3.connect(DB_NAME, timeout=30, check_same_thread=False)

# Constants
CITIES = ["Hyderabad", "Warangal", "Karimnagar"]
PRODUCTS = [
    ("Milk (1L)", "Dairy", 60.0, 45.0),
    ("Bread (Whole Wheat)", "Bakery", 40.0, 25.0),
    ("Eggs (12)", "Dairy", 80.0, 60.0),
    ("Rice (5kg)", "Grains", 350.0, 280.0),
    ("Dal (1kg)", "Grains", 120.0, 90.0),
    ("Apple (1kg)", "Produce", 180.0, 140.0),
    ("Banana (1 Dozen)", "Produce", 60.0, 40.0),
    ("Potato (1kg)", "Produce", 40.0, 25.0),
    ("Onion (1kg)", "Produce", 50.0, 30.0),
    ("Thums Up (2L)", "Beverages", 90.0, 70.0),
    ("Maaza (1L)", "Beverages", 65.0, 50.0),
    ("Lays Chips (Classic)", "Snacks", 20.0, 15.0),
    ("Britannia Biscuits", "Snacks", 30.0, 20.0),
    ("Maggi Noodles", "Snacks", 14.0, 10.0),
    ("Colgate Toothpaste", "Personal Care", 110.0, 80.0),
    ("Lux Soap", "Personal Care", 45.0, 30.0),
    ("Surf Excel (1kg)", "Home Care", 150.0, 120.0),
    ("Vim Bar", "Home Care", 20.0, 12.0),
    ("Amul Butter (500g)", "Dairy", 270.0, 240.0),
    ("Coke (Can)", "Beverages", 40.0, 30.0)
]

FIRST_NAMES = ["Raj", "Rahul", "Priya", "Sneha", "Amit", "Kavita", "Suresh", "Ramesh", "Anjali", "Vikram", "Anita", "Sunil", "Deepa", "Vijay", "Seema", "Arjun", "Divya", "Karan", "Meera", "Sanjay"]
LAST_NAMES = ["Reddy", "Rao", "Kumar", "Sharma", "Singh", "Patel", "Gupta", "Naidu", "Chowdhury", "Verma", "Yadav", "Goud", "Reddy", "Rao"] # Heavy on Reddy/Rao for Telangana context

def generate_random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def generate_random_phone():
    return f"9{random.randint(100000000, 999999999)}"

def seed_customers(n=1000):
    print(f"Seeding {n} customers...")
    conn = get_connection()
    c = conn.cursor()
    
    # Check if we already have many customers
    try:
        c.execute("SELECT COUNT(*) FROM customers")
        if c.fetchone()[0] >= n:
            print("Customers already seeded.")
            conn.close()
            return
    except sqlite3.OperationalError:
        # Table might not exist if app never ran? Assume exists.
        pass

    customers = []
    for _ in range(n):
        name = generate_random_name()
        phone = generate_random_phone()
        email = f"{name.lower().replace(' ', '')}{random.randint(1,99)}@example.com"
        # Weighted cities
        city = random.choices(CITIES, weights=[0.5, 0.3, 0.2])[0]
        pincode = "500001" if city == "Hyderabad" else "506001" if city == "Warangal" else "505001"
        customers.append((name, phone, email, city, pincode))
        
    c.executemany("INSERT INTO customers (name, phone, email, city, pincode) VALUES (?, ?, ?, ?, ?)", customers)
    conn.commit()
    conn.close()
    print("Customers seeded.")

def seed_products():
    print("Seeding products...")
    conn = get_connection()
    c = conn.cursor()
    
    try:
        c.execute("SELECT COUNT(*) FROM products")
        if c.fetchone()[0] > 10:
             print("Products already exist. Skipping.")
             conn.close()
             return
    except:
        pass

    prod_data = []
    for p in PRODUCTS:
        tags = []
        name = p[0].lower()
        # Tags for ShelfSense
        if "apple" in name: tags.append('ethylene_producer')
        if "banana" in name: tags.append('ethylene_sensitive')
        if "potato" in name: tags.append('moisture_sensitive')
        if "onion" in name: tags.append('moisture_producer')
        if "beer" in name or "thums" in name or "coke" in name: tags.append('impulse_drink')
        if "chips" in name: tags.append('impulse_snack')
        
        science_tags_str = str(tags) if tags else None
        
        # name, category, price, cost_price, stock, science_tags
        prod_data.append((p[0], p[1], p[2], p[3], random.randint(50, 500), science_tags_str))
        
    c.executemany("INSERT INTO products (name, category, price, cost_price, stock_quantity, science_tags) VALUES (?, ?, ?, ?, ?, ?)", prod_data)
    conn.commit()
    conn.close()
    print("Products seeded.")

def seed_transactions(n=50000):
    print(f"Seeding {n} transactions... (This may take a moment)")
    conn = get_connection()
    c = conn.cursor()
    
    # Check if we already have tons of transactions
    try:
        c.execute("SELECT COUNT(*) FROM transactions")
        if c.fetchone()[0] >= n:
            print("Transactions already seeded.")
            conn.close()
            return
    except:
        pass
    
    # Get Customer IDs
    c.execute("SELECT id FROM customers")
    customer_ids = [r[0] for r in c.fetchall()]
    
    # Get Product IDs
    c.execute("SELECT id, name, price, cost_price FROM products")
    products = {r[0]: {'name': r[1], 'price': r[2], 'cost': r[3]} for r in c.fetchall()}
    product_keys = list(products.keys())

    if not customer_ids or not product_keys:
        print("No customers or products found.")
        conn.close()
        return

    start_date = datetime.now() - timedelta(days=365)
    
    batch_size = 500
    
    for i in range(0, n, batch_size):
        c.execute("BEGIN TRANSACTION")
        for j in range(batch_size):
            if i+j >= n: break
            
            # Weighted Date Generation for "Recent" bias (good for Analytics)
            # 30% data in last 30 days, 70% in rest of year
            if random.random() < 0.3:
                days_offset = random.randint(335, 365)
            else:
                days_offset = random.randint(0, 335)
                
            current_date = start_date + timedelta(days=days_offset)
            
            # Peak Hours (6 PM - 9 PM)
            hour = random.choices([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21], 
                                  weights=[1,1,1,1,1,1,1,1,3,4,3,2])[0]
            current_date = current_date.replace(hour=hour, minute=random.randint(0,59))
            
            cust_id = random.choice(customer_ids)
            
            # Basket Generation
            basket_size = random.randint(1, 6)
            basket_pids = random.choices(product_keys, k=basket_size)
            
            t_amount = 0
            t_profit = 0
            
            # Create txn hash
            txn_hash = secrets.token_hex(8)
            
            # 1. Insert Txn Shell
            c.execute("INSERT INTO transactions (timestamp, total_amount, total_profit, customer_id, transaction_hash) VALUES (?, 0, 0, ?, ?)", (current_date, cust_id, txn_hash))
            tid = c.lastrowid
            
            curr_items = []
            for pid in basket_pids:
                p_info = products[pid]
                qty = random.randint(1, 2)
                price = p_info['price']
                cost = p_info['cost']
                
                t_amount += (price * qty)
                t_profit += ((price - cost) * qty)
                
                curr_items.append((tid, pid, p_info['name'], qty, price, cost))
                
            # 2. Update Txn Totals
            c.execute("UPDATE transactions SET total_amount = ?, total_profit = ? WHERE id = ?", (t_amount, t_profit, tid))
            
            # 3. Insert Lines
            c.executemany("INSERT INTO transaction_items (transaction_id, product_id, product_name, quantity, price_at_sale, cost_at_sale) VALUES (?, ?, ?, ?, ?, ?)", curr_items)
            
        conn.commit()
        if i % 1000 == 0:
            print(f"Committed batch {i}")

    conn.close()
    print("Transactions seeded.")

if __name__ == "__main__":
    seed_products()
    seed_customers(1000)
    seed_transactions(15000) 
