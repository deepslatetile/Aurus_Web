import sqlite3
import time
from functools import wraps
from flask import jsonify

def handle_db_locks(max_retries=3):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return f(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if "locked" in str(e) and attempt < max_retries - 1:
                        time.sleep(0.5 * (attempt + 1))
                        continue
                    else:
                        return jsonify({
                            "error": "Database is temporarily busy, please try again"
                        }), 503
                except Exception as e:
                    print(f"Database error in {f.__name__}: {e}")
                    return jsonify({"error": "Database error"}), 500
            return jsonify({"error": "Service temporarily unavailable"}), 503
        return decorated_function
    return decorator