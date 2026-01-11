
import streamlit as st
import database as db
import pandas as pd
from datetime import datetime
import ui_components as ui
import json

st.set_page_config(layout="wide", page_title="Kitchen Display System")

ui.render_sidebar() # Ensure Global CSS and Custom Sidebar is applied
ui.render_top_header()

st.title("👨‍🍳 Kitchen Display System (KDS)")

# Controls: Refresh + Section
c_r1, c_r2 = st.columns([1, 4])
if c_r1.button("🔄 Refresh", use_container_width=True):
    st.rerun()

with c_r2:
    selected_section = st.radio(
        "Select Section", 
        ["Kitchen", "Bar", "Dessert", "All"], 
        index=0, 
        horizontal=True,
        label_visibility="collapsed"
    )
    st.session_state.kds_section = selected_section

st.caption(f"📍 Viewing: **{selected_section}**")

# Fetch Table Data
tables = db.get_enriched_tables()

# Filter for tables with Active Orders that have items sent to kitchen
active_tickets = []
for t in tables:
    if t['status'] != 'Available' and t.get('items'):
        # Filter items that are relevant to kitchen and selected section
        kitchen_items = []
        for idx, item in enumerate(t['items']):
            status = item.get('status', 'pending')
            # Routing checks
            item_sec = item.get('section', 'Kitchen')
            
            if status in ['ordered', 'sent', 'preparing', 'ready']:
                 if selected_section == "All" or item_sec == selected_section:
                    # Tuple: (index, item_dict)
                    kitchen_items.append((idx, item))
        
        if kitchen_items:
            active_tickets.append({
                'table_id': t['id'],
                'table_label': t['label'],
                'waiter': t['waiter_id'],
                'items': kitchen_items,
                'start_time': t['start_time'],
                'source': 'TABLE'
            })

# Fetch Accepted Online Orders
online_orders = db.get_accepted_online_orders()
for _, row in online_orders.iterrows():
    # In a real app, we'd map these to internal status properly.
    # For simulation, they start as 'ordered'
    items = json.loads(row['items_json'])
    kitchen_items = []
    for idx, item in enumerate(items):
        # Apply section filtering to online items too
        item_sec = item.get('section', 'Kitchen') # Default to Kitchen if mapping not perfect
        if selected_section == "All" or item_sec == selected_section:
            # Check status of online items - for now we treat all accepted ones as 'ordered' if not specified
            status = item.get('status', 'ordered')
            if status in ['ordered', 'sent', 'preparing', 'ready']:
                kitchen_items.append((idx, item))

    if kitchen_items:
        active_tickets.append({
            'table_id': row['id'], # Sync ID
            'table_label': f"{row['platform']} #{row['external_order_id'][-4:]}",
            'waiter': row['platform'],
            'items': kitchen_items,
            'start_time': row['created_at'],
            'source': row['platform'] # SWIGGY / ZOMATO
        })

if not active_tickets:
    st.info("No active KOT orders.")
else:
    # Grid Layout
    cols = st.columns(3)
    
    for i, ticket in enumerate(active_tickets):
        with cols[i % 3]:
            # Determine Color Code
            max_delay_min = 0
            # Try to start from oldest item
            ticket_time = ticket['start_time']
            # Refine: Use earliest item 'ordered_at' if available
            ordered_times = [it[1].get('ordered_at') for it in ticket['items'] if it[1].get('ordered_at')]
            if ordered_times:
                try:
                    earliest = min(pd.to_datetime(t) for t in ordered_times)
                    diff = datetime.utcnow() - earliest
                    max_delay_min = int(diff.total_seconds() / 60)
                except: pass
            
            # Color Logic
            card_bg = "#dcfce7" # Green (New)
            if any(it[1].get('status') == 'preparing' for it in ticket['items']):
                card_bg = "#fef3c7" # Yellow
            if max_delay_min > 15:
                card_bg = "#fee2e2" # Red
            
            # Source Brand Icon
            source_icon = "📍" if ticket['source'] == 'TABLE' else "🛵" if ticket['source'] == 'SWIGGY' else "🥘"
            
            # Render Ticket
            st.markdown(f"""
            <div style="background-color: {card_bg}; padding: 15px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                    <div style="font-weight:bold; font-size:1.1rem;">{source_icon} {ticket['table_label']}</div>
                    <div style="font-weight:bold; color:#555;">{max_delay_min}m</div>
                </div>
                <div style="font-size:0.8rem; color:#666; margin-bottom:10px;">Source: {ticket['waiter'] or 'N/A'}</div>
                <hr style="border-top:1px dashed #999; margin:5px 0;">
            </div>
            """, unsafe_allow_html=True)
            
            # Interactive Items
            for idx, item in ticket['items']:
                s = item.get('status', 'ordered')
                # Give button more space (2:1 ratio), align vertically
                c1, c2 = st.columns([2, 1], vertical_alignment="center")
                c1.write(f"**{item['qty']}x** {item['name']}")
                
                # Action Button based on status
                if s in ['ordered', 'sent']:
                    if c2.button("Start", key=f"start_{ticket['table_id']}_{idx}", use_container_width=True):
                        if ticket['source'] == 'TABLE':
                            db.update_item_kds_status(ticket['table_id'], idx, 'preparing')
                        else:
                            db.update_online_item_kds_status(ticket['table_id'], idx, 'preparing')
                        st.rerun()
                elif s == 'preparing':
                    if c2.button("Done", key=f"done_{ticket['table_id']}_{idx}", type="primary", use_container_width=True):
                        if ticket['source'] == 'TABLE':
                            db.update_item_kds_status(ticket['table_id'], idx, 'ready')
                        else:
                            db.update_online_item_kds_status(ticket['table_id'], idx, 'ready')
                        st.rerun()
                elif s == 'ready':
                     c2.success("✅")
            
            st.markdown("</div>", unsafe_allow_html=True) 
            # Note: HTML closing tag logic is mixed with native widgets, visual might break if not careful.
            # actually st.markdown doesn't wrap native widgets.
            
            # Correct Approach:
            # 1. Header (HTML)
            # 2. Items (Loop - Native)
            # 3. Footer (if any)
