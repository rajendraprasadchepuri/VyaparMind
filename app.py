import streamlit as st
import database as db
import pandas as pd

# Page Config
st.set_page_config(
    page_title="VyaparMind",
    page_icon="🧠",
    layout="wide"
)

import ui_components as ui

# Initialize DB
db.init_db()

ui.render_sidebar()

# Main Page Content
st.title("🧠 VyaparMind: Intelligent Retail")

st.markdown("""
### Welcome to your Retail Management System
Use the sidebar to navigate between modules.

**Quick Status:**
""")

# Quick Stats (if DB has data)
try:
    conn = db.get_connection()
    product_count = pd.read_sql_query("SELECT COUNT(*) as count FROM products", conn).iloc[0]['count']
    transaction_count = pd.read_sql_query("SELECT COUNT(*) as count FROM transactions", conn).iloc[0]['count']
    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Products", product_count)
    col2.metric("Total Transactions", transaction_count)
    col3.metric("System Status", "Online 🟢")

except Exception as e:
    st.error(f"Database Error: {e}")

st.divider()
st.info("👈 Select **Inventory**, **POS**, or **Dashboard** from the sidebar to begin.")
