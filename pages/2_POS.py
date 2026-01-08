import streamlit as st
import database as db
import pandas as pd
import textwrap

import ui_components as ui

st.set_page_config(page_title="VyaparMind POS", layout="wide")
st.title("💳 VyaparMind POS")

ui.render_sidebar()

# Initialize Cart in Session State
if 'cart' not in st.session_state:
    st.session_state.cart = []

def add_to_cart(product_id, name, price, cost, stock, qty, tax_rate=0.0):
    # Check if already in cart
    current_qty_in_cart = sum(item['qty'] for item in st.session_state.cart if item['id'] == product_id)
    
    if current_qty_in_cart + qty > stock:
        st.toast(f"❌ Not enough stock! Available: {stock}", icon="⚠️")
        return

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

# --- Customer Selection (Main Page) ---
selected_customer_id = None
st.write(" ") # Spacer

with st.expander("👤 Customer Details (Optional)", expanded=True):
    # 1. Search by Phone
    c_s1, c_s2 = st.columns([1, 2])
    with c_s1:
        phone_input = st.text_input("Enter Customer Phone", placeholder="e.g. 9876543210")
    
    with c_s2:
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

# Right: Cart & Checkout (Logic only, UI below)

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
    st.subheader("🛒 Current Cart")
    
    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        
        # Calculate Tax Amount per row for display
        cart_df['tax_amount'] = cart_df['total'] * (cart_df['tax_rate'] / 100)
        
        # Group by product
        cart_view = cart_df.groupby(['id', 'name', 'price']).agg({
            'qty': 'sum', 
            'total': 'sum',
            'tax_amount': 'sum'
        }).reset_index()
        
        # Rename for clearer display
        cart_view = cart_view.rename(columns={'tax_amount': 'GST'})
        
        st.dataframe(
            cart_view[['name', 'qty', 'price', 'GST', 'total']],
            column_config={
                "price": st.column_config.NumberColumn("Price", format="₹%.2f"),
                "GST": st.column_config.NumberColumn("GST", format="₹%.2f"),
                "total": st.column_config.NumberColumn("Total", format="₹%.2f")
            },
            hide_index=True,
            use_container_width=True
        )
        
        total_amount = cart_view['total'].sum()
        total_tax_disp = cart_view['GST'].sum()
        
        # ...

            # Pass Customer ID to DB
            txn_id = db.record_transaction(items_to_record, total_amount, potential_profit, customer_id=selected_customer_id)
            
            if txn_id:
                st.success(f"Transaction #{txn_id} Completed Successfully!")
                st.balloons()
                
                # --- Invoice Generation ---
                # Generate HTML Receipt
                cust_info = ""
                if selected_customer_id:
                     cust = db.get_customer_by_phone(phone_input) # Re-fetch to be safe or use cached
                     if cust is not None:
                         cust_info = f"<p>Customer: {cust['name']}<br>Phone: {cust['phone']}</p>"
                
                # Current Date
                from datetime import datetime
                date_str = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
                
                # Fetch Store Settings (No Global Tax Rate anymore)
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
                    logo_html = "" # Fallback if file missing

                # Calculate Tax Per Item
                total_tax_amount = 0
                items_html = ""
                
                for item in items_to_record:
                    # Retrieve tax rate we stored in cart
                    i_tax = item.get('tax_rate', 0.0)
                    i_total = item['total']
                    
                    # Tax Amount for this line item
                    item_tax = i_total * (i_tax / 100)
                    total_tax_amount += item_tax
                    
                    # User requested Amt = (Qty*Rate) + GST
                    item_grand_total = i_total + item_tax
                    
                    items_html += f"<tr><td>{item['name']} <span style='font-size:9px; color:#666;'>({i_tax}%)</span></td><td>{item['qty']}</td><td>₹{item['price']:.2f}</td><td>₹{item_tax:.2f}</td><td>₹{item_grand_total:.2f}</td></tr>"
                
                grand_total = total_amount + total_tax_amount
                
                # GST Split (50% Central, 50% State)
                cgst_amount = total_tax_amount / 2
                sgst_amount = total_tax_amount / 2
                
                gst_line = f"<p style='text-align: center; font-size: 11px; margin-top: -10px;'>GSTIN: {store_gst}</p>" if store_gst else ""
                phone_line = f"<p style='text-align: center; font-size: 11px; margin-top: -10px;'>Ph: {store_phone}</p>" if store_phone else ""
                
                # Fix Indentation using textwrap.dedent
                invoice_html = textwrap.dedent(f"""
                <div style="border: 1px solid #ccc; padding: 20px; width: 300px; font-family: 'Courier New', monospace; background: white; color: black;">
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
                    <p style="text-align: right; font-size: 12px;">Subtotal: ₹{total_amount:.2f}</p>
                    <p style="text-align: right; font-size: 12px;">CGST (50%): ₹{cgst_amount:.2f}</p>
                    <p style="text-align: right; font-size: 12px;">SGST (50%): ₹{sgst_amount:.2f}</p>
                    <p style="text-align: right; font-size: 16px;"><strong>TOTAL: ₹{grand_total:.2f}</strong></p>
                    <hr>
                    <p style="text-align: center; font-size: 10px;">{footer_msg}</p>
                </div>
                """)
                
                # Store in session state to persist after rerun (if we wanted to clear cart but keep bill)
                # For now, let's just show it.
                st.session_state['last_invoice'] = invoice_html
                st.session_state['cart'] = [] # Clear cart
                st.rerun()
            else:
                st.error("Transaction Failed. Check Database.")
    
    # Show Last Invoice if exists (persists until next action)
    if 'last_invoice' in st.session_state and st.session_state['last_invoice']:
        with st.expander("📄 Last Bill / Print", expanded=True):
            st.markdown(st.session_state['last_invoice'], unsafe_allow_html=True)
            # Browser Print Button Hack
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
            
            if st.button("Close Bill"):
                del st.session_state['last_invoice']
                st.rerun()
                
        if c2.button("Clear Cart 🗑️", use_container_width=True):
            clear_cart()
            st.rerun()
            
    else:
        st.info("Cart is empty.")
