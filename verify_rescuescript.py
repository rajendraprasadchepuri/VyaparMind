import database as db
import pharma_engine as pharma
import datetime
import pandas as pd
import time

def verify_rescuescript():
    print("🧪 Starting RescueScript Verification...")
    
    conn = db.get_connection()
    c = conn.cursor()
    aid = db.get_current_account_id()
    
    try:
        # 1. Setup Data
        print("   [1/5] Creating Chronic Product...")
        # Add Product: "Metformin 500mg" (Chronic, 30 days)
        # We use direct DB call or add_product wrapper
        # Wrapper: name, category, price, cost_price, stock_quantity, tax_rate, salt_composition, manufacturer, schedule_type, override_account_id, is_chronic, refill_interval
        
        # Clean up existing test data
        c.execute(f"DELETE FROM products WHERE name='TestMetformin' AND account_id='{aid}'")
        c.execute(f"DELETE FROM refill_reminders WHERE account_id='{aid}'")
        conn.commit()
        
        succ, msg = db.add_product(
            "TestMetformin", "Pharma", 100.0, 80.0, 100, 5.0, 
            "Metformin", "SunPharma", "H", aid, 
            is_chronic=1, refill_interval=30
        )
        if not succ:
            print(f"❌ Failed to add product: {msg}")
            return
            
        # Get ID
        c.execute(f"SELECT id FROM products WHERE name='TestMetformin' AND account_id='{aid}'")
        pid = c.fetchone()[0]
        
        # Create Dummy Customer
        cid = 'CUST_TEST_RS'
        c.execute(f"INSERT OR REPLACE INTO customers (id, account_id, name, phone) VALUES ('{cid}', '{aid}', 'Chronic Patient', '9999999999')")
        
        # 2. Simulate Transaction (28 Days Ago)
        print("   [2/5] Simulating Past Transaction...")
        # We need to manually insert a transaction because record_transaction timestamps NOW.
        # Or we can record transaction and then update timestamp.
        
        items = [{'id': pid, 'name': 'TestMetformin', 'qty': 1, 'price': 100.0, 'cost': 80.0}]
        txn_hash = db.record_transaction(items, 100.0, 20.0, customer_id=cid, override_account_id=aid)
        
        # Backdate it
        past_date = datetime.datetime.now() - datetime.timedelta(days=28)
        # Logic: 28 days ago + 30 days interval = Due in 2 days.
        
        c.execute(f"UPDATE transactions SET timestamp = ? WHERE transaction_hash = ?", (past_date, txn_hash))
        conn.commit()
        
        # 3. Run Scan
        print("   [3/5] Running Refill Scanner...")
        count = pharma.scan_refills(override_account_id=aid)
        print(f"      -> Generated {count} reminders.")
        
        if count == 0:
            print("❌ Scan failed to generate reminder.")
            # Debug
            # Check is_chronic flag
            c.execute(f"SELECT is_chronic, refill_interval FROM products WHERE id='{pid}'")
            print(f"      Debug Product: {c.fetchone()}")
            return
            
        # 4. Verify Reminder
        print("   [4/5] Verifying Reminder Data...")
        df = pharma.get_due_reminders(days_window=7)
        # Should find our patient
        
        target = df[df['product_name'] == 'TestMetformin']
        if not target.empty:
            due_date = pd.to_datetime(target.iloc[0]['due_date'])
            status = target.iloc[0]['status']
            print(f"      -> Found Reminder! Due: {due_date.strftime('%Y-%m-%d')}, Status: {status}")
            
             # 5. Send WhatsApp
            print("   [5/5] Testing WhatsApp Trigger...")
            rid = target.iloc[0]['reminder_id']
            succ, msg = pharma.send_whatsapp_reminder(rid)
            if succ:
                print(f"      -> {msg}")
            else:
                print(f"❌ Failed to send: {msg}")

        else:
            print("❌ Reminder not found in get_due_reminders.")
            print(df)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        print("🏁 Verification Complete.")

if __name__ == "__main__":
    verify_rescuescript()
