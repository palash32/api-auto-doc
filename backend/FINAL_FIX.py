"""FINAL FIX - Create dev user and ensure it persists"""
import sqlite3

conn = sqlite3.connect('apidoc.db')
conn.isolation_level = None  # Autocommit mode
c = conn.cursor()

# Get repos org
c.execute('SELECT organization_id FROM repositories LIMIT 1')
repos_org = c.fetchone()[0]
print(f"Repos belong to organization: {repos_org}")

# DELETE all dev@test.com users
c.execute('DELETE FROM users WHERE email = "dev@test.com"')
deleted = c.rowcount
print(f"Deleted {deleted} existing dev users")

# Create ONE dev user with the correct org
import uuid
user_id = str(uuid.uuid4())

c.execute('''
    INSERT INTO users (id, email, hashed_password, full_name, organization_id, role, is_active, is_verified, created_at, updated_at)
    VALUES (?, 'dev@test.com', '', 'Development User', ?, 'admin', 1, 1, datetime('now'), datetime('now'))
''', (user_id, repos_org))

print(f"Created dev user with ID: {user_id}")
print(f"Organization: {repos_org}")

# VERIFY immediately
c.execute('SELECT COUNT(*) FROM users WHERE email = "dev@test.com"')
user_count = c.fetchone()[0]
print(f"\nVerification: {user_count} dev user(s) exist")

c.execute('SELECT organization_id FROM users WHERE email = "dev@test.com"')
user_org = c.fetchone()[0]
print(f"Dev user org: {user_org}")

c.execute('SELECT COUNT(*) FROM repositories WHERE organization_id = ?', (user_org,))
repo_count = c.fetchone()[0]
print(f"Repos for this org: {repo_count}")

conn.close()
print("\n✅ DONE - Dev user created and committed!")
