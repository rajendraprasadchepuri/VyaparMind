
import sqlite3
import hashlib
import pandas as pd

def reset_staff():
    conn = sqlite3.connect('retail_supply_chain.db')
    c = conn.cursor()
    
    user = "staff1"
    new_pass = "staff123"
    pwd_hash = hashlib.sha256(new_pass.encode()).hexdigest()
    
    # 1. Reset Password
    c.execute("UPDATE users SET password_hash = ? WHERE username = ?", (pwd_hash, user))
    if c.rowcount > 0:
        print(f"SUCCESS: Reset password for '{user}' to '{new_pass}'")
        conn.commit()
    else:
        print(f"ERROR: User '{user}' not found!")
        conn.close()
        return

    # 2. Get Login Coordinates (Company Name)
    query = """
        SELECT u.username, a.company_name
        FROM users u
        JOIN accounts a ON u.account_id = a.id
        WHERE u.username = ?
    """
    c.execute(query, (user,))
    res = c.fetchone()
    if res:
        print(f"LOGIN DETAILS -> Username: {res[0]}, Company: {res[1]}")
    else:
        print("Could not fetch company details.")
        
    conn.close()

if __name__ == "__main__":
    reset_staff()
