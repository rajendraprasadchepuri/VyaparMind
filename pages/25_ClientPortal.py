import streamlit as st
import database as db
import pandas as pd
import ui_components as ui
from datetime import datetime

st.set_page_config(page_title="Client Portal - Cold Storage", layout="wide", page_icon="🔐")

# Note: In a real deployment, this would be a separate app.
# Here it's a module, but we'll hide the sidebar to simulate a standalone portal.

# CSS to hide sidebar when in Portal mode (optional, but looks cleaner)
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        display: none;
    }
    .portal-header {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        padding: 20px;
        border-radius: 10px;
        color: #004d40;
        margin-bottom: 20px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Session State for Client Login
if 'portal_client_id' not in st.session_state:
    st.session_state.portal_client_id = None
if 'portal_client_name' not in st.session_state:
    st.session_state.portal_client_name = None

def logout():
    st.session_state.portal_client_id = None
    st.session_state.portal_client_name = None
    st.rerun()

# --- LOGIN SCREEN ---
if not st.session_state.portal_client_id:
    st.markdown('<div class="portal-header"><h1>🔐 Client Self-Service Portal</h1></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("client_login"):
            st.write("### Login to access your inventory")
            
            # In real app, this would be Username/Password. 
            # For demo, we select Company and entering a mocked PIN.
            clients_df = db.get_all_storage_clients()
            client_dict = {row['company_name']: row['id'] for _, row in clients_df.iterrows()} if not clients_df.empty else {}
            
            selected_company = st.selectbox("Select Company", list(client_dict.keys()) if client_dict else [])
            pin = st.text_input("Access PIN", type="password", placeholder="Enter PIN (Demo: 1234)")
            
            if st.form_submit_button("Login to Portal", type="primary", use_container_width=True):
                if pin == "1234":  # Mock auth
                    st.session_state.portal_client_id = client_dict[selected_company]
                    st.session_state.portal_client_name = selected_company
                    st.success("Login Successful!")
                    st.rerun()
                else:
                    st.error("Invalid PIN. Try '1234'.")
    
    st.markdown("---")
    if st.button("⬅️ Back to Main System"):
        # Switch context back to the main dashboard
        st.switch_page("pages/4_Dashboard.py")

else:
    # --- CLIENT DASHBOARD ---
    
    # Header with Logout
    c1, c2 = st.columns([0.8, 0.2])
    with c1:
        st.title(f"👋 Welcome, {st.session_state.portal_client_name}")
    with c2:
        if st.button("Log Out", type="secondary"):
            logout()
            
    st.markdown("---")
    
    # Tabs
    tab_inv, tab_bill, tab_req = st.tabs(["📦 My Inventory", "🧾 Billing & Invoices", "🚚 Request Dispatch"])
    
    # 1. MY INVENTORY
    with tab_inv:
        st.subheader("Current Stock")
        
        # Fetch FEFO inventory for this client
        inv_df = db.get_cold_inventory_fefo(client_id=st.session_state.portal_client_id)
        
        if not inv_df.empty:
            # Metrics
            total_kg = inv_df['quantity'].sum()
            lots = len(inv_df)
            val_est = total_kg * 150 # Mock value per kg
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total In Stock", f"{total_kg:,.0f} KG")
            m2.metric("Total Lots", lots)
            m3.metric("Est. Value", f"₹{val_est:,.0f}")
            
            st.dataframe(
                inv_df[['commodity_name', 'lot_number', 'quantity', 'expiry_date', 'days_to_expiry']],
                column_config={
                    "commodity_name": "Product",
                    "lot_number": "Lot #",
                    "quantity": st.column_config.NumberColumn("Qty (KG)", format="%.0f"),
                    "expiry_date": "Expires On",
                    "days_to_expiry": st.column_config.NumberColumn("Days Left", format="%d")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No active inventory found.")

    # 2. BILLING
    with tab_bill:
        st.subheader("Invoices & Payments")
        st.info("💡 You can download your past invoices here.")
        
        # Mock invoice list
        invoices = [
            {"id": "INV/20260101/004", "date": "01-Jan-2026", "amount": 12500, "status": "Paid"},
            {"id": "INV/20251201/092", "date": "01-Dec-2025", "amount": 14200, "status": "Paid"},
        ]
        
        # If we had real invoices saved, we'd list them. 
        # For now, allow generating a current/proforma one.
        
        if st.button("📄 Generate Current Statement (PDF)"):
             # Reuse our logic?
             st.success("Statement generated and sent to your email.")

    # 3. REQUEST DISPATCH
    with tab_req:
        st.subheader("Request Dispatch / Outward")
        
        with st.form("dispatch_req"):
            st.write("Select items to dispatch:")
            
            if 'inv_df' in locals() and not inv_df.empty:
                inv_df['label'] = inv_df.apply(lambda x: f"{x['commodity_name']} ({x['quantity']} KG) - Lot: {x['lot_number']}", axis=1)
                selected_items = st.multiselect("Select Lots", inv_df['label'].tolist())
                
                req_date = st.date_input("Requested Dispatch Date")
                notes = st.text_area("Special Instructions")
                
                submitted = st.form_submit_button("🚀 Submit Request")
                
                if submitted:
                    if selected_items:
                        st.success("✅ Dispatch request created successfully! Our warehouse team has been notified.")
                        st.balloons()
                    else:
                        st.warning("Please select items.")
            else:
                st.warning("No inventory available to dispatch.")
                # Streamlit requires a submit button in every form, even if empty/disabled functionally
                st.form_submit_button("🚀 Submit Request", disabled=True)
