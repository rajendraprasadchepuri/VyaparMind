import streamlit as st
import database as db
import pandas as pd
from datetime import datetime, timedelta
import ui_components as ui

st.set_page_config(page_title="VendorTrust Control Tower", layout="wide")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("🚚 VendorTrust Control Tower")
st.markdown("Automated Supplier Scoring & Risk Analysis.")

tab1, tab2, tab3 = st.tabs(["📊 Supplier Scorecards", "📝 Purchase Orders", "➕ Add Supplier"])

# --- TAB 1: SCORECARDS ---
with tab1:
    st.subheader("Partner Performance")
    
    suppliers = db.get_all_suppliers()
    
    if not suppliers.empty:
        # Display as cards
        for index, row in suppliers.iterrows():
            with st.container(border=True):
                # Calculate Score
                score = db.get_vendor_scorecard(row['id'])
                
                c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
                with c1:
                    st.subheader(row['name'])
                    st.caption(f"Category: {row['category_specialty']}")
                    st.caption(f"Contact: {row['contact_person']} | 📞 {row['phone']}")
                    
                with c2:
                    st.markdown("**On-Time Rate**")
                    val = score['on_time_rate']
                    color = "green" if val >= 90 else "orange" if val >= 70 else "red"
                    st.markdown(f":{color}[**{val:.1f}%**]")
                    
                with c3:
                    st.markdown("**Quality Score**")
                    q = score['avg_quality']
                    st.markdown(f"⭐ **{q:.1f}/5**")
                    
                with c4:
                    st.markdown("**Risk Assessment**")
                    risk = score['risk']
                    if risk == "Low":
                        st.success("✅ LOW RISK")
                    elif risk == "Medium":
                        st.warning("⚠️ MEDIUM RISK")
                    else:
                        st.error("🚨 HIGH RISK")
    else:
        st.info("No suppliers found. Add one in the 'Add Supplier' tab.")

# --- TAB 2: PURCHASE ORDERS ---
with tab2:
    st.subheader("Manage Orders")
    
    col_l, col_r = st.columns([1, 2])
    
    with col_l:
        st.write("#### Create New PO")
        with st.form("new_po_form"):
            if not suppliers.empty:
                s_list = suppliers['name'].tolist()
                sel_s = st.selectbox("Select Supplier", s_list)
                
                # Risk Warning Logic
                if sel_s:
                    s_id = suppliers[suppliers['name'] == sel_s].iloc[0]['id']
                    score = db.get_vendor_scorecard(s_id)
                    if score['risk'] == "High":
                        st.error(f"⚠️ WARNING: {sel_s} is High Risk! (On-Time: {score['on_time_rate']:.0f}%)")
                    elif score['risk'] == "Medium":
                        st.warning(f"Note: {sel_s} has had recent delays.")
                
                exp_date = st.date_input("Expected Delivery")
                notes = st.text_area("Order Notes / Items")
                
                submitted = st.form_submit_button("Create PO")
                if submitted:
                    success, msg = db.create_purchase_order(int(s_id), exp_date, notes)
                    if success:
                        st.success("PO Created!")
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.warning("Add suppliers first.")
                # Must render button even if disabled/useless to satisfy Streamlit
                st.form_submit_button("Create PO", disabled=True)

    with col_r:
        st.write("#### Open Orders (Receive)")
        open_pos = db.get_open_pos()
        
        if not open_pos.empty:
            for i, row in open_pos.iterrows():
                with st.expander(f"📦 PO #{row['id']} - {row['supplier_name']} (Due: {row['expected_date']})"):
                    st.write(f"**Notes:** {row['notes']}")
                    
                    # Receive Form
                    with st.form(f"recv_{row['id']}"):
                        q_rating = st.slider("Quality Rating (1-5)", 1, 5, 5)
                        if st.form_submit_button("Mark Received"):
                            db.receive_purchase_order(row['id'], q_rating)
                            st.toast("Stock Received & Vendor Rated!", icon="✅")
                            st.rerun()
        else:
            st.info("No pending orders.")

# --- TAB 3: ADD SUPPLIER ---
with tab3:
    st.subheader("Onboard New Vendor")
    with st.form("add_supp_form"):
         n = st.text_input("Company Name")
         c = st.text_input("Contact Person")
         p = st.text_input("Phone Number")
         s = st.selectbox("Specialty", ["General", "Electronics", "Groceries", "Clothing", "Logistics"])
         
         if st.form_submit_button("Add Supplier"):
             if n:
                 success, msg = db.add_supplier(n, c, p, s)
                 if success: 
                     st.success("Supplier Added!")
                 else:
                     st.error(msg)
             else:
                 st.warning("Name required.")
