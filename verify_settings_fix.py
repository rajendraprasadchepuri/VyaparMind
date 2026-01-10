import database as db
import sqlite3

def test_settings():
    print("--- Settings Migration & Save Test ---")
    
    # 1. Trigger init_db to run migrations
    db.init_db()
    
    # 2. Check schema
    conn = db.get_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT account_id, key, value FROM settings LIMIT 1")
        print("PASS: 'settings' table has account_id column.")
    except Exception as e:
        print(f"FAIL: Settings table schema issue: {e}")
    conn.close()
    
    # 3. Test Save/Fetch (Simulating Account 2)
    # Note: We need to mock session state if get_current_account_id depends on it.
    import streamlit as st
    if 'account_id' not in st.session_state:
        st.session_state['account_id'] = 999 
        
    key = "test_setting_key"
    val = "test_value_999"
    
    succ = db.set_setting(key, val)
    if succ:
        print(f"PASS: set_setting returned True.")
    else:
        print(f"FAIL: set_setting returned False.")
        
    read_val = db.get_setting(key)
    if read_val == val:
        print(f"PASS: get_setting returned correct value: {read_val}")
    else:
        print(f"FAIL: get_setting returned wrong value: {read_val}")

if __name__ == "__main__":
    test_settings()
