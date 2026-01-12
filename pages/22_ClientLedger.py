import streamlit as st
import database as db
import pandas as pd
import json
from datetime import datetime, timedelta
import ui_components as ui

st.set_page_config(page_title="ClientLedger - Billing & Accounts", layout="wide", page_icon="💰")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("💰 ClientLedger - Multi-Client Billing & Accounts")

# --- TAB NAVIGATION ---
tab1, tab2, tab3 = st.tabs(["👥 Client Master", "🧾 Generate Invoice", "📊 Billing Dashboard"])

# TAB 1: CLIENT MASTER
with tab1:
    st.subheader("👥 Storage Client Management")
    
    # Add new client
    with st.expander("➕ Add New Client", expanded=False):
        with st.form("add_client_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input("Company Name *")
                contact_person = st.text_input("Contact Person")
                phone = st.text_input("Phone *")
            
            with col2:
                email = st.text_input("Email")
                gst_number = st.text_input("GST Number")
            
            st.markdown("#### Rate Card Configuration")
            col_r1, col_r2, col_r3 = st.columns(3)
            
            with col_r1:
                storage_rate = st.number_input("Storage Rate (₹/pallet/day)", min_value=0.0, value=50.0, step=5.0)
            with col_r2:
                handling_in = st.number_input("Handling In (₹/ton)", min_value=0.0, value=100.0, step=10.0)
            with col_r3:
                handling_out = st.number_input("Handling Out (₹/ton)", min_value=0.0, value=100.0, step=10.0)
            
            submitted = st.form_submit_button("Add Client", use_container_width=True)
            
            if submitted:
                if company_name and phone:
                    # Create rate card
                    rate_card = {
                        'storage_rate_per_pallet_per_day': storage_rate,
                        'handling_in_per_ton': handling_in,
                        'handling_out_per_ton': handling_out
                    }
                    
                    success, client_id = db.add_storage_client(
                        company_name, contact_person, phone, email, gst_number, rate_card
                    )
                    
                    if success:
                        st.success(f"✅ Client '{company_name}' added successfully!")
                        st.balloons()
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Failed to add client: {client_id}")
                else:
                    st.warning("Company Name and Phone are required")
    
    # List existing clients
    st.markdown("---")
    st.subheader("Existing Clients")
    
    clients_df = db.get_all_storage_clients()
    
    if not clients_df.empty:
        # Parse rate cards for display
        def parse_rate_card(rate_json):
            if rate_json:
                try:
                    rc = json.loads(rate_json)
                    return f"₹{rc.get('storage_rate_per_pallet_per_day', 0)}/pallet/day"
                except:
                    return "N/A"
            return "N/A"
        
        clients_df['rate_display'] = clients_df['rate_card_json'].apply(parse_rate_card)
        
        st.dataframe(
            clients_df[['company_name', 'contact_person', 'phone', 'email', 'gst_number', 'rate_display', 'status']],
            column_config={
                "company_name": "Company",
                "contact_person": "Contact",
                "phone": "Phone",
                "email": "Email",
                "gst_number": "GST",
                "rate_display": "Storage Rate",
                "status": "Status"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No clients registered yet. Add your first client above!")

# TAB 2: GENERATE INVOICE
with tab2:
    st.subheader("🧾 Generate Storage Invoice")
    
    clients_df = db.get_all_storage_clients()
    
    if not clients_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            client_options = {row['company_name']: row['id'] for _, row in clients_df.iterrows()}
            selected_inv_client_name = st.selectbox("Select Client", list(client_options.keys()), key="inv_client")
            selected_inv_client_id = client_options[selected_inv_client_name]
        
        with col2:
            billing_period = st.selectbox("Billing Period", ["This Month", "Last Month", "Custom"])
        
        # Date range
        if billing_period == "This Month":
            from_date = datetime.now().replace(day=1).date()
            to_date = datetime.now().date()
        elif billing_period == "Last Month":
            last_month = datetime.now().replace(day=1) - timedelta(days=1)
            from_date = last_month.replace(day=1).date()
            to_date = last_month.date()
        else:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                from_date = st.date_input("From Date")
            with col_d2:
                to_date = st.date_input("To Date")
        
        st.write(f"**Billing Period**: {from_date} to {to_date}")
        
        if st.button("💰 Calculate Charges", type="primary", use_container_width=True):
            total_charges, line_items = db.calculate_storage_charges(
                selected_inv_client_id, str(from_date), str(to_date)
            )
            
            if line_items:
                st.success(f"✅ Invoice calculated successfully!")
                
                st.markdown("---")
                st.subheader("Invoice Details")
                
                # Client info
                client_info = clients_df[clients_df['id'] == selected_inv_client_id].iloc[0]
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.markdown(f"""
                    **Bill To:**  
                    {client_info['company_name']}  
                    {client_info['contact_person']}  
                    {client_info['phone']}  
                    GST: {client_info['gst_number'] if client_info['gst_number'] else 'N/A'}
                    """)
                
                with col_info2:
                    invoice_num = f"INV/{datetime.now().strftime('%Y%m%d')}/001"
                    st.markdown(f"""
                    **Invoice #:** {invoice_num}  
                    **Date:** {datetime.now().strftime('%d-%b-%Y')}  
                    **Period:** {from_date} to {to_date}  
                    """)
                
                # Line items
                st.markdown("---")
                st.subheader("Itemized Charges")
                
                line_items_df = pd.DataFrame(line_items)
                st.dataframe(
                    line_items_df,
                    column_config={
                        "commodity": "Commodity",
                        "lot": "Lot #",
                        "quantity": st.column_config.NumberColumn("Quantity (KG)", format="%.0f"),
                        "pallets": st.column_config.NumberColumn("Pallets", format="%d"),
                        "days": st.column_config.NumberColumn("Days", format="%d"),
                        "rate": st.column_config.NumberColumn("Rate (₹/pallet/day)", format="₹%.2f"),
                        "amount": st.column_config.NumberColumn("Amount", format="₹%.2f")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Total
                st.markdown("---")
                col_t1, col_t2, col_t3 = st.columns([2, 1, 1])
                
                with col_t2:
                    st.markdown("**Subtotal:**")
                    st.markdown("**GST (18%):**")
                    st.markdown("### **Total:**")
                
                with col_t3:
                    gst = total_charges * 0.18
                    grand_total = total_charges + gst
                    
                    st.markdown(f"₹{total_charges:,.2f}")
                    st.markdown(f"₹{gst:,.2f}")
                    st.markdown(f"### ₹{grand_total:,.2f}")
                
                st.markdown("---")
                
                # PDF Download
                col_pdf1, col_pdf2 = st.columns(2)
                
                with col_pdf1:
                    if st.button("📥 Download PDF Invoice", use_container_width=True, type="primary"):
                        import pdf_utils
                        
                        # Prepare invoice data
                        invoice_data = {
                            'invoice_number': invoice_num,
                            'client_name': client_info['company_name'],
                            'client_gst': client_info['gst_number'] if client_info['gst_number'] else 'N/A',
                            'client_address': client_info.get('email', ''),
                            'invoice_date': datetime.now().strftime('%d-%b-%Y'),
                            'period_from': str(from_date),
                            'period_to': str(to_date),
                            'line_items': line_items,
                            'subtotal': total_charges,
                            'gst_amount': gst,
                            'total': grand_total
                        }
                        
                        # Generate PDF
                        pdf_filename = f"invoice_{invoice_num.replace('/', '_')}.pdf"
                        pdf_path = pdf_utils.generate_invoice_pdf(invoice_data, pdf_filename)
                        
                        # Download button
                        with open(pdf_path, "rb") as pdf_file:
                            st.download_button(
                                label="⬇️ Click to Download PDF",
                                data=pdf_file,
                                file_name=pdf_filename,
                                mime="application/pdf",
                                use_container_width=True
                            )
                        
                        # Clean up
                        import os
                        if os.path.exists(pdf_path):
                            os.remove(pdf_path)
                
                with col_pdf2:
                    st.info("💡 Email invoice feature coming soon!")
            else:
                st.warning("No billable inventory found for this client in the selected period.")
    else:
        st.warning("Please add clients in the Client Master tab first.")

# TAB 3: BILLING DASHBOARD
with tab3:
    st.subheader("📊 Revenue & Billing Analytics")
    
    clients_df = db.get_all_storage_clients()
    
    if not clients_df.empty:
        # Client-wise inventory value
        st.markdown("#### Client-wise Inventory Summary")
        
        summary_data = []
        for _, client in clients_df.iterrows():
            client_inv = db.get_cold_inventory_fefo(client_id=client['id'])
            if not client_inv.empty:
                total_qty = client_inv['quantity'].sum()
                lots = len(client_inv)
                summary_data.append({
                    'Client': client['company_name'],
                    'Total Quantity (KG)': total_qty,
                    'Number of Lots': lots,
                    'Status': client['status']
                })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, hide_index=True, use_container_width=True)
        else:
            st.info("No active inventory to display")
    else:
        st.info("No clients registered yet.")
