import database as db
import os

# Get Voltas ID (or any ID using default)
conn = db.get_connection()
c = conn.cursor()
c.execute("SELECT id FROM accounts WHERE company_name LIKE '%Voltas%'")
res = c.fetchone()
conn.close()

if res:
    aid = res[0]
    print(f"Checking branding for Account: {aid}")
    branding = db.get_account_branding(aid)
    print(f"Resolved Logo Path: {branding['logo_path']}")
    
    if "uploads" in branding['logo_path'] and os.path.exists(branding['logo_path']):
        print("✅ SUCCESS: Smart Fallback picked up an uploaded logo!")
    elif branding['logo_path'] == "logo_no_text_1.svg":
        print("⚠️ WARNING: Still using default logo.")
    else:
        print(f"ℹ️ Using configured logo: {branding['logo_path']}")
else:
    print("❌ Voltas account not found")
