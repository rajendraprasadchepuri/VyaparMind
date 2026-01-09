import streamlit as st
import database as db
import ui_components as ui

st.set_page_config(page_title="Settings", layout="wide")
ui.require_auth()
ui.render_top_header()
st.title("⚙️ Store Settings")

ui.render_sidebar()

st.write("Configure your store details here. These will appear on your Invoices and Dashboard.")

# Fetch current settings
current_name = db.get_setting('store_name') or "VyaparMind Store"
current_address = db.get_setting('store_address') or "Hyderabad, India"
current_phone = db.get_setting('store_phone') or ""
current_gst = db.get_setting('store_gst') or ""
current_tax_rate = db.get_setting('tax_rate') or "0"
current_footer = db.get_setting('invoice_footer') or "Thank you for shopping!"
current_logo = db.get_setting('app_logo') or "Ascending Lotus"

with st.form("settings_form"):
    st.subheader("🏢 Account / Store Details")
    
    c1, c2 = st.columns(2)
    with c1:
        new_name = st.text_input("Store Name", value=current_name)
        new_gst = st.text_input("GSTIN / Tax ID", value=current_gst, placeholder="e.g. 36AAAAA0000A1Z5")
    with c2:
        new_phone = st.text_input("Store Contact Phone", value=current_phone)
        new_tax = st.number_input("Tax Rate (%)", value=float(current_tax_rate), min_value=0.0, step=0.5)
        
    new_address = st.text_area("Store Address", value=current_address)
    new_footer = st.text_input("Invoice Footer Message", value=current_footer, help="Message at bottom of bill")
    
    st.divider()
    st.subheader("🎨 Appearance")
    new_logo = st.selectbox("Application Logo", ["Ascending Lotus", "Classic"], index=0 if current_logo == "Ascending Lotus" else 1)
    
    if st.form_submit_button("Save Settings", type="primary"):
        db.set_setting('store_name', new_name)
        db.set_setting('store_address', new_address)
        db.set_setting('store_phone', new_phone)
        db.set_setting('store_gst', new_gst)
        db.set_setting('tax_rate', str(new_tax))
        db.set_setting('invoice_footer', new_footer)
        db.set_setting('app_logo', new_logo)
        
        st.success("✅ Settings Saved Successfully!")
        st.toast("Settings updated!", icon="💾")
        import time
        time.sleep(1)
        st.rerun()
