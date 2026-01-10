import sqlite3

def check_schema():
    conn = sqlite3.connect("retail_supply_chain.db")
    c = conn.cursor()
    c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='settings'")
    schema = c.fetchone()
    print(f"Current Settings Schema: {schema[0] if schema else 'Not Found'}")
    conn.close()

if __name__ == "__main__":
    check_schema()
