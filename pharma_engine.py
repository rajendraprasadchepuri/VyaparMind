import pandas as pd
import database as db
import config

# Use the same placeholder as database.py
PLACEHOLDER = "%s" if config.DB_TYPE == "POSTGRES" else "?"

def get_interactions_for_salt(salt):
    """Fetches interactions where one of the salts is the given salt."""
    conn = db.get_connection()
    c = conn.cursor()
    # Check both sides: salt_a or salt_b
    query = f'''
        SELECT * FROM drug_interactions 
        WHERE salt_a LIKE {PLACEHOLDER} OR salt_b LIKE {PLACEHOLDER}
    '''
    # simple partial match or exact? Exact is safer for medical.
    # Let's assume exact match for now to avoid "Paracetamol" matching "Paracetamol + Something" incorrectly without parsing.
    # Actually, salt composition is often comma separated. 
    # For MVP, let's assume the user enters single salts or we check widely.
    # We will stick to exact 'contains' logic if possible, or exact str match for Phase 1.
    
    # Revised: The table is `salt_a` and `salt_b`. 
    # If Product A has "Paracetamol", and Product B has "Warfarin".
    # We query interactions where salt_a='Paracetamol' AND salt_b='Warfarin'.
    
    # So we don't need this helper as much as a bulk checker.
    pass

def check_drug_interactions(cart_df):
    """
    Analyzes the cart for conflicting salts.
    cart_df: DataFrame containing 'salt_composition' and 'name'.
    Returns: List of warning dicts: {'severity': 'High', 'title': '...', 'description': '...'}
    """
    if cart_df.empty or 'salt_composition' not in cart_df.columns:
        return []

    # 1. Extract non-empty salts
    salts = cart_df['salt_composition'].dropna().unique()
    salts = [s.strip() for s in salts if s.strip()]
    
    if len(salts) < 2:
        return []

    conn = db.get_connection()
    warnings = []
    
    # O(N^2) check? Or just query DB?
    # Better to query DB for any pair in this list.
    # "SELECT * FROM drug_interactions WHERE salt_a IN (...) AND salt_b IN (...)"
    # But A and B could be swapped.
    
    placeholders = ','.join([PLACEHOLDER] * len(salts))
    
    # We want interactions where BOTH salt_a AND salt_b are in our current cart's salt list.
    query = f'''
        SELECT * FROM drug_interactions 
        WHERE salt_a IN ({placeholders}) 
        AND salt_b IN ({placeholders})
    '''
    
    # We pass the list of salts twice
    params = list(salts) + list(salts)
    
    try:
        interactions = pd.read_sql_query(query, conn, params=params)
        
        for _, row in interactions.iterrows():
            sa = row['salt_a']
            sb = row['salt_b']
            
            # Find product names for these salts in the cart
            prods_a = cart_df[cart_df['salt_composition'] == sa]['name'].tolist()
            prods_b = cart_df[cart_df['salt_composition'] == sb]['name'].tolist()
            
            # Formatting the message
            msg = f"Potential interaction between {', '.join(prods_a)} ({sa}) and {', '.join(prods_b)} ({sb})."
            
            warnings.append({
                'severity': row['severity'],
                'title': f"{row['severity']} Risk Interaction",
                'description': f"{msg} Risk: {row['description']}"
            })
            
    except Exception as e:
        print(f"Pharma Engine Error: {e}")
    finally:
        conn.close()

    return warnings

def find_substitutes(product_row):
    """
    Finds cheaper or higher margin substitutes for a given product.
    product_row: Series or Dict with 'salt_composition', 'price', 'product_id' (optional)
    """
    salt = product_row.get('salt_composition')
    price = product_row.get('price')
    pid = product_row.get('id') # To exclude itself
    
    if not salt:
        return pd.DataFrame() # Empty
        
    conn = db.get_connection()
    aid = db.get_current_account_id()
    
    # Substitutes = Same Salt, Different ID
    query = f'''
        SELECT * FROM products 
        WHERE account_id = {PLACEHOLDER} 
        AND salt_composition = {PLACEHOLDER}
        AND price < {PLACEHOLDER}
    '''
    params = [aid, salt, price]
    
    if pid:
        query += f" AND id != {PLACEHOLDER}"
        params.append(pid)
        
    query += " ORDER BY price ASC LIMIT 3"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df

def seed_interactions():
    """Seeds some basic interactions for testing."""
    conn = db.get_connection()
    c = conn.cursor()
    
    # Common Dangerous Pairs
    pairs = [
        ('Aspirin', 'Warfarin', 'Severe', 'Increased risk of bleeding due to antiplatelet effect.'),
        ('Paracetamol', 'Warfarin', 'Moderate', 'May enhance anticoagulant effect of Warfarin.'),
        ('Sildenafil', 'Nitrates', 'Severe', 'Fatal drop in blood pressure.'),
        ('Ibuprofen', 'Aspirin', 'Moderate', 'Reduces heart-protection of Aspirin and increases stomach ulcer risk.')
    ]
    
    try:
        for p in pairs:
            # We insert A-B. Logic above checks IN(List) AND IN(List), so order in DB matters less if A and B are both in list.
            # But query checks salt_a IN list AND salt_b IN list.
            # If DB has (A,B), and I have [B, A], query finds it.
            # If DB has (A,B), and I have [A, C], query fails. Correct.
            insert_q = f"INSERT OR IGNORE INTO drug_interactions (id, salt_a, salt_b, severity, description) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})"
            if config.DB_TYPE == "POSTGRES":
                 insert_q = f"INSERT INTO drug_interactions (id, salt_a, salt_b, severity, description) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}) ON CONFLICT DO NOTHING"
            
            c.execute(insert_q, (db.generate_unique_id(), p[0], p[1], p[2], p[3]))
            
        conn.commit()
    except Exception as e:
        print(f"Seeding Error: {e}")
    finally:
        conn.close()

# --- RESCUESCRIPT ENGINE ---

def scan_refills(override_account_id=None):
    """
    Scans past transactions for chronic medications and generates refill reminders.
    Should be run daily or on page load.
    """
    conn = db.get_connection()
    c = conn.cursor()
    aid = override_account_id if override_account_id else db.get_current_account_id()
    
    try:
        # 1. Find Chronic Sales that don't have a reminder yet
        # We look for transactions where the product is chronic
        # AND we haven't already created a reminder for this exact transaction+product combo?
        # A simple way is to check if we have a reminder for (customer, product) around the due date.
        
        # Let's just find ALL chronic sales in the last 60 days
        import datetime
        limit_date = datetime.datetime.now() - datetime.timedelta(days=60)
        
        query = f'''
            SELECT 
                t.customer_id, 
                ti.product_id, 
                t.timestamp as sale_date,
                p.refill_interval,
                p.name as product_name
            FROM transactions t
            JOIN transaction_items ti ON t.id = ti.transaction_id
            JOIN products p ON ti.product_id = p.id
            WHERE t.account_id = {PLACEHOLDER}
            AND p.is_chronic = 1
            AND t.timestamp > {PLACEHOLDER}
            AND t.customer_id IS NOT NULL
        '''
        
        sales = pd.read_sql_query(query, conn, params=(aid, limit_date))
        
        count = 0
        for _, row in sales.iterrows():
            cid = row['customer_id']
            pid = row['product_id']
            sale_date = pd.to_datetime(row['sale_date'])
            interval = int(row['refill_interval'])
            
            due_date = sale_date + datetime.timedelta(days=interval)
            
            # Check if reminder already exists for this Cycle
            # We assume one reminder per product per cycle.
            # We identify "cycle" by due_date being close (within 5 days)
            
            check_q = f'''
                SELECT id FROM refill_reminders 
                WHERE account_id = {PLACEHOLDER}
                AND customer_id = {PLACEHOLDER}
                AND product_id = {PLACEHOLDER}
                AND due_date BETWEEN {PLACEHOLDER} AND {PLACEHOLDER}
            '''
            
            margin = datetime.timedelta(days=5)
            c.execute(check_q, (aid, cid, pid, due_date - margin, due_date + margin))
            if c.fetchone():
                continue # Already detailed
            
            # Create Reminder
            new_id = db.generate_unique_id()
            c.execute(f'''
                INSERT INTO refill_reminders (id, account_id, customer_id, product_id, last_purchase_date, due_date, status)
                VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, 'PENDING')
            ''', (new_id, aid, cid, pid, sale_date, due_date))
            count += 1
            
        conn.commit()
        return count
    except Exception as e:
        print(f"RescueScript Scan Error: {e}")
        return 0
    finally:
        conn.close()

def get_due_reminders(days_window=7):
    """
    Fetches customers who are due for a refill within X days.
    Returns DataFrame with [Patient Name, Phone, Drug, Due Date, Status, Revenue Potential]
    """
    conn = db.get_connection()
    aid = db.get_current_account_id()
    import datetime
    cutoff = datetime.datetime.now() + datetime.timedelta(days=days_window)
    
    query = f'''
        SELECT 
            rr.id as reminder_id,
            c.name as customer_name,
            c.phone as customer_phone,
            p.name as product_name,
            p.price as potential_revenue,
            rr.due_date,
            rr.status,
            rr.last_purchase_date
        FROM refill_reminders rr
        JOIN customers c ON rr.customer_id = c.id
        JOIN products p ON rr.product_id = p.id
        WHERE rr.account_id = {PLACEHOLDER}
        AND rr.due_date <= {PLACEHOLDER}
        AND rr.status != 'REFILLED'
        ORDER BY rr.due_date ASC
    '''
    
    try:
        df = pd.read_sql_query(query, conn, params=(aid, cutoff))
        return df
    except Exception as e:
        print(e)
        return pd.DataFrame()
    finally:
        conn.close()

def send_whatsapp_reminder(reminder_id):
    """
    Simulates sending a WhatsApp reminder.
    """
    conn = db.get_connection()
    c = conn.cursor()
    try:
        c.execute(f"UPDATE refill_reminders SET status = 'SENT', reminder_sent_at = {PLACEHOLDER} WHERE id = {PLACEHOLDER}", 
                  (datetime.datetime.now(), reminder_id))
        conn.commit()
        return True, "WhatsApp Sent! 📱"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
