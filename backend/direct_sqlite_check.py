import sqlite3

conn = sqlite3.connect('apidoc.db')
c = conn.cursor()

print("=" * 70)
print("DIRECT SQLITE QUERY")
print("=" * 70)

c.execute('SELECT COUNT(*) FROM repositories')
print(f"\nTotal repositories: {c.fetchone()[0]}")

c.execute('SELECT COUNT(*) FROM users WHERE email = "dev@test.com"') 
print(f"Dev users (dev@test.com): {c.fetchone()[0]}")

c.execute('SELECT id, email, organization_id FROM users WHERE email = "dev@test.com"')
dev_user = c.fetchone()
if dev_user:
    print(f"\nDev user details:")
    print(f"  ID: {dev_user[0]}")
    print(f"  Email: {dev_user[1]}")
    print(f"  Org ID: {dev_user[2]}")
    
    c.execute('SELECT COUNT(*) FROM repositories WHERE organization_id = ?', (dev_user[2],))
    repo_count = c.fetchone()[0]
    print(f"\nRepositories for dev user's org ({dev_user[2]}): {repo_count}")
    
    if repo_count > 0:
        c.execute('SELECT full_name, organization_id FROM repositories WHERE organization_id = ?', (dev_user[2],))
        repos = c.fetchall()
        for repo in repos:
            print(f"  - {repo[0]} (org: {repo[1]})")
else:
    print("Dev user not found!")

print("\n" + "=" * 70)
print("ALL REPOSITORIES:")
c.execute('SELECT full_name, organization_id FROM repositories')
all_repos = c.fetchall()
for repo in all_repos:
    print(f"  - {repo[0]} (org:{repo[1]})")

conn.close()
