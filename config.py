
import os
from dotenv import load_dotenv

load_dotenv()

# --- DATABASE CONFIG ---
# Options: 'SQLITE', 'POSTGRES'
DB_TYPE = os.getenv("DB_TYPE", "SQLITE")

# SQLite Config
SQLITE_DB = "retail_supply_chain.db"

# PostgreSQL Config
PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = os.getenv("PGPORT", "5432")
PG_NAME = os.getenv("PGDATABASE", "vyaparmind")
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASS = os.getenv("PGPASSWORD", "postgres")

# Global Account ID (for Scoped logic)
DEFAULT_ACCOUNT_ID = "9676260340"
