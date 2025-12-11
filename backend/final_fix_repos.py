"""Reassign repos to match current API user's org"""
import sqlite3

conn = sqlite3.connect('apidoc.db')
c = conn.cursor()

# Get the current API user's org (we know it from the debug endpoint)
# But let's get it from the dev user in the database
c.execute('SELECT organization_id FROM users WHERE email = "dev@test.com"')
result = c.fetchone()

if not result:
    print("ERROR: No dev user found!")
    conn.close()
    exit(1)

current_org_id = result[0]
print(f"Current dev user org_id: {current_org_id}")

# Update ALL repositories to use this org_id
c.execute('UPDATE repositories SET organization_id = ?', (current_org_id,))
updated_count = c.rowcount

conn.commit()
print(f"Updated {updated_count} repositories to org_id: {current_org_id}")

# Verify
c.execute('SELECT COUNT(*) FROM repositories WHERE organization_id = ?', (current_org_id,))
count = c.fetchone()[0]
print(f"Verification: {count} repos now belong to dev org")

conn.close()
print("Done!")
