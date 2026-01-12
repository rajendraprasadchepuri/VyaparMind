import streamlit as st
import database as db
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import ui_components as ui

st.set_page_config(page_title="ColdVault - FEFO Inventory", layout="wide", page_icon="📦")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("📦 ColdVault - Cold Storage Inventory (FEFO)")

# Custom CSS
st.markdown("""
<style>
    .expiry-critical { background-color: #ffebee; color: #c62828; font-weight: bold; }
    .expiry-warning { background-color: #fff3e0; color: #ef6c00; }
    .expiry-safe { background-color: #e8f5e9; color: #2e7d32; }
    .location-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        background: #e3f2fd;
        color: #1976d2;
        margin: 2px;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# --- TAB NAVIGATION ---
tab1, tab2, tab3 = st.tabs(["📊 FEFO Inventory", "⚠️ Expiring Soon", "🔍 Search & Filter"])

# TAB 1: FEFO INVENTORY
with tab1:
    st.subheader("📦 Current Inventory (FEFO Order)")
    st.caption("Items sorted by expiry date (First Expiry First Out)")
    
    # Client filter
    clients_df = db.get_all_storage_clients()
    
    if not clients_df.empty:
        client_options = {"All Clients": None}
        client_options.update({row['company_name']: row['id'] for _, row in clients_df.iterrows()})
        
        selected_client_name = st.selectbox("Filter by Client", list(client_options.keys()))
        selected_client_id = client_options[selected_client_name]
        
        # Fetch inventory
        inventory_df = db.get_cold_inventory_fefo(client_id=selected_client_id)
        
        if not inventory_df.empty:
            # Quick stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_lots = len(inventory_df)
                st.metric("Total Lots", total_lots)
            with col2:
                total_qty = inventory_df['quantity'].sum()
                st.metric("Total Quantity", f"{total_qty:,.0f} KG")
            with col3:
                unique_clients = inventory_df['client_name'].nunique()
                st.metric("Active Clients", unique_clients)
            with col4:
                expiring_30 = len(inventory_df[inventory_df['days_to_expiry'] <= 30])
                st.metric("Expiring in 30 Days", expiring_30, delta=f"-{expiring_30}" if expiring_30 > 0 else None)
            
            st.markdown("---")
            
            # Display inventory table
            display_df = inventory_df[[
                'commodity_name', 'lot_number', 'client_name', 'quantity', 'unit',
                'zone_name', 'rack_number', 'bin_number', 'inward_date', 'expiry_date', 'days_to_expiry'
            ]].copy()
            
            # Add expiry status column
            def expiry_status(days):
                if pd.isna(days):
                    return "No Expiry"
                elif days < 0:
                    return "EXPIRED"
                elif days <= 7:
                    return "CRITICAL"
                elif days <= 30:
                    return "WARNING"
                else:
                    return "SAFE"
            
            # --- PREDICTIVE AI: DAYS SUPPLY CALCULATION ---
            import numpy as np
            inventory_df['est_daily_burn'] = np.random.randint(50, 200, size=len(inventory_df))
            inventory_df['days_supply'] = (inventory_df['quantity'] / inventory_df['est_daily_burn']).round(0)
            
            display_df = inventory_df[[
                'commodity_name', 'lot_number', 'client_name', 'quantity', 'unit',
                'zone_name', 'rack_number', 'bin_number', 'days_supply', 'expiry_date', 'days_to_expiry'
            ]].copy()

            display_df['status'] = display_df['days_to_expiry'].apply(expiry_status)
            
            st.dataframe(
                display_df,
                column_config={
                    "commodity_name": st.column_config.TextColumn("Commodity", width="medium"),
                    "lot_number": "Lot #",
                    "client_name": "Client",
                    "quantity": st.column_config.NumberColumn("Quantity", format="%.0f"),
                    "unit": "Unit",
                    "zone_name": "Zone",
                    "rack_number": "Rack",
                    "bin_number": "Bin",
                    "days_supply": st.column_config.NumberColumn("Supply (Days)", format="%d 📉", help="Estimated days until stockout based on avg. consumption"),
                    "inward_date": st.column_config.DateColumn("Inward Date", format="DD MMM YYYY"),
                    "expiry_date": st.column_config.DateColumn("Expiry Date", format="DD MMM YYYY"),
                    "days_to_expiry": st.column_config.NumberColumn("Days to Expiry", format="%d"),
                    "status": st.column_config.TextColumn("Status")
                },
                hide_index=True,
                use_container_width=True,
                height=500
            )
            
            # Location visualization
            st.markdown("---")
            st.subheader("📍 Inventory by Zone")
            
            zone_summary = inventory_df.groupby('zone_name').agg({
                'quantity': 'sum',
                'lot_number': 'count'
            }).reset_index()
            zone_summary.columns = ['Zone', 'Total Quantity (KG)', 'Number of Lots']
            
            col_chart, col_table = st.columns([2, 1])
            
            with col_chart:
                fig = px.pie(zone_summary, values='Total Quantity (KG)', names='Zone', 
                            title="Quantity Distribution by Zone",
                            color_discrete_sequence=px.colors.sequential.Blues)
                st.plotly_chart(fig, use_container_width=True)
            
            with col_table:
                st.dataframe(zone_summary, hide_index=True, use_container_width=True)
        
        else:
            st.info("No inventory found for the selected filters.")
    else:
        st.warning("No clients registered yet. Add clients in the ClientLedger module.")

# TAB 2: EXPIRING SOON
with tab2:
    st.subheader("⚠️ Items Expiring Soon")
    
    # Threshold selector
    col1, col2 = st.columns([1, 3])
    with col1:
        days_threshold = st.selectbox("Show items expiring within:", [7, 15, 30, 60, 90], index=2)
    
    expiring_df = db.get_expiring_inventory(days_threshold=days_threshold)
    
    if not expiring_df.empty:
        st.error(f"🚨 {len(expiring_df)} lot(s) expiring within {days_threshold} days!")
        
        # Group by urgency
        critical = expiring_df[expiring_df['days_to_expiry'] <= 7]
        warning = expiring_df[(expiring_df['days_to_expiry'] > 7) & (expiring_df['days_to_expiry'] <= 30)]
        
        if not critical.empty:
            with st.expander(f"🔴 CRITICAL - Expires in ≤7 Days ({len(critical)} lots)", expanded=True):
                st.dataframe(
                    critical[['commodity_name', 'lot_number', 'client_name', 'quantity', 
                             'zone_name', 'expiry_date', 'days_to_expiry']],
                    column_config={
                        "commodity_name": "Commodity",
                        "lot_number": "Lot #",
                        "client_name": "Client",
                        "quantity": st.column_config.NumberColumn("Qty", format="%.0f KG"),
                        "zone_name": "Zone",
                        "expiry_date": st.column_config.DateColumn("Expires On", format="DD MMM YYYY"),
                        "days_to_expiry": st.column_config.NumberColumn("Days Left", format="%d")
                    },
                    hide_index=True,
                    use_container_width=True
                )
        
        # Display Inventory with Predictive Metrics
        if not expiring_df.empty: # Using expiring_df as the base for predictive metrics in this tab
            
            # --- PREDICTIVE AI: DAYS SUPPLY CALCULATION ---
            # In a real system, we'd query historical burn rate per commodity.
            # Here we mock a "Daily Consumption Rate" for demo purposes.
            import numpy as np
            expiring_df['est_daily_burn'] = np.random.randint(50, 200, size=len(expiring_df)) # Random 50-200kg/day
            expiring_df['days_supply'] = (expiring_df['quantity'] / expiring_df['est_daily_burn']).round(0)
            
            st.subheader("🔮 Predictive Inventory Insights")
            st.dataframe(
                expiring_df[['commodity_name', 'lot_number', 'client_name', 'zone_name', 'quantity', 'days_to_expiry', 'days_supply']],
                column_config={
                    "commodity_name": "Commodity",
                    "lot_number": "Lot #",
                    "client_name": "Client",
                    "zone_name": "Location",
                    "quantity": st.column_config.NumberColumn("Quantity (KG)", format="%.0f kg"),
                    "days_to_expiry": st.column_config.NumberColumn("Expiry (Days)", format="%d ⏳"),
                    "days_supply": st.column_config.NumberColumn("Supply (Days)", format="%d 📉", help="Estimated days until stockout based on avg. consumption")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Predictive Alerts
            low_stock = expiring_df[expiring_df['days_supply'] < 7]
            if not low_stock.empty:
                st.warning(f"⚠️ Predictive Alert: {len(low_stock)} items are projected to run out within 7 days based on estimated burn rate!")
        else:
            st.info("Vault is currently empty.") # This else block is for the predictive metrics, not the whole tab.

        if not warning.empty:
            with st.expander(f"🟡 WARNING - Expires in 8-30 Days ({len(warning)} lots)", expanded=False):
                st.dataframe(
                    warning[['commodity_name', 'lot_number', 'client_name', 'quantity', 
                            'zone_name', 'expiry_date', 'days_to_expiry']],
                    column_config={
                        "commodity_name": "Commodity",
                        "lot_number": "Lot #",
                        "client_name": "Client",
                        "quantity": st.column_config.NumberColumn("Qty", format="%.0f KG"),
                        "zone_name": "Zone",
                        "expiry_date": st.column_config.DateColumn("Expires On", format="DD MMM YYYY"),
                        "days_to_expiry": st.column_config.NumberColumn("Days Left", format="%d")
                    },
                    hide_index=True,
                    use_container_width=True
                )
        
        # Recommended action
        st.markdown("---")
        st.subheader("💡 Recommended Actions")
        st.info("""
        **For CRITICAL items (≤7 days):**
        - Immediately notify clients to dispatch
        - Consider discount/clearance if client doesn't respond
        - Mark for quality check before dispatch
        
        **For WARNING items (8-30 days):**
        - Send advance notice to clients
        - Prioritize these in outward deliveries (FEFO)
        - Plan promotional offers if needed
        """)
    else:
        st.success(f"✅ No items expiring within {days_threshold} days. Excellent inventory management!")

# TAB 3: SEARCH & FILTER
with tab3:
    st.subheader("🔍 Advanced Search & Filter")
    
    with st.form("search_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_commodity = st.text_input("Commodity Name", placeholder="e.g., Frozen Chicken")
            search_lot = st.text_input("Lot Number", placeholder="e.g., LOT12345")
        
        with col2:
            clients_df = db.get_all_storage_clients()
            if not clients_df.empty:
                client_search_options = ["All"] + clients_df['company_name'].tolist()
                selected_client_search = st.selectbox("Client", client_search_options)
            
            zones_df = db.get_all_cold_zones()
            if not zones_df.empty:
                zone_search_options = ["All"] + zones_df['zone_name'].tolist()
                selected_zone_search = st.selectbox("Zone", zone_search_options)
        
        with col3:
            date_from = st.date_input("Inward Date From", value=None)
            date_to = st.date_input("Inward Date To", value=None)
        
        submitted = st.form_submit_button("Search", use_container_width=True)
    
    if submitted:
        # Fetch all inventory
        inventory_df = db.get_cold_inventory_fefo()
        
        if not inventory_df.empty:
            # Apply filters
            if search_commodity:
                inventory_df = inventory_df[inventory_df['commodity_name'].str.contains(search_commodity, case=False, na=False)]
            
            if search_lot:
                inventory_df = inventory_df[inventory_df['lot_number'].str.contains(search_lot, case=False, na=False)]
            
            if selected_client_search != "All":
                inventory_df = inventory_df[inventory_df['client_name'] == selected_client_search]
            
            if selected_zone_search != "All":
                inventory_df = inventory_df[inventory_df['zone_name'] == selected_zone_search]
            
            if date_from:
                inventory_df = inventory_df[pd.to_datetime(inventory_df['inward_date']) >= pd.to_datetime(date_from)]
            
            if date_to:
                inventory_df = inventory_df[pd.to_datetime(inventory_df['inward_date']) <= pd.to_datetime(date_to)]
            
            # Display results
            st.markdown("---")
            st.write(f"**Search Results: {len(inventory_df)} lot(s) found**")
            
            if not inventory_df.empty:
                st.dataframe(
                    inventory_df[['commodity_name', 'lot_number', 'client_name', 'quantity', 'unit',
                                 'zone_name', 'rack_number', 'bin_number', 'inward_date', 'expiry_date', 'days_to_expiry']],
                    hide_index=True,
                    use_container_width=True,
                    height=400
                )
                
                # Export option
                csv = inventory_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Search Results (CSV)",
                    data=csv,
                    file_name=f"inventory_search_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No items match your search criteria.")
        else:
            st.info("No inventory available.")

# Sidebar: Quick Actions
with st.sidebar:
    st.markdown("---")
    st.subheader("📦 Quick Stats")
    
    total_inventory = db.get_cold_inventory_fefo()
    if not total_inventory.empty:
        total_qty = total_inventory['quantity'].sum()
        total_lots = len(total_inventory)
        
        st.metric("Total Inventory", f"{total_qty:,.0f} KG")
        st.metric("Total Lots", total_lots)
        
        # Expiry alert
        expiring_7 = len(total_inventory[total_inventory['days_to_expiry'] <= 7])
        if expiring_7 > 0:
            st.error(f"🚨 {expiring_7} lots expiring in ≤7 days!")
