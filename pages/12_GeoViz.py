import streamlit as st
import database as db
import pandas as pd
import ui_components as ui
import plotly.express as px

st.set_page_config(page_title="GeoViz Intelligence", layout="wide")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("🗺️ GeoViz: Catchment Analysis")
st.markdown("Visualize where your revenue is coming from.")

try:
    geo_df = db.get_geo_revenue()
except Exception as e:
    st.error("Error fetching geo data. Please ensure 'city' column exists in customers.")
    geo_df = pd.DataFrame()

if not geo_df.empty:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Revenue by Neighborhood / City")
        # Treemap
        fig = px.treemap(geo_df, path=['city'], values='revenue', title="Revenue Heatmap", color='revenue', color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("Top Performers")
        st.dataframe(geo_df[['city', 'revenue']], hide_index=True, use_container_width=True)
        
    st.info("💡 ** Insight**: Target marketing campaigns in your top-performing cities to double-down on growth.")
else:
    st.caption("No geographic data available yet. Add 'City' to your customers.")
    
# Mock Data Generator
with st.expander("🔧 Dev Tools: Impute Mock City Data"):
    st.write("Click this to assign random cities to existing customers for demo.")
    if st.button("Randomize Cities"):
        # We need a direct update hack here for demo
        import secrets
        cities = ["Mumbai", "Delhi", "Bangalore", "Pune", "Hyderabad", "Sector 15", "Sector 22"]
        aid = db.get_current_account_id()
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM customers WHERE account_id = ?", (aid,))
        ids = c.fetchall()
        for i in ids:
            curr_city = secrets.choice(cities)
            c.execute("UPDATE customers SET city = ? WHERE id = ? AND account_id = ?", (curr_city, i[0], aid))
        conn.commit()
        conn.close()
        st.success("Mock Data Injected! Refresh page.")
        st.rerun()
