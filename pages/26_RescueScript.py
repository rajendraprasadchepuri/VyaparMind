import streamlit as st
import pandas as pd
import database as db
import ui_components as ui
import pharma_engine as pharma
import datetime

st.set_page_config(page_title="RescueScript Refill Engine", layout="wide")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("📱 RescueScript: Predictive Refills")

# --- Feature Gating ---
if not ui.has_feature('RescueScript') and not ui.has_feature('PharmaGuard'):
    st.error("🚫 Access Denied: This feature requires the 'RescueScript' or 'PharmaGuard' module.")
    st.stop()

# --- Logic ---
# Auto-scan (lightweight) on load
count = pharma.scan_refills()
if count > 0:
    st.toast(f"Found {count} new refill targets!", icon="🕵️")

# Fetch Data
due_df = pharma.get_due_reminders(days_window=7)

# --- KPIs ---
kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric("Patients Due (7 Days)", len(due_df))
with kpi2:
    rev = due_df['potential_revenue'].sum() if not due_df.empty else 0
    st.metric("Revenue at Risk", f"₹{rev:,.2f}")
with kpi3:
    pending = len(due_df[due_df['status']=='PENDING'])
    st.metric("Pending Actions", pending)

st.markdown("---")

# --- Action Board ---
st.subheader("⚠️ Patients Due for Refill")

if due_df.empty:
    st.info("✅ No patients are due for refills this week.")
else:
    # Custom Grid
    for i, row in due_df.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
            
            with c1:
                st.write(f"**{row['customer_name']}**")
                st.caption(f"📞 {row['customer_phone']}")
            
            with c2:
                st.write(f"💊 **{row['product_name']}**")
                st.caption(f"Last filled: {pd.to_datetime(row['last_purchase_date']).strftime('%d %b')}")
            
            with c3:
                due = pd.to_datetime(row['due_date'])
                days_left = (due - datetime.datetime.now()).days
                
                if days_left < 0:
                    st.error(f"Overdue by {abs(days_left)} days")
                elif days_left == 0:
                    st.warning("Due Today")
                else:
                    st.info(f"Due in {days_left} days")
            
            with c4:
                rid = row['reminder_id']
                status = row['status']
                
                if status == 'PENDING':
                    if st.button("📲 Send WhatsApp", key=f"wa_{rid}", use_container_width=True):
                        succ, msg = pharma.send_whatsapp_reminder(rid)
                        if succ:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    st.success(f"✅ Sent")
