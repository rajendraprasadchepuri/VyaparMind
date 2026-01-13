import database
import os
from dotenv import load_dotenv

load_dotenv()

print("--- Testing FULL Alert Flow (WhatsApp + Email) ---")

# 1. Find a valid zone
conn = database.get_connection()
c = conn.cursor()
c.execute("SELECT id, zone_name FROM cold_zones LIMIT 1")
row = c.fetchone()
conn.close()

if not row:
    print("❌ No zones found. Cannot test.")
    exit(1)

zone_id, zone_name = row
print(f"Target Zone: {zone_name} (ID: {zone_id})")

# 2. Trigger Breach
print("\nAttempting to log breach temperature (100°C)...")
print("Watch console for 🔔 (WhatsApp) and 📧 (Email) logs...")

try:
    success, result = database.log_temperature(zone_id, 100.0, "Email-Test-01")
    
    print(f"\nResult: {result}")
    
    if "BREACH" in result:
        print("\n✅ Breach detected by system.")
        if "FAILED" not in result:
             print("✅ Alerts logic executed successfully!")
        else:
             print("⚠️ Some alerts might have failed (check logs above).")
        
except Exception as e:
    print(f"\n❌ EXCEPTION: {e}")
