
import sqlite3

DB_NAME = "retail_supply_chain.db"

def manual_migrate():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    print("Connected to DB.")
    
    # 1. Waiter ID
    try:
        c.execute("ALTER TABLE restaurant_tables ADD COLUMN waiter_id TEXT")
        print("Added waiter_id")
    except Exception as e:
        print(f"waiter_id error (likely exists): {e}")

    # 2. Pos X
    try:
        c.execute("ALTER TABLE restaurant_tables ADD COLUMN pos_x INTEGER DEFAULT 0")
        print("Added pos_x")
    except Exception as e:
        print(f"pos_x error: {e}")

    # 3. Pos Y
    try:
        c.execute("ALTER TABLE restaurant_tables ADD COLUMN pos_y INTEGER DEFAULT 0")
        print("Added pos_y")
    except Exception as e:
        print(f"pos_y error: {e}")

    # 4. Merged With
    try:
        c.execute("ALTER TABLE restaurant_tables ADD COLUMN merged_with TEXT")
        print("Added merged_with")
    except Exception as e:
        print(f"merged_with error: {e}")

    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == "__main__":
    manual_migrate()
