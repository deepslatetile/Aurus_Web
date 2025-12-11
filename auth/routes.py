from flask import Blueprint, request, jsonify, session
from database import get_db, execute_with_retry
import hashlib
import secrets
from services.utils import login_required, get_current_user
import time

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def auth_login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE nickname = %s", (username,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "Invalid credentials"}), 401

        user = result

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user['password_hash'] != password_hash:
            return jsonify({"error": "Invalid credentials"}), 401

        session_token = secrets.token_hex(32)

        cursor.execute("UPDATE users SET session_token = %s WHERE id = %s", (session_token, user['id']))
        db.commit()

        session['user_id'] = user['id']
        session['session_token'] = session_token
        session['user_group'] = user['user_group']
        session['nickname'] = user['nickname']
        session['subgroup'] = user['subgroup']

        response_data = {
            "message": "Login successful",
            "user": {
                "id": user['id'],
                "nickname": user['nickname'],
                "user_group": user['user_group'],
                "subgroup": user['subgroup']
            }
        }

        return jsonify(response_data), 200

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@auth_bp.route('/post/user', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        nickname = data.get('nickname')
        password = data.get('password')
        user_group = data.get('user_group', 'PAX')
        subgroup = data.get('subgroup', '')

        if not nickname or not password:
            return jsonify({"error": "Nickname and password are required"}), 400

        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE nickname = %s", (nickname,))
        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({"error": "User with this nickname already exists"}), 409

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        created_at = int(time.time())

        cursor.execute('''
                       INSERT INTO users (nickname, password_hash, user_group, subgroup, session_token, created_at, miles)
                       VALUES (%s, %s, %s, %s, NULL, %s, 0)
                       ''', (nickname, password_hash, user_group, subgroup, created_at))

        user_id = cursor.lastrowid
        db.commit()

        return jsonify({
            "message": "Registration successful",
            "user": {
                "id": user_id,
                "nickname": nickname,
                "user_group": user_group
            }
        }), 201

    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def auth_logout():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET session_token = NULL WHERE id = %s", (session['user_id'],))
        db.commit()

        session.clear()
        return jsonify({"message": "Logout successful"}), 200

    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@auth_bp.route('/me', methods=['GET'])
@login_required
def auth_me():
    user = get_current_user()
    if user:
        return jsonify(user), 200
    return jsonify({"error": "User not found"}), 404

@auth_bp.route('/user_session', methods=['GET'])
@login_required
def get_user_session():
    return jsonify({
        "user_id": session.get('user_id'),
        "user_group": session.get('user_group'),
        "nickname": session.get('nickname'),
        "subgroup": session.get('subgroup')
    }), 200
    