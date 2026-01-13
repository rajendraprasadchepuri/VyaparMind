import database as db
import os
import glob

# 1. Find latest logo
upload_dir = "assets/uploads"
latest_logo = "logo_no_text_1.svg" # DefaultFallback
if os.path.exists(upload_dir):
    files = glob.glob(os.path.join(upload_dir, "*logo*"))
    # Filter for image extensions
    files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.svg'))]
    if files:
        latest_logo = max(files, key=os.path.getmtime)
        # Convert absolute/relative path to relative from repo root for DB
        if os.path.isabs(latest_logo):
            latest_logo = os.path.relpath(latest_logo, os.getcwd())
        print(f"Found latest logo: {latest_logo}")

# 2. Update Database
try:
    conn = db.get_connection()
    c = conn.cursor()
    
    # Get Voltas ID
    c.execute("SELECT id FROM accounts WHERE company_name LIKE '%Voltas%'")
    res = c.fetchone()
    
    if res:
        aid = res[0]
        print(f"Updating Account {aid} (Voltas) with logo: {latest_logo}")
        
        # Upsert logo_path
        # Check if setting exists
        c.execute("SELECT key FROM settings WHERE account_id=? AND key='logo_path'", (aid,))
        if c.fetchone():
            c.execute("UPDATE settings SET value=? WHERE account_id=? AND key='logo_path'", (latest_logo, aid))
        else:
            c.execute("INSERT INTO settings (account_id, key, value) VALUES (?, 'logo_path', ?)", (aid, latest_logo))
            
        conn.commit()
        print("✅ Database updated successfully.")
    else:
        print("❌ Voltas account not found!")
        
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
