import streamlit as st
import database as db
import pandas as pd
import ui_components as ui
import shelf_engine as engine

st.set_page_config(page_title="ShelfSense", layout="wide")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("🧬 ShelfSense: Scientific Merchandising")
st.markdown("Optimize your shelf layout using **Chemistry** and **Consumer Psychology**.")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🛒 Virtual Shelf Simulator")
    st.info("Drag and drop logic (Simulated via Selectboxes). Arrange your items.")
    
    # 3x3 Grid Simulator
    # Initialize state for grid if not exists
    if 'shelf_grid' not in st.session_state:
        st.session_state['shelf_grid'] = [
            ["Apple", "Banana", "None"],
            ["Bread", "Milk", "Beer"],
            ["None", "Diapers", "None"]
        ]

    # Available Products for Dropdown (Simplified list for prototype)
    options = ["None", "Apple", "Banana", "Potato", "Onion", "Chips", "Coke", "Beer", "Diapers", "Bread", "Milk", "Jam"]
    
    # Render Grid
    grid_ui = []
    for r in range(3):
        cols = st.columns(3)
        row_data = []
        for c in range(3):
            with cols[c]:
                # Unique key for every cell
                val = st.selectbox(f"Slot {r+1}-{c+1}", options, 
                                   index=options.index(st.session_state['shelf_grid'][r][c]) if st.session_state['shelf_grid'][r][c] in options else 0,
                                   key=f"grid_{r}_{c}",
                                   label_visibility="collapsed")
                row_data.append(val if val != "None" else None)
        grid_ui.append(row_data)
    
    # Button to Analyze
    if st.button("🧪 Analyze Layout Science"):
        st.session_state['shelf_grid'] = grid_ui
        st.rerun()

with col2:
    st.subheader("🔬 Analysis Results")
    
    # Run Analysis
    current_grid = st.session_state['shelf_grid']
    score, logs = engine.analyze_grid(current_grid)
    
    # Score Display
    if score >= 80:
        st.success(f"## Innovation Score: {score}/100")
    elif score >= 50:
        st.warning(f"## Innovation Score: {score}/100")
    else:
        st.error(f"## Innovation Score: {score}/100")
        
    st.divider()
    
    if not logs:
        st.caption("No strong interactions detected. Try combining different items.")
    else:
        for log in logs:
            if "🚨" in log:
                st.error(log)
            elif "✅" in log:
                st.success(log)
            elif "🏆" in log:
                st.balloons()
                st.success(log)
                
    st.markdown("### Knowledge Base")
    with st.expander("See Scientific Rules"):
        st.json(engine.KNOWLEDGE_BASE)
