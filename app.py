from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = "nutrisense-ultra-secret-2025-xK9#mP2@"

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
        "message": "NutriSense AI backend is running!",
        "status": "success",
        "version": "1.0"
    })

@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        age = data.get("age")
        goal = data.get("goal", "").strip()
        password = data.get("password", "")

        if not is_valid_name(name):
            return jsonify({"error": "Invalid name - only letters are allowed"}), 400
        if not is_valid_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        if not is_valid_age(age):
            return jsonify({"error": "Age must be between 1 and 120"}), 400

        valid_goals = ["Weight Loss", "Weight Gain", "Maintain", "Muscle Gain"]
        if goal not in valid_goals:
            return jsonify({"error": "Invalid goal selected"}), 400
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters long"}), 400

        hashed_password = generate_password_hash(password)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "This email is already registered"}), 409

        cursor.execute(
            "INSERT INTO users (name, email, age, goal, password) VALUES (?, ?, ?, ?, ?)",
            (name, email, int(age), goal, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        return jsonify({"message": "Registration successful!", "user_id": user_id, "name": name}), 201

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"error": "Email and password are both required"}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if not user or not check_password_hash(user["password"], password):
            return jsonify({"error": "Invalid email or password"}), 401

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]

        return jsonify({"message": "Welcome back, " + user["name"] + "!", "user_id": user["id"], "goal": user["goal"]}), 200

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logout successful!"}), 200

@app.route("/log-food", methods=["POST"])
def log_food():
    try:
        if "user_id" not in session:
            return jsonify({"error": "Please log in first"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        food_id = data.get("food_id")
        date = data.get("date", datetime.now().strftime("%Y-%m-%d"))

        if not food_id or not str(food_id).isdigit():
            return jsonify({"error": "A valid food ID is required"}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, food_name FROM foods WHERE id = ?", (int(food_id),))
        food = cursor.fetchone()

        if not food:
            conn.close()
            return jsonify({"error": "This food item does not exist in the database"}), 404

        cursor.execute(
            "INSERT INTO meal_log (user_id, food_id, date) VALUES (?, ?, ?)",
            (session["user_id"], int(food_id), date)
        )
        conn.commit()
        conn.close()

        return jsonify({"message": food["food_name"] + " has been logged successfully!", "date": date}), 201

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500

@app.route("/dashboard", methods=["GET"])
def dashboard():
    try:
        if "user_id" not in session:
            return jsonify({"error": "Please log in first"}), 401

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
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500

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
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)