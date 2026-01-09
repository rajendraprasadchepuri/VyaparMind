import streamlit as st
import database as db
import ui_components as ui

st.set_page_config(page_title="Settings", layout="wide")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("⚙️ Settings & Administration")

tab1, tab2, tab3 = st.tabs(["Store Profile", "Subscription Plan", "User Management"])

with tab1:
    st.subheader("Store Details")
    # Fetch existing
    s_name = db.get_setting("store_name") or "VyaparMind Store"
    s_addr = db.get_setting("store_address") or "Hyderabad, India"
    s_phone = db.get_setting("store_phone") or "9876543210"
    s_logo = db.get_setting("app_logo") or "Ascending Lotus"

    with st.form("settings_form"):
        new_name = st.text_input("Store Name", value=s_name)
        new_addr = st.text_input("Address", value=s_addr)
        new_phone = st.text_input("Phone", value=s_phone)
        
        st.markdown("### Branding")
        new_logo = st.selectbox("App Logo Style", ["Ascending Lotus", "Minimal text"], index=0 if s_logo == "Ascending Lotus" else 1)
        
        if st.form_submit_button("Save Changes"):
            db.update_setting("store_name", new_name)
            db.update_setting("store_address", new_addr)
            db.update_setting("store_phone", new_phone)
            db.update_setting("app_logo", new_logo)
            st.success("Settings updated!")
            st.rerun()

with tab2:
    st.subheader("💳 Subscription & Billing")
    
    current_plan = db.get_setting("subscription_plan") or "Starter"
    
    st.info(f"Current Plan: **{current_plan}**")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("### Starter")
        st.caption("Free Forever")
        st.markdown("- POS & Inventory\n- Dashboard")
        if current_plan == "Starter":
            st.button("Current Plan", disabled=True, key="btn_starter")
        else:
            if st.button("Downgrade to Starter", key="btn_down_starter"):
                db.update_setting("subscription_plan", "Starter")
                st.rerun()

    with c2:
        st.markdown("### Business")
        st.caption("₹999 / mo")
        st.markdown("- **Everything in Starter**\n- FreshFlow (Expiry)\n- VendorTrust\n- VoiceAudit")
        if current_plan == "Business":
            st.button("Current Plan", disabled=True, key="btn_business")
        else:
            if st.button("Upgrade to Business", key="btn_up_business"):
                db.update_setting("subscription_plan", "Business")
                st.balloons()
                st.rerun()

    with c3:
        st.markdown("### Enterprise")
        st.caption("₹2999 / mo")
        st.markdown("- **Everything in Business**\n- AI Forecasting (IsoBar)\n- Staff AI (ShiftSmart)\n- Innovations (ShelfSense, etc)")
        if current_plan == "Enterprise":
            st.button("Current Plan", disabled=True, key="btn_enterprise")
        else:
            if st.button("Upgrade to Enterprise", type="primary", key="btn_up_enterprise"):
                db.update_setting("subscription_plan", "Enterprise")
                st.balloons()
                st.rerun()

with tab3:
    st.subheader("👥 User Access Control (RBAC)")
    
    # Check if current user is Admin
    current_role = st.session_state.get('role', 'staff')
    if current_role != 'admin':
        st.error("⛔ Only Admins can manage users.")
    else:
        with st.form("add_user_form"):
            st.markdown("#### Create New Staff User")
            c1, c2 = st.columns(2)
            u_name = c1.text_input("Username")
            u_pass = c2.text_input("Password", type="password")
            u_role = st.selectbox("Role", ["staff", "manager", "admin"])
            
            if st.form_submit_button("Create User"):
                success, msg = db.create_user(u_name, u_pass, "", role=u_role)
                if success:
                    st.success(f"User {u_name} created as {u_role}!")
                else:
                    st.error(msg)
