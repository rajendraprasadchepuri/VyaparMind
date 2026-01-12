import streamlit as st
import database as db
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import ui_components as ui

st.set_page_config(page_title="ColdZone - Temperature Management", layout="wide", page_icon="🌡️")
ui.require_auth()
ui.render_sidebar()
ui.render_top_header()
# --- DASHBOARD HEADER ---
col_h1, col_h2 = st.columns([0.7, 0.3])
with col_h1:
    st.title("🌡️ ColdZone - Temperature Monitoring")
    st.caption("Live monitoring of all cold storage zones")

# Check for active IoT sensors (simulated)
conn = db.get_connection()
c = conn.cursor()
try:
    # Check for logs in last minute from IoT Sensor
    c.execute("SELECT COUNT(*) FROM temperature_logs WHERE recorded_by LIKE 'IoT%' AND recorded_at >= datetime('now', '-2 minutes')")
    iot_active = c.fetchone()[0] > 0
    
    with col_h2:
        if iot_active:
             st.markdown("""
            <div style="text-align: right; padding: 10px;">
                <span style="background-color: #d4edda; color: #155724; padding: 5px 10px; border-radius: 15px; font-weight: bold; border: 1px solid #c3e6cb;">
                    📡 Live Sensors Active
                </span>
            </div>
            """, unsafe_allow_html=True)
            # st.toast("IoT Sensors Connected", icon="📡")
        else:
             st.markdown("""
            <div style="text-align: right; padding: 10px;">
                <span style="background-color: #f8f9fa; color: #6c757d; padding: 5px 10px; border-radius: 15px; font-weight: bold; border: 1px solid #dee2e6;">
                    ⚪ Sensors Offline
                </span>
            </div>
            """, unsafe_allow_html=True)
except Exception:
    pass
finally:
    conn.close()

st.markdown("---")

# Custom CSS for temperature cards
st.markdown("""
<style>
    .temp-card {
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .temp-normal {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .temp-breach {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    .zone-metric {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 10px 0;
    }
    .zone-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# --- TAB NAVIGATION ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Zone Dashboard", "➕ Add Zone", "🌡️ Log Temperature", "📈 Temperature Trends"])

# TAB 1: ZONE DASHBOARD
with tab1:
    st.subheader("Active Temperature Zones")
    
    zones_df = db.get_all_cold_zones()
    
    if not zones_df.empty:
        # Quick Stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Zones", len(zones_df))
        with col2:
            total_capacity = zones_df['capacity_pallets'].sum()
            st.metric("Total Capacity", f"{total_capacity:,} pallets")
        with col3:
            total_occupancy = zones_df['current_occupancy'].sum()
            st.metric("Current Occupancy", f"{total_occupancy:,} pallets")
        with col4:
            utilization = (total_occupancy / total_capacity * 100) if total_capacity > 0 else 0
            st.metric("Utilization", f"{utilization:.1f}%")
        
        st.markdown("---")
        
        # Get latest temperature for each zone (last 24 hours)
        for _, zone in zones_df.iterrows():
            zone_id = zone['id']
            zone_name = zone['zone_name']
            target_min = zone['target_temp_min']
            target_max = zone['target_temp_max']
            
            # Get last temperature log
            conn = db.get_connection()
            last_temp_query = f"""
                SELECT recorded_temp, recorded_at, is_breach
                FROM temperature_logs
                WHERE zone_id = ?
                ORDER BY recorded_at DESC
                LIMIT 1
            """
            temp_df = pd.read_sql_query(last_temp_query, conn, params=(zone_id,))
            conn.close()
            
            # Display zone card
            col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
            
            with col_a:
                if not temp_df.empty:
                    temp = temp_df.iloc[0]['recorded_temp']
                    is_breach = temp_df.iloc[0]['is_breach']
                    recorded_at = temp_df.iloc[0]['recorded_at']
                    
                    # Card HTML
                    card_class = "temp-breach" if is_breach else "temp-normal"
                    breach_icon = "🚨" if is_breach else "✅"
                    
                    st.markdown(f"""
                    <div class="temp-card {card_class}">
                        <div class="zone-label">{breach_icon} {zone_name}</div>
                        <div class="zone-metric">{temp:.1f}°C</div>
                        <div class="zone-label">Target: {target_min}°C to {target_max}°C</div>
                        <div class="zone-label">Last updated: {recorded_at}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="temp-card" style="background: #f0f0f0; color: #666;">
                        <div class="zone-label">⚠️ {zone_name}</div>
                        <div class="zone-metric">--</div>
                        <div class="zone-label">No temperature data</div>
                        <div class="zone-label">Target: {target_min}°C to {target_max}°C</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col_b:
                st.write("")
                st.write("")
                st.metric("Capacity", f"{zone['capacity_pallets']} pallets")
            
            with col_c:
                st.write("")
                st.write("")
                occupancy_pct = (zone['current_occupancy'] / zone['capacity_pallets'] * 100) if zone['capacity_pallets'] > 0 else 0
                st.metric("Occupied", f"{zone['current_occupancy']} ({occupancy_pct:.0f}%)")
            
            with col_d:
                st.write("")
                st.write("")
                available = zone['capacity_pallets'] - zone['current_occupancy']
                st.metric("Available", f"{available} pallets")
        
        # Breach Alert Section
        st.markdown("---")
        st.subheader("🚨 Recent Temperature Breaches (Last 7 Days)")
        
        breaches_df = db.get_temperature_breaches(days=7)
        
        if not breaches_df.empty:
            st.error(f"⚠️ {len(breaches_df)} breach(es) detected in the last 7 days!")
            
            st.dataframe(
                breaches_df[['zone_name', 'recorded_temp', 'recorded_at', 'corrective_action']],
                column_config={
                    "zone_name": "Zone",
                    "recorded_temp": st.column_config.NumberColumn("Temperature", format="%.1f°C"),
                    "recorded_at": st.column_config.DatetimeColumn("Breach Time", format="DD MMM YYYY, HH:mm"),
                    "corrective_action": "Corrective Action"
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.success("✅ No temperature breaches in the last 7 days. Excellent compliance!")
    
    else:
        st.info("No zones configured yet. Add a zone in the 'Add Zone' tab.")

# TAB 2: ADD ZONE
with tab2:
    st.subheader("➕ Add New Temperature Zone")
    
    with st.form("add_zone_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            zone_name = st.text_input("Zone Name", placeholder="e.g., Zone A - Deep Freeze")
            zone_type = st.selectbox("Zone Type", [
                "FROZEN_MINUS_25",
                "FROZEN_MINUS_18",
                "CHILLED_0_TO_4",
                "DRY_AMBIENT"
            ])
            capacity_pallets = st.number_input("Capacity (Pallets)", min_value=0, value=100, step=10)
        
        with col2:
            target_temp_min = st.number_input("Target Temperature Min (°C)", value=-25.0, step=0.5)
            target_temp_max = st.number_input("Target Temperature Max (°C)", value=-23.0, step=0.5)
            capacity_cubic = st.number_input("Capacity (Cubic Meters)", min_value=0.0, value=500.0, step=50.0)
        
        submitted = st.form_submit_button("Add Zone", use_container_width=True)
        
        if submitted:
            if zone_name:
                success, result = db.add_cold_zone(
                    zone_name, zone_type, target_temp_min, target_temp_max, 
                    capacity_pallets, capacity_cubic
                )
                if success:
                    st.success(f"✅ Zone '{zone_name}' added successfully!")
                    st.balloons()
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Failed to add zone: {result}")
            else:
                st.warning("Zone name is required")

# TAB 3: LOG TEMPERATURE
with tab3:
    st.subheader("🌡️ Log Temperature Reading")
    
    zones_df = db.get_all_cold_zones()
    
    if not zones_df.empty:
        with st.form("log_temp_form"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                zone_options = {row['zone_name']: row['id'] for _, row in zones_df.iterrows()}
                selected_zone_name = st.selectbox("Select Zone", list(zone_options.keys()))
                selected_zone_id = zone_options[selected_zone_name]
            
            with col2:
                recorded_temp = st.number_input("Temperature (°C)", value=-24.0, step=0.1)
            
            with col3:
                recorded_by = st.text_input("Recorded By", value="Manual Entry")
            
            corrective_action = st.text_area("Corrective Action (if breach)", 
                                            placeholder="Describe any action taken if temperature was out of range...")
            
            submitted = st.form_submit_button("Log Temperature", use_container_width=True)
            
            if submitted:
                success, result = db.log_temperature(selected_zone_id, recorded_temp, recorded_by)
                
                if success:
                    if result == "BREACH_ALERT":
                        st.error(f"🚨 TEMPERATURE BREACH DETECTED! {recorded_temp}°C is outside the safe range!")
                        st.warning("Please take corrective action immediately and document it.")
                    else:
                        st.success(f"✅ Temperature logged: {recorded_temp}°C for {selected_zone_name}")
                    
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Failed to log temperature: {result}")
    else:
        st.warning("Please add zones first before logging temperatures.")

# TAB 4: TEMPERATURE TRENDS
with tab4:
    st.subheader("📈 Temperature Trends & Analytics")
    
    zones_df = db.get_all_cold_zones()
    
    if not zones_df.empty:
        # Zone selector
        zone_options = {row['zone_name']: row['id'] for _, row in zones_df.iterrows()}
        selected_zone_trend = st.selectbox("Select Zone for Trend Analysis", list(zone_options.keys()), key="trend_zone")
        zone_id_trend = zone_options[selected_zone_trend]
        
        # Date range
        col1, col2 = st.columns(2)
        with col1:
            days_back = st.slider("Days to Show", 1, 30, 7)
        
        # Fetch temperature data
        conn = db.get_connection()
        trend_query = f"""
            SELECT recorded_temp, recorded_at, is_breach
            FROM temperature_logs
            WHERE zone_id = ?
            AND recorded_at >= datetime('now', '-{days_back} days')
            ORDER BY recorded_at ASC
        """
        trend_df = pd.read_sql_query(trend_query, conn, params=(zone_id_trend,))
        conn.close()
        
        if not trend_df.empty:
            # Get zone limits
            zone_info = zones_df[zones_df['id'] == zone_id_trend].iloc[0]
            target_min = zone_info['target_temp_min']
            target_max = zone_info['target_temp_max']
            
            # Convert to datetime
            trend_df['recorded_at'] = pd.to_datetime(trend_df['recorded_at'])
            
            # Plotly chart
            fig = go.Figure()
            
            # Temperature line
            fig.add_trace(go.Scatter(
                x=trend_df['recorded_at'],
                y=trend_df['recorded_temp'],
                mode='lines+markers',
                name='Recorded Temperature',
                line=dict(color='#667eea', width=2),
                marker=dict(size=6)
            ))
            
            # Target range bands
            fig.add_hline(y=target_min, line_dash="dash", line_color="green", 
                         annotation_text=f"Min: {target_min}°C", annotation_position="left")
            fig.add_hline(y=target_max, line_dash="dash", line_color="green", 
                         annotation_text=f"Max: {target_max}°C", annotation_position="left")
            
            # Breach markers
            breaches = trend_df[trend_df['is_breach'] == 1]
            if not breaches.empty:
                fig.add_trace(go.Scatter(
                    x=breaches['recorded_at'],
                    y=breaches['recorded_temp'],
                    mode='markers',
                    name='Breach',
                    marker=dict(color='red', size=12, symbol='x')
                ))
            
            fig.update_layout(
                title=f"Temperature Trend - {selected_zone_trend}",
                xaxis_title="Date & Time",
                yaxis_title="Temperature (°C)",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                avg_temp = trend_df['recorded_temp'].mean()
                st.metric("Avg Temperature", f"{avg_temp:.1f}°C")
            with col2:
                min_temp = trend_df['recorded_temp'].min()
                st.metric("Min Recorded", f"{min_temp:.1f}°C")
            with col3:
                max_temp = trend_df['recorded_temp'].max()
                st.metric("Max Recorded", f"{max_temp:.1f}°C")
            with col4:
                breach_count = len(breaches)
                st.metric("Breaches", breach_count, delta=f"-{breach_count}" if breach_count > 0 else None)
            
            # Download data
            st.markdown("---")
            st.subheader("📥 Download Temperature Logs (For Audit)")
            
            csv = trend_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"temperature_log_{selected_zone_trend}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info(f"No temperature data recorded for {selected_zone_trend} in the last {days_back} days.")
    else:
        st.warning("No zones available for trend analysis.")
