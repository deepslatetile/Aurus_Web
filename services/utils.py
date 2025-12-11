from functools import wraps
from flask import session, jsonify
from database import get_db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401

        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT session_token FROM users WHERE id = %s", (session['user_id'],))
            user = cursor.fetchone()

            if not user or user['session_token'] != session.get('session_token'):
                session.clear()
                return jsonify({"error": "Invalid session"}), 401
        except Exception as e:
            print(f"Session validation error: {e}")
            return jsonify({"error": "Session validation failed"}), 500

        return f(*args, **kwargs)

    return decorated_function

def get_current_user():
    if 'user_id' in session:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()

        if user:
            return {
                "id": user['id'],
                "nickname": user['nickname'],
                "created_at": user['created_at'],
                "virtual_id": user['virtual_id'],
                "social_id": user['social_id'],
                "miles": user['miles'],
                "user_group": user['user_group'],
                "subgroup": user['subgroup']
            }
    return None

def generate_booking_id():
    import random
    import string
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(4))
    