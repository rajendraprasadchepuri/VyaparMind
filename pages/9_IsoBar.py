import streamlit as st
import database as db
import pandas as pd
from datetime import datetime
import ui_components as ui
import plotly.express as px

st.set_page_config(page_title="IsoBar Demand Sensing", layout="wide")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("🌡️ IsoBar: Demand Sensing")
st.markdown("Context-Aware Forecasting. Predict sales based on Weather, Events, and History.")

tab1, tab2 = st.tabs(["🔮 Predict & Simulate", "📅 Context Diary"])

# --- TAB 1: PREDICT ---
with tab1:
    st.subheader("Simulate Tomorrow")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.form("sim_form"):
            st.write("#### Future Context")
            sim_weather = st.selectbox("Forecasted Weather", ["None", "Sunny", "Rainy", "Cloudy", "Cold Wave", "Heatwave"])
            sim_event = st.selectbox("Upcoming Event", ["None", "Weekend", "Holiday", "Festival", "Sports Match"])
            
            if st.form_submit_button("Run Prediction 🔮"):
                st.session_state['sim_result'] = db.analyze_context_demand(sim_weather, sim_event)
                st.session_state['sim_context'] = f"{sim_weather} + {sim_event}"

    with col2:
        if 'sim_result' in st.session_state:
            res = st.session_state['sim_result']
            ctx = st.session_state.get('sim_context', '')
            
            if not res.empty:
                st.success(f"### Prediction for: {ctx}")
                st.markdown("Based on historical data with similar conditions, specific items show **abnormal demand spikes**.")
                
                # Visual
                fig = px.bar(res, x='total_qty', y='product_name', orientation='h', title="Expected Top Sellers", color='total_qty')
                st.plotly_chart(fig, use_container_width=True)
                
                st.info("💡 **Recommendation:** Ensure these items are fully stocked in the 'Front Display'.")
            else:
                st.warning(f"Not enough historical data tagged with '{ctx}' to make a prediction.")
                st.caption("Start tagging your daily context in the 'Context Diary' tab to build intelligence!")
        else:
            st.info("Select parameters to see what sells best under those conditions.")

# --- TAB 2: DIARY ---
with tab2:
    st.subheader("Daily Log")
    st.caption("Teach the AI by logging what happened today.")
    
    # Check if today has entry
    today_str = datetime.now().strftime("%Y-%m-%d")
    current_entry = db.get_daily_context(today_str)
    
    # Defaults
    d_weather = current_entry[1] if current_entry else "Sunny"
    d_event = current_entry[2] if current_entry else "None"
    d_notes = current_entry[3] if current_entry else ""
    
    with st.form("diary_form"):
        c1, c2 = st.columns(2)
        with c1:
            date_pick = st.date_input("Date", value=datetime.now())
            weather = st.selectbox("Weather", ["Sunny", "Rainy", "Cloudy", "Cold Wave", "Heatwave"], index=["Sunny", "Rainy", "Cloudy", "Cold Wave", "Heatwave"].index(d_weather) if d_weather in ["Sunny", "Rainy", "Cloudy", "Cold Wave", "Heatwave"] else 0)
        with c2:
            event = st.selectbox("Event / Type", ["None", "Weekend", "Holiday", "Festival", "Sports Match"], index=["None", "Weekend", "Holiday", "Festival", "Sports Match"].index(d_event) if d_event in ["None", "Weekend", "Holiday", "Festival", "Sports Match"] else 0)
            notes = st.text_input("Notes", value=d_notes)
            
        if st.form_submit_button("Save Context"):
            success, msg = db.set_daily_context(date_pick.strftime("%Y-%m-%d"), weather, event, notes)
            if success:
                st.success("Context Saved!")
            else:
                st.error(msg)
