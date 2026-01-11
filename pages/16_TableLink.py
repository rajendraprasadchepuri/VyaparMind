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

    /* COMPACT LIST TWEAKS - SCOPED TO BORDERED CONTAINERS ONLY */
    /* This targets the vertical block INSIDE a st.container(border=True) 
       preventing global layout collapse */
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
        gap: 0.2rem !important;
    }
    
    /* Reduce Button Margins */
    .stButton button {
        height: auto;
        padding-top: 2px !important;
        padding-bottom: 2px !important;
        margin-top: 2px !important;
    }
    
    /* Reduce Number Input Height */
    .stNumberInput input {
        height: auto;
        padding-top: 2px !important;
        padding-bottom: 2px !important;
    }
    div[data-testid="stNumberInputContainer"] {
        margin-bottom: 0px;
    }
    
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
        font-size: 1.5rem; /* Increased from 1.25 */
        font-weight: 700;
        color: #1f2937;
        margin: 0;
    }
    .kds-badge {
        font-family: 'Inter', sans-serif;
        font-size: 1rem; /* Increased from 0.85 */
        font-weight: 600;
        padding: 5px 12px;
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
        overflow-y: hidden; 
    }
    .kds-item {
        font-family: 'Inter', sans-serif;
        font-size: 1.15rem; /* Increased from 0.95 */
        color: #4b5563;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }
    .kds-qty {
        background: #f3f4f6;
        color: #374151;
        font-weight: 700;
        font-size: 1rem; /* Increased from 0.8 */
        padding: 3px 8px;
        border-radius: 6px;
        margin-right: 10px;
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
# Fetch Enriched Data
floor_data = db.get_enriched_tables()

# --- HEADER & CONTROLS ---
col_head, col_view = st.columns([3, 1], vertical_alignment="center")
col_head.metric("Tables", len(floor_data))
view_mode = col_view.radio("Layout", ["Grid", "Map (Custom)"], horizontal=True, key="view_mode_radio")

# --- MANAGEMENT TOOLS ---
with st.expander("🛠️ Table Operations (Merge/Split)", expanded=False):
    t_opts = {t['label']: t['id'] for t in floor_data}
    
    c_mgr1, c_mgr2 = st.columns(2)
    with c_mgr1:
        st.caption("Merge Tables")
        to_merge = st.multiselect("Select Tables to Join", options=list(t_opts.keys()))
        if st.button("🔗 Merge Selected"):
            if len(to_merge) > 1:
                parent = to_merge[0]
                children = to_merge[1:]
                # Logic: Parent is first.
                parent_id = t_opts[parent]
                child_ids = [t_opts[c] for c in children]
                db.merge_tables(parent_id, child_ids)
                st.toast(f"Merged {', '.join(children)} into {parent}")
                st.rerun()
            else:
                st.error("Select at least 2 tables")
                
    with c_mgr2:
        st.caption("Unmerge")
        merged_tables = [t for t in floor_data if t['merged_with']]
        # Actually unmerge target is usually the CHILD or PARENT?
        # Let's simple unmerge by selecting an Table ID that is a parent or child.
        # Allow selecting ANY table to unmerge relation
        curr_merged_labels = [t['label'] for t in floor_data if t['merged_with']]
        unmerge_tgt = st.selectbox("Select Table to Detach", [""] + curr_merged_labels)
        if st.button("🔓 Unmerge"):
            if unmerge_tgt:
                tid = t_opts[unmerge_tgt]
                db.unmerge_table(tid)
                st.rerun()

st.write("") 

# --- RENDER LOGIC ---

if view_mode == "Grid":
    # Default Grid Logic
    cols = st.columns(4) 
    # Determine iteration order
    display_tables = floor_data
else:
    # Map Logic (6x6 Grid)
    # Create slots
    slots = {} # (x,y) -> table
    for t in floor_data:
        slots[(t['pos_x'], t['pos_y'])] = t
        
    display_tables = [] # Not used directly in grid loop but we construct grid
    st.caption("ℹ️ **Map Mode**: Shows a 6x6 floor plan. Use **Manage -> Update Pos** on a table to place it at a specific (Row, Col). Empty slots show their coordinates.")

# Metrics
occupied = sum(1 for t in floor_data if t['status'] != 'Available')
# available = ... 

# Grid Renderer Wrapper
def render_card(t_data):
    if not t_data: return "" # Empty slot
    
    is_occ = t_data['status'] != 'Available'
    status = t_data['status']
    
    # Styles
    card_class = "bg-free"
    badge_class = "badge-green"
    badge_text = "Free"
    
    if status == 'Occupied':
        card_class = "bg-occupied"
        badge_class = "badge-red"
        badge_text = "Occupied"
    elif status == 'Reserved':
        card_class = "bg-warning" # Or Blue?
        badge_class = "badge-orange" # Use existing classes
        badge_text = "Reserved"
    elif status == 'Bill Requested':
        card_class = "bg-warning"
        badge_class = "badge-orange"
        badge_text = "Bill Req."
        
    # Time Logic
    if is_occ and t_data['start_time']:
        try:
            start = pd.to_datetime(t_data['start_time'])
            now = datetime.utcnow()
            diff = now - start
            mins = int(diff.total_seconds() / 60)
            badge_text += f" ({mins}m)"
        except: pass

    waiter = t_data['waiter_id'] or ""
    waiter_html = f"<div style='font-size:0.8rem; color:#666;'>👤 {waiter}</div>" if waiter else ""
    
    # Merged Logic
    if t_data['merged_with']:
        # Point to parent
        card_class = "bg-occupied" # gray?
        return f"""<div class="kds-card" style="background:#f3f4f6; opacity:0.8;">
             <div class="kds-header"><div class="kds-title">{t_data['label']}</div></div>
             <div class="kds-body" style="height:100px; display:flex; align-items:center; justify-content:center;">
                 Merged 🔗
             </div>
        </div>"""

    # HTML CARD
    # Use one line or textwrap to avoid indentation issues
    html_content = f"""<div class="kds-card {card_class}"><div class="kds-header"><div class="kds-title">{t_data['label']}</div><div class="kds-badge {badge_class}">{badge_text}</div></div>{waiter_html}<div class="kds-body">"""
    
    items = t_data.get('items', [])
    if items:
        for i in items[:3]:
             html_content += f"""<div class="kds-item"><span class="kds-qty">{i['qty']}</span> {i['name']}</div>"""
        if len(items) > 3:
             html_content += f"<div class='kds-item'>+ {len(items)-3} more...</div>"
    elif is_occ:
         html_content += "<div style='color:#ccc; font-size:1.1rem;'>Taking Order...</div>"
    else:
         # Increased Icon and Text Size
         html_content += f"<div style='text-align:center; padding-top:20px; color:#22c55e;'><div style='font-size:3.5rem; margin-bottom:10px;'>🍽️</div><div style='font-size:1.2rem; font-weight:600;'>{t_data['capacity']} Seats</div></div>"
         
    html_content += "</div></div>"
    return html_content

# RENDER LOOP
if view_mode == "Grid":
    cols = st.columns(4)
    for idx, t in enumerate(floor_data):
        with cols[idx % 4]:
            st.markdown(render_card(t), unsafe_allow_html=True)
            # Action Button
            if t['status'] != 'Available' and not t['merged_with']:
                if st.button("Manage", key=f"btn_{t['id']}", use_container_width=True, type="primary"):
                    st.session_state['selected_table'] = t['id']
                    st.session_state['selected_table_label'] = t['label']
                    st.rerun()
            elif not t['merged_with']:
                if st.button("Seat Guests", key=f"seat_{t['id']}", use_container_width=True):
                    db.occupy_table(t['id'])
                    st.rerun()
else:
    # Map Mode (6x6)
    for r in range(6):
        mcols = st.columns(6)
        for c in range(6):
            target = slots.get((c, r)) # x=col, y=row
            with mcols[c]:
                if target:
                    st.markdown(render_card(target), unsafe_allow_html=True)
                    if not target['merged_with']:
                         if target['status'] != 'Available':
                             if st.button("Manage", key=f"mbtn_{target['id']}", use_container_width=True):
                                 st.session_state['selected_table'] = target['id']
                                 st.session_state['selected_table_label'] = target['label']
                                 st.rerun()
                         else:
                             if st.button("Seat", key=f"mseat_{target['id']}", use_container_width=True):
                                 db.occupy_table(target['id'])
                                 st.rerun()
                else:
                    # Empty Slot with Coordinate Label for guidance
                    st.markdown(f"<div style='height:150px; border:1px dashed #e5e7eb; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#e5e7eb; font-size:0.8rem;'>{r},{c}</div>", unsafe_allow_html=True)

# End of Grid Logic - Skip original loop




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
    
    # --- TABLE ACTIONS (Status, Transfer, Layout) ---
    with st.expander("⚙️ Table Actions (Transfer / Status / Layout)", expanded=False):
        c_a1, c_a2, c_a3 = st.columns(3)
        
        with c_a1:
            st.caption("Update Status")
            # Occupied is implicit if viewing this, but allow overriding to special states
            if st.button("Mark Bill Requested", use_container_width=True):
                db.update_table_status(t_id, "Bill Requested")
                st.toast("Table marked as Bill Requested")
                st.rerun()
            if st.button("Mark Reserved", use_container_width=True):
                 db.update_table_status(t_id, "Reserved")
                 st.toast("Table marked as Reserved")
                 st.rerun()

        with c_a2:
            st.caption("Transfer Table")
            new_waiter = st.text_input("New Waiter Name", key=f"waiter_{t_id}")
            if st.button("Transfer"):
                if new_waiter:
                    db.transfer_table(t_id, new_waiter)
                    st.success(f"Transferred to {new_waiter}")
                    st.rerun()
        
        with c_a3:
            st.caption("Edit Map Position")
            # Fetch current pos (need new query or pass in? passing in session state is hard)
            # Just show inputs, default 0
            cx = st.number_input("Grid Row (Y)", 0, 5, 0, key=f"py_{t_id}")
            cy = st.number_input("Grid Col (X)", 0, 5, 0, key=f"px_{t_id}")
            if st.button("Update Pos"):
                db.update_table_position(t_id, cy, cx) # X, Y
                st.toast(f"Moved to ({cy}, {cx})")
                st.rerun()

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
             
        # Add Items Container with Border
        with st.container(border=True):
            for _, prod in inv.iterrows():
                 # Balanced Row: More space for Qty (2.0), less spacer (0.3)
                 # [Name (4), Qty (2), Add (1.2), Spacer (0.3)] - Total ~7.5
                 cc1, cc2, cc3, _ = st.columns([4, 2, 1.2, 0.3], vertical_alignment="center")
                 
                 with cc1:
                     st.write(f"**{prod['name']}** (₹{prod['price']:.0f})")
                 
                 with cc2:
                     qty = st.number_input("Q", 1, 10, 1, key=f"q_{prod['id']}_t", label_visibility="collapsed")
                 
                 with cc3:
                     if st.button("Add", key=f"add_{prod['id']}_t", type="primary"):
                         item_data = {
                             "id": prod['id'],
                             "name": prod['name'],
                             "qty": qty,
                             "price": prod['price'],
                             "cost": prod['cost_price'],
                             "category": prod['category'],
                             "section": db._get_kot_section(prod['category']),
                             # Add Status for KOT
                             "status": "pending", 
                             "total": prod['price'] * qty
                         }
                         db.add_item_to_table(t_id, item_data)
                         st.toast(f"Added {prod['name']}")
                         st.rerun()
    
        st.write("") # Spacer
        if st.button("Close View", use_container_width=True):
            del st.session_state['selected_table']
            st.rerun()

    with c_bill:
        st.subheader("Current Bill")
        if items:
            total_bill = 0
            
            # TABLE BORDER LAYOUT
            with st.container(border=True):
                # Header
                h1, h2, h3, h4 = st.columns([3, 1, 1.5, 0.5])
                h1.markdown("**Item**")
                h2.markdown("**Qty**")
                h3.markdown("**Price**")
                h4.write("")
                st.divider()
                
                for idx, i in enumerate(items):
                    c1, c2, c3, c4 = st.columns([3, 1, 1.5, 0.5], vertical_alignment="center")
                    
                    # Determine Status Icon and Section Badge
                    status = i.get('status', 'pending')
                    section = i.get('section', 'Kitchen')
                    
                    # Status Icons
                    s_icon = "🔴" # Pending
                    if status == 'ordered': s_icon = "👨‍🍳"
                    elif status == 'preparing': s_icon = "🍳"
                    elif status == 'ready': s_icon = "✅"
                    elif status == 'cancelled': s_icon = "❌"
                    
                    # Section Badge
                    sec_emoji = "🍲" if section == "Kitchen" else "🍷" if section == "Bar" else "🍰"
                    
                    with c1:
                        st.write(f"{s_icon} {i['name']}")
                        st.caption(f"{sec_emoji} {section}")
                    with c2:
                        st.write(f"x{i['qty']}")
                    with c3:
                        st.write(f"₹{i['total']:.0f}")
                    with c4:
                        if status == 'pending':
                            if st.button("🗑️", key=f"rem_{t_id}_{idx}", help="Remove", type="tertiary"):
                                db.remove_item_from_table(t_id, idx)
                                st.rerun()
                        elif status != 'cancelled':
                            if st.button("❌", key=f"can_{t_id}_{idx}", help="Cancel KOT", type="tertiary"):
                                db.cancel_table_item(t_id, idx)
                                st.rerun()
                    total_bill += i['total'] if status != 'cancelled' else 0
            
            # KOT CONTROLS
            # Only show if there are pending items? Or always allow sending notes?
            # User wants "Special instructions"
            c_k1, c_k2 = st.columns([2, 1], vertical_alignment="bottom")
            kot_note = c_k1.text_input("Kitchen Note (e.g. Spicy)", key=f"kn_{t_id}", placeholder="msg for chef...")
            
            if c_k2.button("👨‍🍳 Send KOT", use_container_width=True):
                # 1. Filter Pending Items
                pending_items = [x for x in items if x.get('status', 'pending') == 'pending']
                
                if not pending_items:
                    st.warning("No new items to send!")
                else:
                    # 2. Mark as Printed in DB
                    success, msg, order_id = db.mark_items_kot_printed(t_id)
                    
                    if success:
                        # 3. Show Dialog
                        # We pass the user-friendly table Label + Order ID
                        c_user = st.session_state.get('username', 'Staff')
                        ui.show_kot_dialog(pending_items, t_lbl, c_user, kot_note, order_id)
            
            # REPRINT KOT
            if st.button("🔄 Reprint Previous KOT", key=f"rep_{t_id}", use_container_width=True):
                history = db.get_table_kot_history(t_id)
                if history:
                    c_user = st.session_state.get('username', 'Staff')
                    ui.show_kot_dialog(history, t_lbl, c_user, "REPRINT", order_id or "N/A")
                else:
                    st.info("No sent items to reprint.")

            st.markdown("<hr style='margin: 5px 0; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
            
            # --- TAX CALCULATION (5% GST for Food) ---
            # Standard GST for restaurants is often 5%
            tax_rate = 0.05
            tax_amt = total_bill * tax_rate
            grand_total = total_bill + tax_amt
            
            # Display Breakdown
            c_t1, c_t2 = st.columns([4, 1])
            c_t1.write("Subtotal")
            c_t2.write(f"₹{total_bill:.2f}")
            
            c_t1.write("GST (5%)")
            c_t2.write(f"₹{tax_amt:.2f}")
            
            st.divider()
            st.markdown(f"#### Grand Total: ₹{grand_total:.2f}")
            
            # Loyalty Redemption
            points_to_redeem = 0
            if active_customer and active_customer['loyalty_points'] >= 1000:
                 st.info(f"Loyalty Points Available: {active_customer['loyalty_points']}")
                 max_red = min(active_customer['loyalty_points'], int(grand_total))
                 use_pts = st.checkbox("Redeem Points?", key=f"use_pts_{t_id}")
                 if use_pts:
                     points_to_redeem = st.number_input("Points", 0, max_red, 0, step=10, key=f"redeem_{t_id}")
                     st.write(f"**Redeeming: -₹{points_to_redeem}**")
            
            payable = grand_total - points_to_redeem
            if points_to_redeem > 0:
                st.markdown(f"### Net Payable: ₹{payable:.2f}")

            # --- POS FUNCTIONS ---
            c_p1, c_p2 = st.columns(2)
            
            # Payment Mode
            pay_mode = st.radio("Payment Mode", ["CASH", "UPI", "CARD"], horizontal=True)

            if c_p1.button("🖨️ Print Bill", use_container_width=True):
                 # Use Shared Dialog
                 # Tax already calculated above
                 subtotal = total_bill
                 
                 # Add Customer Info to Receipt
                 c_info = f"Table: {t_lbl}"
                 if active_customer:
                     c_info += f" | {active_customer['name']}"

                 ui.show_receipt_dialog(items, payable, subtotal, tax_amt, customer_info=c_info, points_redeemed=points_to_redeem)
            
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



# --- FEEDBACK LOOP ---
if 'last_txn_msg' in st.session_state:
    st.success(st.session_state['last_txn_msg'])
    # Clear it after showing once
    del st.session_state['last_txn_msg']
