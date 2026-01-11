
import sqlite3
import hashlib

def reset_pwd():
    conn = sqlite3.connect('retail_supply_chain.db')
    c = conn.cursor()
    
    new_pass = 'admin123'
    pwd_hash = hashlib.sha256(new_pass.encode()).hexdigest()
    
    user = 'superadmin'
    
    # Update ALL superadmins just in case
    c.execute("UPDATE users SET password_hash = ? WHERE username = ?", (pwd_hash, user))
    
    if c.rowcount > 0:
        print(f"Reset {c.rowcount} users to password '{new_pass}'")
        conn.commit()
    else:
        print("User not found.")
        
    conn.close()

if __name__ == "__main__":
    reset_pwd()
