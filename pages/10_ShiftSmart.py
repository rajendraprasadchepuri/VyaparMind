import streamlit as st
import database as db
import pandas as pd
from datetime import datetime
import ui_components as ui

st.set_page_config(page_title="ShiftSmart Planner", layout="wide")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("👥 ShiftSmart: AI Workforce Planner")
st.markdown("Demand-matched rostering to optimize labor costs.")

tab1, tab2 = st.tabs(["📅 Smart Roster", "👔 Staff Management"])

# --- TAB 1: ROSTER ---
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Plan a Shift")
        
        with st.form("roster_form"):
            date_pick = st.date_input("Select Date", min_value=datetime.now())
            slot = st.selectbox("Shift Slot", ["Morning (9AM-2PM)", "Evening (2PM-9PM)"])
            
            # IsoBar Interpretation
            st.markdown("---")
            st.caption("Step 2: Input expected context for correct sizing")
            w = st.selectbox("Forecast Weather", ["Sunny", "Rainy", "Cloudy", "Cold Wave", "Heatwave"])
            e = st.selectbox("Event", ["None", "Weekend", "Holiday", "Festival"])
            
            if st.form_submit_button("Analyze & Schedule 🤖"):
                # 1. Get Prediction
                needed = db.predict_labor_demand(w, e)
                st.session_state['roster_needed'] = needed
                st.session_state['roster_date'] = date_pick
                st.session_state['roster_slot'] = slot
                
    with col2:
        if 'roster_needed' in st.session_state:
            needed = st.session_state['roster_needed']
            current_date = st.session_state['roster_date']
            current_slot = st.session_state['roster_slot']
            
            st.info(f"🧠 **AI Recommendation**: Based on history ({w}/{e}), you expect high volume. **Suggested Headcount: {needed}**")
            
            # Current Assignments
            shifts_df = db.get_shifts(current_date.strftime("%Y-%m-%d"))
            current_assigned = 0
            if not shifts_df.empty:
                # Filter by slot if we stored slot (we did)
                slot_shifts = shifts_df[shifts_df['slot'] == current_slot]
                current_assigned = len(slot_shifts)
                
                st.write(f"**Currently Assigned to {current_slot}:**")
                for _, row in slot_shifts.iterrows():
                    st.text(f"✅ {row['name']} ({row['role']})")
            
            # Auto-Fill Logic
            to_fill = needed - current_assigned
            if to_fill > 0:
                st.warning(f"⚠️ Understaffed using current roster. Need {to_fill} more.")
                
                if st.button(f"Auto-Assign {to_fill} Available Staff"):
                    all_staff = db.get_all_staff()
                    # Naive assignment: just pick first N who aren't assigned
                    # Exclude already assigned
                    assigned_ids = []
                    if not shifts_df.empty:
                         assigned_ids = shifts_df['staff_id'].tolist()
                    
                    available = all_staff[~all_staff['id'].isin(assigned_ids)]
                    
                    if len(available) >= to_fill:
                        people = available.head(to_fill)
                        for _, p in people.iterrows():
                            db.assign_shift(current_date.strftime("%Y-%m-%d"), current_slot, p['id'])
                        st.success("Staff Assigned! Roster optimized.")
                        st.rerun()
                    else:
                        st.error(f"Not enough staff! Need {to_fill}, but only {len(available)} available.")
            elif to_fill < 0:
                st.warning(f"Overstaffed by {abs(to_fill)}. Consider reducing shift.")
            else:
                st.success("✅ Staffing perfectly matches predicted demand.")

# --- TAB 2: STAFF MANAGER ---
with tab2:
    st.subheader("Employee Directory")
    
    with st.form("add_staff"):
        c1, c2, c3 = st.columns(3)
        n = c1.text_input("Name")
        r = c2.selectbox("Role", ["Store Manager", "Cashier", "Packer/Helper", "Security"])
        rate = c3.number_input("Hourly Rate (₹)", value=100)
        
        if st.form_submit_button("Add Employee"):
            if n:
                db.add_staff(n, r, rate)
                st.success("Employee added.")
                st.rerun()
    
    st.dataframe(db.get_all_staff(), use_container_width=True)
