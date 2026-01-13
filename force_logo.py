import database as db

# Target Logo
LOGO_PATH = r"assets\uploads\logo_O5SQLRP2SQV2KNLM.png"

conn = db.get_connection()
c = conn.cursor()

# Get Voltas ID
c.execute("SELECT id FROM accounts WHERE company_name LIKE '%Voltas%'")
res = c.fetchone()

if res:
    aid = res[0]
    print(f"Updating Voltas ({aid}) -> {LOGO_PATH}")
    
    c.execute("INSERT INTO settings (account_id, key, value) VALUES (?, 'logo_path', ?) ON CONFLICT(account_id, key) DO UPDATE SET value=excluded.value", (aid, LOGO_PATH))
    conn.commit()
    print("✅ UPDATED")
else:
    print("❌ Voltas account not found")

conn.close()
