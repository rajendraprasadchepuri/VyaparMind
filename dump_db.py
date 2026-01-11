
import sqlite3
import pandas as pd

conn = sqlite3.connect('retail_supply_chain.db')
with open('db_dump.txt', 'w') as f:
    f.write("--- ACCOUNTS ---\n")
    df_acc = pd.read_sql_query("SELECT * FROM accounts", conn)
    f.write(df_acc.to_string())
    f.write("\n\n--- USERS ---\n")
    df_users = pd.read_sql_query("SELECT username, role, account_id, permissions FROM users", conn)
    f.write(df_users.to_string())
conn.close()
