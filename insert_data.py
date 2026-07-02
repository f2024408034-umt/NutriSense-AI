# ================================================================
# NUTRISENSE AI - FOOD DATA INSERT SCRIPT
# ================================================================
# This script inserts all food items into the foods table.
# Safe to run multiple times - uses INSERT OR IGNORE to avoid
# duplicate entries.
#
# Source: Muneeba Razzaq (f2024408057-bit/nutriscience_project)
# Updated: Added fat column values + Pakistani food items
#
# How to run:
#   python insert_foods.py
# ================================================================

import sqlite3

conn   = sqlite3.connect("nutrisense.db")
cursor = conn.cursor()

print("Adding food items to database...")

# ----------------------------------------------------------------
# ALL FOOD ITEMS
# Format: (food_name, calories, protein, carbs, fat)
# ----------------------------------------------------------------
foods = [
    # Basic items
    ("Apple",                    95,   0.5,  25,   0.3),
    ("Egg",                      78,   6.0,   1,   5.0),
    ("Banana",                  105,   1.3,  27,   0.4),
    ("Chicken Breast",          165,  31.0,   0,   3.6),

    # Pakistani staples
    ("Roti (1 piece)",          120,   3.0,  24,   1.0),
    ("Rice (1 cup cooked)",     200,   4.0,  45,   0.5),
    ("Daal (1 cup)",            230,  18.0,  40,   1.0),
    ("Chicken Curry",           280,  25.0,   8,  14.0),
    ("Yogurt (1 cup)",          150,   8.0,  12,   8.0),
    ("Milk (1 glass)",          150,   8.0,  12,   8.0),
    ("Almonds (10 pieces)",      70,   2.5,   2,   6.0),
    ("Orange",                   60,   1.0,  15,   0.1),
    ("Spinach (cooked, 1 cup)",  40,   5.0,   6,   0.5),
    ("Brown Bread (1 slice)",    80,   4.0,  15,   1.0),
    ("Salmon Fillet",           200,  22.0,   0,  12.0),
    ("Lentil Soup",             180,  12.0,  28,   3.0),

    # More Pakistani foods
    ("Beef Curry",              250,  20.0,   5,  15.0),
    ("Fish Curry",              220,  22.0,   4,  12.0),
    ("Chapati",                 110,   3.0,  22,   1.5),
    ("Paratha",                 260,   5.0,  30,  12.0),
    ("Boiled Egg",               78,   6.0,   1,   5.0),
    ("Fried Egg",                90,   6.0,   1,   7.0),
    ("Omelette",                154,  11.0,   2,  11.0),
    ("White Bread Slice",        75,   3.0,  14,   1.0),
    ("Whole Wheat Bread",        80,   4.0,  15,   1.0),
    ("Tea with Milk",            70,   2.0,   8,   2.0),
    ("Coffee with Milk",         90,   3.0,  10,   3.0),
    ("Dates (3)",                70,   1.0,  18,   0.1),
    ("Guava",                    68,   2.6,  14,   1.0),
    ("Mango",                    99,   1.4,  25,   0.6),
    ("Watermelon",               46,   1.0,  12,   0.2),
    ("Pear",                    100,   1.0,  27,   0.2),
    ("Peanuts (20g)",           113,   5.0,   4,   9.0),
    ("Cashews (10)",             90,   3.0,   5,   7.0),
    ("Walnuts (5)",             130,   3.0,   3,  13.0),
    ("Paneer",                  265,  18.0,   6,  20.0),
    ("Cheese Slice",            113,   7.0,   1,   9.0),
    ("Butter (1 tbsp)",         102,   0.0,   0,  12.0),
    ("French Fries",            312,   4.0,  41,  15.0),
    ("Burger",                  295,  17.0,  30,  14.0),
    ("Pizza Slice",             285,  12.0,  36,  10.0),
    ("Biryani (1 plate)",       450,  18.0,  55,  16.0),
    ("Pulao (1 cup)",           250,   6.0,  40,   8.0),
    ("Kebab (2)",               220,  16.0,   4,  15.0),
    ("Shami Kebab",             140,  10.0,   6,   8.0),
    ("Chana Masala",            270,  14.0,  35,   7.0),
    ("Rajma",                   215,  13.0,  40,   2.0),
    ("Aloo Sabzi",              180,   4.0,  28,   7.0),
    ("Bhindi",                   90,   3.0,  12,   4.0),
    ("Cucumber",                 16,   1.0,   4,   0.1),
    ("Tomato",                   22,   1.0,   5,   0.2),
    ("Carrot",                   41,   1.0,  10,   0.2),
    ("Apple Juice",             114,   0.0,  28,   0.3),
    ("Orange Juice",            112,   2.0,  26,   0.5),
    ("Ice Cream",               207,   3.0,  24,  11.0),
    ("Chocolate Bar",           230,   3.0,  25,  13.0),
]

# ----------------------------------------------------------------
# INSERT WITH DUPLICATE PROTECTION
# ----------------------------------------------------------------
# INSERT OR IGNORE skips the row if a food with the same name
# already exists — so this script is safe to run multiple times.
# ----------------------------------------------------------------
added   = 0
skipped = 0

for food in foods:
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO foods (food_name, calories, protein, carbs, fat)
            VALUES (?, ?, ?, ?, ?)
        """, food)

        if cursor.rowcount > 0:
            added += 1
        else:
            skipped += 1

    except sqlite3.Error as e:
        print(f"  ❌ Error inserting '{food[0]}': {e}")

conn.commit()
conn.close()

print(f"\n✅ Done!")
print(f"   Added  : {added} food items")
print(f"   Skipped: {skipped} (already existed)")