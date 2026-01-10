
import database as db
import os

def run_test():
    print("--- Login Enhancement Verification ---")
    db.init_db()
    
    # 1. Create a Test Account
    import secrets
    suffix = secrets.token_hex(4)
    company = f"SuperStore_{suffix}"
    user = f"manager_{suffix}"
    email = f"man_{suffix}@example.com"
    pwd = "securepassword"
    
    res, msg = db.create_company_account(company, user, pwd, email)
    if not res:
        print(f"FAILED to create account: {msg}")
        return
    print(f"Created Account: {company}, User: {user}")
    
    # 2. Test Login WITHOUT Company Check (Should still work? No, I made it Mandatory)
    # The new signature requires 3 args.
    # res = db.verify_user(user, pwd) -> This will fail TypeError.
    # Let's verify that it fails if we pass None.
    res = db.verify_user(user, pwd, None)
    if not res[0]:
         print(f"PASS: Login without company check failed as expected: {res[1]}")
    else:
         print("FAIL: Login without company check unexpectedly succeeded.")
        
    # 3. Test Login WITH Correct Company
    res = db.verify_user(user, pwd, company_name_check=company)
    if res[0]:
        print("PASS: Login with CORRECT company check succeeded.")
    else:
        print(f"FAIL: Login with CORRECT company check failed: {res[1]}")

    # 4. Test Login WITH WRONG Company
    wrong_company = "BadStore"
    res = db.verify_user(user, pwd, company_name_check=wrong_company)
    if not res[0] and "does not belong" in res[1]:
        print(f"PASS: Login with WRONG company check failed as expected. Msg: {res[1]}")
    else:
        print(f"FAIL: Login with WRONG company check did NOT fail correctly. Res: {res}")
        
    # 5. Test Password Reset
    print("--- Password Reset Verification ---")
    succ, msg = db.initiate_password_reset(user)
    if succ:
        print(f"PASS: Reset via Username: {msg}")
    else:
        print(f"FAIL: Reset via Username: {msg}")

    # ... (Password Reset Tests) ...
    succ, msg = db.initiate_password_reset(email)
    if succ:
        print(f"PASS: Reset via Email: {msg}")
    else:
        print(f"FAIL: Reset via Email: {msg}")
        
    # 6. Test SCOPED Username Uniqueness (The Fix)
    print("--- Scoped Username Verification ---")
    
    # We already have 'company' with user 'user'.
    # Create Company B with SAME username 'user'.
    company_b = "CompanyB_" + suffix
    # Try to create it. Should SUCCEED now (previously failed).
    # Note: create_company_account creates the user as 'admin' if we passed 'admin',
    # but here we are passing 'user' variable which is 'manager_xxxx'.
    
    res, msg = db.create_company_account(company_b, user, "newpass", "b@example.com")
    if res:
        print(f"PASS: Created Account '{company_b}' with DUPLICATE username '{user}'.")
    else:
        print(f"FAIL: Could not create duplicate username in different account: {msg}")

    # Verify Login for Company B
    res_b = db.verify_user(user, "newpass", company_name_check=company_b)
    if res_b[0]:
        print(f"PASS: Logged in to Company B with duplicate username.")
    else:
        print(f"FAIL: Login B failed: {res_b[1]}")

    # Verify Login for Company A (Old password)
    res_a = db.verify_user(user, pwd, company_name_check=company)
    if res_a[0]:
        print(f"PASS: Logged in to Company A with original credentials.")
    else:
         print(f"FAIL: Login A failed: {res_a[1]}")

if __name__ == "__main__":
    run_test()
