import database as db
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

try:
    conn = db.get_connection()
    df = pd.read_sql("SELECT id, zone_name, account_id FROM cold_zones", conn)
    print("--- ZONES IN DB ---")
    if not df.empty:
        print(df.to_string(index=False))
    else:
        print("Table is empty")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
