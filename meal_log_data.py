import sqlite3

conn = sqlite3.connect("nutrisense.db")
cursor = conn.cursor()

cursor.execute("""
INSERT INTO meal_log (user_id, food_id, date)
VALUES (1, 1, '2026-06-07')
""")

conn.commit()
conn.close()

print("Meal Log Added Successfully!")