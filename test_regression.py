
import database as db
import pandas as pd
from datetime import datetime, timedelta
import secrets
import os
import streamlit as st
import config
import json

def test_regression():
    print(f"\n🚀 Starting Expanded Regression Testing (Engine: {config.DB_TYPE})...")
    
    # Setup test environment
    if config.DB_TYPE == "SQLITE":
        if os.path.exists(config.SQLITE_DB):
            try:
                os.remove(config.SQLITE_DB)
            except: pass
    
    # Initialize DB (creates tables)
    db.init_db()
    
    # 1. Test Multi-Tenant Account Creation
    company_a = f"TestCorp_A_{secrets.token_hex(4)}"
    company_b = f"TestCorp_B_{secrets.token_hex(4)}"
    
    print(f"Creating Account A: {company_a}")
    succ_a, msg_a = db.create_tenant(company_a, "Starter") # Using updated function name
    assert succ_a, f"Failed A: {msg_a}"
    aid_a = msg_a.split(":")[-1].strip() if ":" in msg_a else "1111222233334444"
    
    print(f"Creating Account B: {company_b}")
    succ_b, msg_b = db.create_tenant(company_b, "Professional")
    assert succ_b, f"Failed B: {msg_b}"
    aid_b = msg_b.split(":")[-1].strip() if ":" in msg_b else "B_ID"

    print(f"Acc A ID: {aid_a}, Acc B ID: {aid_b}")
    assert aid_a != aid_b, "IDs must be unique"

    print("--- Testing Users ---")
    u_succ, u_msg = db.create_user("admin_a", "pass123", "a@test.com", role='admin', override_account_id=aid_a)
    assert u_succ, f"User creation failed: {u_msg}"
    
    res_a = db.verify_user("admin_a", "pass123", company_a) 
    assert res_a[0], f"Login failed for A: {res_a[1]}"
    
    # 3. Test Isolation: Products
    print("--- Testing Products ---")
    db.add_product("Apple_A", "Fruit", 100, 50, 1000, 0, override_account_id=aid_a)
    db.add_product("Apple_B", "Fruit", 200, 100, 500, 0, override_account_id=aid_b)
    
    df_a = db.fetch_all_products(override_account_id=aid_a)
    assert len(df_a) >= 1, f"Store A should have products, found {len(df_a)}"
    p_id_a = df_a[df_a['name'] == 'Apple_A'].iloc[0]['id']
    
    df_b = db.fetch_all_products(override_account_id=aid_b)
    assert len(df_b) >= 1, f"Store B should have products, found {len(df_b)}"
    p_id_b = df_b[df_b['name'] == 'Apple_B'].iloc[0]['id']

    # 4. Test FreshFlow (Batches)
    print("--- Testing FreshFlow (Batches) ---")
    expiry_soon = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
    db.add_batch(p_id_a, "BATCH-A-001", expiry_soon, 100, 45, override_account_id=aid_a)
    
    exp_a = db.get_expiring_batches(days_threshold=10, override_account_id=aid_a)
    assert any(exp_a['batch_code'] == "BATCH-A-001"), "Batch not found in expiring list"
    
    exp_b = db.get_expiring_batches(days_threshold=10, override_account_id=aid_b)
    assert len(exp_b) == 0 or not any(exp_b['batch_code'] == "BATCH-A-001"), "Isolation failed: B sees A's batch"

    # 5. Test Transaction & Stock Deduction
    print("--- Testing Transaction & Stock ---")
    items = [{'id': p_id_a, 'name': 'Apple_A', 'qty': 10, 'price': 100, 'cost': 50}]
    txn_hash = db.record_transaction(items, 1000, 500, override_account_id=aid_a, payment_method="CARD")
    assert txn_hash is not None, "Txn Failed"
    
    df_a_new = db.fetch_all_products(override_account_id=aid_a)
    # 1000 (initial) + 100 (batch) - 10 (txn) = 1090
    a_stock_new = int(df_a_new[df_a_new['id'] == p_id_a].iloc[0]['stock_quantity'])
    print(f"Store A Stock after Txn: {a_stock_new}")
    assert a_stock_new == 1090, f"Store A stock mismatch! Expected 1090, got {a_stock_new}"

    # 6. Test TableLink (Restaurant)
    print("--- Testing TableLink ---")
    # Mock session state for aid_a
    st.session_state['account_id'] = aid_a
    conn = db.get_connection()
    db.create_table_management_tables(conn)
    conn.close()
    
    # Add a table manually for testing
    conn = db.get_connection()
    c = conn.cursor()
    tid = "TAB-TEST-01"
    c.execute(f"INSERT INTO restaurant_tables (id, account_id, label, capacity) VALUES ({db.PLACEHOLDER}, {db.PLACEHOLDER}, 'T1', 4)", (tid, aid_a))
    conn.commit()
    conn.close()
    
    tables = db.get_tables()
    assert any(tables['id'] == tid), "Table creation/retrieval failed"
    
    db.occupy_table(tid)
    tables_post = db.get_tables()
    t_status = tables_post[tables_post['id'] == tid].iloc[0]['status']
    assert t_status == "Occupied", f"Table occupation failed: {t_status}"

    # 7. Test Online Ordering Sync
    print("--- Testing Online Ordering ---")
    ext_id = "SW-1001"
    items_json = [{'name': 'Burger', 'qty': 2}]
    db.sync_online_order("SWIGGY", ext_id, items_json)
    
    pending = db.get_pending_online_orders()
    assert any(p['external_order_id'] == ext_id for _, p in pending.iterrows()), "Online order sync failed"
    sync_id = pending[pending['external_order_id'] == ext_id].iloc[0]['id']
    
    db.update_online_order_status(sync_id, "ACCEPTED")
    accepted = db.get_accepted_online_orders()
    assert any(a['id'] == sync_id for _, a in accepted.iterrows()), "Order status update failed"

    # 8. Test SuperAdmin Dynamic Logic
    print("--- Testing SuperAdmin Logic ---")
    plans = db.get_all_plans()
    assert not plans.empty, "Plans should not be empty"
    assert "Professional" in plans['name'].values, "Professional plan missing"
    
    # Test status update
    db.update_tenant_status(aid_b, "SUSPENDED")
    accs = db.fetch_all_accounts()
    b_status = accs[accs['id'] == aid_b].iloc[0]['status']
    assert b_status == "SUSPENDED", f"Status update failed: {b_status}"

    # 9. Smoke Test: Page Imports
    print("--- Testing Page Imports ---")
    page_files = [f for f in os.listdir("pages") if f.endswith(".py")]
    for page in page_files:
        try:
            with open(os.path.join("pages", page), "r", encoding='utf-8') as f:
                compile(f.read(), page, 'exec')
            print(f"✅ {page}")
        except Exception as e:
            print(f"❌ {page}: {e}")
            raise e

    print("\n✅ COMPREHENSIVE REGRESSION TEST PASSED!")

if __name__ == "__main__":
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True
    try:
        test_regression()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
