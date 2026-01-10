import streamlit as st
import database as db
import ui_components as ui
import os

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
        # Custom Logo Upload
        uploaded_logo = st.file_uploader("Upload Store Logo (PNG/JPG)", type=['png', 'jpg', 'jpeg', 'svg'])
        if s_logo and s_logo != "Ascending Lotus" and os.path.exists(s_logo):
             st.image(s_logo, width=150, caption="Current Logo")
        
        if st.form_submit_button("Save Changes"):
            s1, m1 = db.update_setting("store_name", new_name)
            s2, m2 = db.update_setting("store_address", new_addr)
            s3, m3 = db.update_setting("store_phone", new_phone)
            
            # Handle Logo Upload
            logo_success = True
            logo_msg = "Success"
            if uploaded_logo:
                try:
                    # Create directory if not exists
                    save_dir = "assets/uploads"
                    os.makedirs(save_dir, exist_ok=True)
                    
                    # Generate filename: logo_{account_id}.ext
                    aid = db.get_current_account_id()
                    ext = uploaded_logo.name.split('.')[-1]
                    filename = f"logo_{aid}.{ext}"
                    filepath = os.path.join(save_dir, filename)
                    
                    with open(filepath, "wb") as f:
                        f.write(uploaded_logo.getbuffer())
                    
                    logo_success, logo_msg = db.update_setting("app_logo", filepath)
                except Exception as e:
                    st.error(f"Failed to save logo file: {e}")
                    logo_success = False

            if s1 and s2 and s3 and logo_success:
                st.success("All settings and logo updated successfully!")
                import time
                time.sleep(1)
                st.rerun()
            else:
                errors = []
                if not s1: errors.append(f"Store Name: {m1}")
                if not s2: errors.append(f"Address: {m2}")
                if not s3: errors.append(f"Phone: {m3}")
                if not logo_success: errors.append(f"Logo: {logo_msg}")
                st.error("Error saving settings:\n" + "\n".join(errors))

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
                res, msg = db.update_setting("subscription_plan", "Starter")
                if res:
                    st.rerun()
                else:
                    st.error(msg)

    with c2:
        st.markdown("### Business")
        st.caption("₹999 / mo")
        st.markdown("- **Everything in Starter**\n- FreshFlow (Expiry)\n- VendorTrust\n- VoiceAudit")
        if current_plan == "Business":
            st.button("Current Plan", disabled=True, key="btn_business")
        else:
            if st.button("Upgrade to Business", key="btn_up_business"):
                res, msg = db.update_setting("subscription_plan", "Business")
                if res:
                    st.balloons()
                    st.rerun()
                else:
                    st.error(msg)

    with c3:
        st.markdown("### Enterprise")
        st.caption("₹2999 / mo")
        st.markdown("- **Everything in Business**\n- AI Forecasting (IsoBar)\n- Staff AI (ShiftSmart)\n- Innovations (ShelfSense, etc)")
        if current_plan == "Enterprise":
            st.button("Current Plan", disabled=True, key="btn_enterprise")
        else:
            if st.button("Upgrade to Enterprise", type="primary", key="btn_up_enterprise"):
                res, msg = db.update_setting("subscription_plan", "Enterprise")
                if res:
                    st.balloons()
                    st.rerun()
                else:
                    st.error(msg)

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
