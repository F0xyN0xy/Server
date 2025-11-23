from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import re
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)

DATA_FILE = "users.json"

# SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "myteam.noreply@gmail.com"
SMTP_PASS = "quzq gevh ctws gtpp"

# ------------------- Helper functions -------------------
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_reset_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

def password_strength(pw):
    score = 0
    if len(pw) >= 8: score += 1
    if re.search(r"[A-Z]", pw): score += 1
    if re.search(r"[a-z]", pw): score += 1
    if re.search(r"[0-9]", pw): score += 1
    if re.search(r"[\W_]", pw): score += 1
    return score

def send_reset_email(email, reset_code):
    users = load_users()
    full_name = f"{users[email]['data'].get('name','')} {users[email]['data'].get('lastname','')}".strip()

    body = (
        f"Hello {full_name}!\n\n"
        f"Here is your reset code to reset your password:\n\n"
        f"{reset_code}\n\n"
        "If you didn't request this, please ignore this email.\n"
        "Please change it soon!\n\n"
        "This email was sent automatically, please do not reply.\n\n"
        "Best regards,\nYour Team"
    )

    msg = MIMEMultipart()
    msg["From"] = "Your App <myproject.noreply@gmail.com>"
    msg["To"] = email
    msg["Subject"] = "Password Reset Code"
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("Email error:", e)
        return False

# ------------------- API Routes -------------------

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')
    name = data.get('name', '')
    lastname = data.get('lastname', '')
    telephone = data.get('telephone', '')

    users = load_users()

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required"}), 400

    if email in users:
        return jsonify({"success": False, "message": "This email is already registered"}), 400

    if password_strength(password) < 3:
        return jsonify({"success": False, "message": "Password too weak"}), 400

    users[email] = {
        "password": password,
        "data": {
            "name": name,
            "lastname": lastname,
            "telephone": telephone
        }
    }
    save_users(users)

    return jsonify({"success": True, "message": "Account created successfully"})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    users = load_users()

    if email not in users:
        return jsonify({"success": False, "message": "Email does not exist"}), 404

    if users[email]["password"] != password:
        return jsonify({"success": False, "message": "Incorrect password"}), 401

    return jsonify({
        "success": True,
        "message": "Login successful",
        "user": {
            "email": email,
            "data": users[email]["data"]
        }
    })

@app.route('/api/password-strength', methods=['POST'])
def check_password_strength():
    data = request.get_json(silent=True) or {}
    password = data.get('password', '')
    score = password_strength(password)
    
    if score <= 2:
        strength = "weak"
    elif score == 3:
        strength = "medium"
    else:
        strength = "strong"
    
    return jsonify({"score": score, "strength": strength})

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip()

    users = load_users()

    if email not in users:
        return jsonify({"success": False, "message": "Email not found"}), 404

    reset_code = generate_reset_code()
    users[email]["reset_code"] = reset_code
    save_users(users)

    if send_reset_email(email, reset_code):
        return jsonify({"success": True, "message": "Reset code sent to your email"})
    else:
        return jsonify({"success": False, "message": "Could not send email"}), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip()
    code = data.get('code', '').strip()
    new_password = data.get('password', '')

    users = load_users()

    if email not in users:
        return jsonify({"success": False, "message": "Email not found"}), 404

    if users[email].get("reset_code") != code:
        return jsonify({"success": False, "message": "Incorrect reset code"}), 400

    if password_strength(new_password) < 3:
        return jsonify({"success": False, "message": "Password too weak"}), 400

    users[email]["password"] = new_password
    users[email].pop("reset_code", None)
    save_users(users)

    return jsonify({"success": True, "message": "Password changed successfully"})

@app.route('/api/profile/<email>', methods=['GET'])
def get_profile(email):
    users = load_users()
    
    if email not in users:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    return jsonify({
        "success": True,
        "user": {
            "email": email,
            "data": users[email]["data"]
        }
    })

@app.route('/api/profile/<email>', methods=['PUT'])
def update_profile(email):
    data = request.get_json(silent=True) or {}
    new_email = data.get('email', '').strip()
    name = data.get('name', '')
    lastname = data.get('lastname', '')
    telephone = data.get('telephone', '')

    users = load_users()

    if email not in users:
        return jsonify({"success": False, "message": "User not found"}), 404

    # Check if new email is already taken
    if new_email != email and new_email in users:
        return jsonify({"success": False, "message": "This email is already taken"}), 400

    # Update email key if changed
    if new_email != email:
        users[new_email] = users.pop(email)
        email = new_email

    users[email]["data"] = {
        "name": name,
        "lastname": lastname,
        "telephone": telephone
    }
    save_users(users)

    return jsonify({
        "success": True,
        "message": "Profile updated successfully",
        "email": email
    })

@app.route('/api/profile/<email>', methods=['DELETE'])
def delete_account(email):
    data = request.get_json(silent=True) or {}
    password = data.get('password', '')

    users = load_users()

    if email not in users:
        return jsonify({"success": False, "message": "User not found"}), 404

    if users[email]["password"] != password:
        return jsonify({"success": False, "message": "Incorrect password"}), 401

    users.pop(email)
    save_users(users)

    return jsonify({"success": True, "message": "Account deleted successfully"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)