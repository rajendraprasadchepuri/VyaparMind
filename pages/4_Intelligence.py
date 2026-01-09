import streamlit as st
import database as db
import pandas as pd
import plotly.express as px
from datetime import timedelta

import ui_components as ui

st.set_page_config(page_title="VyaparMind AI", layout="wide")
ui.require_auth()
ui.render_top_header()
st.title("🧠 VyaparMind Intelligence")

ui.render_sidebar()

conn = db.get_connection()
transactions = pd.read_sql_query("SELECT * FROM transactions", conn)
items = pd.read_sql_query("SELECT * FROM transaction_items", conn)
products = pd.read_sql_query("SELECT * FROM products", conn)
conn.close()

if not transactions.empty:
    transactions['timestamp'] = pd.to_datetime(transactions['timestamp'])

    # --- 1. Smart Restock Recommendations ---
    st.header("🚨 Smart Restock Recommendations")
    
    # Calculate daily sales velocity per product
    # Get first and last sale date to determine active period
    first_sale = transactions['timestamp'].min()
    last_sale = transactions['timestamp'].max()
    days_active = (last_sale - first_sale).days + 1
    
    velocity = items.groupby('product_id').agg({'quantity': 'sum'}).reset_index()
    velocity['daily_rate'] = velocity['quantity'] / max(days_active, 1) # avoid div by zero
    
    # Merge with current stock
    analysis = pd.merge(products, velocity, left_on='id', right_on='product_id', how='left')
    analysis['daily_rate'] = analysis['daily_rate'].fillna(0)
    
    # Metric: Days of Cover = Stock / Daily Rate
    # Handle Infinite case (zero sales) -> High cover
    analysis['days_cover'] = analysis.apply(
        lambda x: x['stock_quantity'] / x['daily_rate'] if x['daily_rate'] > 0 else 999, axis=1
    )
    
    # Recommendation Logic: If cover < 7 days, REORDER
    restock_needed = analysis[analysis['days_cover'] < 7].sort_values('days_cover')
    
    if not restock_needed.empty:
        st.warning(f"Found {len(restock_needed)} items needing immediate attention.")
        
        # Display nicely
        display_df = restock_needed[['name', 'stock_quantity', 'daily_rate', 'days_cover']].copy()
        display_df['recommended_order'] = (display_df['daily_rate'] * 14) - display_df['stock_quantity'] # Aim for 14 days cover
        display_df['recommended_order'] = display_df['recommended_order'].apply(lambda x: max(10, int(x))) # Min order 10
        
        st.dataframe(
            display_df,
            column_config={
                "daily_rate": st.column_config.NumberColumn("Avg Sales/Day", format="%.1f"),
                "days_cover": st.column_config.NumberColumn("Days Left", format="%.1f days"),
                "recommended_order": st.column_config.NumberColumn("Suggested Order Qty", format="%d pcs")
            },
            use_container_width=True
        )
    else:
        st.success("✅ Inventory levels look healthy! No immediate restocks needed.")

    st.divider()

    # --- 2. Market Basket Analysis (Simplified) ---
    st.header("🛍️ Combo Opportunities (Affinity Analysis)")
    
    # Find transactions with > 1 item
    txn_item_counts = items['transaction_id'].value_counts()
    multi_item_txns = txn_item_counts[txn_item_counts > 1].index
    
    if len(multi_item_txns) > 0:
        relevant_items = items[items['transaction_id'].isin(multi_item_txns)]
        
        # Self join to find pairs
        merged = pd.merge(relevant_items, relevant_items, on='transaction_id')
        # Filter out same item pairs and mirror duplicates (keep A < B)
        pairs = merged[merged['product_name_x'] < merged['product_name_y']]
        
        if not pairs.empty:
            combo_counts = pairs.groupby(['product_name_x', 'product_name_y']).size().reset_index(name='frequency')
            combo_counts = combo_counts.sort_values('frequency', ascending=False).head(10)
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write("**Frequently Bought Together**")
                st.table(combo_counts)
            
            with c2:
                # Network graph or similar visual could go here, for now a bar chart
                combo_counts['pair'] = combo_counts['product_name_x'] + " + " + combo_counts['product_name_y']
                fig = px.bar(combo_counts, x='frequency', y='pair', orientation='h', title="Top Combinations")
                st.plotly_chart(fig, use_container_width=True)
                
            st.info("💡 **Tip:** Bundle these items together to increase average transaction value!")
        else:
            st.info("Not enough multi-item transaction data yet to find patterns.")
    else:
        st.info("Need more multi-item transactions to perform analysis.")

else:
    st.info("Gathering data... Run some transactions in POS first!")
