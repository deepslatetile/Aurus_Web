import sqlite3
from flask import g
import os
import time

def get_db():
    if 'db' not in g:
        database_url = os.getenv('DATABASE_URL', 'airline.db')
        g.db = sqlite3.connect(database_url, timeout=15.0)
        g.db.execute('PRAGMA journal_mode=DELETE')
        g.db.execute('PRAGMA synchronous=NORMAL')
        g.db.execute('PRAGMA busy_timeout=15000')
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except:
            pass

def execute_with_retry(query, params=(), max_retries=3):
    for attempt in range(max_retries):
        try:
            db = get_db()
            cursor = db.execute(query, params)
            db.commit()
            return cursor
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            else:
                raise


def init_db():
    max_retries = 5
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(os.getenv('DATABASE_URL', 'airline.db'), timeout=15.0)
            conn.execute('PRAGMA journal_mode=DELETE')
            conn.execute('PRAGMA synchronous=NORMAL')

            cursor = conn.cursor()

            # Schedule table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedule
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    flight_number TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    departure TEXT NOT NULL,
                    arrival TEXT NOT NULL,
                    datetime INTEGER NOT NULL,
                    enroute TEXT NOT NULL,
                    status TEXT NOT NULL,
                    seatmap TEXT NOT NULL,
                    aircraft TEXT NOT NULL,
                    meal TEXT NOT NULL,
                    pax_service TEXT NOT NULL,
                    boarding_pass_default TEXT NOT NULL
                )
            ''')

            # PAX Service table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pax_service
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    image BLOB,
                    groupname TEXT NOT NULL,
                    subgroupname TEXT NOT NULL,
                    price REAL DEFAULT 0
                )
            ''')

            # Bookings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bookings
                (
                    id TEXT PRIMARY KEY,
                    flight_number TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    seat TEXT NOT NULL,
                    serve_class TEXT NOT NULL,
                    pax_service TEXT,
                    boarding_pass TEXT,
                    note TEXT,
                    valid INTEGER,
                    passenger_name TEXT
                )
            ''')

            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nickname TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    virtual_id INTEGER UNIQUE,
                    social_id INTEGER UNIQUE,
                    miles INTEGER NOT NULL,
                    bonuses TEXT,
                    user_group TEXT NOT NULL,
                    subgroup TEXT NOT NULL,
                    link TEXT,
                    pfp BLOB,
                    metadata TEXT,
                    pending TEXT,
                    status TEXT,
                    password_hash TEXT NOT NULL,
                    session_token TEXT
                )
            ''')

            # Meals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS meals
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    serve_class TEXT NOT NULL,
                    serve_time TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    image BLOB
                )
            ''')

            # About us table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS about_us
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    image BLOB,
                    about_group TEXT NOT NULL,
                    subgroup TEXT NOT NULL,
                    link TEXT
                )
            ''')

            # Configs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configs
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    image BLOB
                )
            ''')

            # Web configs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS web_configs
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    page_name TEXT NOT NULL UNIQUE,
                    page_display TEXT NOT NULL,
                    state INTEGER DEFAULT 1,
                    content TEXT,
                    last_updated INTEGER
                )
            ''')

            # OAuth connections table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS oauth_connections
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    provider TEXT NOT NULL,
                    provider_user_id TEXT NOT NULL,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    expires_at INTEGER,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE (user_id, provider)
                )
            ''')

            # Transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    booking_id TEXT,
                    amount REAL NOT NULL,
                    description TEXT NOT NULL,
                    type TEXT NOT NULL,
                    admin_user_id INTEGER NOT NULL,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (admin_user_id) REFERENCES users (id)
                )
            ''')

            # Flight Configs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS flight_configs
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    description TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            ''')

            # Weather Cache table
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS weather_cache
                           (
                               icao_code
                               TEXT
                               PRIMARY
                               KEY,
                               data
                               TEXT
                               NOT
                               NULL,
                               created_at
                               INTEGER
                               NOT
                               NULL,
                               expires_at
                               INTEGER
                               NOT
                               NULL
                           )
                           ''')
            cursor.execute('''
                           CREATE INDEX IF NOT EXISTS idx_weather_cache_expires
                               ON weather_cache(expires_at)
                           ''')

            conn.commit()
            conn.close()
            break
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                time.sleep(1)
                continue
            else:
                raise

init_db()