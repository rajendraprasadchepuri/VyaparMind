
import streamlit as st
import database as db
import pandas as pd
from datetime import datetime
import ui_components as ui
import json

st.set_page_config(layout="wide", page_title="Online Ordering Integration")

ui.render_sidebar()
ui.render_top_header()

st.title("🛵 Online Ordering Integration")
st.markdown("### Swiggy & Zomato Auto-Sync Dashboard")

tabs = st.tabs(["📊 Live Orders", "📋 Menu Mapping", "🧪 Integration Test (Simulation)"])

# --- TAB 1: LIVE ORDERS ---
with tabs[0]:
    st.subheader("Incoming Online Orders")
    pending = db.get_pending_online_orders()
    
    if pending.empty:
        st.info("No pending online orders at the moment.")
    else:
        for _, order in pending.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 3, 1])
                icon = "🛵" if order['platform'] == 'SWIGGY' else "🥘"
                c1.markdown(f"### {icon} {order['platform']}")
                c1.caption(f"ID: {order['external_order_id']}")
                
                items = json.loads(order['items_json'])
                with c2:
                    for it in items:
                        st.write(f"- {it['qty']}x **{it['name']}**")
                
                with c3:
                    if st.button("Accept", key=f"acc_{order['id']}", type="primary", use_container_width=True):
                        # 1. Enrich items using mappings
                        items = json.loads(order['items_json'])
                        mappings = db.get_online_mappings()
                        mapping_dict = {m['external_item_name']: m for _, m in mappings.iterrows()}
                        
                        enriched_items = []
                        for it in items:
                            ext_name = it['name']
                            if ext_name in mapping_dict:
                                m = mapping_dict[ext_name]
                                it['product_id'] = m['internal_product_id']
                                it['name'] = m['internal_name'] # Use internal name
                                # Fetch internal category for routing
                                # We can helper this or just assume 'Kitchen' if unknown
                                # Let's try to find category from product table if possible
                            
                            # Automatically assign section for KDS routing
                            # We'll use a simplified check or a helper if we had one accessible
                            # Since we don't want to over-query, let's use the item name for now
                            it['section'] = db._get_kot_section(it.get('category', it['name']))
                            enriched_items.append(it)
                            
                        # Update order with enriched items
                        db.update_online_item_kds_status(order['id'], -1, 'ordered') # -1 to update entire json if needed? 
                        # Actually, let's just update the status of the sync record.
                        db.update_online_order_status(order['id'], 'ACCEPTED')
                        
                        # Re-save enriched items to order record
                        conn = db.get_connection()
                        c = conn.cursor()
                        c.execute("UPDATE online_orders_sync SET items_json = ? WHERE id = ?", (json.dumps(enriched_items), order['id']))
                        conn.commit()
                        conn.close()
                        
                        st.success("Order Accepted! Sent to Kitchen.")
                        st.rerun()
                    
                    if st.button("Reject", key=f"rej_{order['id']}", type="secondary", use_container_width=True):
                        db.update_online_order_status(order['id'], 'REJECTED')
                        st.rerun()

# --- TAB 2: MENU MAPPING ---
with tabs[1]:
    st.subheader("Map External Items to Internal Products")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        plat = st.selectbox("Platform", ["SWIGGY", "ZOMATO"])
        ext_name = st.text_input("External Item Name (exactly as on platform)", placeholder="e.g. Chicken Hakka Noodles (Regular)")
    
    with col_m2:
        products = db.fetch_all_products()
        prod_options = {p['name']: p['id'] for _, p in products.iterrows()}
        int_prod_name = st.selectbox("Internal Product", list(prod_options.keys()))
    
    if st.button("Save Mapping", type="primary"):
        if ext_name:
            if db.map_online_item(plat, ext_name, prod_options[int_prod_name]):
                st.success(f"Mapped '{ext_name}' to '{int_prod_name}'")
                st.rerun()
        else:
            st.error("Please enter external item name.")

    st.divider()
    st.write("Current Mappings:")
    mappings = db.get_online_mappings()
    if not mappings.empty:
        st.dataframe(mappings[['platform', 'external_item_name', 'internal_name']], use_container_width=True)
    else:
        st.caption("No mappings created yet.")

# --- TAB 3: SIMULATION ---
with tabs[2]:
    st.warning("This tool simulates an order being pushed from Swiggy/Zomato APIs.")
    
    s_plat = st.selectbox("Simulate Platform", ["SWIGGY", "ZOMATO"], key="sim_plat")
    s_order_id = st.text_input("Mock Order ID", value=f"EXT-{db.generate_unique_id(6, numeric_only=True)}")
    
    # Simple item builder for simulation
    if 'sim_items' not in st.session_state:
        st.session_state.sim_items = []
        
    s_c1, s_c2, s_c3 = st.columns([3, 1, 1])
    s_item = s_c1.text_input("Item Name", placeholder="e.g. Spicy Chicken Rice")
    s_qty = s_c2.number_input("Qty", 1, 10, 1)
    if s_c3.button("Add Item to Mock", use_container_width=True):
        st.session_state.sim_items.append({"name": s_item, "qty": s_qty})
        
    if st.session_state.sim_items:
        st.write("Items in Mock Order:")
        for i in st.session_state.sim_items:
            st.write(f"- {i['qty']}x {i['name']}")
            
        if st.button("🚀 Push Order to System", type="primary"):
            res = db.sync_online_order(s_plat, s_order_id, st.session_state.sim_items)
            if res:
                st.success("Order Synced! Check the 'Live Orders' tab.")
                st.session_state.sim_items = []
                st.rerun() 
            else:
                st.error("Sync failed.")
    else:
        st.caption("Add items to create a mock order.")

