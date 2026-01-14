import database as db
import pandas as pd
import datetime

def verify_regubot():
    print("👮‍♂️ Starting ReguBot Verification...")
    
    conn = db.get_connection()
    c = conn.cursor()
    aid = db.get_current_account_id()
    
    try:
        # 1. Setup H1 Product
        print("   [1/3] Creating H1 Schedule Product...")
        c.execute(f"DELETE FROM products WHERE name='TestAlpraz' AND account_id='{aid}'")
        c.execute(f"DELETE FROM transactions WHERE account_id='{aid}' AND doctor_name='Dr. Test'")
        conn.commit()
        
        # Add Product: "TestAlpraz" (Schedule H1)
        succ, msg = db.add_product(
            "TestAlpraz", "Pharma", 50.0, 30.0, 100, 12.0, 
            "Alprazolam", "TestLabs", "H1", aid
        )
        if not succ:
            print(f"❌ Failed to add product: {msg}")
            return
            
        # Get ID
        c.execute(f"SELECT id FROM products WHERE name='TestAlpraz' AND account_id='{aid}'")
        pid = c.fetchone()[0]
        
        # 2. Record Transaction with Doctor Details
        print("   [2/3] Recording Transaction with Doctor Details...")
        items = [{'id': pid, 'name': 'TestAlpraz', 'qty': 10, 'price': 50.0, 'cost': 30.0}]
        
        # We manually call record_transaction passing the new args
        txn_id = db.record_transaction(
            items, 500.0, 200.0, 
            customer_id=None, 
            override_account_id=aid,
            doctor_name="Dr. Test",
            doctor_reg_no="REG12345"
        )
        
        print(f"      -> Transaction Recorded: {txn_id}")
        
        # 3. Verify Data in Transactions Table
        print("   [3/3] Verifying Database Storage...")
        c.execute(f"SELECT doctor_name, doctor_reg_no FROM transactions WHERE id='{txn_id}'")
        row = c.fetchone()
        
        if row and row[0] == "Dr. Test" and row[1] == "REG12345":
            print("      ✅ Success! Doctor details stored correctly.")
        else:
            print(f"      ❌ Failed! Stored data: {row}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        print("🏁 ReguBot Verification Complete.")

if __name__ == "__main__":
    verify_regubot()
