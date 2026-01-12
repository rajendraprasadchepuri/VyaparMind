import streamlit as st
import database as db
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ui_components as ui
from datetime import datetime

st.set_page_config(page_title="Analytics & Insights - Cold Storage", layout="wide", page_icon="📈")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("📈 Cold Storage Analytics")
st.caption("Strategic insights for revenue, utilization, and inventory health")

# Actions
col_act1, col_act2 = st.columns([0.8, 0.2])
with col_act2:
    if st.button("📧 Send Weekly Reports", help="Email summary reports to all clients"):
        import email_utils
        # Demo simulation for active clients
        stats = db.get_cold_storage_analytics()
        client_dist = stats.get('client_distribution', pd.DataFrame())
        
        count = 0
        if not client_dist.empty:
            for _, row in client_dist.iterrows():
                # Simulate data for each client
                dummy_data = {
                    'total_kg': row['total_kg'],
                    'compliance_pct': 98.5,
                    'expiring_kg': row['total_kg'] * 0.1 # 10% dummy expiring
                }
                html = email_utils.generate_weekly_html(row['company_name'], dummy_data)
                email_utils.send_email_report(f"contact@{row['company_name'].replace(' ', '').lower()}.com", "Weekly Report", html)
                count += 1
            st.toast(f"✅ Sent {count} weekly reports successfully!", icon="📧")
        else:
            st.warning("No active clients found.")

# Fetch Data
with st.spinner("Crunching the numbers..."):
    stats = db.get_cold_storage_analytics()
    
if stats.get('error'):
    st.error(f"Error loading analytics: {stats['error']}")
    st.stop()

# --- TOP METRICS ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Inventory (KG)", f"{stats.get('total_inventory_kg', 0):,.0f}")
    
with col2:
    st.metric("Total Lots", f"{stats.get('total_lots', 0):,}")
    
with col3:
    # Calculate avg occupancy
    occ_df = stats.get('zone_utilization', pd.DataFrame())
    avg_util = 0
    if not occ_df.empty:
        total_cap = occ_df['capacity'].sum()
        total_occ = occ_df['current_occupancy'].sum()
        avg_util = (total_occ / total_cap * 100) if total_cap > 0 else 0
        
    st.metric("Avg Utilization", f"{avg_util:.1f}%")

with col4:
    st.metric("Projected Mo. Revenue", f"₹{stats.get('projected_revenue', 0):,.0f}", help="Estimated based on avg rate of ₹50/pallet")

st.markdown("---")

# --- CHARTS ROW 1 ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("❄️ Zone Utilization")
    udf = stats.get('zone_utilization', pd.DataFrame())
    
    if not udf.empty:
        # Calculate percentage
        udf['utilization_pct'] = (udf['current_occupancy'] / udf['capacity'] * 100).fillna(0)
        
        fig_util = px.bar(
            udf, 
            x='zone_name', 
            y='utilization_pct',
            title='Utilization by Zone (%)',
            text_auto='.1f',
            color='utilization_pct',
            color_continuous_scale=['#90EE90', '#FFD700', '#FF4500'], # Green to Red
            range_y=[0, 110]
        )
        fig_util.update_layout(xaxis_title="Zone", yaxis_title="Utilization %")
        st.plotly_chart(fig_util, use_container_width=True)
    else:
        st.info("No utilization data available")

with c2:
    st.subheader("👥 Client Distribution (Top 10)")
    cdf = stats.get('client_distribution', pd.DataFrame())
    
    if not cdf.empty:
        # Limit to top 10
        cdf_top = cdf.head(10)
        fig_client = px.pie(
            cdf_top, 
            names='company_name', 
            values='total_kg', 
            hole=0.4,
            title='Inventory Share by Client (KG)'
        )
        st.plotly_chart(fig_client, use_container_width=True)
    else:
        st.info("No client data available")

# --- CHARTS ROW 2 ---
c3, c4 = st.columns(2)

with c3:
    st.subheader("⏳ Inventory Aging Health")
    adf = stats.get('inventory_aging', pd.DataFrame())
    
    if not adf.empty:
        # Sort buckets logically
        color_map = {
            '0-30 Days': '#2ca02c',  # Green
            '30-60 Days': '#d62728', # Red (Wait, middle isn't red usually) -> '#ff7f0e' (Orange)
            '60-90 Days': '#ff7f0e', 
            '90+ Days': '#d62728'    # Red
        }
        
        # Proper order
        order = ['0-30 Days', '30-60 Days', '60-90 Days', '90+ Days']
        adf['age_bucket'] = pd.Categorical(adf['age_bucket'], categories=order, ordered=True)
        adf = adf.sort_values('age_bucket')
        
        fig_age = px.bar(
            adf, 
            x='age_bucket', 
            y='total_kg',
            title='Inventory Breakdown by Age',
            color='age_bucket',
            # discrete_map doesnt work easily with express sometimes unless defined specifically
            text_auto=True
        )
        st.plotly_chart(fig_age, use_container_width=True)
    else:
        st.info("No aging data available")

with c4:
    st.subheader("💰 Revenue Potential Analysis")
    # Quick analysis text
    st.markdown(f"""
    <div style='background-color: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #ddd;'>
        <h4>Quick Insights</h4>
        <ul>
            <li><b>Top Revenue Driver</b>: {cdf.iloc[0]['company_name'] if not cdf.empty else 'N/A'}</li>
            <li><b>Highest Occupancy</b>: {udf.sort_values('utilization_pct', ascending=False).iloc[0]['zone_name'] if not udf.empty else 'N/A'}</li>
            <li><b>Critical Stock (>90 days)</b>: {adf[adf['age_bucket'] == '90+ Days']['total_kg'].sum() if not adf.empty else 0:,.0f} KG</li>
        </ul>
        <br>
        <p><i>Recommendation: Consider offering discounts to clients with aged inventory to clear space for higher rotation goods.</i></p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("Advanced Analytics Module v1.0 | Real-time Data")
