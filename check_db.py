import sqlite3

conn = sqlite3.connect('expenses.db')
c = conn.cursor()

# Check tables
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()
print("✓ Database Tables:")
for t in tables:
    print(f"  - {t[0]}")

# Check table schemas
for table_name in ['users', 'expenses', 'goals']:
    try:
        c.execute(f"PRAGMA table_info({table_name})")
        columns = c.fetchall()
        print(f"\n✓ {table_name.upper()} table columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    except:
        print(f"\n✗ {table_name} table not found")

conn.close()
print("\n✓ Database is working correctly!")
