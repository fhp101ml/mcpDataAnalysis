import sqlite3

conn = sqlite3.connect("sandbox/kdd_memory.sqlite")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

if tables:
    for t in tables:
        print(f"\nSchema for {t[0]}:")
        cursor.execute(f"PRAGMA table_info({t[0]});")
        print(cursor.fetchall())
        
    cursor.execute("SELECT DISTINCT thread_id FROM checkpoints;")
    print("\nThread IDs:")
    print(cursor.fetchall())

conn.close()
