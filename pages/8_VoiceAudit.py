import streamlit as st
import database as db
import nlp_engine as nlp
import pandas as pd
import ui_components as ui

st.set_page_config(page_title="Voice Inventory Audit", layout="wide")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()

st.title("🗣️ VoiceAudit: Hands-Free Inventory")

# Instructions
st.info("💡 **Tip:** Tap the microphone on your mobile keyboard and speak commands like: *'Add 50 packets of Maggi'* or *'Set stock of Coke to 20'*.")

# Initialize Session State for Log
if 'audit_log' not in st.session_state:
    st.session_state['audit_log'] = []

# --- Input Area ---
with st.container(border=True):
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # The "Dictation" Box
        command = st.text_input("🎤 Dictate Command Here:", placeholder="Listening... (Type or Speak)", key="voice_input")
        
    with col2:
        st.write("") # Spacer
        st.write("")
        if st.button("Process Command 🚀", type="primary", use_container_width=True):
            if command:
                with st.spinner("Analyzing..."):
                    # 1. Parse
                    parsed = nlp.parse_voice_command(command)
                    
                    if parsed['status_msg'] == "Success":
                        # 2. Execute
                        success, exec_msg = nlp.execute_parsed_command(parsed)
                        
                        # 3. Log
                        log_entry = {
                            "command": command,
                            "action": parsed['action'],
                            "product": parsed['product_name'],
                            "qty": parsed['qty'],
                            "status": "✅ Success" if success else "❌ Failed",
                            "message": exec_msg
                        }
                        st.session_state['audit_log'].insert(0, log_entry) # Add to top
                        
                        if success:
                            st.success(f"Executed: {exec_msg}")
                        else:
                            st.error(f"Execution Failed: {exec_msg}")
                            
                    else:
                        # Parse Failed
                        log_entry = {
                            "command": command,
                            "action": parsed['action'],
                            "product": parsed['product_name'] or "???",
                            "qty": parsed['qty'],
                            "status": "⚠️ Unclear",
                            "message": parsed['status_msg']
                        }
                        st.session_state['audit_log'].insert(0, log_entry)
                        st.warning(f"Did not understand: {parsed['status_msg']}")
            else:
                st.warning("Please speak or type a command first.")

# --- Audit Log ---
st.subheader("📝 Activity Log")

if st.session_state['audit_log']:
    # Display log
    for entry in st.session_state['audit_log']:
        # Color coding
        s_color = "green" if "Success" in entry['status'] else "red" if "Failed" in entry['status'] else "orange"
        
        with st.expander(f":{s_color}[{entry['status']}] {entry['command']}"):
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Action:** {entry['action']}")
            c2.write(f"**Product:** {entry['product']}")
            c3.write(f"**Qty:** {entry['qty']}")
            st.caption(f"System Message: {entry['message']}")
else:
    st.caption("No voice commands processed yet.")

# --- Quick Reference of Products ---
with st.expander("🔎 Product Reference List"):
    df = db.fetch_all_products()
    st.dataframe(df[['name', 'stock_quantity']], use_container_width=True)
