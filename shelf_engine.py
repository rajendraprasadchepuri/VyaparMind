import json

# The "Brain" of ShelfSense
# Contains molecular rules and psychological associations.

KNOWLEDGE_BASE = {
    # Molecular Rules
    'ethylene_producer': {
        'conflicts_with': ['ethylene_sensitive'],
        'msg': "🚨 BIO-HAZARD: Ethylene Producer next to Sensitive item! (Will Rot Faster)",
        'score': -50
    },
    'moisture_producer': {
        'conflicts_with': ['moisture_sensitive'],
        'msg': "🚨 SPOILAGE RISK: High moisture item will ruin dry goods.",
        'score': -30
    },
    
    # Psychological Rules (Affinity)
    'impulse_snack': {
        'boosts': ['impulse_drink'], # Chips -> Coke
        'msg': "✅ COMBO BOOST: Great pairing! Snack + Drink = +25% Sales.",
        'score': 20
    },
    'target_men': {
        'boosts': ['target_new_dads'], # Beer -> Diapers (The classic example)
        'msg': "🏆 GOLDEN INSIGHT: 'Diapers & Beer' correlation detected. High probability of cross-sell.",
        'score': 50
    },
    'breakfast_staple': {
        'boosts': ['breakfast_complement'], # Bread -> Jam/Eggs
        'msg': "✅ MORNING ROUTINE: Placing breakfast items together increases basket size.",
        'score': 15
    }
}

# Mock Database of Science Tags (Since we might not have them in DB for all items yet)
# In production, this comes from 'science_tags' column in DB.
PRODUCT_SCIENCE_DB = {
    # produce
    'Apple': ['ethylene_producer', 'breakfast_staple'],
    'Banana': ['ethylene_sensitive', 'breakfast_staple'],
    'Potato': ['moisture_sensitive'],
    'Onion': ['moisture_producer'],
    
    # fmcg
    'Chips': ['impulse_snack'],
    'Coke': ['impulse_drink'],
    'Beer': ['target_men'],
    'Diapers': ['target_new_dads'],
    'Bread': ['breakfast_staple'],
    'Jam': ['breakfast_complement'],
    'Milk': ['breakfast_complement']
}

def get_tags(product_name):
    # Fuzzy match or direct lookup. 
    # For prototype, we check if key is IN the product name
    tags = []
    for key, val in PRODUCT_SCIENCE_DB.items():
        if key.lower() in product_name.lower():
            tags.extend(val)
    return list(set(tags))

def analyze_grid(grid):
    """
    Analyzes a 2D grid (list of lists) of product names.
    Returns: score (0-100), logs (list of strings with HTML formatting)
    """
    rows = len(grid)
    cols = len(grid[0])
    
    score = 100 # Start perfect
    logs = []
    
    # Helper to get neighbors
    def get_neighbors(r, c):
        n = []
        if r > 0: n.append(grid[r-1][c]) # Up
        if r < rows - 1: n.append(grid[r+1][c]) # Down
        if c > 0: n.append(grid[r][c-1]) # Left
        if c < cols - 1: n.append(grid[r][c+1]) # Right
        return [x for x in n if x] # Filter empty
        
    processed_pairs = set()

    for r in range(rows):
        for c in range(cols):
            current_item = grid[r][c]
            if not current_item: continue
            
            my_tags = get_tags(current_item)
            neighbors = get_neighbors(r, c)
            
            for neighbor in neighbors:
                # Avoid checking A-B and B-A twice
                pair_key = tuple(sorted([current_item, neighbor]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                
                neighbor_tags = get_tags(neighbor)
                
                # Check Rules
                for tag in my_tags:
                    rules = KNOWLEDGE_BASE.get(tag)
                    if not rules: continue
                    
                    # 1. Check Conflicts
                    if 'conflicts_with' in rules:
                        for bad_tag in rules['conflicts_with']:
                            if bad_tag in neighbor_tags:
                                score += rules['score'] # Negative
                                logs.append(f"{rules['msg']} ({current_item} ↔ {neighbor})")
                                
                    # 2. Check Boosts
                    if 'boosts' in rules:
                        for good_tag in rules['boosts']:
                            if good_tag in neighbor_tags:
                                score += rules['score'] # Positive
                                logs.append(f"{rules['msg']} ({current_item} ↔ {neighbor})")

    # Clamp score
    score = max(0, min(100, score))
    return score, logs
