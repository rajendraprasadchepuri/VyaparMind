
import sqlite3
import pandas as pd

def check_staff():
    conn = sqlite3.connect('retail_supply_chain.db')
    c = conn.cursor()
    
    user = "staff1"
    
    print(f"--- CHECKING USER: {user} ---")
    c.execute("SELECT username, role, account_id, permissions FROM users WHERE username=?", (user,))
    row = c.fetchone()
    if row:
        print(f"Row: {row}")
        perms = row[3]
        print(f"Permissions Raw Type: {type(perms)}")
        print(f"Permissions Raw Value: '{perms}'")
    else:
        print("User not found!")

    # Check if Account is Active
    if row:
        aid = row[2]
        c.execute("SELECT status FROM accounts WHERE id=?", (aid,))
        acc_row = c.fetchone()
        print(f"Account Status: {acc_row}")

    conn.close()

if __name__ == "__main__":
    check_staff()
