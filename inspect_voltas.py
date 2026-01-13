import database as db

conn = db.get_connection()
c = conn.cursor()

# Find the account
c.execute("SELECT id, company_name FROM accounts WHERE company_name LIKE '%Voltas%'")
accounts = c.fetchall()

print("Found Accounts:")
for acc in accounts:
    print(f"ID: {acc[0]} | Name: {acc[1]}")
    
    # Check current settings
    c.execute("SELECT key, value FROM settings WHERE account_id=?", (acc[0],))
    settings = c.fetchall()
    print("  Settings:", settings)

conn.close()
