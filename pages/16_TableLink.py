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
# 1. Floor Map (KDS Style)
st.subheader("Live Floor Status")

# --- CUSTOM CSS FOR KDS CARDS (PREMIUM) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    /* Container Tweaks */
    .block-container { padding-top: 2rem; }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #E6E7E8;
        border-radius: 12px;
        padding: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    /* KDS Card Base */
    .kds-card {
        background: white;
        border-radius: 16px;
        border: 1px solid #f0f0f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        padding: 0;
        margin-bottom: 20px;
        transition: all 0.3s ease;
        overflow: hidden;
        position: relative;
    }
    .kds-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.12);
    }

    /* Status Gradients */
    .bg-occupied {
        background: linear-gradient(145deg, #fff5f5 0%, #ffe3e3 100%);
        border-left: 6px solid #ff4d4d;
    }
    .bg-free {
        background: linear-gradient(145deg, #f0fff4 0%, #dcfce7 100%);
        border-left: 6px solid #22c55e;
    }
    .bg-warning {
        background: linear-gradient(145deg, #fffbeb 0%, #fef3c7 100%);
        border-left: 6px solid #f59e0b;
    }

    /* Header Section */
    .kds-header {
        padding: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(0,0,0,0.05);
    }
    .kds-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: #1f2937;
        margin: 0;
    }
    .kds-badge {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .badge-red { background: #fee2e2; color: #991b1b; }
    .badge-green { background: #dcfce7; color: #166534; }
    .badge-orange { background: #fef3c7; color: #92400e; }

    /* Body Section - FIXED HEIGHT FOR ALIGNMENT */
    .kds-body {
        padding: 15px;
        height: 200px;
        overflow-y: hidden; /* Hide overflow for clean look, or auto if needed */
    }
    .kds-item {
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        color: #4b5563;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
    }
    .kds-qty {
        background: #f3f4f6;
        color: #374151;
        font-weight: 700;
        font-size: 0.8rem;
        padding: 2px 6px;
        border-radius: 6px;
        margin-right: 8px;
    }

    /* Footer Section */
    .kds-footer {
        padding: 10px 15px;
        background: rgba(255,255,255,0.5);
        border-top: 1px solid rgba(0,0,0,0.03);
    }
    
    /* Hide Default Streamlit Button Borders for cleaner look if possible, or just use primary */
</style>
""", unsafe_allow_html=True)

# Fetch Enriched Data
floor_data = db.fetch_floor_status()

# Metrics
occupied = sum(1 for t in floor_data if t['status'] == 'Occupied')
available = len(floor_data) - occupied
m1, m2, m3 = st.columns(3)
m1.metric("Available", available)
m2.metric("Occupied", occupied)

st.write("") # Spacer

# Grid Layout
cols = st.columns(4) # 4 Tables per row

for idx, t_data in enumerate(floor_data):
    col_idx = idx % 4
    with cols[col_idx]:
        is_occ = t_data['status'] == 'Occupied'
        
        # Determine Styles
        card_class = "bg-free"
        badge_class = "badge-green"
        badge_text = "Free"
        
        time_str = ""
        mins = 0
        if is_occ:
            card_class = "bg-occupied"
            badge_class = "badge-red"
            
            if t_data['start_time']:
                try:
                    start = pd.to_datetime(t_data['start_time'])
                    now = datetime.now()
                    diff = now - start
                    mins = int(diff.total_seconds() / 60)
                    time_str = f"{mins}m"
                    badge_text = f"⏱️ {time_str}"
                    
                    if mins > 20: 
                        card_class = "bg-warning"
                        badge_class = "badge-orange"
                    if mins > 45:
                        card_class = "bg-occupied" # Back to red for urgency
                        badge_class = "badge-red"
                except:
                    badge_text = "Active"
        
        # HTML CARD
        html_content = f"""<div class="kds-card {card_class}">
    <div class="kds-header">
        <div class="kds-title">{t_data['label']}</div>
        <div class="kds-badge {badge_class}">{badge_text}</div>
    </div>
    <div class="kds-body">"""
        
        # Items Logic
        if is_occ:
            items = t_data.get('items', [])
            if items:
                for i in items[:4]: # Show top 4
                    html_content += f"""<div class="kds-item">
    <span class="kds-qty">{i['qty']}</span> {i['name']}
</div>"""
                if len(items) > 4:
                    html_content += f"<div class='kds-item' style='color:#9ca3af;'>+ {len(items)-4} more...</div>"
            else:
                html_content += "<div class='kds-item' style='color:#9ca3af; font-style:italic;'>No items yet</div>"
        else:
            html_content += f"""<div style="text-align:center; padding-top:20px; color:#22c55e;">
    <div style="font-size:2rem; margin-bottom:5px;">🍽️</div>
    <div style="font-size:0.9rem; font-weight:600;">{t_data['capacity']} Seats</div>
</div>"""
            
        html_content += """</div>
</div>"""
        
        st.markdown(html_content, unsafe_allow_html=True)
        
        # BUTTONS (Native Streamlit Buttons outside HTML)
        # We overlay them visually or just place below because Streamlit can't embed buttons in HTML
        if is_occ:
            if st.button(f"Manage Order", key=f"mng_{t_data['id']}", type="primary", use_container_width=True):
                st.session_state['selected_table'] = t_data['id']
                st.session_state['selected_table_label'] = t_data['label']
                st.rerun()
        else:
            if st.button(f"Seat Guests", key=f"seat_{t_data['id']}", use_container_width=True):
                db.occupy_table(t_data['id'])
                st.rerun()
        
        st.write("") # Margin bottom

# --- RECEIPT DIALOG ---
import textwrap

# --- RECEIPT DIALOG ---
@st.dialog("🧾 Bill Receipt")
def show_receipt_dialog(items, total, t_label, t_id):
    # Professional HTML Receipt
    date_str = datetime.now().strftime('%d-%b-%Y %H:%M:%S')
    import secrets
    receipt_id = secrets.token_hex(4) # Short random ID
    
    # Calculate Subtotal & Tax (Assuming 5% tax included for demo or just showing breakdown)
    tax_amt = total * 0.05
    subtotal = total - tax_amt
    
    # --- CUSTOM LOGO LOGIC ---
    import os
    import base64
    
    # 1. Determine Logo Path (Copy logic from ui_components)
    try:
        logo_choice = db.get_setting('app_logo') or "Ascending Lotus"
    except:
        logo_choice = "Ascending Lotus"

    if logo_choice and logo_choice != "Ascending Lotus" and os.path.exists(logo_choice):
        logo_file = logo_choice
    elif logo_choice == "Ascending Lotus":
         logo_file = "logo_no_text_3.svg"  # Default
    else:
         logo_file = "logo_no_text_1.svg"

    # 2. Encode to Base64
    logo_b64 = ""
    try:
        if os.path.exists(logo_file):
            with open(logo_file, "rb") as image_file:
                logo_b64 = base64.b64encode(image_file.read()).decode()
    except Exception as e:
        st.error(f"Logo error: {e}")

    # 3. Construct Image Tag
    if logo_b64:
        # Check ext for mime type (rudimentary)
        mime = "image/svg+xml" if logo_file.endswith(".svg") else "image/png"
        logo_html = f'<img src="data:{mime};base64,{logo_b64}" style="max-height: 80px; width: auto;">'
    else:
        logo_html = '<span style="font-size: 40px;">🍚</span>'
    
    # Use simple flat strings
    html_bill = f"""
<div style="font-family: 'Courier New', monospace; padding: 20px; background: #fff; color: #000; border: 1px solid #ddd; max-width: 400px; margin: auto;">
<!-- Header -->
<div style="text-align: center; margin-bottom: 20px;">
<div style="display: flex; justify-content: center; margin-bottom: 10px;">
<!-- Logo -->
{logo_html}
</div>
<h2 style="margin: 0; font-weight: bold; font-size: 24px; text-transform: uppercase;">Chings Chinese Restaurant</h2>
<p style="margin: 5px 0; font-size: 12px;">Telephone Colony, Hyderabad, India<br>Ph: 9876543210</p>
</div>

<hr style="border-top: 1px dashed #000; margin: 10px 0;">

<!-- Metadata -->
<div style="font-size: 14px; margin-bottom: 10px;">
<strong>Receipt #:</strong> {receipt_id}<br>
<strong>Date:</strong> {date_str}
</div>

<hr style="border-top: 1px dashed #000; margin: 10px 0;">

<!-- Table -->
<table style="width: 100%; font-size: 14px; border-collapse: collapse;">
<thead>
<tr style="border-bottom: 1px dashed #000;">
<th style="text-align: left; padding: 5px 0;">Item</th>
<th style="text-align: center; padding: 5px 0;">Qty</th>
<th style="text-align: right; padding: 5px 0;">Rate</th>
<th style="text-align: right; padding: 5px 0;">Amt</th>
</tr>
</thead>
<tbody>
"""
    
    for i in items:
        rate = i['total'] / i['qty'] if i['qty'] > 0 else 0
        html_bill += f"""
<tr>
<td style="text-align: left; padding: 5px 0;">{i['name']}</td>
<td style="text-align: center; padding: 5px 0;">{i['qty']}</td>
<td style="text-align: right; padding: 5px 0;">₹{rate:.2f}</td>
<td style="text-align: right; padding: 5px 0;">₹{i['total']:.2f}</td>
</tr>
"""
        
    html_bill += f"""
</tbody>
</table>

<hr style="border-top: 1px dashed #000; margin: 10px 0;">

<!-- Totals -->
<div style="text-align: right; font-size: 14px; line-height: 1.6;">
Subtotal: ₹{subtotal:.2f}<br>
CGST (2.5%): ₹{tax_amt/2:.2f}<br>
SGST (2.5%): ₹{tax_amt/2:.2f}<br>
<div style="font-size: 20px; font-weight: bold; margin-top: 10px;">TOTAL: ₹{total:.2f}</div>
</div>

<hr style="border-top: 2px solid #000; margin: 10px 0;">
<div style="text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 20px;">
NET PAYABLE: ₹{total:.2f}
</div>

<hr style="border-top: 1px dashed #000; margin: 10px 0;">

<div style="text-align: center; font-size: 12px; margin-top: 20px;">
Thank you for dining with us!
</div>
</div>
"""
    
    st.markdown(html_bill, unsafe_allow_html=True)
    
    st.markdown("---")
    st.info("💡 Pro-Tip: Press Ctrl+P to print this popup.")
    
    if st.button("Close Preview", key="close_receipt"):
        st.rerun()

# --- ORDER MODAL / SECTION ---
# --- ORDER MODAL / SECTION ---
if 'selected_table' in st.session_state:
    st.divider()
    t_id = st.session_state['selected_table']
    t_lbl = st.session_state['selected_table_label']
    
    st.markdown(f"## 📝 Order Details: Table {t_lbl}")
    
    # --- CUSTOMER DETAILS (ADDED) ---
    active_customer = None
    points_to_redeem = 0
    cust_phone_key = f"t_cust_phone_{t_id}"

    with st.expander("👤 Customer Details & Loyalty", expanded=True):
        with st.form(f"t_cust_search_{t_id}"):
             tc1, tc2 = st.columns([3, 1], vertical_alignment="bottom")
             phone_val = tc1.text_input("Customer Phone", key=cust_phone_key, placeholder="Enter Phone...")
             if tc2.form_submit_button("Search"):
                 pass
        
        if phone_val:
            cust = db.get_customer_by_phone(phone_val)
            if cust:
                st.success(f"✅ {cust['name']} | Points: {cust['loyalty_points']}")
                active_customer = cust
            else:
                st.warning("Customer not found. Register?")
                with st.form(f"t_cust_reg_{t_id}"):
                    tr1, tr2 = st.columns(2)
                    tn = tr1.text_input("Name")
                    tem = tr2.text_input("Email")
                    if st.form_submit_button("Register"):
                         db.add_customer(tn, phone_val, tem)
                         st.rerun()

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
            
            # Loyalty Redemption
            if active_customer and active_customer['loyalty_points'] >= 1000:
                 st.info(f"Loyalty Points Available: {active_customer['loyalty_points']}")
                 max_red = min(active_customer['loyalty_points'], int(total_bill))
                 use_pts = st.checkbox("Redeem Points?", key=f"use_pts_{t_id}")
                 if use_pts:
                     points_to_redeem = st.number_input("Points", 0, max_red, 0, step=10, key=f"redeem_{t_id}")
                     st.write(f"**Redeeming: -₹{points_to_redeem}**")
            
            payable = total_bill - points_to_redeem
            if points_to_redeem > 0:
                st.markdown(f"### Net Payable: ₹{payable:.2f}")

            # --- POS FUNCTIONS ---
            c_p1, c_p2 = st.columns(2)
            
            # Payment Mode
            pay_mode = st.radio("Payment Mode", ["CASH", "UPI", "CARD"], horizontal=True)

            if c_p1.button("🖨️ Print Bill", use_container_width=True):
                 # Use Shared Dialog
                 tax_amt = total_bill * 0.05
                 subtotal = total_bill - tax_amt
                 
                 # Add Customer Info to Receipt
                 c_info = f"Table: {t_lbl}"
                 if active_customer:
                     c_info += f" | {active_customer['name']}"

                 ui.show_receipt_dialog(items, payable, total_bill, tax_amt, customer_info=c_info, points_redeemed=points_to_redeem)
            
            if c_p2.button("✅ Pay & Close", type="primary", use_container_width=True):
                # 1. Record Transaction using database function
                txn_items = []
                # Convert active record to simple dict for record_transaction if needed
                for x in items:
                     txn_items.append(x)
                
                # We need simple profit calc
                profit = sum((x['price'] - x['cost']) * x['qty'] for x in items)
                
                cid = active_customer['id'] if active_customer else None
                new_txn = db.record_transaction(items, total_bill, profit, payment_method=pay_mode, customer_id=cid, points_redeemed=points_to_redeem)
                
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
