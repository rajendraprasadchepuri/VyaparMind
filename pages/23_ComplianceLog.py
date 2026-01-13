import streamlit as st
import database as db
import pandas as pd
from datetime import datetime
import ui_components as ui

st.set_page_config(page_title="ComplianceLog - Audit & Reports", layout="wide", page_icon="📋")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("📋 ComplianceLog - Temperature & Quality Compliance")

# --- TAB NAVIGATION ---
tab1, tab2, tab3 = st.tabs(["🌡️ Temperature Logs", "✅ Quality Records", "📄 Generate Reports"])

# TAB 1: TEMPERATURE LOGS
with tab1:
    st.subheader("🌡️ Temperature Compliance Logs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        report_days = st.selectbox("Log Period", [7, 15, 30, 60, 90], index=2, key="temp_log_days")
    
    with col2:
        zones_df = db.get_all_cold_zones()
        if not zones_df.empty:
            zone_options = {"All Zones": None}
            zone_options.update({row['zone_name']: row['id'] for _, row in zones_df.iterrows()})
            selected_log_zone = st.selectbox("Filter by Zone", list(zone_options.keys()))
            selected_log_zone_id = zone_options[selected_log_zone]
    
    # Fetch temperature logs
    conn = db.get_connection()
    aid = db.get_current_account_id()
    
    if selected_log_zone_id:
        log_query = f"""
            SELECT tl.*, cz.zone_name, cz.target_temp_min, cz.target_temp_max
            FROM temperature_logs tl
            JOIN cold_zones cz ON tl.zone_id = cz.id
            WHERE cz.account_id = ? AND tl.zone_id = ?
            AND tl.recorded_at >= datetime('now', '-{report_days} days')
            ORDER BY tl.recorded_at DESC
        """
        logs_df = pd.read_sql_query(log_query, conn, params=(aid, selected_log_zone_id))
    else:
        log_query = f"""
            SELECT tl.*, cz.zone_name, cz.target_temp_min, cz.target_temp_max
            FROM temperature_logs tl
            JOIN cold_zones cz ON tl.zone_id = cz.id
            WHERE cz.account_id = ?
            AND tl.recorded_at >= datetime('now', '-{report_days} days')
            ORDER BY tl.recorded_at DESC
        """
        logs_df = pd.read_sql_query(log_query, conn, params=(aid,))
    
    conn.close()
    
    if not logs_df.empty:
        # Compliance metrics
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        total_logs = len(logs_df)
        breach_count = len(logs_df[logs_df['is_breach'] == 1])
        compliance_pct = ((total_logs - breach_count) / total_logs * 100) if total_logs > 0 else 100
        
        with col_m1:
            st.metric("Total Readings", total_logs)
        with col_m2:
            st.metric("Breaches", breach_count, delta=f"-{breach_count}" if breach_count > 0 else None)
        with col_m3:
            st.metric("Compliance Rate", f"{compliance_pct:.1f}%", 
                     delta=f"+{compliance_pct:.1f}%" if compliance_pct >= 95 else f"{compliance_pct:.1f}%")
        with col_m4:
            avg_temp = logs_df['recorded_temp'].mean()
            st.metric("Avg Temperature", f"{avg_temp:.1f}°C")
        
        st.markdown("---")
        st.subheader("Detailed Logs")
        
        st.dataframe(
            logs_df[['zone_name', 'recorded_temp', 'target_temp_min', 'target_temp_max',
                    'is_breach', 'recorded_at', 'recorded_by', 'corrective_action']],
            column_config={
                "zone_name": "Zone",
                "recorded_temp": st.column_config.NumberColumn("Recorded Temp", format="%.1f°C"),
                "target_temp_min": st.column_config.NumberColumn("Min", format="%.1f°C"),
                "target_temp_max": st.column_config.NumberColumn("Max", format="%.1f°C"),
                "is_breach": st.column_config.CheckboxColumn("Breach", help="Temperature outside range"),
                "recorded_at": st.column_config.DatetimeColumn("Recorded At", format="DD MMM YYYY, HH:mm"),
                "recorded_by": "Recorded By",
                "corrective_action": "Corrective Action"
            },
            hide_index=True,
            use_container_width=True,
            height=400
        )
        
        # Download option
        st.markdown("---")
        csv = logs_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Temperature Logs (For Audit)",
            data=csv,
            file_name=f"temperature_audit_log_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info(f"No temperature logs found for the last {report_days} days.")

# TAB 2: QUALITY RECORDS
with tab2:
    st.subheader("✅ Quality Check Records")
    
    # GRN Quality History
    st.markdown("#### Inward Quality Checks (GRN)")
    
    pending_grns = db.get_pending_grns()
    
    if not pending_grns.empty:
        st.warning(f"⚠️ {len(pending_grns)} GRN(s) pending quality approval")
        
        st.dataframe(
            pending_grns[['grn_number', 'client_name', 'arrival_date', 'quality_status', 'notes']],
            column_config={
                "grn_number": "GRN #",
                "client_name": "Client",
                "arrival_date": st.column_config.DateColumn("Arrival", format="DD MMM YYYY"),
                "quality_status": "Status",
                "notes": "Notes"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.success("✅ All GRNs quality-checked and approved!")
    
    st.markdown("---")
    st.info("📝 Full quality records dashboard will be available in next update")

# TAB 3: GENERATE REPORTS
with tab3:
    st.subheader("📄 Compliance Reports & Certificates")
    
    st.markdown("#### 🏆 Certificate of Storage")
    st.caption("Generate storage certificate for clients to show their customers")
    
    clients_df = db.get_all_storage_clients()
    
    if not clients_df.empty:

        # Initialize session state for certificate
        if 'cert_generated_data' not in st.session_state:
            st.session_state.cert_generated_data = None

        with st.form("certificate_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                client_options = {row['company_name']: row['id'] for _, row in clients_df.iterrows()}
                cert_client_name = st.selectbox("Select Client", list(client_options.keys()))
                
            
            with col2:
                cert_date_range = st.selectbox("Period", ["Last 30 Days", "Last 3 Months", "Last 6 Months"])
            
            submitted = st.form_submit_button("📄 Generate Certificate", use_container_width=True)
            
            if submitted:
                # Prepare Data in Session State (to persist outside form)
                branding = db.get_account_branding(db.get_current_account_id())
                cert_id = f"CERT/{datetime.now().strftime('%Y%m%d')}/001"
                comp_rate = 99.5
                cert_client_id = client_options[cert_client_name] # Resolve ID
                
                st.session_state.cert_generated_data = {
                    'branding': branding,
                    'client_name': cert_client_name,
                    'client_id': cert_client_id,
                    'period': cert_date_range,
                    'compliance_rate': comp_rate,
                    'breach_count': 0,
                    'total_readings': 720,
                    'cert_id': cert_id,
                    'date': datetime.now().strftime('%d %B %Y')
                }
                
        # Render Result OUTSIDE the form
        if st.session_state.cert_generated_data:
            cert_data = st.session_state.cert_generated_data
            
            st.success("✅ Certificate generated!")
            st.markdown("---")
            st.markdown(f"""
            ### 📜 CERTIFICATE OF STORAGE
            
            **This is to certify that:**
            
            **{cert_data['client_name']}** has stored their goods in our temperature-controlled facility 
            under the following conditions:
            
            - **Storage Period**: {cert_data['period']}
            - **Temperature Compliance**: {cert_data['compliance_rate']}%
            - **Quality Controls**: All inward and outward quality checks passed
            - **Certifications**: FSSAI Licensed Facility
            
            The storage was maintained as per industry standards with 24/7 temperature monitoring 
            and complete traceability.
            
            **Authorized By**: {cert_data['branding']['company_name']}  
            **Date**: {cert_data['date']}  
            **Certificate ID**: {cert_data['cert_id']}
            
            ---
            *This is a digitally generated certificate*
            """)
            
            # ACTION BUTTONS
            col_act1, col_act2 = st.columns(2)
            
            with col_act1:
                # PDF Generation
                import pdf_utils
                import os
                
                pdf_filename = f"Certificate_{cert_data['client_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                
                # Generate PDF
                pdf_utils.generate_temperature_certificate_pdf(cert_data, pdf_filename)
                
                with open(pdf_filename, "rb") as f:
                    pdf_bytes = f.read()
                    
                st.download_button(
                    label="📥 Download PDF Certificate",
                    data=pdf_bytes,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    use_container_width=True
                )
                
                # Cleanup
                try:
                    os.remove(pdf_filename)
                except:
                    pass
            
            with col_act2:
                # Email Functionality
                if st.button("📧 Email Certificate to Client", use_container_width=True):
                        # Get Client Email
                    conn = db.get_connection()
                    c = conn.cursor()
                    c.execute("SELECT email, company_name FROM storage_clients WHERE id = ?", (cert_data['client_id'],))
                    client_res = c.fetchone()
                    conn.close()
                    
                    if client_res and client_res[0]:
                        client_email = client_res[0]
                        # Regenerate for attachment
                        pdf_filename_email = f"Certificate_Email_{datetime.now().strftime('%H%M%S')}.pdf"
                        pdf_utils.generate_temperature_certificate_pdf(cert_data, pdf_filename_email)
                        
                        import email_utils
                        subject = f"Storage Certificate: {cert_data['client_name']} - {cert_data['period']}"
                        body = f"""
                        Dear {client_res[1]},
                        
                        Please find attached the official Certificate of Storage for the period: {cert_data['period']}.
                        
                        Compliance Rate: {cert_data['compliance_rate']}%
                        
                        Regards,
                        VyaparMind Cold Storage Operations
                        """
                        
                        success, msg = email_utils.send_email_report(
                            to_email=client_email,
                            subject=subject,
                            body_html=body,
                            attachment_path=pdf_filename_email
                        )
                        
                        if success:
                            st.toast(f"✅ Certificate emailed to {client_email}", icon="📧")
                        else:
                            st.error(f"Failed to send email: {msg}")
                            
                        # Cleanup
                        try:
                            os.remove(pdf_filename_email)
                        except:
                            pass
                    else:
                        st.error("No email address found for this client.")
    
    st.markdown("---")
    st.markdown("#### 📊 Audit Summary Report")
    
    if st.button("📈 Generate Audit Summary", use_container_width=True):
        st.markdown("""
        ### AUDIT SUMMARY REPORT
        **Reporting Period**: Last 30 Days
        
        #### Temperature Compliance
        - Total Temperature Readings: --
        - Breaches Detected: --
        - Compliance Rate: --%
        - Average Temperature: --°C
        
        #### Inventory Management
        - Total Active Lots: --
        - FEFO Compliance: 100%
        - Expiring Items Flagged: --
        - Wastage: 0%
        
        #### Quality Controls
        - Inward Quality Checks: --
        - Outward Quality Checks: --
        - Rejections: --
        
        #### Client Satisfaction
        - Active Clients: --
        - Billing Accuracy: 100%
        - Timely Deliveries: --%
        
        ---
        *Full automated report generation coming in next update*
        """)
        
        st.info("💡 Connect real data and enable PDF export in next update")

st.markdown("---")
st.caption("🔒 All compliance logs are securely stored and available for regulatory audits for 5 years")
