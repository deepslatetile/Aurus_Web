from flask import Blueprint, request, jsonify, session
import sqlite3
import hashlib
import secrets
from services.utils import login_required, get_current_user

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

        conn = sqlite3.connect('airline.db')
        c = conn.cursor()
        
        # Ищем пользователя по nickname (это то что в интерфейсе называется username)
        c.execute("SELECT * FROM users WHERE nickname = ?", (username,))
        user = c.fetchone()

        if not user:
            conn.close()
            return jsonify({"error": "Invalid credentials"}), 401

        # Проверяем пароль
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user[14] != password_hash:  # password_hash в колонке 14
            conn.close()
            return jsonify({"error": "Invalid credentials"}), 401

        # Генерируем новый session_token
        session_token = secrets.token_hex(32)
        c.execute("UPDATE users SET session_token = ? WHERE id = ?", (session_token, user[0]))
        conn.commit()
        conn.close()

        # Сохраняем информацию в сессии
        session['user_id'] = user[0]
        session['session_token'] = session_token
        session['user_group'] = user[7]  # user_group в колонке 7
        session['nickname'] = user[1]    # nickname в колонке 1
        session['subgroup'] = user[8]    # subgroup в колонке 8

        response_data = {
            "message": "Login successful",
            "user": {
                "id": user[0],
                "nickname": user[1],
                "user_group": user[7],
                "subgroup": user[8]
            }
        }

        return jsonify(response_data), 200

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@auth_bp.route('/post/user', methods=['POST'])
def create_user():
    """Endpoint for user registration (used by frontend)"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        nickname = data.get('nickname')
        password = data.get('password')
        user_group = data.get('user_group', 'PAX')  # Default to 'PAX'
        subgroup = data.get('subgroup', '')  # Default to empty

        if not nickname or not password:
            return jsonify({"error": "Nickname and password are required"}), 400

        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        # Проверяем, не существует ли уже пользователь с таким nickname
        c.execute("SELECT id FROM users WHERE nickname = ?", (nickname,))
        if c.fetchone():
            conn.close()
            return jsonify({"error": "User with this nickname already exists"}), 409

        # Хешируем пароль
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Создаем нового пользователя
        c.execute('''
            INSERT INTO users (nickname, password_hash, user_group, subgroup, session_token)
            VALUES (?, ?, ?, ?, NULL)
        ''', (nickname, password_hash, user_group, subgroup))

        user_id = c.lastrowid
        conn.commit()
        conn.close()

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
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()
        c.execute("UPDATE users SET session_token = NULL WHERE id = ?", (session['user_id'],))
        conn.commit()
        conn.close()

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
    """Get current session data"""
    return jsonify({
        "user_id": session.get('user_id'),
        "user_group": session.get('user_group'),
        "nickname": session.get('nickname'),
        "subgroup": session.get('subgroup')
    }), 200