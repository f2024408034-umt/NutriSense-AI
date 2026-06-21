import sqlite3

conn = sqlite3.connect("nutrisense.db")
cursor = conn.cursor()

# User 1
cursor.execute("""
INSERT OR IGNORE INTO users (name, email, age, goal)
VALUES ('Ali', 'ali@gmail.com', 22, 'Weight Loss')
""")

# User 2
cursor.execute("""
INSERT OR IGNORE INTO users (name, email, age, goal)
VALUES ('Sara', 'sara@gmail.com', 21, 'Weight Gain')
""")

# Food 1
cursor.execute("""
INSERT INTO foods (food_name, calories, protein, carbs)
VALUES ('Apple', 95, 0.5, 25)
""")

# Food 2
cursor.execute("""
INSERT INTO foods (food_name, calories, protein, carbs)
VALUES ('Egg', 78, 6, 1)
""")

# Food 3
cursor.execute("""
INSERT INTO foods (food_name, calories, protein, carbs)
VALUES ('Banana', 105, 1.3, 27)
""")

# Food 4
cursor.execute("""
INSERT INTO foods (food_name, calories, protein, carbs)
VALUES ('Chicken Breast', 165, 31, 0)
""")

conn.commit()
conn.close()

print("Data Inserted Successfully!")