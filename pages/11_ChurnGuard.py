import streamlit as st
import database as db
import pandas as pd
import ui_components as ui

st.set_page_config(page_title="ChurnGuard", layout="wide")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("🛡️ ChurnGuard: Retention Autopilot")
st.markdown("Identify and win back customers who are slipping away.")

# Metrics
churn_df = db.get_churn_metrics(days_threshold=30)
if not churn_df.empty:
    col1, col2, col3 = st.columns(3)
    loss_val = churn_df['total_spent'].sum()
    at_risk_count = len(churn_df)
    
    col1.metric("Revenue at Risk", f"₹{loss_val:,.2f}", delta="-12%", delta_color="inverse")
    col2.metric("Customers at Risk", at_risk_count)
    col3.metric("Win-Back Opportunity", "High")
    
    st.divider()
    
    st.subheader("⚠️ At-Risk VIPs (Last Seen > 30 Days)")
    
    for index, row in churn_df.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
            
            with c1:
                st.subheader(row['name'])
                st.caption(f"Phone: {row['phone']}")
                
            with c2:
                st.markdown("**Days Absent**")
                st.error(f"{int(row['days_since'])} Days")
                
            with c3:
                st.markdown("**Total LTV**")
                st.write(f"₹{row['total_spent']:,.0f}")
                
            with c4:
                st.markdown("**Auto-Action**")
                if st.button("🚀 Send 'Miss You' Offer", key=f"c_{row['id']}"):
                    st.toast(f"Offer sent to +91-{row['phone']}!", icon="📨")
else:
    st.success("✅ No churn risks detected! Your customers are loyal.")
    
# Debug: Show all
with st.expander("Reference: All Customer Stats"):
    st.dataframe(db.fetch_customers())
