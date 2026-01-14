import streamlit as st
import database as db
import pandas as pd

import ui_components as ui

st.set_page_config(page_title="VyaparMind Inventory", layout="wide")

ui.require_auth()
ui.render_sidebar()
ui.render_top_header()
st.title("📦 VyaparMind Inventory")

# --- Actions ---
# --- Actions (Moved to Main Page) ---
with st.expander("➕ Add New Product / Update Stock", expanded=False):
    with st.form("product_form"):
        st.write("Enter product details below:")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Product Name")
            category = st.selectbox("Category", ["General", "Electronics", "Groceries", "Clothing", "Pharma", "Others"])
            stock = st.number_input("Stock Quantity", min_value=0, step=1)
            
            manufacturer = None
            if ui.has_feature('MoleculeMatch') or ui.has_feature('PharmaGuard'):
                manufacturer = st.text_input("Manufacturer")

        with col2:
            price = st.number_input("Selling Price (₹)", min_value=0.0, step=10.0)
            cost = st.number_input("Cost Price (₹)", min_value=0.0, step=10.0)
            tax_rate = st.number_input("Tax Rate (%)", min_value=0.0, step=0.5, value=0.0)
            
            schedule_type = None
            if ui.has_feature('MoleculeMatch') or ui.has_feature('PharmaGuard'):
                schedule_type = st.selectbox("Schedule Type", ["OTC", "H", "H1", "X"])
        
        salt_composition = None
        if ui.has_feature('MoleculeMatch') or ui.has_feature('PharmaGuard'):
            salt_composition = st.text_input("Salt Composition (e.g., Paracetamol 500mg)")

        is_chronic = 0
        refill_interval = 30
        if ui.has_feature('RescueScript') or ui.has_feature('PharmaGuard'):
             is_chronic = 1 if st.checkbox("🔄 Chronic Condition (Auto-Refill)") else 0
             if is_chronic:
                 refill_interval = st.number_input("Refill Interval (Days)", min_value=1, value=30, step=1)

        submitted = st.form_submit_button("Add Product", use_container_width=True)
        
        if submitted:
            if name:
                success = db.add_product(name, category, price, cost, stock, tax_rate, salt_composition, manufacturer, schedule_type, is_chronic=is_chronic, refill_interval=refill_interval)
                if success:
                    st.success(f"Successfully added {name} to inventory!")
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to add product. It might already exist.")
            else:
                st.warning("Product Name is required.")

# --- Bulk Upload Section ---
with st.expander("📂 Bulk Upload Products (CSV/Excel/Txt)", expanded=False):
    st.write("Upload a file with the following columns: **Product Name**, **Selling Price**, **Category**, **Cost Price**, **Stock Quantity**, **Tax Rate**")
    
    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx', 'txt'])
    
    if uploaded_file is not None:
        try:
            # Determine file type and read
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                df_upload = pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith('.txt'):
                # Try comma first, then tab
                try:
                    df_upload = pd.read_csv(uploaded_file, sep=',')
                    if len(df_upload.columns) < 2:
                         uploaded_file.seek(0)
                         df_upload = pd.read_csv(uploaded_file, sep='\t')
                except:
                     st.error("Could not parse text file. Please ensure it is CSV or Tab separated.")
                     df_upload = None

            if df_upload is not None:
                # Column Normalization (strip whitespace, lower case for matching)
                df_upload.columns = [c.strip() for c in df_upload.columns]
                
                # Check Required Columns (Flexible Name Matching)
                required_map = {
                    'product name': ['product name', 'name', 'item', 'product'],
                    'selling price': ['selling price', 'price', 'mrp', 'rate'],
                    'category': ['category', 'cat', 'type'],
                    'cost price': ['cost price', 'cost', 'cp', 'buy price'],
                    'stock quantity': ['stock quantity', 'stock', 'quantity', 'qty', 'count'],
                    'tax rate': ['tax rate', 'tax', 'gst', 'vat']
                }
                
                # Validation Logic
                found_cols = {k: None for k in required_map}
                missing_cols = []
                
                for req, alternatives in required_map.items():
                    for col in df_upload.columns:
                        if col.lower() in alternatives:
                            found_cols[req] = col
                            break
                    if not found_cols[req]:
                        # Optional fields logic? 
                        # Requirements said all these columns. Let's enforce for now but maybe Defaults?
                        # Tax Rate could be default 0. Category default "General".
                        if req in ['tax rate', 'category']:
                            pass # We can handle missing optional later
                        else:
                            missing_cols.append(req)

                if missing_cols:
                    st.error(f"Missing required columns: {', '.join(missing_cols)}")
                    st.info(f"Expected header variations: {required_map}")
                else:
                    st.success("File columns verified! Processing...")
                    
                    if st.button("Start Import"):
                        progress_bar = st.progress(0)
                        success_count = 0
                        errors = []
                        
                        total_rows = len(df_upload)
                        
                        for i, row in df_upload.iterrows():
                            # Extract Values safely
                            p_name = row[found_cols['product name']]
                            p_price = row[found_cols['selling price']] if found_cols['selling price'] else 0.0
                            p_cost = row[found_cols['cost price']] if found_cols['cost price'] else 0.0
                            p_qty = row[found_cols['stock quantity']] if found_cols['stock quantity'] else 0
                            
                            # Optionals
                            p_cat = row[found_cols['category']] if found_cols['category'] else "General"
                            p_tax = row[found_cols['tax rate']] if found_cols['tax rate'] else 0.0
                            
                            # Type Conversion / Safety
                            try:
                                p_price = float(str(p_price).replace(',','').replace('₹',''))
                                p_cost = float(str(p_cost).replace(',','').replace('₹',''))
                                p_tax = float(str(p_tax).replace('%',''))
                                p_qty = int(p_qty)
                            except ValueError:
                                errors.append(f"Row {i+1}: Invalid number format for {p_name}")
                                continue

                            # DB Insert
                            status, msg = db.add_product(p_name, p_cat, p_price, p_cost, p_qty, p_tax)
                            if status:
                                success_count += 1
                            else:
                                errors.append(f"Row {i+1} ({p_name}): {msg}")
                            
                            progress_bar.progress((i + 1) / total_rows)
                        
                        st.balloons()
                        st.success(f"Import Complete! Added {success_count} products.")
                        if errors:
                            with st.expander("View Import Errors"):
                                for e in errors:
                                    st.write(f"❌ {e}")
                        
                        import time
                        time.sleep(2)
                        st.rerun()

        except Exception as e:
            st.error(f"Error processing file: {e}")

# --- Display Inventory ---
st.subheader("Current Stock")

# Search Form (Outside fragment to maintain proper form behavior)
with st.form("search_form_inventory"):
    search_term = st.text_input("🔍 Search Products", "")
    if st.form_submit_button("Search"):
        pass 

# Fragment for inventory display to reduce full-page reruns
@st.fragment
def render_inventory_table():
    # Load Data (Optimized - uses server-side search from database.py)
    df = db.fetch_all_products(search_term=search_term if 'search_term' in locals() else None)
    
    # Feature Gate Columns
    if not (ui.has_feature('MoleculeMatch') or ui.has_feature('PharmaGuard')):
        # Drops columns if they exist
        cols_to_drop = ['salt_composition', 'manufacturer', 'schedule_type']
        df = df.drop(columns=[c for c in cols_to_drop if c in df.columns], errors='ignore')

    if not df.empty:
        # Alerts (Contextual to search)
        low_stock = df[df['stock_quantity'] < 10]
        if not low_stock.empty:
            st.warning(f"⚠️ {len(low_stock)} items are low on stock!")

        # Editable Data Editor
        # We use a key to track changes
        edited_df = st.data_editor(
            df,
            column_config={
                "price": st.column_config.NumberColumn("Price (₹)", format="₹%.2f"),
                "cost_price": st.column_config.NumberColumn("Cost (₹)", format="₹%.2f"),
                "stock_quantity": st.column_config.NumberColumn("Stock", min_value=0, step=1), # Changed to Number for editing
                "tax_rate": st.column_config.NumberColumn("Tax (%)", min_value=0.0, step=0.5, format="%.1f%%"),
                "updated_at": st.column_config.DatetimeColumn("Last Updated", format="D MMM, HH:mm"),
                "salt_composition": st.column_config.TextColumn("Salt"),
                "manufacturer": st.column_config.TextColumn("Mfg"),
                "schedule_type": st.column_config.SelectboxColumn("Sch", options=["OTC", "H", "H1", "X"]),
            },
            disabled=["id", "created_at", "updated_at"],
            hide_index=True,
            use_container_width=True,
            key="inventory_editor"
        )
        
        # Logic to detect changes and update DB
        # st.data_editor doesn't return just changed rows, it returns the final state.
        # We can use session_state to track or just iterate if data is small. 
        # For robust editing, let's use the 'on_change' callback pattern or button save, 
        # but Streamlit's data_editor is better handled by comparing state if instant save is needed.
        # Actually, simpler: Button "Save Changes" is safest, but user wants seamless.
        # Let's check if 'edited_df' differs from 'df' (snapshot).
        
        if not df.equals(edited_df):
            # Find changed rows
            # Iterate and update. (Inefficient for huge data but fine here)
            changes_count = 0
            for index, row in edited_df.iterrows():
                original_row = df.loc[index]
                
                # Check for specific field changes (Price, Cost, Stock, Tax, Pharma)
                if (row['price'] != original_row['price']) or \
                   (row['cost_price'] != original_row['cost_price']) or \
                   (row['stock_quantity'] != original_row['stock_quantity']) or \
                   (row['tax_rate'] != original_row['tax_rate']) or \
                   (row['salt_composition'] != original_row.get('salt_composition')) or \
                   (row['manufacturer'] != original_row.get('manufacturer')) or \
                   (row['schedule_type'] != original_row.get('schedule_type')):
                   
                    db.update_product(row['id'], row['price'], row['cost_price'], row['stock_quantity'], row['tax_rate'], 
                                      row.get('salt_composition'), row.get('manufacturer'), row.get('schedule_type'))
                    changes_count += 1
            
            if changes_count > 0:
                st.toast(f"✅ Updated {changes_count} products!", icon="💾")
                # We need to rerun to refresh the 'original' df so we don't loop update
                # But st.data_editor triggers rerun on edit automatically.
                # We just need to make sure we don't create an infinite loop. 
                # Since we write to DB, next fetch gets new data, so df == edited_df next run.
                # Wait, fetch happens at top. So:
                # 1. Edit happens -> rerun.
                # 2. Fetch gets OLD data (if we didn't write yet).
                # 3. Code sees diff -> Writes to DB.
                # 4. We should probably rerun again to show updated timestamp.
                import time
                time.sleep(0.5) # subtle delay to ensure write
                st.rerun()
    else:
        st.info("No products in inventory yet. Add some using the sidebar!")

render_inventory_table()
