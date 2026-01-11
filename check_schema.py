
import sqlite3

try:
    conn = sqlite3.connect('retail_supply_chain.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    cols = c.fetchall()
    print("Columns in users table:")
    found = False
    for col in cols:
        print(col)
        if col[1] == 'permissions':
            found = True
            
    if not found:
        print("ADDING permissions COLUMN...")
        c.execute("ALTER TABLE users ADD COLUMN permissions TEXT")
        conn.commit()
        print("Column added.")
    else:
        print("Permissions column already exists.")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
