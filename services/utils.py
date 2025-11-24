from functools import wraps
from flask import session, jsonify
import sqlite3

from functools import wraps
from flask import session, jsonify
import sqlite3


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401

        try:
            conn = sqlite3.connect('airline.db')
            c = conn.cursor()
            c.execute("SELECT session_token FROM users WHERE id = ?", (session['user_id'],))
            user = c.fetchone()
            conn.close()

            if not user or user[0] != session.get('session_token'):
                session.clear()
                return jsonify({"error": "Invalid session"}), 401
        except Exception as e:
            print(f"Session validation error: {e}")
            return jsonify({"error": "Session validation failed"}), 500

        return f(*args, **kwargs)

    return decorated_function

def get_current_user():
    if 'user_id' in session:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        user = c.fetchone()
        conn.close()

        if user:
            return {
                "id": user[0],
                "nickname": user[1],
                "created_at": user[2],
                "virtual_id": user[3],
                "social_id": user[4],
                "miles": user[5],
                "user_group": user[7],
                "subgroup": user[8]
            }
    return None

def generate_booking_id():
    """Generate random 4-character booking ID"""
    import random
    import string
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(4))