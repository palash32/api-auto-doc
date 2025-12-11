"""Check current database state"""
import sqlite3

conn = sqlite3.connect('apidoc.db')
c = conn.cursor()

print("=== USERS ===")
c.execute('SELECT email, organization_id FROM users')
for row in c.fetchall():
    print(f"{row[0]}: {row[1]}")

print("\n=== ORGANIZATIONS ===")
c.execute('SELECT id, name FROM organizations')
for row in c.fetchall():
    print(f"{row[1]}: {row[0]}")

print("\n=== REPOSITORIES ===")
c.execute('SELECT full_name, organization_id FROM repositories LIMIT 3')
for row in c.fetchall():
    print(f"{row[0]}: {row[1]}")

conn.close()
