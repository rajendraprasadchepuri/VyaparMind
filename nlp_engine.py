import re
import difflib
import database as db

def find_closest_product(spoken_name, products_list):
    """
    Finds the closest match for spoken_name in products_list using difflib.
    products_list should be a list of dicts: [{'id': 1, 'name': 'Maggi'}, ...]
    Returns (product_dict, confidence_score)
    """
    if not products_list:
        return None, 0.0
        
    names = [p['name'] for p in products_list]
    # Get close matches
    matches = difflib.get_close_matches(spoken_name, names, n=1, cutoff=0.4)
    
    if matches:
        best_match_name = matches[0]
        # Find the product object
        for p in products_list:
            if p['name'] == best_match_name:
                # Calculate simple ratio for confidence
                ratio = difflib.SequenceMatcher(None, spoken_name.lower(), best_match_name.lower()).ratio()
                return p, ratio
    return None, 0.0

def parse_voice_command(text):
    """
    Parses a voice command string.
    Expected patterns:
    - "Add 50 Maggi"
    - "Set stock of Coke to 20"
    - "Sold 5 Lays"
    
    Returns dict: {'action': 'ADD'|'SET'|'REMOVE'|'UNKNOWN', 'qty': int, 'product_id': int, 'product_name': str, 'original_text': str}
    """
    text = text.strip()
    result = {
        'action': 'UNKNOWN',
        'qty': 0,
        'product_id': None,
        'product_name': None,
        'original_text': text,
        'confidence': 0.0,
        'status_msg': ""
    }
    
    if not text:
        result['status_msg'] = "Empty command."
        return result

    # 1. Extract Quantity (Find first number)
    # Using regex to find digits
    numbers = re.findall(r'\d+', text)
    if numbers:
        result['qty'] = int(numbers[0])
    else:
        # Fallback: simple text-to-number mapping could go here (one, two, ten)
        # For MVP, assume voice typing creates digits (which modern OS usually does: "five" -> "5")
        result['status_msg'] = "Could not find a quantity number."
        return result

    # 2. Identify Intent
    lower_text = text.lower()
    if any(x in lower_text for x in ['add', 'plus', 'restock', 'buy', 'bought', 'in']):
        result['action'] = 'ADD'
    elif any(x in lower_text for x in ['set', 'update', 'count', 'change', 'is', 'equals', 'make']):
        result['action'] = 'SET'
    elif any(x in lower_text for x in ['remove', 'sell', 'sold', 'sale', 'minus', 'deduct', 'out']):
        result['action'] = 'REMOVE'
    else:
        pass

    if result['action'] == 'UNKNOWN':
        result['status_msg'] = "Could not understand action (Add/Set/Sold)."
        return result

    # 3. Extract Product Name
    clean_text = lower_text
    # Remove digits
    clean_text = re.sub(r'\d+', '', clean_text)
    
    # Remove action keywords (naive)
    keywords = ['add', 'plus', 'restock', 'buy', 'bought', 'set', 'update', 'count', 'change', 'make', 'remove', 'sell', 'sold', 'sale', 'minus', 'deduct', 'stock', 'of', 'to', 'units', 'pieces', 'boxes', 'packets']
    
    words = clean_text.split()
    product_query_words = [w for w in words if w not in keywords]
    product_query = " ".join(product_query_words)
    
    if len(product_query) < 2:
         result['status_msg'] = "Could not identify product name."
         return result
         
    # 4. Fuzzy Match Product
    all_products_df = db.fetch_all_products()
    if all_products_df.empty:
        result['status_msg'] = "Database is empty."
        return result
        
    products_list = all_products_df.to_dict('records')
    matched_product, conf = find_closest_product(product_query, products_list)
    
    if matched_product and conf > 0.4:
        result['product_id'] = matched_product['id']
        result['product_name'] = matched_product['name']
        result['confidence'] = conf
        result['status_msg'] = "Success"
    else:
        result['status_msg'] = f"Product '{product_query}' not found."
        
    return result

def execute_parsed_command(parsed_result):
    """
    Executes the command against the DB.
    """
    if parsed_result['status_msg'] != "Success":
        return False, parsed_result['status_msg']
        
    p_id = parsed_result['product_id']
    qty = parsed_result['qty']
    action = parsed_result['action']
    
    try:
        conn = db.get_connection()
        c = conn.cursor()
        aid = db.get_current_account_id()
        
        if action == 'ADD':
            # Add to stock
            c.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ? AND account_id = ?", (qty, p_id, aid))
            msg = f"Added {qty} to {parsed_result['product_name']}"
            
        elif action == 'SET':
            # Set exact stock
            c.execute("UPDATE products SET stock_quantity = ? WHERE id = ? AND account_id = ?", (qty, p_id, aid))
            msg = f"Set {parsed_result['product_name']} stock to {qty}"
            
        elif action == 'REMOVE':
            # Deduct
            c.execute("UPDATE products SET stock_quantity = max(0, stock_quantity - ?) WHERE id = ? AND account_id = ?", (qty, p_id, aid))
            msg = f"Removed {qty} from {parsed_result['product_name']}"
            
        conn.commit()
        conn.close()
        
        # Invalidate cache
        if hasattr(db.fetch_all_products, 'clear'):
            db.fetch_all_products.clear()
            
        return True, msg
        
    except Exception as e:
        return False, str(e)
