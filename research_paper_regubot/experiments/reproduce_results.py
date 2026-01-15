import sys
import os
import sqlite3
import random
import time
import datetime
import difflib

# Add source directory to path to import nlp_engine
source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'source_code'))
sys.path.append(source_path)
print(f"DEBUG: Added {source_path} to sys.path")


# Creating a mock DB module to satisfy nlp_engine imports if it tries to import 'database'
# Since nlp_engine has 'import database as db', we can mock it or ensure it works.
# For isolation, we will create a standalone mocking context here.

class MockDB:
    def __init__(self, conn):
        self.conn = conn
        self.config = type('Config', (), {'DB_TYPE': 'SQLITE'})
    
    def get_connection(self):
        return self.conn
        
    def get_current_account_id(self):
        return 1

    def fetch_all_products(self):
        import pandas as pd
        return pd.read_sql("SELECT * FROM products", self.conn)

# Setup Environment
DB_FILE = "research_experiment.db"
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

conn = sqlite3.connect(DB_FILE)
mock_db = MockDB(conn)

# Inject mock into nlp_engine
# We need to load nlp_engine differently or modify it to accept db dependency.
# Or, simply, since we copied `nlp_engine.py`, let's create a `database.py` stub in source_code.

def setup_database():
    print("[1/4] Setting up Synthetic Database...")
    c = conn.cursor()
    
    # Tables
    c.execute('''CREATE TABLE products (
        id INTEGER PRIMARY KEY, account_id INTEGER, name TEXT, 
        stock_quantity INTEGER, schedule_type TEXT, manufacturer TEXT
    )''')
    
    c.execute('''CREATE TABLE customers (
        id INTEGER PRIMARY KEY, name TEXT, phone TEXT, city TEXT
    )''')
    
    c.execute('''CREATE TABLE transactions (
        id INTEGER PRIMARY KEY, account_id INTEGER, customer_id INTEGER, 
        timestamp DATETIME, doctor_name TEXT, doctor_reg_no TEXT
    )''')
    
    c.execute('''CREATE TABLE transaction_items (
        id INTEGER PRIMARY KEY, transaction_id INTEGER, product_id INTEGER, quantity INTEGER
    )''')
    
    # Data Generation
    # Products (200 items)
    products = []
    drug_names = ["Paracetamol", "Azithromycin", "Alprazolam", "Cough Syrup", "Vitamin C", "Metformin", "Atorvastatin", "Amoxicillin", "Diazepam", "Ibuprofen"]
    suffixes = ["500mg", "250mg", "Syrup", "Tablet", "Gel"]
    
    for i in range(1, 201):
        name = f"{random.choice(drug_names)} {random.choice(suffixes)} {i}"
        sched = random.choices(['H1', 'X', 'Normal'], weights=[15, 5, 80])[0]
        products.append((i, 1, name, random.randint(0, 100), sched, "PharmaCorp"))
        
    c.executemany("INSERT INTO products VALUES (?,?,?,?,?,?)", products)
    
    # Transactions (5000 items)
    print("[2/4] Generating 5,000 Synthetic Transactions...")
    
    doctors = [("Dr. Smith", "REG123"), ("Dr. Jones", "REG456"), ("Dr. Strange", "REG789")]
    
    trans_list = []
    items_list = []
    
    start_date = datetime.date(2025, 1, 1)
    
    for i in range(1, 5001):
        # Random date in 2025
        day_offset = random.randint(0, 364)
        date = start_date + datetime.timedelta(days=day_offset)
        ts = f"{date} 10:00:00"
        
        doc = random.choice(doctors)
        trans_list.append((i, 1, 1, ts, doc[0], doc[1]))
        
        # 1-3 items per transaction
        for _ in range(random.randint(1, 3)):
            pid = random.randint(1, 200)
            items_list.append((None, i, pid, random.randint(1, 5)))
            
    c.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?)", trans_list)
    c.executemany("INSERT INTO transaction_items VALUES (?,?,?,?)", items_list)
    
    conn.commit()
    print("      Database populated successfully.")

def benchmark_query_latency():
    print("\n[3/4] Benchmarking Query Latency (Compliance Report)...")
    
    c = conn.cursor()
    query = '''
        SELECT 
            t.timestamp, t.doctor_name, t.doctor_reg_no, p.name, ti.quantity
        FROM transactions t
        JOIN transaction_items ti ON t.id = ti.transaction_id
        JOIN products p ON ti.product_id = p.id
        WHERE t.account_id = 1
        AND date(t.timestamp) BETWEEN '2025-01-01' AND '2025-01-31'
        AND p.schedule_type IN ('H1', 'X')
    '''
    
    start_time = time.perf_counter()
    # Run 100 times to get average
    iterations = 100
    for _ in range(iterations):
        c.execute(query)
        rows = c.fetchall()
        
    end_time = time.perf_counter()
    avg_time_ms = ((end_time - start_time) / iterations) * 1000
    
    print(f"      Rows fetched: {len(rows)}")
    print(f"      Average Latency: {avg_time_ms:.2f} ms")
    return avg_time_ms

def test_nlp_engine():
    print("\n[4/4] Testing NLP Engine Accuracy...")
    
    # We need to hack the import because nlp_engine expects 'database' module
    # We will create a dummy database.py in source_code
    
    import nlp_engine
    # Monkey patch the db used in nlp_engine
    nlp_engine.db = mock_db
    
    test_cases = [
        # (Input, Expected Action, Expected Product Substring)
        ("Sold 5 Azithromycin", "REMOVE", "Azithromycin"),
        ("Add 100 Paracetamol", "ADD", "Paracetamol"),
        ("Stock of Alprazolam is 50", "SET", "Alprazolam"),
        ("sold ten units of Ibuprofen", "REMOVE", "Ibuprofen"), # Might fail if digits only logic
        ("Remove 2 Diazepam", "REMOVE", "Diazepam"),
        ("Sales return 5 Metformin", "ADD", "Metformin") # 'return' might not be in keywords, let's see
    ]
    
    # Since our DB products have random suffixes, we just check if it finds *something*
    # We need to fetch current product list to ensure valid names
    c = conn.cursor()
    c.execute("SELECT name FROM products")
    all_names = [r[0] for r in c.fetchall()]
    
    # Generate test phrases based on ACTUAL names in DB
    correct = 0
    total = 0
    
    print("      Running 500 iterations...")
    
    for _ in range(500):
        target_name = random.choice(all_names)
        # Simplify name for speech simulation (remove suffix)
        spoken_name = target_name.split()[0] 
        qty = random.randint(1, 10)
        
        # 80% chance of 'sold', 20% 'add'
        if random.random() < 0.8:
            cmd = f"Sold {qty} {spoken_name}"
            expected_action = "REMOVE"
        else:
            cmd = f"Add {qty} {spoken_name}"
            expected_action = "ADD"
            
        res = nlp_engine.parse_voice_command(cmd)
        
        total += 1
        
        # Check Action
        action_match = (res['action'] == expected_action)
        
        # Check Product (Relaxed: Found product must contain the spoken word)
        # e.g. "Paracetamol" matches "Paracetamol 500mg" -> True
        prod_match = (spoken_name in res['product_name']) if res['product_name'] else False
        
        if action_match and prod_match:
            correct += 1
            
    accuracy = (correct / total) * 100
    print(f"      NLP Accuracy: {accuracy:.2f}%")
    return accuracy

if __name__ == "__main__":
    setup_database()
    lat = benchmark_query_latency()
    acc = test_nlp_engine()
    
    with open("experiment_results.txt", "w") as f:
        f.write("ReguBot Experiment Results\n")
        f.write("==========================\n")
        f.write(f"Date: {datetime.datetime.now()}\n")
        f.write(f"Dataset: 5,000 Transactions, 200 Products\n")
        f.write(f"Query Latency (Avg): {lat:.2f} ms\n")
        f.write(f"NLP Accuracy (n=500): {acc:.2f}%\n")
        
    conn.close()
