import streamlit as st
import database as db
import pandas as pd
import ui_components as ui

st.set_page_config(page_title="CrowdStock Funding", layout="wide")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("🔮 CrowdStock: Zero-Risk Inventory")
st.markdown("Launch 'Kickstarter' campaigns for new products. Order only if customers pay first.")

tab1, tab2 = st.tabs(["🗳️ Active Campaigns", "🚀 Launch New Idea"])

with tab1:
    st.subheader("Community Voting")
    
    camps = db.get_campaigns()
    if not camps.empty:
        for idx, row in camps.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                
                with c1:
                    st.markdown(f"### {row['item_name']}")
                    st.write(row['description'])
                    st.caption(f"Est Price: ₹{row['price_est']}")
                    
                with c2:
                    current = row['votes_current']
                    needed = row['votes_needed']
                    progress = min(1.0, current / needed)
                    st.progress(progress, text=f"{current} / {needed} Votes")
                    
                with c3:
                    if st.button(f"✋ I Want This!", key=f"vote_{row['id']}"):
                        success, msg = db.vote_campaign(row['id'])
                        if success:
                            if "FUNDED" in msg:
                                st.balloons()
                            st.success(msg)
                            st.rerun()
    else:
        st.info("No active campaigns. Launch one!")

with tab2:
    st.subheader("Test the Market")
    
    with st.form("new_camp"):
        item = st.text_input("Item Name (e.g. Avocado)")
        desc = st.text_area("Pitch (e.g. Premium Hass Avocados, direct from Peru)")
        votes = st.number_input("Votes Needed to Order", value=20)
        price = st.number_input("Estimated Price (₹)", value=100)
        
        if st.form_submit_button("🚀 Launch Campaign"):
            db.create_campaign(item, desc, votes, price)
            st.success("Campaign is LIVE! Customers can now vote.")
            st.rerun()
