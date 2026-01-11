import streamlit as st
import database as db
import pandas as pd
import plotly.express as px
from datetime import datetime
import ui_components as ui

st.set_page_config(page_title="VyaparMind Analytics", layout="wide")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()
st.title("📊 VyaparMind Insight")

# --- CUSTOM CSS FOR METRIC CARDS ---
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        height: 140px; /* Fixed Height */
        display: flex;
        flex-direction: column;
        justify-content: center;
        overflow: hidden;
    }
    div[data-testid="stMetric"] > div {
        width: 100%;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #666;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: bold;
        color: #333;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# Optimized Data Fetching (SQL Aggregation)
# Instead of loading ALL transactions, we fetch aggregated metrics directly.
# This scales to millions of records.
conn = db.get_connection()
aid = db.get_current_account_id()

# Dates
now = datetime.now()
curr_month = now.month
curr_year = now.year

# Previous Month Logic
first_of_this_month = now.replace(day=1)
last_month = first_of_this_month - pd.DateOffset(days=1)
prev_month_num = last_month.month
prev_year_num = last_month.year

# --- 1. Top Level Metrics (Optimized) ---
# Current Month Metrics
q_curr = """
    SELECT 
        SUM(t.total_amount) as revenue,
        SUM(t.total_profit) as profit,
        SUM(ti.quantity) as items_sold,
        AVG(t.total_amount) as avg_order
    FROM transactions t
    LEFT JOIN transaction_items ti ON t.id = ti.transaction_id
    WHERE t.account_id = ? 
    AND strftime('%m', t.timestamp) = ? 
    AND strftime('%Y', t.timestamp) = ?
"""
# Note: strftime returns '01', '02' etc. Python str(month) might be '1'. Pad it.
c_m_str = f"{curr_month:02d}"
c_y_str = str(curr_year)

curr_df = pd.read_sql_query(q_curr, conn, params=(aid, c_m_str, c_y_str))
curr_metrics = curr_df.iloc[0]

# Previous Month Metrics
q_prev = """
    SELECT 
        SUM(t.total_amount) as revenue,
        SUM(t.total_profit) as profit,
        SUM(ti.quantity) as items_sold
    FROM transactions t
    LEFT JOIN transaction_items ti ON t.id = ti.transaction_id
    WHERE t.account_id = ? 
    AND strftime('%m', t.timestamp) = ? 
    AND strftime('%Y', t.timestamp) = ?
"""
p_m_str = f"{prev_month_num:02d}"
p_y_str = str(prev_year_num)

prev_df = pd.read_sql_query(q_prev, conn, params=(aid, p_m_str, p_y_str))
prev_metrics = prev_df.iloc[0]

conn.close()

# Prepare Values (Handle None from SQL SUM if 0 records)
c_rev = curr_metrics['revenue'] or 0
c_prof = curr_metrics['profit'] or 0
c_items = curr_metrics['items_sold'] or 0
c_avg = curr_metrics['avg_order'] or 0

p_rev = prev_metrics['revenue'] or 0
p_prof = prev_metrics['profit'] or 0
p_items = prev_metrics['items_sold'] or 0

# Delta Logic
def calc_delta(curr, prev):
    if prev == 0: return "100%" if curr > 0 else "0%"
    delta = ((curr - prev) / prev) * 100
    return f"{delta:+.1f}%"

with st.container():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue (This Month)", f"₹{c_rev:,.0f}", delta=calc_delta(c_rev, p_rev))
    c2.metric("Net Profit (This Month)", f"₹{c_prof:,.0f}", delta=calc_delta(c_prof, p_prof))
    c3.metric("Items Sold", int(c_items), delta=calc_delta(c_items, p_items))
    c4.metric("Avg Order Value", f"₹{c_avg:,.0f}")

st.markdown("---")

# --- 2. Charts (Optimized) ---
# Row 1: Big Chart Left (2/3), Pie Chart Right (1/3)
row1_col1, row1_col2 = st.columns([2, 1])

with row1_col1:
    st.subheader("📈 Revenue Trends (Daily)")
    # Optimized Trend Query (Group by Date in SQL)
    conn = db.get_connection()
    aid = db.get_current_account_id()
    q_trend = """
        SELECT date(timestamp) as date, SUM(total_amount) as total_amount
        FROM transactions 
        WHERE account_id = ?
        GROUP BY date(timestamp)
        ORDER BY date(timestamp) ASC
    """
    trend_df = pd.read_sql_query(q_trend, conn, params=(aid,))
    
    if not trend_df.empty:
        fig_trend = px.area(trend_df, x='date', y='total_amount', title="", markers=True, 
                            color_discrete_sequence=['#004e92'])
        fig_trend.update_layout(xaxis_title=None, yaxis_title=None, margin=dict(l=0, r=0, t=0, b=0), height=350)
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No sales data for trends.")

with row1_col2:
    st.subheader("Category Distribution")
    # Category Query (Optimized Group By)
    cat_query = '''
        SELECT p.category, SUM(ti.quantity * ti.price_at_sale) as revenue
        FROM transaction_items ti
        JOIN products p ON ti.product_id = p.id
        JOIN transactions t ON ti.transaction_id = t.id
        WHERE t.account_id = ?
        GROUP BY p.category
    '''
    cat_df = pd.read_sql_query(cat_query, conn, params=(aid,))
    conn.close()
    
    # Calculate Total Revenue for Insight (All Time)
    # We need total revenue from db for the percentage calc
    conn = db.get_connection() # Open fresh or reuse if open (it was closed above)
    # Re-open for isolated logic or keep open? Let's just quick query.
    total_rev_all = pd.read_sql_query("SELECT SUM(total_amount) FROM transactions WHERE account_id=?", conn, params=(aid,)).iloc[0][0] or 1
    conn.close()

    if not cat_df.empty:
        fig_pie = px.pie(cat_df, values='revenue', names='category', hole=0.6,
                           color_discrete_sequence=px.colors.sequential.RdBu)
        fig_pie.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=200)
        
        st.plotly_chart(fig_pie, use_container_width=True)
        
        top_cat = cat_df.sort_values('revenue', ascending=False).iloc[0]
        st.caption(f"**Insight**: *{top_cat['category']}* is driving **{int(top_cat['revenue']/total_rev_all*100)}%** of sales.")
    else:
        st.info("No category data.")

    # Row 2: Full Width "Leaderboard" styled as horizontal bars
st.subheader("🏆 Product Leaderboard")

conn = db.get_connection()
aid = db.get_current_account_id()

leaderboard_query = """
    SELECT 
        ti.product_name, 
        SUM(ti.quantity) as quantity, 
        SUM(ti.price_at_sale * ti.quantity) as price_at_sale
    FROM transaction_items ti
    JOIN transactions t ON ti.transaction_id = t.id
    WHERE t.account_id = ?
    GROUP BY ti.product_name
    ORDER BY quantity DESC
    LIMIT 5
"""
top_products = pd.read_sql_query(leaderboard_query, conn, params=(aid,))
conn.close()

if not top_products.empty:
    # Custom HTML Table for "Template" feel
    # We can use st.dataframe with progress bars for a clean look
    st.dataframe(
        top_products,
        column_config={
            "product_name": "Product",
            "quantity": st.column_config.ProgressColumn("Volume Sold", format="%d", min_value=0, max_value=int(top_products['quantity'].max())),
            "price_at_sale": st.column_config.NumberColumn("Revenue Generated", format="₹%.2f")
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No product sales yet.")

st.markdown("---")

# --- 3. Customer Insights (Marketing) ---
st.subheader("👥 Customer Insights (Marketing)")

conn = db.get_connection()
aid = db.get_current_account_id()
try:
    # Check if we have customer data linked (Scoped)
    cust_query = '''
        SELECT c.name, c.email, COUNT(t.id) as visits, SUM(t.total_amount) as total_spend, MAX(t.timestamp) as last_visit
        FROM transactions t
        JOIN customers c ON t.customer_id = c.id
        WHERE t.account_id = ?
        GROUP BY c.id
        ORDER BY total_spend DESC
        LIMIT 10
    '''
    top_customers = pd.read_sql_query(cust_query, conn, params=(aid,))
    
    if not top_customers.empty:
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.markdown("#### Top Spenders (VIPs)")
            st.dataframe(
                top_customers[['name', 'visits', 'total_spend', 'last_visit']],
                column_config={
                    "name": "Customer",
                    "visits": st.column_config.NumberColumn("Visits", format="%d"),
                    "total_spend": st.column_config.ProgressColumn("Total Spend", format="₹%d", min_value=0, max_value=int(top_customers['total_spend'].max())),
                    "last_visit": st.column_config.DatetimeColumn("Last Seen", format="D MMM YYYY")
                },
                use_container_width=True,
                hide_index=True
            )
        
        with c2:
            st.markdown("#### Quick Stats")
            avg_val = top_customers['total_spend'].mean()
            retention = len(top_customers[top_customers['visits'] > 1])
            
            st.metric("Avg VIP Value", f"₹{avg_val:,.0f}")
            st.metric("Returning Customers", retention, help="Customers with > 1 visit")
            
            if retention > 0:
                st.success(f"🚀 {retention} loyal customers identified!")
            else:
                st.info("Tip: Encourage repeat visits!")
                
    else:
        st.info("No customer transaction data yet. Use the POS 'Customer Details' feature to tag sales!", icon="ℹ️")
        
except Exception as e:
    st.error(f"Could not load customer data: {e}")
finally:
    conn.close()
