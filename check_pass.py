
import sqlite3
import hashlib
import pandas as pd

def check_pass():
    conn = sqlite3.connect('retail_supply_chain.db')
    c = conn.cursor()
    
    # Get stored hash
    c.execute("SELECT password_hash FROM users WHERE username='superadmin'")
    stored_hash = c.fetchone()[0]
    print(f"Stored Hash: {stored_hash}")
    
    candidates = ['admin123', 'admin', 'superadmin', 'password', '123456']
    
    for pwd in candidates:
        h = hashlib.sha256(pwd.encode()).hexdigest()
        if h == stored_hash:
            print(f"MATCH FOUND! Password is: {pwd}")
            return
            
    print("No common password matched.")
    conn.close()

if __name__ == "__main__":
    check_pass()
