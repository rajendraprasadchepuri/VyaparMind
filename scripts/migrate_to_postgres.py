
import sqlite3
import asyncpg
import asyncio
import os

# Configuration
SQLITE_DB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "retail_supply_chain.db"))
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/vyaparmind") # Edit this or set env var

async def migrate():
    print(f"Migrating from {SQLITE_DB} to {POSTGRES_URL}...")
    
    if not os.path.exists(SQLITE_DB):
        print("Source SQLite DB not found.")
        return

    # 1. Connect to Postgres
    try:
        pg = await asyncpg.connect(POSTGRES_URL)
    except Exception as e:
        print(f"Failed to connect to Postgres: {e}")
        print("Ensure DATABASE_URL is set and Postgres is running.")
        return

    # 2. Apply Schema
    schema_path = os.path.join(os.path.dirname(__file__), "..", "migrations", "schema_postgres.sql")
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    print("Applying schema...")
    await pg.execute(schema_sql)
    
    # 3. Transfer Data
    tables = ["accounts", "settings", "products", "customers", "transactions", "transaction_items"]
    
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    for table in tables:
        print(f"Migrating table: {table}...")
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            if not rows:
                continue
                
            columns = rows[0].keys()
            col_names = ",".join(columns)
            placeholders = ",".join([f"${i+1}" for i in range(len(columns))])
            
            # Prepare Query
            insert_query = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
            
            # Batch Insert
            data_to_insert = [tuple(row) for row in rows]
            await pg.executemany(insert_query, data_to_insert)
            
            print(f"  - Copied {len(rows)} rows.")
            
        except Exception as e:
            print(f"Error migrating {table}: {e}")
            
    conn.close()
    await pg.close()
    print("Migration Complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
