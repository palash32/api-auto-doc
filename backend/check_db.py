import sqlite3

conn = sqlite3.connect('apidoc.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [t[0] for t in cursor.fetchall()]
print(f"Found {len(tables)} tables:")
for t in tables:
    print(f"  - {t}")
conn.close()
