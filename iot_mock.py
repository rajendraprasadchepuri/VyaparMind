"""
IoT Sensor Simulator for VyaparMind Cold Storage
------------------------------------------------
This script simulates real-time temperature sensors for all cold zones.
It runs in a loop, generating realistic temperature data and logging it to the database.

Features:
- Auto-discovery of all active zones
- Realistic temperature fluctuation (random walk)
- Occasional "Chaos Mode" (simulated failures/breaches)
- Triggers existing alert pipeline (WhatsApp/DB logs)

Usage:
    python iot_mock.py
"""

import time
import random
import database as db
from datetime import datetime
import pandas as pd
import warnings
from dotenv import load_dotenv

# Load environment variables (Twilio/Email credentials)
load_dotenv()

# Suppress warnings
warnings.filterwarnings("ignore")

# Configuration
UPDATE_INTERVAL = 10  # Seconds between readings
BREACH_PROBABILITY = 0.05  # 5% chance of a breach event per reading
CHAOS_MODE = False  # Set to True to force erratic behavior

def get_zones():
    """Fetch all zones with their target temperatures."""
    try:
        df = db.get_all_cold_zones()
        return df
    except Exception as e:
        print(f"Error fetching zones: {e}")
        return pd.DataFrame()

def simulate_reading(current_temp, target_min, target_max):
    """
    Generate next temperature reading based on current state.
    Keeps it mostly within range, with occasional drifts.
    """
    target_avg = (target_min + target_max) / 2
    
    # Random drift
    drift = random.uniform(-0.5, 0.5)
    
    # Corrective force (thermostat logic)
    if current_temp > target_max:
        drift -= 0.8  # Cool down hard
    elif current_temp < target_min:
        drift += 0.8  # Heat up hard
    else:
        # Small random fluctuation around average
        if current_temp > target_avg:
            drift -= 0.1
        else:
            drift += 0.1
            
    # Chaos Event (Simulate door open or compressor failure)
    if random.random() < BREACH_PROBABILITY or CHAOS_MODE:
        spike = random.uniform(2.0, 5.0) * random.choice([-1, 1])
        print(f"⚠️ CHAOS EVENT! Temperature spike: {spike:+.1f}°C")
        return current_temp + spike
        
    return current_temp + drift

def main():
    print("🤖 IoT Sensor Simulator Starting...")
    print(f"⏱️ Update Interval: {UPDATE_INTERVAL}s")
    print("----------------------------------------")
    
    # Initialize state
    zones = get_zones()
    if zones.empty:
        print("❌ No zones found! Please create zones in the application first.")
        return
        
    # Initial state map: {zone_id: current_temp}
    params = {}
    for _, row in zones.iterrows():
        # Start at ideal temperature
        start_temp = (row['target_temp_min'] + row['target_temp_max']) / 2
        params[row['id']] = start_temp
        print(f"✅ Sensor Online: {row['zone_name']} (Target: {row['target_temp_min']} to {row['target_temp_max']}°C)")
        
    print("----------------------------------------")
    print("📡 Streaming Sensor Data...")
    
    while True:
        try:
            # Refresh zone config occasionally (in case user changed settings)
            if random.random() < 0.1: 
                zones = get_zones()
            
            for _, row in zones.iterrows():
                zid = row['id']
                zname = row['zone_name']
                tmin = row['target_temp_min']
                tmax = row['target_temp_max']
                
                # Get last mock temp or re-initialize
                current = params.get(zid, (tmin + tmax)/2)
                
                # Generate new reading
                new_temp = simulate_reading(current, tmin, tmax)
                params[zid] = new_temp  # Update state
                
                # Round for display
                display_temp = round(new_temp, 1)
                
                # Log to DB (This triggers alerts!)
                status, msg = db.log_temperature(zid, display_temp, recorded_by="IoT_Sensor_01")
                
                # Console feedback
                status_icon = "🟢"
                if "BREACH" in msg:
                    status_icon = "🔴 BREACH!"
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {zname}: {display_temp}°C | {status_icon}")
                
            time.sleep(UPDATE_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n🛑 Simulator stopped by user.")
            break
        except Exception as e:
            print(f"\n❌ Error in simulation loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
