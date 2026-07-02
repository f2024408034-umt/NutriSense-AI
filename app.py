# ================================================================
# NUTRISENSE AI - FLASK BACKEND
# ================================================================
# This is the main backend file for NutriSense AI.
# It handles all API routes that the frontend communicates with.
#
# Tech Stack:
#   - Flask      : Python web framework (handles routes/requests)
#   - SQLite     : Lightweight database (stores users, meals, foods)
#   - Werkzeug   : Password hashing (security)
#   - Flask-CORS : Allows frontend HTML files to talk to this server
#   - Pandas     : Data analysis (used in admin stats route)
#
# How to run:
#   python app.py
#   Server starts at: http://127.0.0.1:5000
# ================================================================


# ----------------------------------------------------------------
# IMPORTS
# ----------------------------------------------------------------
# Flask      - core web framework
# request    - reads incoming data from frontend (JSON, form data)
# jsonify    - converts Python dicts to JSON responses
# session    - stores logged-in user info server-side
import os
from flask import Flask, request, jsonify, session, send_from_directory

# CORS - allows requests from frontend running on different port
from flask_cors import CORS

# Password security - never store plain text passwords
from werkzeug.security import generate_password_hash, check_password_hash

# sqlite3 - built-in Python database library
import sqlite3

# re - regular expressions for email/username validation
import re

# datetime - for getting today's date when logging meals
from datetime import datetime

# pandas - data analysis library (used in admin stats)
import pandas as pd


# ----------------------------------------------------------------
# APP CONFIGURATION
# ----------------------------------------------------------------
app = Flask(__name__, static_folder=".", static_url_path="")

# Secret key is used to encrypt session cookies
# In production, this should be stored in environment variables
app.secret_key = "nutrisense-ultra-secret-2025-xK9#mP2@"

# CORS setup - now everything runs on port 5000, no Live Server needed
CORS(app, supports_credentials=True, origins=[
    "http://127.0.0.1:5000",
    "http://localhost:5000",
    "null"
])


# ================================================================
# SERVE HTML FILES
# ================================================================
# Flask now serves all HTML/JS/CSS files from the project folder.
# No Live Server needed — just run "py app.py" and open:
# http://127.0.0.1:5000
# ================================================================

@app.route("/")
def serve_index():
    """Serve the main landing page"""
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    """
    Serve any static file from the project folder.
    Examples:
      http://127.0.0.1:5000/meal_logger.html
      http://127.0.0.1:5000/admin.html
      http://127.0.0.1:5000/who_tips.js
    """
    return send_from_directory(".", filename)


# ================================================================
# HELPER FUNCTIONS
# ================================================================
# These are reusable utility functions used across multiple routes.
# Putting them here avoids repeating code in every route.
# ================================================================

def get_db():
    """
    Opens and returns a connection to the SQLite database.
    row_factory = sqlite3.Row allows us to access columns by name
    instead of index. Example: user["email"] instead of user[0]
    """
    conn = sqlite3.connect("nutrisense.db")
    conn.row_factory = sqlite3.Row
    return conn


def is_valid_email(email):
    """
    Checks if an email address has a valid format.
    Example valid:   user@example.com
    Example invalid: userexample.com / user@.com
    """
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None


def is_valid_username(username):
    """
    Validates username format:
    - Only letters, numbers, underscores, hyphens allowed
    - Must be between 3 and 30 characters
    - Example valid:   umar_jutt589 / ali-raza / john123
    - Example invalid: umar jutt / @umar / ab
    """
    return bool(username) and re.match(r'^[\w\-]{3,30}$', username)


def is_valid_name(name):
    """
    Validates a real name (first name or last name):
    - Only letters and spaces allowed (no numbers or symbols)
    - Maximum 50 characters
    - Example valid:   Muhammad Ali / Sara
    - Example invalid: Ali123 / Ali@Raza
    """
    return bool(name) and len(name) <= 50 and re.match(r'^[a-zA-Z\s]+$', name)


def is_valid_age(age):
    """
    Validates age - must be a number between 1 and 120.
    Returns False if age is not a valid integer.
    """
    try:
        age = int(age)
        return 1 <= age <= 120
    except (TypeError, ValueError):
        return False


def login_required():
    """
    Checks if a user is currently logged in.
    Returns True if logged in, False otherwise.
    Used at the start of protected routes.
    """
    return "user_id" in session


def admin_required():
    """
    Checks if the current session belongs to an admin.
    Returns True if admin is logged in, False otherwise.
    """
    return session.get("is_admin") is True


# ================================================================
# SECTION 2 - AUTH ROUTES
# ================================================================
# These routes handle user registration, login, and logout.
# After login, a session is created server-side so we know
# which user is making each request.
# ================================================================

@app.route("/register", methods=["POST"])
def register():
    """
    POST /register
    Creates a new user account.

    Expected JSON body:
    {
        "username" : "umar_jutt589",
        "email"    : "umar@gmail.com",
        "password" : "mypassword123"
    }

    Returns:
        201 - Registration successful
        400 - Validation error (bad username, email, password)
        409 - Email or username already exists
        500 - Server error
    """
    try:
        # Step 1: Read the incoming JSON data from frontend
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        # Step 2: Extract fields from the request
        username = data.get("username", "").strip().lower()
        email    = data.get("email", "").strip().lower()
        password = data.get("password", "")

        # Step 3: Validate each field
        if not is_valid_username(username):
            return jsonify({
                "error": "Invalid username. Use 3-30 characters. Letters, numbers, underscores and hyphens only."
            }), 400

        if not is_valid_email(email):
            return jsonify({"error": "Invalid email format"}), 400

        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        # Step 4: Hash the password before storing
        # NEVER store plain text passwords in a database
        hashed_password = generate_password_hash(password)

        # Step 5: Check for duplicate username or email in the database
        conn   = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "This username is already taken"}), 409

        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "This email is already registered"}), 409

        # Step 6: Insert the new user into the database
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid  # Gets the ID of the newly inserted user
        conn.close()

        # Step 7: Automatically log the user in after registration
        # This way they don't need to log in again after signing up
        session["user_id"]   = user_id
        session["username"]  = username

        return jsonify({
            "message" : "Registration successful!",
            "user_id" : user_id,
            "username": username
        }), 201

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500


@app.route("/login", methods=["POST"])
def login():
    """
    POST /login
    Logs in a user using username OR email + password.

    Expected JSON body:
    {
        "login"    : "umar_jutt589"  OR  "umar@gmail.com",
        "password" : "mypassword123"
    }

    Returns:
        200 - Login successful (session created)
        400 - Missing fields
        401 - Wrong credentials
        500 - Server error
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        # "login" field accepts either username or email
        login_input = data.get("login", "").strip().lower()
        password    = data.get("password", "")

        if not login_input or not password:
            return jsonify({"error": "Username/email and password are required"}), 400

        conn   = get_db()
        cursor = conn.cursor()

        # Check if input looks like an email or a username
        # then search the database accordingly
        if "@" in login_input:
            # Looks like an email
            cursor.execute("SELECT * FROM users WHERE email = ?", (login_input,))
        else:
            # Looks like a username
            cursor.execute("SELECT * FROM users WHERE username = ?", (login_input,))

        user = cursor.fetchone()
        conn.close()

        # Verify user exists and password matches the stored hash
        if not user or not check_password_hash(user["password"], password):
            return jsonify({"error": "Incorrect username/email or password"}), 401

        # Create session - this keeps the user logged in
        session["user_id"]  = user["id"]
        session["username"] = user["username"]

        return jsonify({
            "message" : f"Welcome back, {user['username']}!",
            "user_id" : user["id"],
            "username": user["username"]
        }), 200

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500


@app.route("/logout", methods=["POST"])
def logout():
    """
    POST /logout
    Logs out the current user by clearing their session.

    Returns:
        200 - Logout successful
    """
    session.clear()
    return jsonify({"message": "Logged out successfully!"}), 200


# ================================================================
# SECTION 3 - PROFILE ROUTES
# ================================================================
# These routes handle saving and retrieving the user's
# detailed profile (name, age, height, weight, goal, etc.)
# Profile is separate from auth - filled after registration.
# ================================================================

@app.route("/save-profile", methods=["POST"])
def save_profile():
    """
    POST /save-profile
    Saves or updates the logged-in user's profile information.

    Expected JSON body:
    {
        "first_name"     : "Umar",
        "last_name"      : "Farooq",
        "age"            : 20,
        "gender"         : "Male",
        "activity_level" : "Moderately Active",
        "height"         : 175,
        "weight"         : 70,
        "goal"           : "Weight Loss",
        "conditions"     : ["Diabetes", "None"]
    }

    Returns:
        200 - Profile saved successfully
        400 - Validation error
        401 - Not logged in
        500 - Server error
    """
    try:
        # Check if user is logged in
        if not login_required():
            return jsonify({"error": "Please log in first"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        # Extract all profile fields
        first_name     = data.get("first_name", "").strip()
        last_name      = data.get("last_name",  "").strip()
        age            = data.get("age")
        gender         = data.get("gender",         "").strip()
        activity_level = data.get("activity_level", "").strip()
        height         = data.get("height")
        weight         = data.get("weight")
        goal           = data.get("goal",           "").strip()
        conditions     = data.get("conditions",     "")

        # Validate name fields (only letters allowed)
        if first_name and not is_valid_name(first_name):
            return jsonify({"error": "First name can only contain letters"}), 400

        if last_name and not is_valid_name(last_name):
            return jsonify({"error": "Last name can only contain letters"}), 400

        # Validate age
        if not is_valid_age(age):
            return jsonify({"error": "Age must be between 1 and 120"}), 400

        # Validate goal
        valid_goals = ["Weight Loss", "Weight Gain", "Maintain Weight", "Muscle Gain"]
        if goal not in valid_goals:
            return jsonify({"error": f"Invalid goal. Choose from: {', '.join(valid_goals)}"}), 400

        # Validate height and weight are numbers
        try:
            height = float(height)
            weight = float(weight)
        except (TypeError, ValueError):
            return jsonify({"error": "Height and weight must be valid numbers"}), 400

        # Convert conditions list to comma-separated string for storage
        if isinstance(conditions, list):
            conditions = ", ".join(conditions)

        # Update the user's profile in the database
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET first_name     = ?,
                last_name      = ?,
                age            = ?,
                gender         = ?,
                activity_level = ?,
                height         = ?,
                weight         = ?,
                goal           = ?,
                conditions     = ?
            WHERE id = ?
        """, (
            first_name, last_name, int(age),
            gender, activity_level,
            height, weight, goal, conditions,
            session["user_id"]
        ))
        conn.commit()
        conn.close()

        return jsonify({"message": "Profile saved successfully!"}), 200

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500


@app.route("/get-profile", methods=["GET"])
def get_profile():
    """
    GET /get-profile
    Returns the logged-in user's full profile information.

    Returns:
        200 - Profile data as JSON
        401 - Not logged in
        404 - User not found
        500 - Server error
    """
    try:
        if not login_required():
            return jsonify({"error": "Please log in first"}), 401

        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, email, first_name, last_name,
                   age, goal, gender, activity_level,
                   height, weight, conditions
            FROM users
            WHERE id = ?
        """, (session["user_id"],))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify(dict(user)), 200

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500


# ================================================================
# SECTION 4 - FOOD ROUTES
# ================================================================
# These routes handle the foods database.
# Foods are pre-loaded items users can select when logging meals.
# ================================================================

@app.route("/foods", methods=["GET"])
def get_foods():
    """
    GET /foods
    Returns a list of all available foods from the database.
    No login required - foods list is public.

    Returns:
        200 - List of all foods with nutrition info
        500 - Server error
    """
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM foods ORDER BY food_name ASC")
        foods = cursor.fetchall()
        conn.close()

        return jsonify({"foods": [dict(f) for f in foods]}), 200

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500


# ================================================================
# SECTION 5 - MEAL ROUTES
# ================================================================
# These routes handle logging meals and viewing daily dashboard.
# ================================================================

@app.route("/log-food", methods=["POST"])
def log_food():
    """
    POST /log-food
    Logs a food item as eaten by the current user.

    Expected JSON body:
    {
        "food_id"   : 3,
        "meal_type" : "Breakfast",
        "quantity"  : 2,
        "date"      : "2025-06-10"   (optional, defaults to today)
    }

    Returns:
        201 - Food logged successfully
        400 - Invalid food ID
        401 - Not logged in
        404 - Food not found in database
        500 - Server error
    """
    try:
        if not login_required():
            return jsonify({"error": "Please log in first"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        food_id   = data.get("food_id")
        meal_type = data.get("meal_type", "Meal")
        quantity  = data.get("quantity", 1)
        date      = data.get("date", datetime.now().strftime("%Y-%m-%d"))

        # Validate food_id is a number
        if not food_id or not str(food_id).isdigit():
            return jsonify({"error": "Please provide a valid food ID"}), 400

        # Validate quantity
        try:
            quantity = int(quantity)
            if quantity < 1:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "Quantity must be a positive number"}), 400

        conn   = get_db()
        cursor = conn.cursor()

        # Check if the food exists in the database
        cursor.execute("SELECT id, food_name FROM foods WHERE id = ?", (int(food_id),))
        food = cursor.fetchone()

        if not food:
            conn.close()
            return jsonify({"error": "This food item does not exist in our database"}), 404

        # Insert the meal log entry
        cursor.execute(
            "INSERT INTO meal_log (user_id, food_id, meal_type, quantity, date) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], int(food_id), meal_type, quantity, date)
        )
        conn.commit()
        conn.close()

        return jsonify({
            "message" : f"{food['food_name']} logged successfully!",
            "date"    : date,
            "quantity": quantity
        }), 201

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500


@app.route("/dashboard", methods=["GET"])
def dashboard():
    """
    GET /dashboard
    Returns today's meal summary for the logged-in user.
    Includes total calories, protein, carbs, and meal list.

    Returns:
        200 - Today's nutrition summary
        401 - Not logged in
        500 - Server error
    """
    try:
        if not login_required():
            return jsonify({"error": "Please log in first"}), 401

        conn   = get_db()
        cursor = conn.cursor()
        today  = datetime.now().strftime("%Y-%m-%d")

        # Join meal_log with foods to get nutrition data
        cursor.execute("""
            SELECT
                foods.food_name,
                foods.calories,
                foods.protein,
                foods.carbs,
                foods.fat,
                meal_log.meal_type,
                meal_log.quantity,
                meal_log.date
            FROM meal_log
            JOIN foods ON meal_log.food_id = foods.id
            WHERE meal_log.user_id = ?
            AND   meal_log.date    = ?
            ORDER BY meal_log.id ASC
        """, (session["user_id"], today))

        meals = cursor.fetchall()
        conn.close()

        # Calculate totals (multiply by quantity, default to 1 if NULL)
        total_calories = sum(m["calories"] * (m["quantity"] or 1) for m in meals)
        total_protein  = sum(m["protein"]  * (m["quantity"] or 1) for m in meals)
        total_carbs    = sum(m["carbs"]    * (m["quantity"] or 1) for m in meals)
        total_fat      = sum((m["fat"] or 0) * (m["quantity"] or 1) for m in meals)

        return jsonify({
            "date"           : today,
            "meals"          : [dict(m) for m in meals],
            "total_calories" : total_calories,
            "total_protein"  : round(total_protein, 1),
            "total_carbs"    : round(total_carbs,   1),
            "total_fat"      : round(total_fat,      1)
        }), 200

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500


# ================================================================
# SECTION 6 - ANALYSIS ROUTE
# ================================================================
# Analyzes today's nutrition and gives personalized health
# warnings and suggestions based on the user's goal.
# ================================================================

@app.route("/analyze", methods=["GET"])
def analyze():
    """
    GET /analyze
    Analyzes the logged-in user's today's meals and returns:
    - Total nutrition (calories, protein, carbs)
    - Health warnings (e.g. too many carbs, low protein)
    - Goal-based suggestions (based on user's health goal)

    Returns:
        200 - Analysis result with warnings and suggestions
        401 - Not logged in
        500 - Server error
    """
    try:
        if not login_required():
            return jsonify({"error": "Please log in first"}), 401

        conn   = get_db()
        cursor = conn.cursor()
        today  = datetime.now().strftime("%Y-%m-%d")

        # Get the user's health goal and conditions
        cursor.execute(
            "SELECT goal, conditions FROM users WHERE id = ?",
            (session["user_id"],)
        )
        user       = cursor.fetchone()
        goal       = user["goal"]       or "Maintain Weight"
        conditions = user["conditions"] or ""

        # Get today's meals with nutrition info
        cursor.execute("""
            SELECT
                foods.food_name,
                foods.calories,
                foods.protein,
                foods.carbs,
                meal_log.quantity
            FROM meal_log
            JOIN foods ON meal_log.food_id = foods.id
            WHERE meal_log.user_id = ?
            AND   meal_log.date    = ?
        """, (session["user_id"], today))

        meals = cursor.fetchall()
        conn.close()

        # Calculate totals
        total_calories = sum(m["calories"] * (m["quantity"] or 1) for m in meals)
        total_protein  = sum(m["protein"]  * (m["quantity"] or 1) for m in meals)
        total_carbs    = sum(m["carbs"]    * (m["quantity"] or 1) for m in meals)

        # ---- BUILD WARNINGS ----
        warnings = []

        if total_calories == 0:
            warnings.append("ℹ️ No meals logged today yet")
        elif total_calories > 2000:
            warnings.append("⚠️ High calorie intake - you have exceeded 2000 calories")

        if total_carbs > 150:
            warnings.append("⚠️ High carb/sugar intake - this may increase diabetes risk")

        if total_protein < 50 and total_calories > 0:
            warnings.append("⚠️ Low protein intake - protein is important for muscle health")

        # Extra warning for users with diabetes condition
        if "Diabetes" in conditions and total_carbs > 100:
            warnings.append("⚠️ You have diabetes - please monitor your carb intake carefully")

        if not warnings:
            warnings.append("✅ Everything looks good - no health concerns today")

        # ---- BUILD SUGGESTIONS based on goal ----
        suggestions = []

        if goal == "Weight Loss":
            if total_calories > 1800:
                suggestions.append("🥗 Try lighter meals - you are over your Weight Loss calorie target")
            else:
                suggestions.append("✅ Calorie intake is on track for your Weight Loss goal")

        elif goal == "Weight Gain":
            if total_calories < 2200:
                suggestions.append("🍗 Eat more calories and protein to support your Weight Gain goal")
            else:
                suggestions.append("✅ Calorie intake is on track for your Weight Gain goal")

        elif goal == "Muscle Gain":
            if total_protein < 80:
                suggestions.append("💪 Increase protein intake - try chicken, eggs, or lentils")
            else:
                suggestions.append("✅ Great protein intake for your Muscle Gain goal")

        elif goal == "Maintain Weight":
            suggestions.append("✅ Keep maintaining a balanced and consistent diet")

        return jsonify({
            "date"           : today,
            "goal"           : goal,
            "total_calories" : total_calories,
            "total_protein"  : round(total_protein, 1),
            "total_carbs"    : round(total_carbs,   1),
            "warnings"       : warnings,
            "suggestions"    : suggestions
        }), 200

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500


# ================================================================
# SECTION 7 - USER ACCOUNT ROUTES
# ================================================================

@app.route("/delete-account", methods=["DELETE"])
def delete_account():
    """
    DELETE /delete-account
    Permanently deletes the logged-in user's account and all
    their associated meal logs from the database.

    Returns:
        200 - Account deleted successfully
        401 - Not logged in
        500 - Server error
    """
    try:
        if not login_required():
            return jsonify({"error": "Please log in first"}), 401

        user_id = session["user_id"]
        conn    = get_db()
        cursor  = conn.cursor()

        # Delete meal logs first (because of foreign key constraint)
        # Foreign key means meal_log.user_id references users.id
        # So we must delete the child records before the parent
        cursor.execute("DELETE FROM meal_log WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users    WHERE id      = ?", (user_id,))
        conn.commit()
        conn.close()

        # Clear the session so user is logged out
        session.clear()

        return jsonify({"message": "Your account has been permanently deleted"}), 200

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500


# ================================================================
# SECTION 8 - WEEKLY REPORT ROUTE
# ================================================================
# Returns the last 7 days of meal data for the logged-in user.
# Used by weekly_reports.html to show a real summary from the
# database instead of reading from localStorage.
# ================================================================

@app.route("/weekly-report", methods=["GET"])
def weekly_report():
    """
    GET /weekly-report
    Returns meal logs for the last 7 days grouped by date.

    Returns:
        200 - Weekly summary with per-day breakdown
        401 - Not logged in
        500 - Server error
    """
    try:
        if not login_required():
            return jsonify({"error": "Please log in first"}), 401

        conn   = get_db()
        cursor = conn.cursor()

        # Get the last 7 days of meal logs with food nutrition data
        cursor.execute("""
            SELECT
                meal_log.date,
                foods.food_name,
                foods.calories,
                foods.protein,
                foods.carbs,
                foods.fat,
                meal_log.meal_type,
                meal_log.quantity
            FROM meal_log
            JOIN foods ON meal_log.food_id = foods.id
            WHERE meal_log.user_id = ?
            AND   meal_log.date   >= date('now', '-6 days')
            ORDER BY meal_log.date ASC, meal_log.id ASC
        """, (session["user_id"],))

        rows = cursor.fetchall()

        # Get user goal for analysis
        cursor.execute(
            "SELECT goal, first_name, last_name, username FROM users WHERE id = ?",
            (session["user_id"],)
        )
        user = cursor.fetchone()
        conn.close()

        # ---- Group meals by date ----
        # Build a dict: { "2025-06-10": { calories, protein, carbs, meals: [] } }
        from collections import defaultdict
        days = defaultdict(lambda: {
            "calories": 0,
            "protein" : 0,
            "carbs"   : 0,
            "fat"     : 0,
            "meals"   : []
        })

        for row in rows:
            date = row["date"]
            qty  = row["quantity"] or 1
            days[date]["calories"] += row["calories"] * qty
            days[date]["protein"]  += row["protein"]  * qty
            days[date]["carbs"]    += row["carbs"]    * qty
            days[date]["fat"]      += (row["fat"] or 0) * qty
            days[date]["meals"].append(row["food_name"])

        # Convert to a sorted list for the frontend
        daily_data = []
        for date, data in sorted(days.items()):
            daily_data.append({
                "date"    : date,
                "calories": round(data["calories"], 1),
                "protein" : round(data["protein"],  1),
                "carbs"   : round(data["carbs"],    1),
                "fat"     : round(data["fat"],      1),
                "meals"   : data["meals"]
            })

        # ---- Weekly totals ----
        total_calories = sum(d["calories"] for d in daily_data)
        total_protein  = sum(d["protein"]  for d in daily_data)
        total_meals    = sum(len(d["meals"]) for d in daily_data)
        avg_calories   = round(total_calories / 7, 1)

        # ---- Nutrition score (out of 100) ----
        score = 0
        if 1200 <= avg_calories <= 1800: score += 40
        if total_protein >= 60:          score += 30
        if total_meals   >= 7:           score += 20
        if len(daily_data) >= 5:         score += 10

        # ---- Display name ----
        display_name = " ".join(filter(None, [
            user["first_name"], user["last_name"]
        ])) if user else "User"

        return jsonify({
            "display_name"   : display_name or user["username"],
            "goal"           : user["goal"] if user else "-",
            "daily_data"     : daily_data,
            "total_calories" : round(total_calories, 1),
            "total_protein"  : round(total_protein,  1),
            "total_meals"    : total_meals,
            "avg_calories"   : avg_calories,
            "nutrition_score": score
        }), 200

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500


# ================================================================
# SECTION 9 - ADMIN ROUTES
# ================================================================
# Admin has a separate login with hardcoded credentials.
# Admin can view all users, see stats, and delete accounts.
# Pandas is used in /admin/stats for data analysis.
#
# Admin credentials:
#   Email   : admin@nutrisense.com
#   Password: admin123
# ================================================================

# Hardcoded admin credentials
# In a real production app, this would be in a .env file
ADMIN_EMAIL    = "admin@nutrisense.com"
ADMIN_PASSWORD = "admin123"


@app.route("/admin/login", methods=["POST"])
def admin_login():
    """
    POST /admin/login
    Logs in the admin user.

    Expected JSON body:
    {
        "email"    : "admin@nutrisense.com",
        "password" : "admin123"
    }

    Returns:
        200 - Admin logged in successfully
        400 - No data received
        401 - Wrong credentials
        500 - Server error
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        email    = data.get("email",    "").strip().lower()
        password = data.get("password", "")

        # Check against hardcoded admin credentials
        if email != ADMIN_EMAIL or password != ADMIN_PASSWORD:
            return jsonify({"error": "Incorrect admin credentials"}), 401

        # Set admin flag in session
        session["is_admin"] = True

        return jsonify({"message": "Welcome Admin!", "admin": True}), 200

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    """
    POST /admin/logout
    Logs out the admin by removing admin flag from session.

    Returns:
        200 - Admin logged out
    """
    session.pop("is_admin", None)
    return jsonify({"message": "Admin logged out successfully!"}), 200


@app.route("/admin/users", methods=["GET"])
def admin_get_users():
    """
    GET /admin/users
    Returns a list of all registered users with their profile data.
    Admin access required.

    Returns:
        200 - List of all users
        403 - Not an admin
        500 - Server error
    """
    try:
        if not admin_required():
            return jsonify({"error": "Admin access required"}), 403

        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                id, username, email,
                first_name, last_name,
                age, goal, gender,
                activity_level, height,
                weight, conditions
            FROM users
            ORDER BY id DESC
        """)
        users = cursor.fetchall()
        conn.close()

        return jsonify({"users": [dict(u) for u in users]}), 200

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500


@app.route("/admin/stats", methods=["GET"])
def admin_stats():
    """
    GET /admin/stats
    Returns detailed statistics about all users using Pandas.

    Pandas is used here to:
    - Count users per goal (value_counts)
    - Count users per gender
    - Count users per activity level
    - Calculate average age, height, weight
    - Find the most common conditions

    Returns:
        200 - Stats as JSON (used for charts in admin dashboard)
        403 - Not an admin
        500 - Server error
    """
    try:
        if not admin_required():
            return jsonify({"error": "Admin access required"}), 403

        conn   = get_db()
        cursor = conn.cursor()

        # Fetch all users into a Pandas DataFrame
        # A DataFrame is like an Excel table in Python
        cursor.execute("""
            SELECT
                id, age, goal, gender,
                activity_level, height,
                weight, conditions
            FROM users
        """)
        rows    = cursor.fetchall()
        columns = ["id", "age", "goal", "gender",
                   "activity_level", "height", "weight", "conditions"]

        # Total meals count
        cursor.execute("SELECT COUNT(*) as total FROM meal_log")
        total_meals = cursor.fetchone()["total"]
        conn.close()

        # Convert to Pandas DataFrame for analysis
        df = pd.DataFrame(rows, columns=columns)

        # Handle empty database
        if df.empty:
            return jsonify({
                "total_users"   : 0,
                "total_meals"   : total_meals,
                "goal_stats"    : [],
                "gender_stats"  : [],
                "activity_stats": [],
                "averages"      : {}
            }), 200

        # ---- PANDAS ANALYSIS ----

        # 1. Goal distribution - how many users per goal
        # value_counts() counts occurrences of each unique value
        goal_counts = df["goal"].dropna().value_counts()
        goal_stats  = [
            {"goal": goal, "count": int(count)}
            for goal, count in goal_counts.items()
        ]

        # 2. Gender distribution
        gender_counts = df["gender"].dropna().value_counts()
        gender_stats  = [
            {"gender": gender, "count": int(count)}
            for gender, count in gender_counts.items()
        ]

        # 3. Activity level distribution
        activity_counts = df["activity_level"].dropna().value_counts()
        activity_stats  = [
            {"activity_level": level, "count": int(count)}
            for level, count in activity_counts.items()
        ]

        # 4. Averages - mean() calculates the average of a column
        # round() keeps it to 1 decimal place
        averages = {}
        if df["age"].dropna().any():
            averages["avg_age"]    = round(float(df["age"].dropna().mean()),    1)
        if df["height"].dropna().any():
            averages["avg_height"] = round(float(df["height"].dropna().mean()), 1)
        if df["weight"].dropna().any():
            averages["avg_weight"] = round(float(df["weight"].dropna().mean()), 1)

        return jsonify({
            "total_users"   : len(df),
            "total_meals"   : total_meals,
            "goal_stats"    : goal_stats,
            "gender_stats"  : gender_stats,
            "activity_stats": activity_stats,
            "averages"      : averages
        }), 200

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500


@app.route("/admin/report", methods=["GET"])
def admin_report():
    """
    GET /admin/report
    Generates a CSV summary report of all users using Pandas.
    Admin can download this file.

    Pandas is used here to:
    - Create a clean DataFrame from user data
    - Export it to CSV format
    - Send it as a downloadable file

    Returns:
        200 - CSV file download
        403 - Not an admin
        500 - Server error
    """
    try:
        if not admin_required():
            return jsonify({"error": "Admin access required"}), 403

        from flask import Response

        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                id, username, email,
                first_name, last_name,
                age, goal, gender,
                activity_level, height,
                weight, conditions
            FROM users
            ORDER BY id ASC
        """)
        rows = cursor.fetchall()
        conn.close()

        # Define column headers for the CSV
        columns = [
            "ID", "Username", "Email",
            "First Name", "Last Name",
            "Age", "Goal", "Gender",
            "Activity Level", "Height (cm)",
            "Weight (kg)", "Conditions"
        ]

        # Create a Pandas DataFrame from the database rows
        df = pd.DataFrame([dict(r) for r in rows])

        if df.empty:
            return jsonify({"error": "No users found to generate report"}), 404

        # Rename columns to be clean and readable
        df.columns = columns[:len(df.columns)]

        # Convert DataFrame to CSV string
        # index=False means don't include row numbers
        csv_data = df.to_csv(index=False)

        # Send as downloadable file
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=nutrisense_users_report.csv"
            }
        )

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500


@app.route("/admin/delete-user/<int:user_id>", methods=["DELETE"])
def admin_delete_user(user_id):
    """
    DELETE /admin/delete-user/<user_id>
    Permanently deletes a user account by ID.
    Admin access required.

    URL parameter:
        user_id - the ID of the user to delete

    Returns:
        200 - User deleted successfully
        403 - Not an admin
        404 - User not found
        500 - Server error
    """
    try:
        if not admin_required():
            return jsonify({"error": "Admin access required"}), 403

        conn   = get_db()
        cursor = conn.cursor()

        # First check if the user exists
        cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return jsonify({"error": "User not found"}), 404

        # Delete meal logs first (foreign key constraint)
        cursor.execute("DELETE FROM meal_log WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users    WHERE id      = ?", (user_id,))
        conn.commit()
        conn.close()

        return jsonify({
            "message": f"User '{user['username']}' has been permanently deleted"
        }), 200

    except Exception as e:
        return jsonify({"error": "Server error occurred", "detail": str(e)}), 500


# ================================================================
# RUN THE APP
# ================================================================
# This block only runs when you execute: python app.py
# debug=True means:
#   - Server auto-restarts when you save changes
#   - Shows detailed error messages in browser
# In production, debug should be False
# ================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0" , debug=True)