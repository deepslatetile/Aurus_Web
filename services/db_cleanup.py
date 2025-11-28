import sqlite3
import os

def cleanup_database():
    try:
        db_path = os.getenv('DATABASE_URL', 'airline.db')
        conn = sqlite3.connect(db_path, timeout=10.0)
        conn.execute("PRAGMA optimize")
        conn.close()
        print("Database cleanup completed")
    except:
        print("Database cleanup failed")
