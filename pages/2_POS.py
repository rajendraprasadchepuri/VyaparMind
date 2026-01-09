import streamlit as st
import database as db
import pandas as pd
import textwrap

import ui_components as ui

st.set_page_config(page_title="VyaparMind POS", layout="wide")
ui.require_auth()
ui.render_top_header()
st.title("💳 VyaparMind POS")

ui.render_sidebar()


# Initialize Cart in Session State
if 'cart' not in st.session_state:
    st.session_state.cart = []

if 'held_bills' not in st.session_state:
    st.session_state['held_bills'] = []

def add_to_cart(product_id, name, price, cost, stock, qty, tax_rate=0.0):
    # Check total quantity currently in cart for this product
    existing_item_index = next((index for (index, d) in enumerate(st.session_state.cart) if d["id"] == product_id), None)
    current_qty_in_cart = st.session_state.cart[existing_item_index]['qty'] if existing_item_index is not None else 0
    
    if current_qty_in_cart + qty > stock:
        st.toast(f"❌ Not enough stock! Available: {stock}", icon="⚠️")
        return

    if existing_item_index is not None:
        # Update existing item
        st.session_state.cart[existing_item_index]['qty'] += qty
        st.session_state.cart[existing_item_index]['total'] = st.session_state.cart[existing_item_index]['price'] * st.session_state.cart[existing_item_index]['qty']
        st.toast(f"Updated {name} quantity to {st.session_state.cart[existing_item_index]['qty']}", icon="🛒")
    else:
        # Add new item
        st.session_state.cart.append({
            "id": product_id,
            "name": name,
            "price": price,
            "cost": cost,
            "qty": qty,
            "tax_rate": tax_rate,
            "total": price * qty
        })
        st.toast(f"Added {qty} x {name} to cart", icon="🛒")

def clear_cart():
    st.session_state.cart = []

def hold_current_bill(cust_phone=None):
    if not st.session_state.cart:
        st.warning("Cart is empty!")
        return
    
    from datetime import datetime
    bill_data = {
        'id': datetime.now().strftime('%H:%M:%S'),
        'timestamp': datetime.now(),
        'cart': st.session_state.cart,
        'total': sum(i['total'] for i in st.session_state.cart),
        'customer_phone': cust_phone
    }
    st.session_state['held_bills'].append(bill_data)
    st.session_state.cart = []
    if 'last_invoice' in st.session_state:
        del st.session_state['last_invoice']
    st.toast("Bill Held Successfully! ⏸️")
    st.rerun()

# --- Customer Selection (Main Page) ---
selected_customer_id = None
st.write(" ") # Spacer

with st.expander("👤 Customer Details (Optional)", expanded=True):
    # 1. Search by Phone
    c_s1, c_s2 = st.columns([1, 2])
    with c_s1:
        phone_input = st.text_input("Enter Customer Phone", placeholder="e.g. 9876543210", key="pos_cust_phone")
    
    with c_s2:
        st.write("") # Spacer to align with text_input label
        st.write("")
        if phone_input:
            # Search DB
            cust = db.get_customer_by_phone(phone_input)
            
            if cust is not None:
                # Found
                st.success(f"✅ **{cust['name']}** found! (Points: {cust['loyalty_points']})")
                selected_customer_id = int(cust['id'])
            else:
                # Not Found -> Add New
                st.warning("New Customer! Quick Register:")
                with st.form("new_cust_form_pos"):
                    c_n1, c_n2 = st.columns(2)
                    with c_n1:
                        new_name = st.text_input("Name")
                    with c_n2:
                        new_email = st.text_input("Email")
                    
                    st.caption(f"Registering for Phone: {phone_input}")
                    
                    if st.form_submit_button("Create & Tag"):
                        if new_name:
                            success, msg = db.add_customer(new_name, phone_input, new_email)
                            if success:
                                st.success("Created!")
                                st.rerun()
                            else:
                                st.error(msg)
        else:
            st.info("Enter phone number to earn loyalty points.")

# --- Layout ---
col_products, col_cart = st.columns([3, 2])

# Left: Product Selection
with col_products:
    st.subheader("Select Products")
    
    # Reload inventory every time to get fresh stock
    inventory = db.fetch_all_products()
    
    if not inventory.empty:
        # Search
        search = st.text_input("Search Item", placeholder="Barcode or Name...")
        if search:
            inventory = inventory[inventory['name'].str.contains(search, case=False) | inventory['category'].str.contains(search, case=False)]
        
        # Product Grid (using metrics for compact view)
        for _, row in inventory.iterrows():
            with st.container(border=True):
                # Adjusted columns to fit Quantity Input
                c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
                with c1:
                    st.markdown(f"**{row['name']}**")
                    st.caption(f"{row['category']}")
                with c2:
                    st.markdown(f"**₹{row['price']:.2f}**")
                with c3:
                    if row['stock_quantity'] > 0:
                        st.success(f"{row['stock_quantity']} In Stock")
                    else:
                        st.error("Out of Stock")
                
                # New Quantity Input and Add Button
                if row['stock_quantity'] > 0:
                    with c4:
                        # Max defaulted to 10 or stock, whichever is lower? No, let user decide, but cap at stock.
                        qty_val = st.number_input("Qty", min_value=1, max_value=row['stock_quantity'], value=1, step=1, key=f"qty_{row['id']}", label_visibility="collapsed")
                    with c5:
                        if st.button("Add", key=f"add_{row['id']}", use_container_width=True):
                            # Get tax rate, default to 0 if missing
                            tr = row.get('tax_rate', 0.0)
                            if pd.isna(tr): tr = 0.0
                            add_to_cart(row['id'], row['name'], row['price'], row['cost_price'], row['stock_quantity'], qty_val, tr)
    else:
        st.info("No products found.")

# Right Column Start
with col_cart:
    # --- HELD BILLS SECTION ---
    if st.session_state['held_bills']:
        with st.expander(f"⏸️ Held Transactions ({len(st.session_state['held_bills'])})", expanded=False):
            for idx, bill in enumerate(st.session_state['held_bills']):
                c1, c2, c3, c4 = st.columns([1.5, 1.5, 1, 1])
                cust_label = f" | 📞 {bill['customer_phone']}" if bill.get('customer_phone') else ""
                c1.caption(f"🕒 {bill['id']}{cust_label}")
                c2.caption(f"Items: {len(bill['cart'])} | ₹{bill['total']:.0f}")
                
                if c3.button("Resume", key=f"resume_{idx}", use_container_width=True):
                    # Auto-hold current if exists
                    if st.session_state.cart:
                         from datetime import datetime
                         current_hold = {
                            'id': datetime.now().strftime('%H:%M:%S'),
                            'timestamp': datetime.now(),
                            'cart': st.session_state.cart,
                            'total': sum(i['total'] for i in st.session_state.cart),
                            'customer_phone': st.session_state.get('pos_cust_phone')
                         }
                         st.session_state['held_bills'].append(current_hold)
                         st.toast("Auto-held current bill.")
                    
                    st.session_state.cart = bill['cart']
                    # Restore customer phone if exists
                    if bill.get('customer_phone'):
                        st.session_state['pos_cust_phone'] = bill['customer_phone']
                    
                    st.session_state['held_bills'].pop(idx)
                    if 'last_invoice' in st.session_state:
                        del st.session_state['last_invoice']
                    st.rerun()
                    
                if c4.button("❌", key=f"discard_{idx}", help="Discard Hold"):
                    st.session_state['held_bills'].pop(idx)
                    st.rerun()
            st.divider()

    st.subheader("🛒 Current Cart")
    
    if st.session_state.cart:
        # Header for Cart
        col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([2, 1, 1, 1, 0.5])
        with col_h1: st.markdown("**Item**")
        with col_h2: st.markdown("**Price**")
        with col_h3: st.markdown("**Qty**")
        with col_h4: st.markdown("**Total**")
        
        # Display Items with Remove Button
        index_to_remove = None
        
        for i, item in enumerate(st.session_state.cart):
             with st.container(border=True):
                 c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 0.5])
                 with c1: st.write(f"{item['name']}")
                 with c2: st.write(f"₹{item['price']:.2f}")
                 with c3: st.write(f"{item['qty']}")
                 with c4: st.write(f"₹{item['total']:.2f}")
                 with c5:
                     if st.button("🗑️", key=f"del_{i}", help="Remove Item"):
                         index_to_remove = i
        
        # Handle Removal outside loop
        if index_to_remove is not None:
            st.session_state.cart.pop(index_to_remove)
            st.rerun()
        
        # Totals Display
        if st.session_state.cart:
            current_total = sum(item['total'] for item in st.session_state.cart)
            current_tax = sum(item['total'] * (item['tax_rate']/100) for item in st.session_state.cart)
            
            st.write("---")
            st.markdown(f"**Subtotal: ₹{current_total:.2f}**")
            st.markdown(f"**GST: ₹{current_tax:.2f}**")
            st.markdown(f"<h3>Total: ₹{(current_total + current_tax):.2f}</h3>", unsafe_allow_html=True)
            
            # Checkout Section
            st.write("---")
            
            # Loyalty Redemption Logic
            points_to_redeem = 0
            cust_points = 0
            
            if selected_customer_id:
                # Re-fetch latest points to be sure
                cust_data = db.get_customer_by_phone(phone_input)
                if cust_data is not None:
                    cust_points = cust_data['loyalty_points']
                    
                    if cust_points >= 1000:
                        total_payable_pre = current_total + current_tax
                        max_redeem = min(cust_points, int(total_payable_pre))
                        
                        st.info(f"🎉 You have {cust_points} Loyalty Points! (Min 1000 to redeem)")
                        use_points = st.checkbox("Redeem Points?", key="redeem_chk")
                        
                        if use_points:
                            points_to_redeem = st.number_input("Points to Redeem (1 Point = ₹1)", 
                                                             min_value=0, max_value=max_redeem, value=0, step=10)
                            if points_to_redeem > 0:
                                st.success(f"Redeeming {points_to_redeem} points. -₹{points_to_redeem}")

            c1_btn, c2_btn = st.columns(2)
            
            txn_id = None # Initialize to prevent NameError
            
            with c1_btn:
                potential_profit = sum((item['price'] - item['cost']) * item['qty'] for item in st.session_state.cart)
                
                # Show Final Pay
                final_total_pay = (current_total + current_tax) - points_to_redeem
                st.markdown(f"**Net Payable: ₹{final_total_pay:.2f}**")
                
                if st.button("Checkout ✅", use_container_width=True):
                    # Consolidate items for DB
                    from collections import defaultdict
                    grouped_cart = {}
                    for item in st.session_state.cart:
                        pid = item['id']
                        if pid in grouped_cart:
                            grouped_cart[pid]['qty'] += item['qty']
                            grouped_cart[pid]['total'] += item['total']
                        else:
                            grouped_cart[pid] = item.copy()
                            
                    items_to_record = list(grouped_cart.values())
                    total_amt_base = sum(x['total'] for x in items_to_record)
                    
                    # Pass points_redeemed to DB
                    txn_id = db.record_transaction(items_to_record, total_amt_base, potential_profit, 
                                                 customer_id=selected_customer_id, points_redeemed=points_to_redeem)
            
            # Invoice Generation Block
            if txn_id:
                st.success(f"Transaction Recorded! Ref: {txn_id}")
                st.balloons()
                
                cust_info = ""
                if selected_customer_id:
                     cust = db.get_customer_by_phone(phone_input) 
                     if cust is not None:
                         # Fetch new points balance after transaction
                         cust_info = f"<p>Customer: {cust['name']}<br>Phone: {cust['phone']}<br>Points Bal: {cust['loyalty_points']}</p>"
                
                from datetime import datetime
                date_str = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
                
                store_name = db.get_setting('store_name') or "VyaparMind Store"
                store_addr = db.get_setting('store_address') or "Hyderabad, India"
                store_phone = db.get_setting('store_phone') or ""
                store_gst = db.get_setting('store_gst') or ""
                footer_msg = db.get_setting('invoice_footer') or "Thank you for shopping!"
                
                # Logo Logic
                logo_setting = db.get_setting('app_logo') or "Ascending Lotus"
                logo_filename = "logo_no_text_3.svg" if logo_setting == "Ascending Lotus" else "logo_no_text_1.svg"
                
                import base64
                try:
                    with open(logo_filename, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode()
                    logo_html = f'<img src="data:image/svg+xml;base64,{encoded_string}" style="width: 50px; display: block; margin: 0 auto 5px auto;">'
                except:
                    logo_html = "" 

                # Re-consolidate for display consistency
                grouped_cart_disp = {}
                for item in st.session_state.cart:
                     pid = item['id']
                     if pid in grouped_cart_disp:
                         grouped_cart_disp[pid]['qty'] += item['qty']
                         grouped_cart_disp[pid]['total'] += item['total']
                     else:
                         grouped_cart_disp[pid] = item.copy()
                
                items_disp = list(grouped_cart_disp.values())
                
                total_amount_disp = 0
                total_tax_disp = 0
                items_html = ""
                
                for item in items_disp:
                    i_tax = item.get('tax_rate', 0.0)
                    i_total = item['total']
                    item_tax = i_total * (i_tax / 100)
                    total_tax_disp += item_tax
                    item_grand_total = i_total + item_tax
                    total_amount_disp += i_total
                    
                    items_html += f"<tr><td>{item['name']} <span style='font-size:9px; color:#666;'>ID: {item['id']}</span></td><td>{item['qty']}</td><td>₹{item['price']:.2f}</td><td>₹{item_tax:.2f}</td><td>₹{item_grand_total:.2f}</td></tr>"
                
                grand_total_disp = total_amount_disp + total_tax_disp
                cgst_disp = total_tax_disp / 2
                sgst_disp = total_tax_disp / 2
                
                # Adjust finals for Redemption
                final_payable_disp = grand_total_disp - points_to_redeem
                
                gst_line = f"<p style='text-align: center; font-size: 11px; margin-top: -10px;'>GSTIN: {store_gst}</p>" if store_gst else ""
                phone_line = f"<p style='text-align: center; font-size: 11px; margin-top: -10px;'>Ph: {store_phone}</p>" if store_phone else ""
                
                redemption_html = ""
                if points_to_redeem > 0:
                    redemption_html = f"<p style='text-align: right; font-size: 12px; color: green;'>Points Redeemed: -₹{points_to_redeem:.2f}</p>"
                
                # --- REVERTED TO ORIGINAL STYLE WITH RESPONSIVE WIDTH FIX ---
                # Changed width: 450px to width: 100%; max-width: 450px;
                # FLATTENED HTML TO PREVENT MARKDOWN CODE BLOCK RENDERING
                invoice_html = f"""
<div style="border: 1px solid #ccc; padding: 20px; width: 100%; max-width: 450px; font-family: 'Courier New', monospace; background: white; color: black; box-sizing: border-box; overflow-x: hidden; margin: auto;">
{logo_html}
<h3 style="text-align: center; margin: 0;">{store_name}</h3>
<p style="text-align: center; font-size: 12px; margin-bottom: 5px;">{store_addr}</p>
{phone_line}
{gst_line}
<hr>
<p><strong>Receipt #:</strong> {txn_id}<br><strong>Date:</strong> {date_str}</p>
{cust_info}
<hr>
<table style="width: 100%; font-size: 12px; border-collapse: collapse;">
<tr style="border-bottom: 1px dashed black;">
<th style="text-align: left;">Item</th>
<th style="text-align: right;">Qty</th>
<th style="text-align: right;">Rate</th>
<th style="text-align: right;">Tax</th>
<th style="text-align: right;">Amt</th>
</tr>
{items_html}
</table>
<hr>
<p style="text-align: right; font-size: 12px;">Subtotal: ₹{total_amount_disp:.2f}</p>
<p style="text-align: right; font-size: 12px;">CGST (50%): ₹{cgst_disp:.2f}</p>
<p style="text-align: right; font-size: 12px;">SGST (50%): ₹{sgst_disp:.2f}</p>
<p style="text-align: right; font-size: 16px;"><strong>TOTAL: ₹{grand_total_disp:.2f}</strong></p>
{redemption_html}
<p style="text-align: right; font-size: 18px; border-top: 1px solid black; margin-top: 5px; padding-top: 5px;"><strong>NET PAYABLE: ₹{final_payable_disp:.2f}</strong></p>
<hr>
<p style="text-align: center; font-size: 10px;">{footer_msg}</p>
</div>
"""
                
                st.session_state['last_invoice'] = invoice_html
                # Cart retained for review until "Close Bill" or explicit "Clear Cart"
                st.rerun()
    
        # --- Hold / Clear Buttons (Visible if cart not empty) ---
        c_hold, c_clear = st.columns(2)
        with c_hold:
            if st.button("Hold Bill ⏸️", help="Save transaction and clear cart", use_container_width=True):
                hold_current_bill(phone_input)
        
        with c_clear:
            if st.button("Clear Cart 🗑️", type="primary", use_container_width=True):
                clear_cart()
                if 'last_invoice' in st.session_state:
                    del st.session_state['last_invoice']
                st.rerun()

        # Show Last Invoice if exists
        if 'last_invoice' in st.session_state and st.session_state['last_invoice']:
            with st.expander("📄 Last Bill / Print", expanded=True):
                st.markdown(st.session_state['last_invoice'], unsafe_allow_html=True)
                st.markdown("""
                <button onclick="window.print()">🖨️ Print Receipt</button>
                <script>
                function printReceipt() {
                    var printContents = document.querySelector('.element-container:has(h3)').innerHTML;
                    var originalContents = document.body.innerHTML;
                    document.body.innerHTML = printContents;
                    window.print();
                    document.body.innerHTML = originalContents;
                }
                </script>
                """, unsafe_allow_html=True)
                
                if st.button("Close Bill", type="primary"):
                    clear_cart() # Clear cart/transaction on close
                    del st.session_state['last_invoice']
                    st.rerun()
            
    else:
        st.info("Cart is empty.")
