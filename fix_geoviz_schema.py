
import sqlite3
import pandas as pd
import os

DB_FILE = 'retail_supply_chain.db'

def fix_schema():
    print(f"Checking schema for {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check if column exists
    c.execute("PRAGMA table_info(customers)")
    cols = [row[1] for row in c.fetchall()]
    
    if 'city' not in cols:
        print("Column 'city' missing. Adding it...")
        try:
            c.execute("ALTER TABLE customers ADD COLUMN city TEXT DEFAULT 'Unknown'")
            conn.commit()
            print("Successfully added 'city' column.")
        except Exception as e:
            print(f"Error adding column: {e}")
    else:
        print("Column 'city' already exists.")
        
    conn.close()

if __name__ == "__main__":
    if os.path.exists(DB_FILE):
        fix_schema()
    else:
        print("Database file not found.")
