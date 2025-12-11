"""Create dev user with the organization that has all the repos"""
import sqlite3
import uuid

conn = sqlite3.connect('apidoc.db')
c = conn.cursor()

# Get the org that has all the repos
c.execute('SELECT organization_id FROM repositories LIMIT 1')
result = c.fetchone()

if not result:
    print("ERROR: No repositories found!")
    conn.close()
    exit(1)

correct_org_id = result[0]
print(f"Repos belong to org: {correct_org_id}")

# Check if this org exists
c.execute('SELECT id, name FROM organizations WHERE id = ?', (correct_org_id,))
org = c.fetchone()

if org:
    print(f"Organization exists: {org[1]}")
else:
    print("ERROR: Organization not found! Creating it...")
    c.execute('''INSERT INTO organizations 
                 (id, name, subdomain, subscription_tier, developer_count, created_at, updated_at)
                 VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))''',
              (correct_org_id, 'Development Organization', 'dev-org', 'free', 1))
    print("Created organization")

# Delete any existing dev@test.com user
c.execute('DELETE FROM users WHERE email = "dev@test.com"')

# Create dev user with correct org
user_id = str(uuid.uuid4())
c.execute('''INSERT INTO users
             (id, email, hashed_password, full_name, organization_id, role, is_active, is_verified, created_at, updated_at)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))''',
          (user_id, 'dev@test.com', '', 'Development User', correct_org_id, 'admin', 1, 1))

conn.commit()
print(f"Created dev user with org_id: {correct_org_id}")

# Verify
c.execute('SELECT COUNT(*) FROM repositories WHERE organization_id = ?', (correct_org_id,))
repo_count = c.fetchone()[0]
print(f"Verification: {repo_count} repos belong to this org")

conn.close()
print("DONE!")
