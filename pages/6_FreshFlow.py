import streamlit as st
import database as db
import pandas as pd
from datetime import datetime, timedelta
import ui_components as ui

st.set_page_config(page_title="FreshFlow Engine", layout="wide")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("🍏 FreshFlow: Zero-Waste Engine")
st.markdown("Automated Expiry Tracking & Dynamic Pricing to eliminate spoilage.")

tab1, tab2 = st.tabs(["🚀 Command Center", "📦 Batch Ingestion"])

# --- TAB 1: COMMAND CENTER ---
with tab1:
    st.subheader("⚠️ At-Risk Inventory (Expiring Soon)")
    
    # 1. Fetch Expiring Batches (Logic Layer)
    # Default lookahead: 10 days
    days_lookahead = st.slider("Lookahead Days", min_value=1, max_value=30, value=10)
    
    expiring_df = db.get_expiring_batches(days_lookahead)
    
    if not expiring_df.empty:
        # Calculate dynamic discounts
        # Rule: < 2 days = 50%, < 5 days = 30%, < 10 days = 10%
        today = datetime.now().date()
        
        def calculate_discount(expiry_str):
            try:
                exp_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
                days_left = (exp_date - today).days
                if days_left <= 2: return 50
                if days_left <= 5: return 30
                if days_left <= 10: return 10
                return 0
            except:
                return 0

        expiring_df['days_left'] = expiring_df['expiry_date'].apply(lambda x: (datetime.strptime(x, '%Y-%m-%d').date() - today).days)
        expiring_df['suggested_discount'] = expiring_df['expiry_date'].apply(calculate_discount)
        expiring_df['new_price'] = expiring_df['current_price'] * (1 - expiring_df['suggested_discount'] / 100)
        
        # Display Metrics
        col1, col2, col3 = st.columns(3)
        total_risk_value = (expiring_df['quantity'] * expiring_df['cost_price']).sum()
        critical_count = len(expiring_df[expiring_df['days_left'] <= 2])
        
        col1.metric("Total Stock Value at Risk", f"₹{total_risk_value:,.2f}")
        col2.metric("Critical Items (< 48h)", critical_count)
        col3.metric("Batches Flagged", len(expiring_df))
        
        st.divider()
        
        # Actionable Grid
        for index, row in expiring_df.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 2, 2])
                
                with c1:
                    st.markdown(f"**{row['product_name']}**")
                    st.caption(f"Batch: {row['batch_code']}")
                
                with c2:
                    color = "red" if row['days_left'] <= 2 else "orange"
                    st.markdown(f":{color}[**{row['days_left']} Days Left**]")
                    st.caption(f"Exp: {row['expiry_date']}")
                    
                with c3:
                    st.write(f"Qty: {row['quantity']}")
                    st.write(f"Cost: ₹{row['cost_price']}")
                    
                with c4:
                    st.markdown(f"**Recomm: {row['suggested_discount']}% OFF**")
                    st.markdown(f"₹{row['current_price']} ➝ **₹{row['new_price']:.2f}**")
                    
                    if st.button(f"⚡ FLASH SALE ({row['suggested_discount']}%)", key=f"f_{row['id']}"):
                        # Logic to update main product price to this new price
                        # Note: This changes global price. In a complex system we'd have 'batch specific pricing' at POS.
                        # For this MVP, we update the Global Price to clear stock.
                        res = db.update_product(row['product_id'], row['new_price'], row['cost_price'], row['quantity'], 0) # simplified update
                        if res:
                            st.toast(f"Price updated to ₹{row['new_price']:.2f} for clearance!", icon="💸")
                            st.rerun()
                            
    else:
        st.success("✅ No expiring inventory found in this window. Great job!")

# --- TAB 2: BATCH INGESTION ---
with tab2:
    st.subheader("📥 Receive New Batch")
    
    with st.form("batch_form"):
        # Select Product
        products_df = db.fetch_all_products()
        if not products_df.empty:
            prod_names = products_df['name'].tolist()
            selected_name = st.selectbox("Product", prod_names)
            
            c1, c2 = st.columns(2)
            with c1:
                batch_code = st.text_input("Batch Code / Lot Number")
                expiry = st.date_input("Expiry Date")
            with c2:
                qty = st.number_input("Quantity Received", min_value=1, step=1)
                cost = st.number_input("Cost Per Unit (₹)", min_value=0.0, step=0.1)
                
            display_on_board = st.checkbox("High Priority (FreshFlow Board)", value=True)
            
            if st.form_submit_button("Ingest Batch"):
                prod_id = products_df[products_df['name'] == selected_name].iloc[0]['id']
                success, msg = db.add_batch(int(prod_id), batch_code, expiry, int(qty), float(cost))
                if success:
                    st.success(f"Batch {batch_code} ingested!")
                else:
                    st.error(msg)
        else:
            st.warning("Create products in Inventory first.")
