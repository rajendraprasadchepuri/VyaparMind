import streamlit as st
import pandas as pd
import database as db
import ui_components as ui
import datetime

st.set_page_config(page_title="ReguBot Compliance", layout="wide")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("👮‍♂️ ReguBot: Narcotic & H1 Compliance")

# --- Feature Gating ---
# We assume this is part of standard 'Professional' or specific module
# Ideally check ui.has_feature('ReguBot')
if not ui.has_feature('ReguBot') and not ui.has_feature('PharmaGuard'):
     st.error("🚫 Access Denied: This feature requires the 'ReguBot' or 'PharmaGuard' module.")
     st.stop()

# --- Filter Controls ---
c1, c2 = st.columns(2)
with c1:
    date_range = st.date_input("Select Date Range", [datetime.date.today(), datetime.date.today()])
with c2:
    status_filter = st.selectbox("Register Type", ["Schedule H1", "Narcotic / X"])

st.markdown("---")

# --- Report Logic ---
# Query Logic:
# Join Transactions -> TransactionItems -> Products
# WHERE product.schedule_type IN (...)
# AND date BETWEEN ...

if len(date_range) == 2:
    d_start, d_end = date_range
    
    # We might need a custom query in database.py or raw SQL here
    # Raw SQL safest for complex join
    conn = db.get_connection()
    c = conn.cursor()
    aid = db.get_current_account_id()
    
    # Schedule Types map
    types = ("'H1'", "'H'") if status_filter == "Schedule H1" else ("'X'", "'Narcotic'")
    
    query = f'''
        SELECT 
            t.timestamp as "Date",
            t.id as "Invoice No",
            c.name as "Patient Name",
            c.phone as "Patient Phone",
            c.city as "Address", -- Assuming City as Address proxy for MVP
            t.doctor_name as "Doctor Name",
            t.doctor_reg_no as "Reg No",
            p.name as "Drug Name",
            ti.quantity as "Qty",
            p.manufacturer as "Manufacturer"
        FROM transactions t
        JOIN transaction_items ti ON t.id = ti.transaction_id
        JOIN products p ON ti.product_id = p.id
        LEFT JOIN customers c ON t.customer_id = c.id
        WHERE t.account_id = ?
        AND date(t.timestamp) BETWEEN ? AND ?
        AND p.schedule_type IN {types}
    '''
    
    # Adapt placeholder for POSTGRES if needed, but assuming SQLite default for now or using db.PLACEHOLDER logic
    # But `types` injection is safeish here as it is from selectbox
    
    try:
        # Use simple ? or %s
        p_holder = "?" if db.config.DB_TYPE == "SQLITE" else "%s"
        # We need to replace ? with %s if postgres, but let's stick to sqlite default 
        # provided by the `db` layer usually, but here we write raw.
        # Let's trust pandas read_sql
        
        # Actually, let's just fetch all potential rows and filter in pandas if volume is low, 
        # or use correct param style.
        
        # Safe Param Style
        q_final = query.replace("?", p_holder)
        
        df = pd.read_sql_query(q_final, conn, params=(aid, d_start, d_end))
        
        st.subheader(f"📄 {status_filter} Register")
        
        if df.empty:
            st.info(f"No transactions found for {status_filter} in this period.")
        else:
            st.dataframe(df, use_container_width=True)
            
            # Export
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download CSV Report (Drug Inspector Format)",
                csv,
                f"H1_Register_{d_start}_{d_end}.csv",
                "text/csv",
                key='download-csv'
            )
            
            # PDF Generation Placeholder
            if st.button("🖨️ Generate PDF Register"):
                st.toast("PDF generation initiated...", icon="📄")
                # Adding actual PDF generation would require FPDF/ReportLab. 
                # For now, CSV is standard requirement.
                st.info("PDF feature coming in next update. Please use CSV for now.")

    except Exception as e:
        st.error(f"Query Error: {e}")
    finally:
        conn.close()
