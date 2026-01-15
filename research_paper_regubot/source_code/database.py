
# Mock Database Interface for Experiment
# This file mimics the 'database.py' in the main app to allow 'nlp_engine' to run standalone.

class Config:
    DB_TYPE = "SQLITE"

config = Config()

def get_connection():
    # Only used if nlp_engine calls it directly, but we monkeypatch in the script
    return None

def get_current_account_id():
    return 1

def fetch_all_products():
    # Placeholder, will be patched
    return []
