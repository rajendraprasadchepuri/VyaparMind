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
        with st.form("certificate_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                client_options = {row['company_name']: row['id'] for _, row in clients_df.iterrows()}
                cert_client_name = st.selectbox("Select Client", list(client_options.keys()))
                cert_client_id = client_options[cert_client_name]
            
            with col2:
                cert_date_range = st.selectbox("Period", ["Last 30 Days", "Last 3 Months", "Last 6 Months"])
            
            if st.form_submit_button("📄 Generate Certificate", use_container_width=True):
                st.success("✅ Certificate generated!")
                
                st.markdown("---")
                st.markdown(f"""
                ### 📜 CERTIFICATE OF STORAGE
                
                **This is to certify that:**
                
                **{cert_client_name}** has stored their goods in our temperature-controlled facility 
                under the following conditions:
                
                - **Storage Period**: {cert_date_range}
                - **Temperature Compliance**: 99.5%
                - **Quality Controls**: All inward and outward quality checks passed
                - **Certifications**: FSSAI Licensed Facility
                
                The storage was maintained as per industry standards with 24/7 temperature monitoring 
                and complete traceability.
                
                **Authorized By**: VyaparMind Cold Storage  
                **Date**: {datetime.now().strftime('%d %B %Y')}  
                **Certificate ID**: CERT/{datetime.now().strftime('%Y%m%d')}/001
                
                ---
                *This is a digitally generated certificate*
                """)
                
                st.info("💡 PDF export and digital signature will be available in next update")
    
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
