from flask import Blueprint, request, jsonify, session
import sqlite3
import hashlib
import secrets
from services.utils import login_required, get_current_user
import time

auth_bp = Blueprint('auth', __name__)


def execute_with_retry(query, params=(), max_retries=3):
    """Безопасное выполнение запроса с повторными попытками"""
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect('airline.db', timeout=20.0)
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            result = cursor.fetchall() if query.strip().upper().startswith('SELECT') else None
            conn.close()
            return result
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            else:
                if 'conn' in locals():
                    try:
                        conn.close()
                    except:
                        pass
                raise
        except Exception as e:
            if 'conn' in locals():
                try:
                    conn.close()
                except:
                    pass
            raise


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

        # Используем безопасное выполнение с повторными попытками
        result = execute_with_retry("SELECT * FROM users WHERE nickname = ?", (username,))

        if not result:
            return jsonify({"error": "Invalid credentials"}), 401

        user = result[0]

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user[14] != password_hash:
            return jsonify({"error": "Invalid credentials"}), 401

        session_token = secrets.token_hex(32)

        # Обновляем токен с повторными попытками
        execute_with_retry("UPDATE users SET session_token = ? WHERE id = ?", (session_token, user[0]))

        session['user_id'] = user[0]
        session['session_token'] = session_token
        session['user_group'] = user[7]
        session['nickname'] = user[1]
        session['subgroup'] = user[8]

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

    except sqlite3.OperationalError as e:
        if "locked" in str(e):
            return jsonify({"error": "Database is temporarily busy, please try again"}), 503
        else:
            print(f"Database error during login: {e}")
            return jsonify({"error": "Database error"}), 500
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

        # Проверяем существование пользователя с повторными попытками
        result = execute_with_retry("SELECT id FROM users WHERE nickname = ?", (nickname,))

        if result:
            return jsonify({"error": "User with this nickname already exists"}), 409

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Создаем пользователя с повторными попытками
        conn = sqlite3.connect('airline.db', timeout=20.0)
        cursor = conn.cursor()

        cursor.execute('''
                       INSERT INTO users (nickname, password_hash, user_group, subgroup, session_token)
                       VALUES (?, ?, ?, ?, NULL)
                       ''', (nickname, password_hash, user_group, subgroup))

        user_id = cursor.lastrowid
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

    except sqlite3.OperationalError as e:
        if "locked" in str(e):
            return jsonify({"error": "Database is temporarily busy, please try again"}), 503
        else:
            print(f"Database error during registration: {e}")
            return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({"error": "Something went wrong"}), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
def auth_logout():
    try:
        # Используем безопасное выполнение с повторными попытками
        execute_with_retry("UPDATE users SET session_token = NULL WHERE id = ?", (session['user_id'],))

        session.clear()
        return jsonify({"message": "Logout successful"}), 200

    except sqlite3.OperationalError as e:
        if "locked" in str(e):
            return jsonify({"error": "Database is temporarily busy, please try again"}), 503
        else:
            print(f"Database error during logout: {e}")
            return jsonify({"error": "Database error"}), 500
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