"""Quick database check - minimal output"""
import sqlite3

conn = sqlite3.connect('apidoc.db')
c = conn.cursor()

# Count repos
c.execute('SELECT COUNT(*) FROM repositories')
repo_count = c.fetchone()[0]

# Count users
c.execute('SELECT COUNT(*) FROM users WHERE email = "dev@test.com"')
user_count = c.fetchone()[0]

# Get dev user org if exists
if user_count > 0:
    c.execute('SELECT organization_id FROM users WHERE email = "dev@test.com"')
    dev_org = c.fetchone()[0]
    
    # Count repos for dev org
    c.execute('SELECT COUNT(*) FROM repositories WHERE organization_id = ?', (dev_org,))
    dev_repos = c.fetchone()[0]
    
    print(f"Repos: {repo_count} total, {dev_repos} for dev org ({dev_org})")
else:
    print(f"Repos: {repo_count} total, NO DEV USER")

conn.close()
