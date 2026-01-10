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

conn = db.get_connection()
aid = db.get_current_account_id()

# Load Data (Scoped to Account)
transactions = pd.read_sql_query("SELECT * FROM transactions WHERE account_id = ?", conn, params=(aid,))
# Transaction items don't have account_id, but we can filter by transaction_id in the previously filtered transactions
# Actually, the transactions table has account_id, so we should filter transaction_items by joining with transactions
items_query = """
    SELECT ti.* 
    FROM transaction_items ti 
    JOIN transactions t ON ti.transaction_id = t.id 
    WHERE t.account_id = ?
"""
items = pd.read_sql_query(items_query, conn, params=(aid,))
conn.close()

if not transactions.empty:
    transactions['timestamp'] = pd.to_datetime(transactions['timestamp'])
    
    # --- 1. Top Level Metrics (4-Column Grid) ---
    # Calculate KPIs
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Filter for Current Month
    df_curr = transactions[(transactions['timestamp'].dt.month == current_month) & (transactions['timestamp'].dt.year == current_year)]
    # Filter for Previous Month
    prev_month = (datetime.now().replace(day=1) - pd.DateOffset(days=1))
    df_prev = transactions[(transactions['timestamp'].dt.month == prev_month.month) & (transactions['timestamp'].dt.year == prev_month.year)]
    
    # Current Metrics
    curr_rev = df_curr['total_amount'].sum()
    curr_profit = df_curr['total_profit'].sum()
    curr_items = items[items['transaction_id'].isin(df_curr['id'])]['quantity'].sum()
    curr_avg = df_curr['total_amount'].mean() if not df_curr.empty else 0
    
    # Previous Metrics
    prev_rev = df_prev['total_amount'].sum()
    prev_profit = df_prev['total_profit'].sum()
    prev_items = items[items['transaction_id'].isin(df_prev['id'])]['quantity'].sum()
    
    # Calculate Total Revenue (All Time) for Category Insight
    total_rev = transactions['total_amount'].sum()
    
    # Delta Calculations
    def calc_delta(curr, prev):
        if prev == 0: return "100%" if curr > 0 else "0%"
        delta = ((curr - prev) / prev) * 100
        return f"{delta:+.1f}%"

    with st.container():
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Revenue (This Month)", f"₹{curr_rev:,.0f}", delta=calc_delta(curr_rev, prev_rev))
        c2.metric("Net Profit (This Month)", f"₹{curr_profit:,.0f}", delta=calc_delta(curr_profit, prev_profit))
        c3.metric("Items Sold", int(curr_items), delta=calc_delta(curr_items, prev_items))
        c4.metric("Avg Order Value", f"₹{curr_avg:,.0f}") # Added comma logic
    
    st.markdown("---")
    
    # --- 2. Asymmetric "Combination" Layout (Mosaic) ---
    # Row 1: Big Chart Left (2/3), Pie Chart Right (1/3)
    row1_col1, row1_col2 = st.columns([2, 1])
    
    with row1_col1:
        st.subheader("📈 Revenue Trends")
        # Ensure daily grouping works
        daily_sales = transactions.resample('D', on='timestamp').sum().reset_index()
        fig_trend = px.area(daily_sales, x='timestamp', y='total_amount', title="", markers=True, 
                            color_discrete_sequence=['#004e92'])
        fig_trend.update_layout(xaxis_title=None, yaxis_title=None, margin=dict(l=0, r=0, t=0, b=0), height=350)
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with row1_col2:
        st.subheader("Category Distribution")
        # Reuse previous logic for cat_df (Scoped)
        conn = db.get_connection()
        aid = db.get_current_account_id()
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
        
        if not cat_df.empty:
            # Fixed: px.donut does not exist. Use px.pie with hole param.
            fig_pie = px.pie(cat_df, values='revenue', names='category', hole=0.6,
                               color_discrete_sequence=px.colors.sequential.RdBu)
            fig_pie.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=200)
            
            # Stack another metric or chart below in this same column (Combination)
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Mini-insight card below
            top_cat = cat_df.sort_values('revenue', ascending=False).iloc[0]
            st.caption(f"**Insight**: *{top_cat['category']}* is driving **{int(top_cat['revenue']/total_rev*100)}%** of sales.")
        else:
            st.info("No category data.")

    # Row 2: Full Width "Leaderboard" styled as horizontal bars
    st.subheader("🏆 Product Leaderboard")
    top_products = items.groupby('product_name').agg({'quantity': 'sum', 'price_at_sale': 'sum'}).sort_values('quantity', ascending=False).head(5).reset_index()
    
    # Custom HTML Table for "Template" feel
    # We can use st.dataframe with progress bars for a clean look
    st.dataframe(
        top_products,
        column_config={
            "product_name": "Product",
            # Fixed: Cast numpy int64 to native int for JSON serialization
            "quantity": st.column_config.ProgressColumn("Volume Sold", format="%d", min_value=0, max_value=int(top_products['quantity'].max())),
            "price_at_sale": st.column_config.NumberColumn("Revenue Generated", format="₹%.2f")
        },
        use_container_width=True,
        hide_index=True
    )
    
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

else:
    st.info("No sales data available yet. Go to POS and streamline some sales!")
