from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = "nutrisense-ultra-secret-2025-xK9#mP2@"
CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5500", "http://localhost:5500", "null"])

def get_db():
    conn = sqlite3.connect("nutrisense.db")
    conn.row_factory = sqlite3.Row
    return conn

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def is_valid_name(name):
    return bool(name) and len(name) <= 50 and re.match(r'^[a-zA-Z\s]+$', name)

def is_valid_age(age):
    try:
        age = int(age)
        return 1 <= age <= 120
    except:
        return False

@app.route("/")
def home():
    return jsonify({
        "message": "NutriSense AI Backend Chal Raha Hai!",
        "status": "success",
        "version": "1.0"
    })

@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Koi data nahi mila"}), 400

        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        age = data.get("age")
        goal = data.get("goal", "").strip()
        password = data.get("password", "")

        if not is_valid_name(name):
            return jsonify({"error": "Naam galat hai - sirf letters allowed hain"}), 400
        if not is_valid_email(email):
            return jsonify({"error": "Email format galat hai"}), 400
        if not is_valid_age(age):
            return jsonify({"error": "Age 1 se 120 ke beech honi chahiye"}), 400

        valid_goals = ["Weight Loss", "Weight Gain", "Maintain", "Muscle Gain"]
        if goal not in valid_goals:
            return jsonify({"error": "Goal galat hai"}), 400
        if len(password) < 6:
            return jsonify({"error": "Password kam az kam 6 characters ka hona chahiye"}), 400

        hashed_password = generate_password_hash(password)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "Ye email pehle se registered hai"}), 409

        cursor.execute(
            "INSERT INTO users (name, email, age, goal, password) VALUES (?, ?, ?, ?, ?)",
            (name, email, int(age), goal, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        return jsonify({"message": "Registration successful!", "user_id": user_id, "name": name}), 201

    except Exception as e:
        return jsonify({"error": "Server error hua", "detail": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Koi data nahi mila"}), 400

        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"error": "Email aur password dono zaroori hain"}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if not user or not check_password_hash(user["password"], password):
            return jsonify({"error": "Email ya password galat hai"}), 401

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]

        return jsonify({"message": "Welcome back, " + user["name"] + "!", "user_id": user["id"], "goal": user["goal"]}), 200

    except Exception as e:
        return jsonify({"error": "Server error hua", "detail": str(e)}), 500

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logout successful!"}), 200

@app.route("/log-food", methods=["POST"])
def log_food():
    try:
        if "user_id" not in session:
            return jsonify({"error": "Pehle login karo"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"error": "Koi data nahi mila"}), 400

        food_id = data.get("food_id")
        date = data.get("date", datetime.now().strftime("%Y-%m-%d"))

        if not food_id or not str(food_id).isdigit():
            return jsonify({"error": "Sahi food ID do"}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, food_name FROM foods WHERE id = ?", (int(food_id),))
        food = cursor.fetchone()

        if not food:
            conn.close()
            return jsonify({"error": "Ye food database mein nahi hai"}), 404

        cursor.execute(
            "INSERT INTO meal_log (user_id, food_id, date) VALUES (?, ?, ?)",
            (session["user_id"], int(food_id), date)
        )
        conn.commit()
        conn.close()

        return jsonify({"message": food["food_name"] + " log ho gaya!", "date": date}), 201

    except Exception as e:
        return jsonify({"error": "Server error hua", "detail": str(e)}), 500

@app.route("/dashboard", methods=["GET"])
def dashboard():
    try:
        if "user_id" not in session:
            return jsonify({"error": "Pehle login karo"}), 401

        conn = get_db()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT foods.food_name, foods.calories, foods.protein, foods.carbs, meal_log.date
            FROM meal_log
            JOIN foods ON meal_log.food_id = foods.id
            WHERE meal_log.user_id = ? AND meal_log.date = ?
        """, (session["user_id"], today))

        meals = cursor.fetchall()
        total_calories = sum(m["calories"] for m in meals)
        total_protein = sum(m["protein"] for m in meals)
        total_carbs = sum(m["carbs"] for m in meals)
        conn.close()

        return jsonify({
            "date": today,
            "meals": [dict(m) for m in meals],
            "total_calories": total_calories,
            "total_protein": round(total_protein, 1),
            "total_carbs": round(total_carbs, 1)
        }), 200

    except Exception as e:
        return jsonify({"error": "Server error hua", "detail": str(e)}), 500

@app.route("/foods", methods=["GET"])
def get_foods():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM foods")
        foods = cursor.fetchall()
        conn.close()
        return jsonify({"foods": [dict(f) for f in foods]}), 200

    except Exception as e:
        return jsonify({"error": "Server error hua", "detail": str(e)}), 500

# ============================================================
# ROUTE 8 - HEALTH ANALYSIS / RECOMMENDATION ENGINE
# ============================================================
# User ke aaj ke khane ko analyze karta hai aur health
# warnings + diet suggestions deta hai based on his goal.
# Method: GET
# URL: /analyze

@app.route("/analyze", methods=["GET"])
def analyze():
    try:
        if "user_id" not in session:
            return jsonify({"error": "Pehle login karo"}), 401

        conn = get_db()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        # User ka goal nikalo
        cursor.execute("SELECT goal FROM users WHERE id = ?", (session["user_id"],))
        user = cursor.fetchone()
        goal = user["goal"]

        # Aaj ka khana nikalo
        cursor.execute("""
            SELECT foods.food_name, foods.calories, foods.protein, foods.carbs
            FROM meal_log
            JOIN foods ON meal_log.food_id = foods.id
            WHERE meal_log.user_id = ? AND meal_log.date = ?
        """, (session["user_id"], today))

        meals = cursor.fetchall()
        conn.close()

        # Total nutrition nikalo
        total_calories = sum(m["calories"] for m in meals)
        total_protein = sum(m["protein"] for m in meals)
        total_carbs = sum(m["carbs"] for m in meals)

        # ---- WARNINGS LIST ----
        warnings = []
        suggestions = []

        # Calorie Check
        if total_calories > 2000:
            warnings.append("⚠️ Calorie intake high hai - 2000 se zyada calories")
        elif total_calories == 0:
            warnings.append("ℹ️ Aaj abhi koi khana log nahi hua")

        # Carbs/Sugar Check
        if total_carbs > 150:
            warnings.append("⚠️ Carbs/Sugar zyada hai - diabetes risk barh sakta hai")

        # Protein Check
        if total_protein < 50 and total_calories > 0:
            warnings.append("⚠️ Protein kam hai - muscle health ke liye protein zaroori hai")

        # ---- GOAL BASED SUGGESTIONS ----
        if goal == "Weight Loss":
            if total_calories > 1800:
                suggestions.append("🥗 Weight Loss ke liye calories kam karo - light meals try karo")
            else:
                suggestions.append("✅ Calories aapke Weight Loss goal ke mutabiq hain")

        elif goal == "Weight Gain":
            if total_calories < 2200:
                suggestions.append("🍗 Weight Gain ke liye zyada calories aur protein lo")
            else:
                suggestions.append("✅ Calories aapke Weight Gain goal ke mutabiq hain")

        elif goal == "Muscle Gain":
            if total_protein < 80:
                suggestions.append("💪 Muscle Gain ke liye protein intake barhao - chicken, eggs lo")
            else:
                suggestions.append("✅ Protein intake achi hai Muscle Gain ke liye")

        elif goal == "Maintain":
            suggestions.append("✅ Apna balanced diet continue rakho")

        # Agar koi warning nahi hai
        if not warnings:
            warnings.append("✅ Sab kuch normal hai - koi health risk nahi")

        return jsonify({
            "date": today,
            "goal": goal,
            "total_calories": total_calories,
            "total_protein": round(total_protein, 1),
            "total_carbs": round(total_carbs, 1),
            "warnings": warnings,
            "suggestions": suggestions
        }), 200

    except Exception as e:
        return jsonify({"error": "Server error hua", "detail": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)