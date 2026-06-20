from flask import Flask

# Create the Flask app
app = Flask(__name__)

# Secret key required for sessions
app.secret_key = "nutrisense-secret-key-2025"

# Test route - confirms the server is running
@app.route("/")
def home():
    return "NutriSense AI is running! ✅"

if __name__ == "__main__":
    app.run(debug=True)