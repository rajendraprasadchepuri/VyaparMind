import streamlit as st
import pandas as pd
import database as db
import time
import ui_components as ui

st.set_page_config(page_title="Super Admin", page_icon="🛡️", layout="wide")

# Render Custom Sidebar (Hides native nav, applies theme, restricts links)
ui.render_sidebar()

# --- AUTHENTICATION CHECK ---
def check_access():
    # Allow if role is super_admin OR for demo purposes if username is 'admin' (Change strictly later)
    # For now, let's enforce 'super_admin' role check.
    # If user is not logged in or not super admin, stop.
    
    if 'role' not in st.session_state or st.session_state['role'] != 'super_admin':
        # Backdoor for Dev: If username is 'admin', allow them to elevate to super_admin for this session?
        # No, let's show an access denied screen with a "Switch Mode" button if they are admin.
        
        if st.session_state.get('role') == 'admin':
             st.warning("⚠️ Restricted Access: This area is for Super Admins only.")
             if st.button("Simulate Super Admin Access (Dev)"):
                 st.session_state['role'] = 'super_admin'
                 st.rerun()
             st.stop()
        else:
            st.error("⛔ Access Denied")
            st.stop()

check_access()

# --- TOP HEADER (User + Logout) ---
ui.render_top_header()

# --- DASHBOARD LOGIC ---

st.title("🛡️ Super Admin Dashboard")
st.markdown("Manage Tenants, Subscriptions, and System Health.")

# Tabs
tab_dash, tab_tenants, tab_plans, tab_billing = st.tabs(["📊 Overview", "🏢 Tenant Management", "💎 Manage Plans", "💳 Billing Reports"])

with tab_dash:
    st.header("System Health")
    stats = db.get_system_overview()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Tenants", stats['Total Tenants'])
    c2.metric("Active Tenants", stats['Active Tenants'])
    c3.metric("Global Transactions", stats['Total Transactions'])
    
    st.info("System is running in WAL Mode (Write-Ahead Logging) for performance.")

with tab_tenants:
    st.header("Tenant Management")
    
    # Action Bar
    with st.expander("➕ Onboard New Tenant", expanded=False):
        st.subheader("Onboard New Tenant")
        with st.form("add_tenant_form"):
            new_company = st.text_input("Company Name")
            
            # Dynamic Plans
            plans_df = db.get_all_plans()
            if not plans_df.empty:
                plan_options = plans_df['name'].tolist()
            else:
                plan_options = ["Starter", "Professional", "Enterprise"] # Fallback if no plans defined
                
            new_plan = st.selectbox("Subscription Plan", plan_options)
            
            if st.form_submit_button("Create Tenant"):
                if new_company:
                    success, msg = db.create_tenant(new_company, new_plan)
                    if success:
                        st.success(f"✅ {msg}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                else:
                    st.error(f"❌ {msg}")

    # List Tenants
    accounts = db.fetch_all_accounts()
    
    # Fetch available plans for the dropdown
    all_plans_df = db.get_all_plans()
    try:
        if not all_plans_df.empty:
            available_plans = all_plans_df['name'].tolist()
        else:
            available_plans = ["Starter", "Professional", "Enterprise"]
    except:
        available_plans = ["Starter", "Professional", "Enterprise"]

    for index, row in accounts.iterrows():
        with st.container(border=True):
            cols = st.columns([3, 2, 2, 2, 2])
            cols[0].subheader(row['company_name'])
            cols[0].caption(f"ID: {row['id']}")
            
            # Mutable Plan Selection
            current_plan = row['subscription_plan']
            
            # Ensure current plan is in list (handle legacy data)
            display_plans = list(available_plans)
            if current_plan not in display_plans:
                display_plans.append(current_plan)
                
            try:
                p_idx = display_plans.index(current_plan)
            except:
                p_idx = 0
                
            selected_plan = cols[1].selectbox("Plan", display_plans, index=p_idx, key=f"sel_plan_{row['id']}", label_visibility="collapsed")
            
            # Update Button (Only visible if changed - ideally, but limitations apply. Just show 'Update' button?)
            # Better UX: Small 'Save' button below if we want, or just always show "Update Plan" icon button.
            # Let's use a small primary button for update
            if selected_plan != current_plan:
                 if cols[1].button("💾 Save", key=f"save_plan_{row['id']}", help="Update Subscription Plan"):
                     succ, msg = db.update_tenant_plan(row['id'], selected_plan)
                     if succ:
                         st.success("Updated")
                         time.sleep(0.5)
                         st.rerun()
                     else:
                         st.error("Failed")
            
            cols[2].text("Status")
            status_color = "green" if row['status'] == 'ACTIVE' else "red"
            cols[2].markdown(f":{status_color}[{row['status']}]")
            
            cols[3].text("Actions")
            # Don't show actions for System Account
            is_system = (row['id'] == 'SYS_001' or row['id'] == '1111222233334444' or row['company_name'] == 'VyaparMind System')
            
            if is_system:
                cols[3].info("Protected")
            elif row['status'] == 'ACTIVE':
                if cols[3].button("Suspend", key=f"susp_{row['id']}"):
                    db.update_tenant_status(row['id'], 'SUSPENDED')
                    st.rerun()
            else:
                if cols[3].button("Activate", key=f"act_{row['id']}"):
                    db.update_tenant_status(row['id'], 'ACTIVE')
                    st.rerun()

            cols[4].text("Created")
            cols[4].caption(row['created_at'])


with tab_plans:
    st.header("Manage Subscription Plans")
    st.markdown("Create and manage strict pricing tiers.")
    
    # Constants (Master List of Modules)
    ALL_MODULES = [
        "Inventory", "POS Terminal", "FreshFlow", "VendorTrust", 
        "VoiceAudit", "TableLink", "IsoBar", "ShiftSmart", 
        "GeoViz", "ChurnGuard", "StockSwap", "ShelfSense", "CrowdStock"
    ]
    
    col_p1, col_p2 = st.columns([1, 2], gap="large")
    
    with col_p1:
        with st.container(border=True):
            st.subheader("Manage Plan")
            
            # --- EDIT MODE TOGGLE ---
            current_plans = db.get_all_plans()
            mode = "Add New Plan"
            selected_plan_data = None
            
            if not current_plans.empty:
                plan_names = ["Add New Plan"] + current_plans['name'].tolist()
                mode = st.selectbox("Select Action", plan_names)
                
                if mode != "Add New Plan":
                    selected_plan_data = current_plans[current_plans['name'] == mode].iloc[0]
            
            # --- FORM ---
            with st.form("plan_manager_form"):
                if mode == "Add New Plan":
                    p_name = st.text_input("Plan Name", placeholder="e.g. Gold Tier")
                    p_price = st.number_input("Monthly Price (₹)", min_value=0.0, step=100.0)
                    
                    # Multi-Select Modules
                    p_features = st.multiselect("Included Modules", ALL_MODULES)
                    
                    submitted = st.form_submit_button("Create Plan", use_container_width=True)
                    if submitted:
                        if p_name:
                            feat_str = ",".join(p_features)
                            succ, msg = db.add_plan(p_name, p_price, feat_str)
                            if succ:
                                st.success(msg)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.warning("Plan Name required")
                
                else:
                    # EDIT MODE
                    # Pre-fill data
                    st.info(f"Editing: {mode}")
                    old_name = mode
                    
                    # Parse existing features
                    existing_feats = []
                    if selected_plan_data['features']:
                        existing_feats = str(selected_plan_data['features']).split(',')
                        # Clean whitespace
                        existing_feats = [f.strip() for f in existing_feats if f.strip() in ALL_MODULES]
                    
                    new_name = st.text_input("Plan Name", value=selected_plan_data['name'])
                    new_price = st.number_input("Monthly Price (₹)", min_value=0.0, step=100.0, value=float(selected_plan_data['price']))
                    new_features = st.multiselect("Included Modules", ALL_MODULES, default=existing_feats)
                    
                    submitted = st.form_submit_button("Update Plan", use_container_width=True)
                    if submitted:
                        if new_name:
                            feat_str = ",".join(new_features)
                            succ, msg = db.update_plan(old_name, new_name, new_price, feat_str)
                            
                            if succ:
                                st.success(msg)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.warning("Plan Name required")

    
    with col_p2:
        st.subheader("Active Plans Overview")
        current_plans = db.get_all_plans()
        
        if not current_plans.empty:
            st.dataframe(current_plans, use_container_width=True, hide_index=True)
            
            st.write("---")
            # Separate Delete UI
            c_del1, c_del2 = st.columns([3, 1])
            with c_del1:
                del_plan = st.selectbox("Select Plan to Delete", current_plans['name'].tolist(), key="del_plan_sel")
            with c_del2:
                st.write("") 
                st.write("") 
                if st.button("Delete", type="primary", use_container_width=True):
                     db.delete_plan(del_plan)
                     st.rerun()
        else:
            st.info("No custom plans found. Use the form to add one.")

with tab_billing:
    st.header("Billing & Subscriptions")
    st.markdown("Overview of all active subscriptions and recurring revenue.")
    
    # Mock Billing Data derived from Accounts
    # Real app would fetch from Stripe/Razorpay
    
    if not accounts.empty:
        billing_data = accounts[['company_name', 'subscription_plan', 'status']].copy()
        
        # Price Mapping
        prices = {'Starter': 29, 'Professional': 99, 'Enterprise': 299}
        billing_data['MRR'] = billing_data['subscription_plan'].map(prices)
        
        total_mrr = billing_data[billing_data['status'] == 'ACTIVE']['MRR'].sum()
        
        st.metric("Total MRR (Monthly Recurring Revenue)", f"${total_mrr:,}")
        
        st.dataframe(billing_data, use_container_width=True)
    else:
        st.info("No accounts found.")

