import streamlit as st
import database as db
import pandas as pd
import ui_components as ui
import json
from datetime import datetime

st.set_page_config(page_title="TableLink", layout="wide")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("🍽️ TableLink: Restaurant Manager")
st.markdown("Manage seating, track occupancy, and handle table-specific billing.")

# Initialize DB tables if first run
try:
    db.get_tables()
except:
    conn = db.get_connection()
    db.create_table_management_tables(conn)

# --- REFRESH CONTROL ---
c_ref, c_cfg = st.columns([1, 4])
if c_ref.button("🔄 Refresh Floor Map"):
    st.rerun()

with c_cfg.expander("⚙️ Configure Floor Plan (Add/Edit Tables)"):
    tab_add, tab_edit = st.tabs(["Add Table", "Edit Existing"])
    
    with tab_add:
        with st.form("add_table_form"):
            c1, c2 = st.columns(2)
            n_label = c1.text_input("Table Label", placeholder="e.g. Garden-1")
            n_cap = c2.number_input("Capacity", 1, 20, 4)
            if st.form_submit_button("Add Table"):
                if n_label:
                    db.add_restaurant_table(n_label, n_cap)
                    st.success(f"Added {n_label}")
                    st.rerun()
                else:
                    st.error("Label required")

    with tab_edit:
        st.write("Modify Existing Tables")
        all_tables = db.get_tables()
        for i, t_row in all_tables.iterrows():
            ec1, ec2, ec3 = st.columns([2, 2, 1])
            ec1.write(f"**{t_row['label']}**")
            new_cap = ec2.number_input(f"Cap ({t_row['label']})", 1, 20, t_row['capacity'], key=f"ec_{t_row['id']}")
            
            if ec2.button("Update", key=f"upd_{t_row['id']}"):
                 db.update_restaurant_table_capacity(t_row['id'], new_cap)
                 st.toast("Updated")
                 st.rerun()
                 
            if ec3.button("🗑️", key=f"del_{t_row['id']}", help="Delete Table"):
                res, msg = db.delete_restaurant_table(t_row['id'])
                if res:
                    st.success("Deleted")
                    st.rerun()
                else:
                    st.error(msg)

# --- MAIN LAYOUT ---
tables_df = db.get_tables()

# 1. Floor Map
st.subheader("Floor Plan")

# Grid Layout
cols = st.columns(4) # 4 Tables per row

for idx, row in tables_df.iterrows():
    col_idx = idx % 4
    with cols[col_idx]:
        # Card Logic
        status_color = "green" if row['status'] == 'Available' else "red"
        status_icon = "🟢" if row['status'] == 'Available' else "🔴"
        
        with st.container(border=True):
            st.markdown(f"### {row['label']}")
            st.caption(f"Capacity: {row['capacity']} Pax")
            st.markdown(f"**Status**: :{status_color}[{row['status']}]")
            
            if row['status'] == 'Available':
                if st.button(f"Seating {row['label']}", key=f"seat_{row['id']}", use_container_width=True):
                    db.occupy_table(row['id'])
                    st.rerun()
            else:
                if st.button(f"Manage Order 📝", key=f"mng_{row['id']}", type="primary", use_container_width=True):
                    st.session_state['selected_table'] = row['id']
                    st.session_state['selected_table_label'] = row['label']

# --- RECEIPT DIALOG ---
@st.dialog("🧾 Bill Receipt")
def show_receipt_dialog(items, total, t_label, t_id):
    st.markdown(f"### Table: {t_label}")
    st.markdown(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.divider()
    
    # Items
    for i in items:
        st.write(f"{i['name']} x {i['qty']} ... ₹{i['total']:.2f}")
    
    st.divider()
    st.markdown(f"### Total: ₹{total:.2f}")
    st.caption("Tax included where applicable.")
    
    st.markdown("---")
    st.info("💡 Pro-Tip: Press Ctrl+P to print this popup.")
    
    if st.button("Close Preview"):
        st.rerun()

# --- ORDER MODAL / SECTION ---
if 'selected_table' in st.session_state:
    st.divider()
    t_id = st.session_state['selected_table']
    t_lbl = st.session_state['selected_table_label']
    
    st.markdown(f"## 📝 Order Details: Table {t_lbl}")
    
    c_menu, c_bill = st.columns([1.5, 1])
    
    # FETCH ORDERS
    order_id, items = db.get_table_order(t_id)
    
    with c_menu:
        st.subheader("Add Items")
        # Reuse Inventory Search logic
        search = st.text_input("Search Food/Drink", placeholder="e.g. Pasta")
        
        inv = db.fetch_pos_inventory()
        if search:
            inv = inv[inv['name'].str.contains(search, case=False)]
        else:
             inv = inv.head(5) # Show top 5 default
             
        for _, prod in inv.iterrows():
             cc1, cc2, cc3 = st.columns([3, 1, 1])
             cc1.write(f"**{prod['name']}** (₹{prod['price']})")
             qty = cc2.number_input("Q", 1, 10, 1, key=f"q_{prod['id']}_t", label_visibility="collapsed")
             if cc3.button("Add", key=f"add_{prod['id']}_t"):
                 item_data = {
                     "id": prod['id'],
                     "name": prod['name'],
                     "qty": qty,
                     "price": prod['price'],
                     "cost": prod['cost_price'],
                     "total": prod['price'] * qty
                 }
                 db.add_item_to_table(t_id, item_data)
                 st.toast(f"Added {prod['name']}")
                 st.rerun()
    
    with c_bill:
        st.subheader("Current Bill")
        if items:
            total_bill = 0
            for i in items:
                st.write(f"{i['name']} x {i['qty']} = ₹{i['total']:.2f}")
                total_bill += i['total']
            
            st.divider()
            st.write(f"#### Total: ₹{total_bill:.2f}")
            
            # --- POS FUNCTIONS ---
            c_p1, c_p2 = st.columns(2)
            
            # Payment Mode
            pay_mode = st.radio("Payment Mode", ["CASH", "UPI", "CARD"], horizontal=True)

            if c_p1.button("🖨️ Print Bill", use_container_width=True):
                 show_receipt_dialog(items, total_bill, t_lbl, t_id)
            
            if c_p2.button("✅ Pay & Close", type="primary", use_container_width=True):
                # 1. Record Transaction using database function
                txn_items = []
                # Convert active record to simple dict for record_transaction if needed
                for x in items:
                     txn_items.append(x)
                
                # We need simple profit calc
                profit = sum((x['price'] - x['cost']) * x['qty'] for x in items)
                
                # Passing Payment Method logic would require updating db.record_transaction signature or handling it
                # For now using default (CASH) or we accept the limitation of the base function
                # Base function `record_transaction` might handle payment method if we updated it? 
                # Let's check db signature. It defaults to 'CASH' or accepts arg?
                # It accepts: items, total_amount, total_profit, payment_method='CASH'
                
                new_txn = db.record_transaction(items, total_bill, profit, payment_method=pay_mode)
                
                # 2. Free Table
                db.free_table(t_id)
                
                st.session_state['last_txn_msg'] = f"Bill Settled! Txn #{new_txn}"
                del st.session_state['selected_table']
                st.rerun()
                
            if st.button("❌ Cancel / Clear Table"):
                db.free_table(t_id)
                del st.session_state['selected_table']
                st.rerun()
        else:
            st.info("No items yet.")
            if st.button("❌ Release Table"):
                db.free_table(t_id)
                del st.session_state['selected_table']
                st.rerun()

    if st.button("Close View"):
        del st.session_state['selected_table']
        st.rerun()

# --- FEEDBACK LOOP ---
if 'last_txn_msg' in st.session_state:
    st.success(st.session_state['last_txn_msg'])
    # Clear it after showing once
    del st.session_state['last_txn_msg']
