import streamlit as st
import database as db
import ui_components as ui
import os
import time

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
                    
                    # Cleanup old logos for this account to ensure clean overwrite
                    # (e.g., if switching from png to jpg)
                    for file in os.listdir(save_dir):
                        if file.startswith(f"logo_{aid}."):
                            try:
                                os.remove(os.path.join(save_dir, file))
                            except:
                                pass

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
        # --- 1. LIST USERS ---
        st.markdown("### Existing Users")
        users_df = db.get_all_account_users()
        if not users_df.empty:
            # Show Permissions column to ensure visibility
            st.dataframe(users_df[['username', 'role', 'email', 'permissions', 'created_at']], use_container_width=True, hide_index=True)
            
            user_list = users_df['username'].tolist()
            current_username = st.session_state.get('username')
            # Filter out self for deletion safety in UI (db has check too)
            manageable_users = [u for u in user_list if u != current_username]
        else:
            st.info("No users found.")
            manageable_users = []

        st.divider()

        # --- 2. MANAGE ACTIONS ---
        col_m1, col_m2 = st.columns(2, gap="large")
        
        with col_m1:
            with st.container(border=True):
                st.markdown("#### ➕ Create New User")
                with st.form("add_user_form"):
                    u_name = st.text_input("Username")
                    u_pass = st.text_input("Password", type="password")
                    u_role = st.selectbox("Role", ["staff", "manager", "admin"])
                    
                    if st.form_submit_button("Create User", type="primary", use_container_width=True):
                        if u_name and u_pass:
                            success, msg = db.create_user(u_name, u_pass, "", role=u_role)
                            if success:
                                st.success(f"User {u_name} created!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.warning("Username and Password required.")

        with col_m2:
            with st.container(border=True):
                st.markdown("#### 🔧 Manage User")
                if manageable_users:
                    selected_user = st.selectbox("Select User", manageable_users)
                    
                    action = st.radio("Action", ["Reset Password", "Delete User", "Manage Access"], horizontal=True)
                    
                    if action == "Reset Password":
                        new_pass = st.text_input("New Password", type="password", key="reset_pass_input")
                        if st.button("Update Password", use_container_width=True):
                            if new_pass:
                                succ, msg = db.admin_reset_password(selected_user, new_pass)
                                if succ:
                                    st.success(f"Password updated for {selected_user}")
                                else:
                                    st.error(msg)
                            else:
                                st.warning("Enter new password")
                                
                    elif action == "Delete User":
                        st.warning(f"Are you sure you want to permanently delete {selected_user}?")
                        if st.button("Confirm Delete", type="primary", use_container_width=True):
                            succ, msg = db.delete_user(selected_user)
                            if succ:
                                st.success(f"User {selected_user} deleted.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(msg)
                                
                    elif action == "Manage Access":
                        st.info("Override default role-based access for this user.")
                        
                        user_row = users_df[users_df['username'] == selected_user].iloc[0]
                        current_perms_str = user_row.get('permissions')
                        
                        default_modules = []
                        if current_perms_str and isinstance(current_perms_str, str):
                            default_modules = [p.strip() for p in current_perms_str.split(',') if p.strip()]
                            
                        # Show available modules strictly based on PLAN
                        current_plan_name = db.get_setting("subscription_plan") or "Starter"
                        
                        # Use TIERS from ui_components for consistency
                        tier_map = ui.TIERS
                        
                        if current_plan_name in tier_map:
                             # Standard Plan
                             allowed_files = tier_map[current_plan_name]
                             if '*' in allowed_files:
                                 # All modules in map
                                 available_modules = list(ui.MODULE_MAP.keys())
                             else:
                                 # Map file basenames back to Feature Names
                                 inv_map = {v: k for k, v in ui.MODULE_MAP.items()}
                                 available_modules = []
                                 for f in allowed_files:
                                     if f in inv_map:
                                         available_modules.append(inv_map[f])
                                     # Basics like Dashboard/Settings are implicit, but 'Dashboard' is in MODULE_MAP
                        else:
                             # Custom Plan (DB)
                             plan_feats = db.get_plan_features(current_plan_name)
                             available_modules = plan_feats
                        
                        # Add basics if missing
                        basics = ["Dashboard", "Settings"]
                        for b in basics:
                            if b not in available_modules:
                                available_modules.append(b)
                                
                        available_modules = sorted(list(set(available_modules)))

                        
                        selected_modules = st.multiselect("Allowed Modules (Limit by Plan)", 
                                                        available_modules, default=[m for m in default_modules if m in available_modules])
                        
                        if st.button("Update Permissions", use_container_width=True):
                            succ, msg = db.update_user_permissions(selected_user, selected_modules)
                            if succ:
                                st.success("Updated!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(msg)
                        
                else:
                    st.info("No other users to manage.")
