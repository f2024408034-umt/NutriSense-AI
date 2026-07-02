# ================================================================
# NUTRISENSE AI - DATABASE SETUP
# ================================================================
# This file creates all the database tables needed for NutriSense AI.
#
# What is SQLite?
#   SQLite is a lightweight database that stores all data in a
#   single file called "nutrisense.db". No separate database
#   server needed - it works right inside Python.
#
# How to run this file:
#   python database.py
#
# When to run this file:
#   - First time setting up the project
#   - When new columns are added to any table
#   - Safe to run multiple times (will not delete existing data)
# ================================================================


# ----------------------------------------------------------------
# IMPORTS
# ----------------------------------------------------------------
import sqlite3
import os


# ----------------------------------------------------------------
# CONNECT TO DATABASE
# ----------------------------------------------------------------
# This creates the database file if it does not exist yet.
# If it already exists, it simply opens it.
conn   = sqlite3.connect("nutrisense.db")
cursor = conn.cursor()

print("=" * 50)
print("  NutriSense AI - Database Setup")
print("=" * 50)


# ================================================================
# TABLE 1 - USERS
# ================================================================
# Stores all registered user accounts.
#
# Columns:
#   id             - Unique ID for each user (auto-incremented)
#   username       - Unique login name e.g. "umar_jutt589"
#   email          - Unique email address
#   password       - Hashed password (never plain text)
#   first_name     - User's first name e.g. "Umar"
#   last_name      - User's last name  e.g. "Farooq"
#   age            - Age in years
#   gender         - Male / Female / Other
#   activity_level - Sedentary / Lightly Active / etc.
#   height         - Height in centimeters
#   weight         - Weight in kilograms
#   goal           - Health goal e.g. "Weight Loss"
#   conditions     - Medical conditions e.g. "Diabetes, Hypertension"
#
# NOTE ON OLD "name" COLUMN:
#   Earlier versions of this project used a single "name" column
#   with a NOT NULL constraint. That column has since been
#   replaced by "username", "first_name", and "last_name".
#   If your existing database still has that old "name" column
#   marked NOT NULL, new registrations will fail with an
#   IntegrityError. SQLite cannot drop a NOT NULL constraint
#   with ALTER TABLE, so the fix below rebuilds the table
#   safely while keeping any data you already have.
# ================================================================

print("\n[1/3] Setting up USERS table...")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        username       TEXT    UNIQUE NOT NULL,
        email          TEXT    UNIQUE NOT NULL,
        password       TEXT    NOT NULL,
        first_name     TEXT,
        last_name      TEXT,
        age            INTEGER,
        gender         TEXT,
        activity_level TEXT,
        height         REAL,
        weight         REAL,
        goal           TEXT,
        conditions     TEXT
    )
""")

# Check if the old "name" column exists with a NOT NULL constraint.
# If it does, we need to rebuild the table without it, because
# SQLite does not support dropping or modifying constraints
# with a simple ALTER TABLE statement.
cursor.execute("PRAGMA table_info(users)")
existing_columns = cursor.fetchall()
# Each row looks like: (index, name, type, notnull, default, pk)
has_old_name_column = any(
    col[1] == "name" and col[3] == 1   # column named "name" AND notnull=1
    for col in existing_columns
)

if has_old_name_column:
    print("  ⚠️  Old 'name' column found with NOT NULL constraint")
    print("  🔧 Rebuilding users table to remove it safely...")

    # Step 1: Rename the old table out of the way
    cursor.execute("ALTER TABLE users RENAME TO users_old")

    # Step 2: Create the new clean table (matches the schema above)
    cursor.execute("""
        CREATE TABLE users (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            username       TEXT    UNIQUE NOT NULL,
            email          TEXT    UNIQUE NOT NULL,
            password       TEXT    NOT NULL,
            first_name     TEXT,
            last_name      TEXT,
            age            INTEGER,
            gender         TEXT,
            activity_level TEXT,
            height         REAL,
            weight         REAL,
            goal           TEXT,
            conditions     TEXT
        )
    """)

    # Step 3: Copy over any existing data that has a valid username
    # (rows with no username can't be migrated since it's required)
    cursor.execute("""
        INSERT INTO users (
            id, username, email, password, first_name, last_name,
            age, gender, activity_level, height, weight, goal, conditions
        )
        SELECT
            id, username, email, password, first_name, last_name,
            age, gender, activity_level, height, weight, goal, conditions
        FROM users_old
        WHERE username IS NOT NULL
    """)

    # Step 4: Remove the old table
    cursor.execute("DROP TABLE users_old")

    print("  ✅ Users table rebuilt successfully - old 'name' column removed")

else:
    # Table is already clean - just make sure all expected columns exist
    users_new_columns = [
        ("username",       "TEXT"),
        ("password",       "TEXT"),
        ("first_name",     "TEXT"),
        ("last_name",      "TEXT"),
        ("age",            "INTEGER"),
        ("gender",         "TEXT"),
        ("activity_level", "TEXT"),
        ("height",         "REAL"),
        ("weight",         "REAL"),
        ("goal",           "TEXT"),
        ("conditions",     "TEXT"),
    ]

    for col_name, col_type in users_new_columns:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"  ✅ Column '{col_name}' added to users")
        except sqlite3.OperationalError:
            print(f"  ⏩ Column '{col_name}' already exists - skipped")


# ================================================================
# TABLE 2 - FOODS
# ================================================================
# Stores the food items available for users to log.
#
# Columns:
#   id        - Unique ID for each food item
#   food_name - Name of the food e.g. "Chicken Biryani"
#   calories  - Calories per serving
#   protein   - Protein in grams per serving
#   carbs     - Carbohydrates in grams per serving
#   fat       - Fat in grams per serving
# ================================================================

print("\n[2/3] Setting up FOODS table...")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS foods (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        food_name TEXT    NOT NULL,
        calories  INTEGER,
        protein   REAL,
        carbs     REAL,
        fat       REAL
    )
""")

# Add fat column if it does not exist (older versions may not have it)
try:
    cursor.execute("ALTER TABLE foods ADD COLUMN fat REAL")
    print("  ✅ Column 'fat' added to foods")
except sqlite3.OperationalError:
    print("  ⏩ Column 'fat' already exists - skipped")


# ================================================================
# TABLE 3 - MEAL LOG
# ================================================================
# Records every meal that a user logs throughout the day.
#
# Columns:
#   id        - Unique ID for each log entry
#   user_id   - Which user logged this meal (links to users.id)
#   food_id   - Which food was eaten (links to foods.id)
#   meal_type - Breakfast / Lunch / Dinner / Snack
#   quantity  - How many servings were eaten (default is 1)
#   date      - Date the meal was logged e.g. "2025-06-10"
#
# FOREIGN KEY:
#   A foreign key is a link between two tables.
#   user_id references users.id means every meal log must
#   belong to a real user - you cannot log a meal for a
#   user that does not exist.
# ================================================================

print("\n[3/3] Setting up MEAL_LOG table...")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS meal_log (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id   INTEGER NOT NULL,
        food_id   INTEGER NOT NULL,
        meal_type TEXT,
        quantity  INTEGER DEFAULT 1,
        date      TEXT    NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (food_id) REFERENCES foods (id)
    )
""")

# Add newer columns if they do not exist in an older version
meal_log_new_columns = [
    ("meal_type", "TEXT"),
    ("quantity",  "INTEGER DEFAULT 1"),
]

for col_name, col_type in meal_log_new_columns:
    try:
        cursor.execute(f"ALTER TABLE meal_log ADD COLUMN {col_name} {col_type}")
        print(f"  ✅ Column '{col_name}' added to meal_log")
    except sqlite3.OperationalError:
        print(f"  ⏩ Column '{col_name}' already exists - skipped")


# ================================================================
# SAVE AND CLOSE
# ================================================================
# commit() saves all the changes made above to the database file.
# close()  closes the connection to free up resources.
# ================================================================

conn.commit()
conn.close()

print("\n" + "=" * 50)
print("  ✅ Database setup complete!")
print("  📁 File: nutrisense.db")
print("  📋 Tables: users, foods, meal_log")
print("=" * 50)