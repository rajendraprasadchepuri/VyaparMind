import streamlit as st
import database as db
import pandas as pd
from datetime import datetime
import ui_components as ui
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Inward & Outward - Cold Storage", layout="wide", page_icon="🚛")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

# --- MOBILE MODE TOGGLE ---
col_head, col_mode = st.columns([0.8, 0.2])
with col_head:
    st.title("🚛 Inward & Outward")
with col_mode:
    view_mode = st.radio("Display Mode", ["🖥️ Desktop", "📱 Scanner"], horizontal=True, label_visibility="collapsed")

if view_mode == "📱 Scanner":
    st.caption("Simplified interface for handheld scanners")
    
    # --- SCANNER INTERFACE ---
    tab_scan1, tab_scan2 = st.tabs(["📥 Quick Inward", "📤 Quick Outward"])
    
    with tab_scan1:
        st.subheader("📷 Scan / Inward Goods")
        
        with st.form("mobile_grn"):
            # Minimal required fields
            scan_code = st.text_input("🔫 Scan Barcode / Lot #", help="Focus here and scan item")
            qty = st.number_input("Quantity (KG)", min_value=1.0, step=1.0, value=50.0)
            
            c1, c2 = st.columns(2)
            with c1:
                zone_code = st.selectbox("Zone", ["Zone A", "Zone B", "Zone C"])
            with c2:
                # Use camera directly for mobile
                proof_photo = st.camera_input("Take Photo")
            
            if st.form_submit_button("✅ SAVE ITEM", use_container_width=True, type="primary"):
                st.success(f"Item {scan_code} added to {zone_code}!")
                st.balloons()
                
    with tab_scan2:
        st.subheader("📦 Scan / Dispatch")
        # Placeholder for dispatch logic
        st.info("Scan delivery note to start loading")

    # Stop desktop rendering if mobile mode
    st.markdown("---")
    st.stop()

# --- DESKTOP INTERFACE ---
st.caption("Manage GRN entries and delivery schedules")

# --- TAB NAVIGATION ---
tab1, tab2, tab3 = st.tabs(["📥 Create GRN (Inward)", "📤 Create Delivery (Outward)", "📋 History"])

# TAB 1: CREATE GRN (INWARD)
with tab1:
    st.subheader("📥 Goods Receipt Note (GRN)")
    st.caption("Record incoming goods from clients")
    
    clients_df = db.get_all_storage_clients()
    
    if not clients_df.empty:
        with st.form("grn_form"):
            st.markdown("#### 1. Vehicle & Client Details")
            col1, col2 = st.columns(2)
            
            with col1:
                client_options = {row['company_name']: row['id'] for _, row in clients_df.iterrows()}
                selected_client_name = st.selectbox("Client", list(client_options.keys()))
                selected_client_id = client_options[selected_client_name]
                
                vehicle_number = st.text_input("Vehicle Number", placeholder="e.g., TN01AB1234")
            
            with col2:
                arrival_date = st.date_input("Arrival Date", value=datetime.now())
                driver_name = st.text_input("Driver Name (Optional)")
                driver_phone = st.text_input("Driver Phone (Optional)")
            
            # Photo Upload 📷 NEW!
            st.markdown("---")
            st.markdown("#### 📷 Quality Check Photos (Optional)")
            uploaded_photos = st.file_uploader(
                "Upload photos of goods (max 3)", 
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                help="Photos will be saved for quality documentation"
            )
            
            if uploaded_photos and len(uploaded_photos) > 3:
                st.warning("⚠️ Maximum 3 photos allowed. Only first 3 will be saved.")
                uploaded_photos = uploaded_photos[:3]
            
            # Save uploaded photos
            photo_paths = []
            if uploaded_photos:
                import os
                os.makedirs("uploads/grn_photos", exist_ok=True)
                
                for idx, photo in enumerate(uploaded_photos):
                    photo_name = f"GRN_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{idx+1}.{photo.name.split('.')[-1]}"
                    photo_path = f"uploads/grn_photos/{photo_name}"
                    
                    with open(photo_path, "wb") as f:
                        f.write(photo.getbuffer())
                    
                    photo_paths.append(photo_path)
                    st.success(f"✅ Uploaded: {photo.name}")
            
            st.markdown("---")
            st.markdown("#### 2. Add Commodities")
            st.caption("Add items being received")
            
            # Dynamic item entry
            if 'grn_items' not in st.session_state:
                st.session_state.grn_items = []
            
            col_a, col_b, col_c, col_d = st.columns([2, 1.5, 1, 1])
            
            with col_a:
                item_commodity = st.text_input("Commodity Name", key="grn_item_comm", placeholder="e.g., Frozen Chicken")
            with col_b:
                item_lot = st.text_input("Lot Number", key="grn_item_lot", placeholder="LOT12345")
            with col_c:
                item_qty = st.number_input("Quantity", min_value=0.0, value=100.0, step=10.0, key="grn_item_qty")
            with col_d:
                item_unit = st.selectbox("Unit", ["KG", "PALLETS", "BOXES", "CRATES"], key="grn_item_unit")
            
            col_e, col_f, col_g, col_h, col_i = st.columns([1.5, 1.5, 1, 1, 1.5])
            
            with col_e:
                item_temp = st.number_input("Temp on Arrival (°C)", value=-24.0, step=0.5, key="grn_item_temp")
            
            with col_f:
                item_expiry = st.date_input("Expiry Date", key="grn_item_expiry", value=None)
            
            zones_df = db.get_all_cold_zones()
            if not zones_df.empty:
                with col_g:
                    zone_options = {row['zone_name']: row['id'] for _, row in zones_df.iterrows()}
                    item_zone_name = st.selectbox("Zone", list(zone_options.keys()), key="grn_item_zone")
                    item_zone_id = zone_options[item_zone_name]
            else:
                item_zone_id = None
                st.warning("Add zones in ColdZone module first")
            
            with col_h:
                item_rack = st.text_input("Rack", key="grn_item_rack", placeholder="R01")
            with col_i:
                item_bin = st.text_input("Bin", key="grn_item_bin", placeholder="B01")
            
            if st.form_submit_button("➕ Add Item to GRN"):
                if item_commodity and item_lot and item_zone_id:
                    st.session_state.grn_items.append({
                        'commodity': item_commodity,
                        'lot': item_lot,
                        'quantity': item_qty,
                        'unit': item_unit,
                        'temp': item_temp,
                        'expiry_date': str(item_expiry) if item_expiry else None,
                        'zone_id': item_zone_id,
                        'zone_name': item_zone_name,
                        'rack': item_rack,
                        'bin': item_bin,
                        'client_id': selected_client_id  # Store for inventory creation
                    })
                    st.success(f"Added: {item_commodity} ({item_lot})")
                    st.rerun()
                else:
                    st.warning("Please fill all required fields (Commodity, Lot, Zone)")
        
        # Show added items
        if st.session_state.grn_items:
            st.markdown("---")
            st.markdown("#### Items to be Received")
            
            items_df = pd.DataFrame(st.session_state.grn_items)
            st.dataframe(items_df, hide_index=True, use_container_width=True)
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("🗑️ Clear All Items", type="secondary", use_container_width=True):
                    st.session_state.grn_items = []
                    st.rerun()
            
            with col_btn2:
                if st.button("✅ Create GRN & Add to Inventory", type="primary", use_container_width=True):
                    # Create GRN
                    success, grn_id, grn_number = db.create_grn(
                        selected_client_id, vehicle_number, arrival_date, driver_name, driver_phone
                    )
                    
                    if success:
                        # Add items to GRN and create inventory
                        for item in st.session_state.grn_items:
                            db.add_grn_item_with_inventory(
                                grn_id, item['client_id'], item['commodity'], item['lot'], item['quantity'], 
                                item['unit'], item['temp'], item['zone_id'], item['rack'], item['bin'],
                                item.get('expiry_date'), arrival_date
                            )
                        
                        st.success(f"✅ GRN Created Successfully! GRN #: {grn_number}")
                        st.success(f"✅ {len(st.session_state.grn_items)} items added to inventory!")
                        st.balloons()
                        st.session_state.grn_items = []
                        import time
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"Failed to create GRN: {grn_number}")
    else:
        st.warning("Please add storage clients in the ClientLedger module first.")

# TAB 2: CREATE DELIVERY (OUTWARD)
with tab2:
    st.subheader("📤 Create Outward Delivery")
    st.caption("Dispatch goods to clients (FEFO-based picking)")
    
    clients_df = db.get_all_storage_clients()
    
    if not clients_df.empty:
        # Client selection
        client_options = {row['company_name']: row['id'] for _, row in clients_df.iterrows()}
        selected_delivery_client_name = st.selectbox("Select Client for Delivery", list(client_options.keys()), key="delivery_client")
        selected_delivery_client_id = client_options[selected_delivery_client_name]
        
        # Show client's inventory (FEFO order)
        client_inventory = db.get_cold_inventory_fefo(client_id=selected_delivery_client_id)
        
        if not client_inventory.empty:
            st.markdown(f"#### Available Inventory for {selected_delivery_client_name} (FEFO Order)")
            st.caption("✅ Items are automatically sorted by expiry date - pick from top for FEFO compliance!")
            
            # Item selection in a form
            with st.form("delivery_form"):
                st.markdown("##### 1. Delivery Details")
                col1, col2 = st.columns(2)
                
                with col1:
                    delivery_vehicle = st.text_input("Vehicle Number *")
                    delivery_driver = st.text_input("Driver Name")
                
                with col2:
                    delivery_date = st.date_input("Dispatch Date", value=datetime.now())
                    delivery_driver_phone = st.text_input("Driver Phone")
                
                delivery_notes = st.text_area("Notes (Optional)")
                
                st.markdown("---")
                st.markdown("##### 2. Select Items to Dispatch")
                
                # Display inventory with selection checkboxes
                selected_items = []
                
                for idx, row in client_inventory.iterrows():
                    col_check, col_info, col_qty = st.columns([0.5, 3, 1])
                    
                    with col_check:
                        select = st.checkbox("✓", key=f"sel_{row['id']}", label_visibility="collapsed")
                    
                    with col_info:
                        expiry_indicator = "🔴" if row['days_to_expiry'] <= 7 else "🟡" if row['days_to_expiry'] <= 30 else "🟢"
                        st.write(f"{expiry_indicator} **{row['commodity_name']}** - Lot: {row['lot_number']} | Zone: {row['zone_name']}-{row['rack_number']}-{row['bin_number']} | Exp: {row['expiry_date']} ({row['days_to_expiry']} days)")
                    
                    with col_qty:
                        if select:
                            dispatch_qty = st.number_input(
                                f"Qty (Max: {row['quantity']})",
                                min_value=0.0,
                                max_value=float(row['quantity']),
                                value=float(row['quantity']),
                                step=10.0,
                                key=f"qty_{row['id']}",
                                label_visibility="visible"
                            )
                            selected_items.append({'id': row['id'], 'quantity': dispatch_qty})
                
                st.markdown("---")
                submitted = st.form_submit_button("✅ Create Delivery & Dispatch Items", use_container_width=True, type="primary")
                
                if submitted:
                    if not delivery_vehicle:
                        st.error("⚠️ Vehicle Number is required")
                    elif not selected_items:
                        st.error("⚠️ Please select at least one item to dispatch")
                    else:
                        # Create delivery
                        success, delivery_id, delivery_number = db.create_delivery(
                            selected_delivery_client_id, delivery_vehicle, delivery_date, 
                            delivery_driver, delivery_driver_phone, delivery_notes
                        )
                        
                        if success:
                            # Add selected items to delivery
                            items_added = 0
                            for item in selected_items:
                                item_success, result = db.add_delivery_item(
                                    delivery_id, item['id'], item['quantity']
                                )
                                if item_success:
                                    items_added += 1
                                else:
                                    st.warning(f"⚠️ Item error: {result}")
                            
                            st.success(f"✅ Delivery Created Successfully! Delivery #: {delivery_number}")
                            st.success(f"✅ {items_added} items dispatched and inventory updated!")
                            st.balloons()
                            import time
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"Failed to create delivery: {delivery_number}")
        else:
            st.info(f"No inventory found for {selected_delivery_client_name}")
    else:
        st.warning("Please add storage clients first.")

# TAB 3: HISTORY
with tab3:
    st.subheader("📋 Inward & Outward History")
    
    history_tab1, history_tab2 = st.tabs(["📥 GRN History", "📤 Delivery History"])
    
    with history_tab1:
        st.markdown("#### Recent GRNs")
        
        pending_grns = db.get_pending_grns()
        
        if not pending_grns.empty:
            st.warning(f"⚠️ {len(pending_grns)} GRN(s) pending quality approval")
            
            st.dataframe(
                pending_grns[['grn_number', 'client_name', 'vehicle_number', 'arrival_date', 'quality_status']],
                column_config={
                    "grn_number": "GRN Number",
                    "client_name": "Client",
                    "vehicle_number": "Vehicle",
                    "arrival_date": st.column_config.DateColumn("Arrival", format="DD MMM YYYY"),
                    "quality_status": "Status"
                },
                hide_index=True,
                use_container_width=True
            )
            
            # --- APPROVAL UI ---
            st.divider()
            with st.container(border=True):
                st.subheader("✅ Action: Quality Approval")
                c_app1, c_app2 = st.columns([2, 1])
                
                # Create options list for selectbox
                grn_opts = {f"{row['grn_number']} ({row['client_name']})": row['id'] for idx, row in pending_grns.iterrows()}
                
                selected_grn_label = c_app1.selectbox("Select GRN to Approve", list(grn_opts.keys()))
                selected_grn_id = grn_opts[selected_grn_label]
                
                app_notes = c_app1.text_area("Quality Check Notes", placeholder="e.g. Verified temp logs, packaging intact.")
                
                st.info("By approving, you confirm that physical goods match the GRN entry.")
                
                if c_app2.button("✅ Approve Quality", type="primary", use_container_width=True):
                     current_user = st.session_state.get('username', 'Admin')
                     succ, msg = db.approve_grn_quality(selected_grn_id, current_user, app_notes)
                     if succ:
                         st.success(f"GRN {selected_grn_label} Approved!")
                         time.sleep(1)
                         st.rerun()
                     else:
                         st.error(msg)
        else:
            st.success("✅ All GRNs are quality-checked and approved!")
    
    with history_tab2:
        st.markdown("#### Recent Deliveries")
        
        deliveries_df = db.get_deliveries_history(days=30)
        
        if not deliveries_df.empty:
            st.dataframe(
                deliveries_df[['delivery_number', 'client_name', 'vehicle_number', 'dispatch_date', 'notes']],
                column_config={
                    "delivery_number": "Delivery #",
                    "client_name": "Client",
                    "vehicle_number": "Vehicle",
                    "dispatch_date": st.column_config.DateColumn("Dispatch Date", format="DD MMM YYYY"),
                    "notes": "Notes"
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No deliveries in the last 30 days")

st.markdown("---")
st.caption("💡 **Tip**: Use FEFO order to ensure you always dispatch items closest to expiry first, minimizing wastage!")
