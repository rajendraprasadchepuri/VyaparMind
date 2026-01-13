import database as db
import os

conn = db.get_connection()
c = conn.cursor()

# Get Voltas ID
c.execute("SELECT id, company_name FROM accounts WHERE company_name LIKE '%Voltas%'")
rows = c.fetchall()

print(f"Found {len(rows)} accounts:")
for r in rows:
    print(f"ID: {r[0]}, Name: {r[1]}")

# List latest logos
upload_dir = "assets/uploads"
if os.path.exists(upload_dir):
    files = [os.path.join(upload_dir, f) for f in os.listdir(upload_dir) if "logo" in f]
    files.sort(key=os.path.getmtime, reverse=True)
    print("\nLatest Logos:")
    for f in files[:3]:
        print(f)

conn.close()
