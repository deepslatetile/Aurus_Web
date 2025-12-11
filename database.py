import mysql.connector
from flask import g
import os
from mysql.connector import Error
import time

def get_db():
    if 'db' not in g:
        try:
            g.db = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST'),
                user=os.getenv('MYSQL_USER'),
                password=os.getenv('MYSQL_PASSWORD'),
                database=os.getenv('MYSQL_DB'),
                autocommit=True,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
        except Error as e:
            print(f"Database connection error: {e}")
            raise
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
            cursor = db.cursor(dictionary=True)
            cursor.execute(query, params)
            return cursor
        except Error as e:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            else:
                raise

def init_db():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'yourusername.mysql.pythonanywhere-services.com'),
            user=os.getenv('MYSQL_USER', 'yourusername'),
            password=os.getenv('MYSQL_PASSWORD', 'your_mysql_password'),
            database=os.getenv('MYSQL_DB', 'yourusername$default'),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        cursor = conn.cursor()

        print("🔄 Creating tables...")

        # Schedule table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule
            (
                id INT AUTO_INCREMENT PRIMARY KEY,
                flight_number VARCHAR(255) NOT NULL,
                created_at BIGINT NOT NULL,
                departure VARCHAR(255) NOT NULL,
                arrival VARCHAR(255) NOT NULL,
                datetime BIGINT NOT NULL,
                enroute TEXT NOT NULL,
                status VARCHAR(255) NOT NULL,
                seatmap TEXT NOT NULL,
                aircraft VARCHAR(255) NOT NULL,
                meal VARCHAR(255) NOT NULL,
                pax_service VARCHAR(255) NOT NULL,
                boarding_pass_default TEXT NOT NULL
            )
        ''')
        print("✅ Schedule table created")

        # PAX Service table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pax_service
            (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                image LONGBLOB,
                groupname VARCHAR(255) NOT NULL,
                subgroupname VARCHAR(255) NOT NULL,
                price DECIMAL(10,2) DEFAULT 0
            )
        ''')
        print("✅ PAX Service table created")

        # Bookings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings
            (
                id VARCHAR(255) PRIMARY KEY,
                flight_number VARCHAR(255) NOT NULL,
                created_at BIGINT NOT NULL,
                user_id INT NOT NULL,
                seat VARCHAR(255) NOT NULL,
                serve_class VARCHAR(255) NOT NULL,
                pax_service TEXT,
                boarding_pass TEXT,
                note TEXT,
                valid INT,
                passenger_name TEXT
            )
        ''')
        print("✅ Bookings table created")

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users
            (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nickname VARCHAR(255) NOT NULL,
                created_at BIGINT NOT NULL,
                virtual_id INT UNIQUE,
                social_id INT UNIQUE,
                miles INT NOT NULL,
                bonuses TEXT,
                user_group VARCHAR(255) NOT NULL,
                subgroup VARCHAR(255) NOT NULL,
                link TEXT,
                pfp LONGBLOB,
                metadata TEXT,
                pending TEXT,
                status VARCHAR(255),
                password_hash TEXT NOT NULL,
                session_token TEXT
            )
        ''')
        print("✅ Users table created")

        # Meals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meals
            (
                id INT AUTO_INCREMENT PRIMARY KEY,
                serve_class VARCHAR(255) NOT NULL,
                serve_time VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                image VARCHAR(255)
            )
        ''')
        print("✅ Meals table created")

        # About us table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS about_us
            (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                image LONGBLOB,
                about_group VARCHAR(255) NOT NULL,
                subgroup VARCHAR(255) NOT NULL,
                link TEXT,
                role VARCHAR(255),
                position VARCHAR(255),
                years_experience INT,
                fleet_type VARCHAR(255),
                registration_number VARCHAR(255),
                capacity INT,
                first_flight YEAR,
                display_order INT DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        print("✅ About us table created")

        # Configs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configs
            (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                image LONGBLOB
            )
        ''')
        print("✅ Configs table created")

        # Web configs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS web_configs
            (
                id INT AUTO_INCREMENT PRIMARY KEY,
                page_name VARCHAR(255) NOT NULL UNIQUE,
                page_display VARCHAR(255) NOT NULL,
                state INT DEFAULT 1,
                content TEXT,
                last_updated BIGINT
            )
        ''')
        print("✅ Web configs table created")

        # OAuth connections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS oauth_connections
            (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                provider VARCHAR(255) NOT NULL,
                provider_user_id VARCHAR(255) NOT NULL,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                expires_at BIGINT,
                created_at BIGINT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE (user_id, provider)
            )
        ''')
        print("✅ OAuth connections table created")

        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions
            (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                booking_id VARCHAR(255),
                amount DECIMAL(10,2) NOT NULL,
                description TEXT NOT NULL,
                type VARCHAR(255) NOT NULL,
                admin_user_id INT NOT NULL,
                created_at BIGINT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (admin_user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        print("✅ Transactions table created")

        # Flight Configs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flight_configs
            (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                type VARCHAR(255) NOT NULL,
                data TEXT NOT NULL,
                description TEXT,
                created_at BIGINT NOT NULL,
                updated_at BIGINT NOT NULL,
                is_active INT DEFAULT 1
            )
        ''')
        print("✅ Flight Configs table created")

        # Weather Cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_cache
            (
                icao_code VARCHAR(255) PRIMARY KEY,
                data TEXT NOT NULL,
                created_at BIGINT NOT NULL,
                expires_at BIGINT NOT NULL
            )
        ''')
        print("✅ Weather Cache table created")

        try:
            cursor.execute('''
                CREATE INDEX idx_weather_cache_expires 
                ON weather_cache(expires_at)
            ''')
            print("✅ Weather cache index created")
        except Error as e:
            if "Duplicate key name" not in str(e):
                print(f"⚠️ Could not create index (might already exist): {e}")

        print("🎉 All MySQL tables created successfully")
        conn.commit()
        conn.close()

    except Error as e:
        print(f"❌ Database initialization failed: {e}")
        raise
        