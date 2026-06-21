import sqlite3

conn = sqlite3.connect("nutrisense.db")
cursor = conn.cursor()

print("Users Table:")
cursor.execute("SELECT * FROM users")
for row in cursor.fetchall():
    print(row)

print("\nFoods Table:")
cursor.execute("SELECT * FROM foods")
for row in cursor.fetchall():
    print(row)

conn.close()