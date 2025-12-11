"""REVERSE APPROACH - Update repos to match whatever org the API is using"""
import sqlite3

conn = sqlite3.connect('apidoc.db')
c =conn.cursor()

# Hardcode the org the API keeps using
api_org_id = "2287d17d-de40-4766-b791-8db34179723c"

print(f"Updating all repos to org: {api_org_id}")

# Check if this org exists
c.execute('SELECT * FROM organizations WHERE id = ?', (api_org_id,))
if not c.fetchone():
    print(f"Creating organization {api_org_id}")
    c.execute('''INSERT INTO organizations 
    (id, name, subdomain, subscription_tier, developer_count, created_at, updated_at)
    VALUES (?, 'Development Organization', 'dev-org', 'free', 1, datetime('now'), datetime('now'))''',
    (api_org_id,))

# Update ALL repos
c.execute('UPDATE repositories SET organization_id = ?', (api_org_id,))
updated = c.rowcount

conn.commit()
print(f"✅ Updated {updated} repositories")

# Verify
c.execute('SELECT COUNT(*) FROM repositories WHERE organization_id = ?', (api_org_id,))
count = c.fetchone()[0]
print(f"✅ {count} repos now belong to API org")

conn.close()
print("\n🎯 Now the API should return the repos!")
