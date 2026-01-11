import sqlite3
import database as db
import pandas as pd
from datetime import datetime, timedelta
import secrets
import os
import streamlit as st

def test_regression():
    print("\n🚀 Starting Expanded Regression Testing...")
    
    # Use a separate test database
    test_db = "test_supply_chain.db"
    db.DB_NAME = test_db
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Ensure DB is clean/initialized
    db.init_db()
    
    # 1. Test Multi-Tenant Account Creation
    company_a = f"TestCorp_A_{secrets.token_hex(4)}"
    company_b = f"TestCorp_B_{secrets.token_hex(4)}"
    
    print(f"Creating Account A: {company_a}")
    succ_a, msg_a = db.create_company_account(company_a, "admin_a", "pass123", "a@test.com")
    assert succ_a, f"Failed A: {msg_a}"
    
    print(f"Creating Account B: {company_b}")
    succ_b, msg_b = db.create_company_account(company_b, "admin_b", "pass123", "b@test.com")
    assert succ_b, f"Failed B: {msg_b}"

    # 2. Test Login/Verification
    res_a = db.verify_user("admin_a", "pass123", company_name_check=company_a)
    assert res_a[0], f"Login failed for A: {res_a[1]}"
    aid_a = res_a[2]
    
    res_b = db.verify_user("admin_b", "pass123", company_name_check=company_b)
    assert res_b[0], f"Login failed for B: {res_b[1]}"
    aid_b = res_b[2]
    
    print(f"Acc A ID: {aid_a}, Acc B ID: {aid_b}")
    assert aid_a != aid_b, "IDs must be unique"

    # 3. Test Isolation: Products
    print("--- Testing Products ---")
    db.add_product("Apple_A", "Fruit", 100, 50, 1000, override_account_id=aid_a)
    db.add_product("Apple_B", "Fruit", 200, 100, 500, override_account_id=aid_b)
    
    df_a = db.fetch_all_products(override_account_id=aid_a)
    assert len(df_a) == 1, f"Store A should have 1 product, found {len(df_a)}"
    p_id_a = df_a.iloc[0]['id']
    
    df_b = db.fetch_all_products(override_account_id=aid_b)
    assert len(df_b) == 1, f"Store B should have 1 product, found {len(df_b)}"
    p_id_b = df_b.iloc[0]['id']

    # 4. Test FreshFlow (Batches)
    print("--- Testing FreshFlow (Batches) ---")
    expiry_soon = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
    db.add_batch(p_id_a, "BATCH-A-001", expiry_soon, 100, 45, override_account_id=aid_a)
    
    # Verify A sees the batch
    exp_a = db.get_expiring_batches(days_threshold=10, override_account_id=aid_a)
    assert len(exp_a) == 1, f"Store A should see 1 expiring batch, found {len(exp_a)}"
    assert exp_a.iloc[0]['batch_code'] == "BATCH-A-001"
    
    # Verify B does NOT see A's batch
    exp_b = db.get_expiring_batches(days_threshold=10, override_account_id=aid_b)
    assert len(exp_b) == 0, f"Store B should see 0 expiring batches, found {len(exp_b)}"

    # 5. Test VendorTrust (Suppliers & POs)
    print("--- Testing VendorTrust (Suppliers & POs) ---")
    db.add_supplier("Supplier_A", "Contact A", "1112223333", "Fruits", override_account_id=aid_a)
    db.add_supplier("Supplier_B", "Contact B", "4445556666", "Vegetables", override_account_id=aid_b)
    
    supps_a = db.get_all_suppliers(override_account_id=aid_a)
    assert len(supps_a) == 1, f"Store A should have 1 supplier, found {len(supps_a)}"
    s_id_a = supps_a.iloc[0]['id']
    
    supps_b = db.get_all_suppliers(override_account_id=aid_b)
    assert len(supps_b) == 1, f"Store B should have 1 supplier, found {len(supps_b)}"
    
    # Verify PO creation isolation
    db.create_purchase_order(s_id_a, (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'), "Urgent order", override_account_id=aid_a)
    
    conn = sqlite3.connect(test_db)
    pos_a = conn.execute("SELECT COUNT(*) FROM purchase_orders WHERE account_id = ?", (aid_a,)).fetchone()[0]
    pos_b = conn.execute("SELECT COUNT(*) FROM purchase_orders WHERE account_id = ?", (aid_b,)).fetchone()[0]
    conn.close()
    
    assert pos_a == 1, f"Store A should have 1 PO, found {pos_a}"
    assert pos_b == 0, f"Store B should have 0 POs, found {pos_b}"

    # 6. Test Transaction & Stock Deduction
    print("--- Testing Transaction & Stock ---")
    items = [{'id': p_id_a, 'name': 'Apple_A', 'qty': 10, 'price': 100, 'cost': 50}]
    # Verify payment method usage
    txn_hash = db.record_transaction(items, 1000, 500, override_account_id=aid_a, payment_method="CARD")
    assert txn_hash is not None, "Txn Failed"
    
    # Verify stock deduction for A
    df_a_new = db.fetch_all_products(override_account_id=aid_a)
    # 1000 (initial) + 100 (batch) - 10 (txn) = 1090
    a_stock_new = int(df_a_new.iloc[0]['stock_quantity'])
    print(f"Store A Stock after Txn: {a_stock_new}")
    assert a_stock_new == 1090, f"Store A stock mismatch! Expected 1090, got {a_stock_new}"
    
    # Verify B's stock unchanged (Isolation)
    df_b_new = db.fetch_all_products(override_account_id=aid_b)
    b_stock_new = int(df_b_new.iloc[0]['stock_quantity'])

    print(f"Store B Stock: {b_stock_new}")
    assert b_stock_new == 500, f"Store B stock polluted! Expected 500, got {b_stock_new}"

    # 7. Test User Management Isolation
    print("--- Testing User Management ---")
    db.create_user("staff_a", "pass123", "staff_a@test.com", role='staff', override_account_id=aid_a)
    
    # Verify B cannot see A's user indirectly or create same username in B
    # (Username uniqueness is per-account)
    succ_b_u, msg_b_u = db.create_user("staff_a", "pass456", "staff_b@test.com", role='staff', override_account_id=aid_b)
    assert succ_b_u, f"Account B should be able to have its own 'staff_a', but failed: {msg_b_u}"
    
    # 8. Test ShiftSmart Isolation
    print("--- Testing ShiftSmart Isolation ---")
    db.add_staff("Employee_A", "Cashier", 150, override_account_id=aid_a)
    staff_a_df = db.get_all_staff(override_account_id=aid_a)
    e_id_a = staff_a_df.iloc[0]['id']
    
    # Try to assign A's staff to a shift in a context that might be B (if we didn't have scoping)
    # Try to assign A's staff to a shift in a context that might be B (if we didn't have scoping)
    # This simulates Account B trying to schedule Account A's employee
    succ_shift, msg_shift = db.assign_shift("2026-01-20", "Morning", e_id_a, override_account_id=aid_b)
    assert not succ_shift, "Account B should NOT be able to assign shifts to Account A's staff!"
    print(f"Shift Isolation Verified: {msg_shift}")
    # 9. Test Page Imports (Smoke Test)
    print("--- Testing Page Imports ---")
    page_files = [f for f in os.listdir("pages") if f.endswith(".py")]
    for page in page_files:
        try:
            # We can't easily import streamlits pages as modules because they are scripts,
            # but we can check if they have syntax errors or basic import errors by compiling them.
            with open(os.path.join("pages", page), "r", encoding='utf-8') as f:
                compile(f.read(), page, 'exec')
            print(f"✅ Verified syntax: {page}")
        except Exception as e:
            print(f"❌ Syntax Error in {page}: {e}")
            raise e

    # 10. Test B2B Deals (StockSwap)
    print("--- Testing StockSwap (B2B) ---")
    # This module (13_StockSwap.py) writes to b2b_deals table. 
    # Let's manually verify the table exists and can be written to.
    conn = db.get_connection()
    try:
        conn.execute("INSERT INTO b2b_deals (account_id, store_name, product_name, quantity, price_per_unit) VALUES (?, 'Store A', 'Widget', 10, 5.0)", (aid_a,))
        conn.commit()
    except Exception as e:
        assert False, f"StockSwap DB Error: {e}"
    finally:
        conn.close()
    
    # 11. Test CrowdStock (Campaigns)
    print("--- Testing CrowdStock ---")
    conn = db.get_connection()
    try:
        conn.execute("INSERT INTO crowd_campaigns (account_id, item_name, votes_needed) VALUES (?, 'New Feature', 100)", (aid_a,))
        conn.commit()
    except Exception as e:
        assert False, f"CrowdStock DB Error: {e}"
    finally:
        conn.close()
        
    # 12. Test IsoBar (Daily Context)
    print("--- Testing IsoBar ---")
    succ_iso, msg_iso = db.set_daily_context("2026-01-01", "Sunny", "None") # verify this function uses proper scoping
    # Note: set_daily_context uses get_current_account_id() internally which depends on st.session_state.
    # We set account_id to 1 in __main__, but for multi-tenant we need to fake it if we want to test specific accounts.
    # The existing regression test uses 'override_account_id' param for most functions, 
    # but set_daily_context might not have it. Let's check database.py.
    # Looking at database.py (from context), set_daily_context does NOT take override_account_id.
    # It strictly uses get_current_account_id().
    # So we must mock st.session_state['account_id']
    
    st.session_state['account_id'] = aid_b
    succ_iso_b, msg_iso_b = db.set_daily_context("2026-01-02", "Rainy", "Expo")
    assert succ_iso_b, f"IsoBar Failed for B: {msg_iso_b}"
    
    res_iso = db.get_daily_context("2026-01-02")
    assert res_iso is not None, "Failed to fetch context for B"
    assert res_iso[2] == "Rainy", "Context retrieval mismatch" # weather_tag is index 2?
    # Schema: account_id, date, weather_tag, event_tag, notes. OR date, account_id... 
    # database.py init_db says: CREATE TABLE daily_context (account_id, date, weather_tag...)
    # So index 0=aid, 1=date, 2=weather. Correct.

    # 13. Optimization Verification (Search)
    print("--- Testing Search Optimization ---")
    # Add dummy product for search
    db.add_product("SearchTestItem", "General", 100, 50, 10, 0, override_account_id=aid_a)
    
    # Test fetch_pos_inventory with search
    df = db.fetch_pos_inventory(search_term="SearchTest", limit=10, override_account_id=aid_a)
    assert not df.empty, "Search should return results"
    assert "SearchTestItem" in df['name'].values, "Search result should contain the item"
    
    # Test unrelated search
    df_empty = db.fetch_pos_inventory(search_term="NonExistentThingXYZ", limit=10, override_account_id=aid_a)
    assert df_empty.empty, "Search for non-existent item should be empty"
    print("Optimization Search Verified.")

    print("\n✅ FINAL EXPANDED REGRESSION TEST PASSED!")

if __name__ == "__main__":
    if 'account_id' not in st.session_state:
        st.session_state['account_id'] = 1
    try:
        test_regression()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
