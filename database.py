import sqlite3
from flask import g
import os

def get_db():
    if 'db' not in g:
        database_url = os.getenv('DATABASE_URL', 'airline.db')
        g.db = sqlite3.connect(database_url)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    conn = sqlite3.connect(os.getenv('DATABASE_URL', 'airline.db'))
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

    # Push Subscriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            endpoint TEXT,
            p256dh TEXT,
            auth TEXT,
            created_at INTEGER NOT NULL,
            expires_at INTEGER,
            fcm_token TEXT UNIQUE,  -- Новое поле для FCM токена
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    cursor.execute('''
                   CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user
                       ON push_subscriptions(user_id)
                   ''')

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS notification_logs
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       admin_user_id
                       INTEGER
                       NOT
                       NULL,
                       title
                       TEXT
                       NOT
                       NULL,
                       body
                       TEXT
                       NOT
                       NULL,
                       target
                       TEXT
                       NOT
                       NULL,
                       target_id
                       TEXT,
                       sent_at
                       INTEGER
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       admin_user_id
                   ) REFERENCES users
                   (
                       id
                   )
                       )
                   ''')

    conn.commit()
    conn.close()

init_db()