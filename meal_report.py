import sqlite3

conn = sqlite3.connect("nutrisense.db")
cursor = conn.cursor()

cursor.execute("""
SELECT users.name,
       foods.food_name,
       foods.calories,
       meal_log.date
FROM meal_log
JOIN users ON meal_log.user_id = users.id
JOIN foods ON meal_log.food_id = foods.id
""")

rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()