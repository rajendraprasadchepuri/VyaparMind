import streamlit as st
import database as db
import pandas as pd
import ui_components as ui

st.set_page_config(page_title="StockSwap Network", layout="wide")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("🕸️ StockSwap: Retailer Mesh Network")
st.markdown("Turn your Dead Stock into Cash. Turn your Competitors into Suppliers.")

tab1, tab2 = st.tabs(["🛒 Marketplace Feed", "📢 Broadcast Deal"])

with tab1:
    st.subheader("Live Deals from Nearby Stores")
    
    deals = db.get_b2b_deals()
    if not deals.empty:
        for idx, row in deals.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
                with c1:
                    st.markdown(f"**{row['product_name']}**")
                    st.caption(f"Seller: {row['store_name']}")
                with c2:
                    st.markdown(f"**{row['quantity']} Units**")
                with c3:
                    st.success(f"₹{row['price_per_unit']}/unit")
                with c4:
                    if st.button(f"📞 Contact {row['store_name']}", key=f"deal_{idx}"):
                        st.info(f"Connecting you to {row['acc_phone']}...")
    else:
        st.info("No active deals in the network. Be the first to post!")

with tab2:
    st.subheader("Liquidity Engine")
    st.caption("Got excess stock expiring soon? Sell it at cost to other retailers.")
    
    with st.form("post_deal"):
        c1, c2 = st.columns(2)
        prod = c1.text_input("Product Name")
        qty = c2.number_input("Quantity", min_value=1)
        price = c1.number_input("Price / Unit (Disposal Price)", min_value=0.0)
        phone = c2.text_input("Your Phone Number")
        
        if st.form_submit_button("📢 Broadcast to Network"):
            # In a real app, 'store_name' comes from auth. Using 'My Store' for demo.
            db.create_b2b_deal("My Store (You)", prod, qty, price, phone)
            st.success("Deal is Live! 50 retailers nearby have been notified.")
            st.rerun()
