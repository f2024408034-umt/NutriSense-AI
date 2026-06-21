import sqlite3

conn = sqlite3.connect("nutrisense.db")
cursor = conn.cursor()

# Users Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    age INTEGER,
    goal TEXT
)
""")

# Foods Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS foods(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_name TEXT NOT NULL,
    calories INTEGER,
    protein REAL,
    carbs REAL
)
""")

# Meal Log Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS meal_log(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    food_id INTEGER,
    date TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(food_id) REFERENCES foods(id)
)
""")

conn.commit()
conn.close()

print("All Tables Created Successfully!")