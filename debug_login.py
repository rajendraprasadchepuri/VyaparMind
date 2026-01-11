
import sqlite3
import pandas as pd
import hashlib

def check_db():
    conn = sqlite3.connect('retail_supply_chain.db')
    c = conn.cursor()
    
    print("--- ACCOUNTS ---")
    df_acc = pd.read_sql_query("SELECT * FROM accounts", conn)
    print(df_acc)
    
    print("\n--- USERS ---")
    df_users = pd.read_sql_query("SELECT username, role, account_id, permissions FROM users WHERE username='superadmin'", conn)
    print(df_users)
    
    # Check Manual password verification
    # Assuming password is 'admin123' (standard default) or whatever user uses.
    # Let's check what hash is stored vs common passwords
    
    print("\n--- TEST LOGIN QUERY ---")
    user = "superadmin"
    company = "VyaparMind System"
    # We don't know the password to hash, but we can check if the JOIN works.
    
    query = """
            SELECT u.role, u.account_id, a.company_name, a.status, u.permissions
            FROM users u 
            JOIN accounts a ON u.account_id = a.id
            WHERE u.username = ? AND a.company_name = ?
        """
    try:
        c.execute(query, (user, company))
        res = c.fetchone()
        print(f"Query Result for '{user}' at '{company}': {res}")
    except Exception as e:
        print(f"Query Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    check_db()
