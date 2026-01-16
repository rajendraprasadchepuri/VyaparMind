
import requests
import pandas as pd
import streamlit as st

API_URL = "http://127.0.0.1:8000"

def _get_account_id():
    # Mimic original logic
    if hasattr(st, 'session_state') and 'account_id' in st.session_state:
        return st.session_state['account_id']
    return '1111222233334444' # Default

# --- Settings ---
@st.cache_data(ttl=300)
def get_setting(key, _account_id=None):
    # Pass account_id explicitly or resolve it before calling this cached func
    # If called without account_id, we need to resolve it inside?
    # Streamlit cache key depends on args.
    # To avoid cache collisions between users, account_id MUST be an arg.
    if not _account_id:
        _account_id = _get_account_id()
        
    try:
        resp = requests.get(f"{API_URL}/settings/{key}", params={"account_id": _account_id})
        if resp.status_code == 200:
            return resp.json()['value']
        return None
    except:
        return None

# --- Products ---
@st.cache_data(ttl=60)
def _fetch_inventory_cached(account_id, search_term, limit):
    params = {"account_id": account_id, "limit": limit}
    if search_term:
        params["search"] = search_term
        
    try:
        resp = requests.get(f"{API_URL}/products/", params=params)
        if resp.status_code == 200:
            return pd.DataFrame(resp.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def fetch_pos_inventory(search_term=None, limit=50, override_account_id=None):
    aid = override_account_id or _get_account_id()
    return _fetch_inventory_cached(aid, search_term, limit)

@st.cache_data(ttl=60)
def fetch_product_by_id(product_id):
    try:
        resp = requests.get(f"{API_URL}/products/{product_id}")
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None

# --- Customers ---
def get_customer_by_phone(phone):
    aid = _get_account_id()
    try:
        resp = requests.get(f"{API_URL}/customers/phone/{phone}", params={"account_id": aid})
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None

def add_customer(name, phone, email, city="Unknown", pincode="000000"):
    aid = _get_account_id()
    payload = {
        "account_id": aid,
        "name": name,
        "phone": phone,
        "email": email,
        "city": city,
        "pincode": pincode
    }
    try:
        resp = requests.post(f"{API_URL}/customers/", json=payload)
        if resp.status_code == 200:
            return True, "Success"
        return False, resp.json().get('detail', 'Error')
    except Exception as e:
        return False, str(e)

# --- Transactions ---
def record_transaction(items, total_amt, profit, customer_id=None, points_redeemed=0, doctor_name=None, doctor_reg_no=None):
    aid = _get_account_id()
    
    # Map items to API schema
    api_items = []
    for i in items:
        api_items.append({
            "id": i['id'],
            "name": i['name'],
            "qty": i['qty'],
            "price": float(i['price']),
            "cost": float(i.get('cost', 0)),
            "total": float(i['total']),
            "tax_rate": float(i.get('tax_rate', 0.0))
        })
        
    payload = {
        "account_id": aid,
        "items": api_items,
        "total_amount": float(total_amt),
        "total_profit": float(profit),
        "customer_id": customer_id,
        "points_redeemed": points_redeemed,
        "doctor_name": doctor_name,
        "doctor_reg_no": doctor_reg_no
    }
    
    try:
        resp = requests.post(f"{API_URL}/transactions/", json=payload)
        if resp.status_code == 200:
            return resp.json()['id']
        return None
    except:
        return None
