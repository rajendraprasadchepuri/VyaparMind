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
        
        # Initialize session state for invoice
        if 'invoice_data' not in st.session_state:
            st.session_state.invoice_data = None
            
        if st.button("💰 Calculate Charges", type="primary", use_container_width=True):
            total_charges, line_items = db.calculate_storage_charges(
                selected_inv_client_id, str(from_date), str(to_date)
            )
            
            if line_items:
                st.session_state.invoice_data = {
                    'total_charges': total_charges,
                    'line_items': line_items,
                    'client_id': selected_inv_client_id,
                    'from_date': str(from_date),
                    'to_date': str(to_date)
                }
                st.success("✅ Invoice calculated successfully!")
            else:
                st.session_state.invoice_data = None
                st.warning("No billable inventory found for this client in the selected period.")

        # Display Invoice if data exists
        if st.session_state.invoice_data and st.session_state.invoice_data.get('client_id') == selected_inv_client_id:
            data = st.session_state.invoice_data
            
            st.markdown("---")
            st.subheader("Invoice Details")
            
            # Client info
            client_info = clients_df[clients_df['id'] == data['client_id']].iloc[0]
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
                **Period:** {data['from_date']} to {data['to_date']}  
                """)
            
            # Line items
            st.markdown("---")
            st.subheader("Itemized Charges")
            
            line_items_df = pd.DataFrame(data['line_items'])
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
            
            gst = data['total_charges'] * 0.18
            grand_total = data['total_charges'] + gst
            
            with col_t2:
                st.markdown("**Subtotal:**")
                st.markdown("**GST (18%):**")
                st.markdown("### **Total:**")
            
            with col_t3:
                st.markdown(f"₹{data['total_charges']:,.2f}")
                st.markdown(f"₹{gst:,.2f}")
                st.markdown(f"### ₹{grand_total:,.2f}")
            
            st.markdown("---")
            
            # PDF Generation - Prepare Data
            branding_info = db.get_account_branding(db.get_current_account_id())
            invoice_pdf_data = {
                'branding': branding_info,
                'invoice_number': invoice_num,
                'client_name': client_info['company_name'],
                'client_gst': client_info['gst_number'] if client_info['gst_number'] else 'N/A',
                'client_address': client_info.get('email', ''),
                'invoice_date': datetime.now().strftime('%d-%b-%Y'),
                'period_from': data['from_date'],
                'period_to': data['to_date'],
                'line_items': data['line_items'],
                'subtotal': data['total_charges'],
                'gst_amount': gst,
                'total': grand_total
            }
            
            col_pdf1, col_pdf2 = st.columns(2)
            
            with col_pdf1:
                # Generate PDF immediately so download button has content
                import pdf_utils
                import os
                
                pdf_filename = f"Invoice_{invoice_num.replace('/', '_')}.pdf"
                try:
                    # Always regenerate to ensure latest version/fixes
                    pdf_utils.generate_invoice_pdf(invoice_pdf_data, pdf_filename)
                    
                    with open(pdf_filename, "rb") as f:
                        pdf_bytes = f.read()
                        
                    st.download_button(
                        label="📥 Download PDF Invoice",
                        data=pdf_bytes,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error generating PDF: {e}")

            with col_pdf2:
                if st.button("📧 Email Invoice to Client", use_container_width=True):
                    client_email = client_info.get('email')
                    if client_email and "@" in client_email:
                        try:
                            import email_utils
                            import pdf_utils
                            
                            # Ensure PDF exists for attachment
                            pdf_path_email = f"Invoice_Email_{invoice_num.replace('/', '_')}.pdf"
                            pdf_utils.generate_invoice_pdf(invoice_pdf_data, pdf_path_email)
                            
                            # Send Email
                            subject = f"Invoice {invoice_num} from VyaparMind Cold Storage"
                            body = f"""
                            <html>
                            <body>
                                <h3>Invoice Ready</h3>
                                <p>Dear {client_info['contact_person'] or 'Customer'},</p>
                                <p>Please find attached the invoice for the period <b>{data['from_date']} to {data['to_date']}</b>.</p>
                                <p><b>Total Amount:</b> ₹{grand_total:,.2f}</p>
                                <br>
                                <p>Thank you for your business!</p>
                            </body>
                            </html>
                            """
                            
                            success, msg = email_utils.send_email_report(client_email, subject, body, attachment_path=pdf_path_email)
                            
                            if success:
                                st.success(f"✅ Invoice emailed to {client_email} successfully!")
                            else:
                                st.error(f"❌ Failed to send email: {msg}")
                                
                            # Cleanup Email PDF
                            if os.path.exists(pdf_path_email):
                                os.remove(pdf_path_email)
                                
                        except Exception as e:
                            st.error(f"Error processing email: {e}")
                    else:
                        st.error("Client does not have a valid email address configured.")
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
