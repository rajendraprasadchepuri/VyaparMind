
import streamlit as st
# Mock Session State BEFORE importing database if it uses top-level session access (it does not, only inside functions)
if "account_id" not in st.session_state:
    st.session_state["account_id"] = 1

import database as db
import pandas as pd
import os

def run_test():
    print("--- Starting Multi-Tenancy Verification ---")
    
    # 1. Create Account A
    # Use generic names to avoid conflicts if re-running (or clear DB)
    import secrets
    suffix = secrets.token_hex(4)
    user_a = f"admin_a_{suffix}"
    user_b = f"admin_b_{suffix}"
    
    res, msg = db.create_company_account(f"Company A {suffix}", user_a, "pass", "a@example.com")
    print(f"Account A ({user_a}) Creation: {msg}")
    
    # 2. Login as A (Get ID)
    res_a = db.verify_user(user_a, "pass")
    if not res_a[0]:
        print(f"LOGIN A FAILED: {res_a[1]}")
        return
    success, role, aid_a, name_a = res_a
    print(f"Login A: ID={aid_a}, Company={name_a}")
    
    # 3. Simulate Session A
    st.session_state["account_id"] = aid_a
    
    # 4. Add Product as A
    db.add_product("Product A Only", "Cat", 100, 50, 10)
    print("Added 'Product A Only' to Account A")
    
    # Verify A sees it
    df_a = db.fetch_all_products()
    print(f"Account A Product Count: {len(df_a)}")
    if len(df_a) >= 1 and "Product A Only" in df_a['name'].values:
        print("-> A sees its product.")
    else:
        print("-> FAILURE: A cannot see its product.")

    # 5. Create Account B
    res, msg = db.create_company_account(f"Company B {suffix}", user_b, "pass", "b@example.com")
    print(f"Account B ({user_b}) Creation: {msg}")
    
    # 6. Login as B
    res_b = db.verify_user(user_b, "pass")
    if not res_b[0]:
        print(f"LOGIN B FAILED: {res_b[1]}")
        return
    success, role, aid_b, name_b = res_b
    print(f"Login B: ID={aid_b}, Company={name_b}")
    
    # 7. Simulate Session B
    st.session_state["account_id"] = aid_b
    
    # 8. Fetch Products as B
    # Clear Cache first to be fair (since we mocked session state change in same process)
    # The cache key depends on args. `fetch_all_products` logic:
    # aid = get_current_account_id() -> returns aid_b
    # _fetch_impl(aid_b) -> Cache Miss -> DB Query -> Returns empty?
    
    # We must ensure cache isn't returning A's data due to some bug
    df_b = db.fetch_all_products()
    print(f"Account B Product Count: {len(df_b)}")
    print("B's Products:")
    print(df_b)
    
    if len(df_b) == 0:
        print("SUCCESS: Data Isolation Verified! Account B sees 0 products.")
    elif "Product A Only" not in df_b['name'].values:
        print("SUCCESS: Data Isolation Verified! B has products but NOT A's.")
    else:
        print("FAILURE: Account B can see Account A's product!")

if __name__ == "__main__":
    db.init_db()
    run_test()
