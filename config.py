import os


def init_app(app):
    # Базовая конфигурация
    app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key-change-in-production')

    # OAuth конфигурация
    app.config['DISCORD_CLIENT_ID'] = os.getenv('DISCORD_CLIENT_ID')
    app.config['DISCORD_CLIENT_SECRET'] = os.getenv('DISCORD_CLIENT_SECRET')
    app.config['DISCORD_REDIRECT_URI'] = os.getenv('DISCORD_REDIRECT_URI',
                                                   'http://localhost:2121/auth/discord/callback')
    app.config['DISCORD_AUTH_URL'] = os.getenv('DISCORD_AUTH_URL')

    app.config['ROBLOX_CLIENT_ID'] = os.getenv('ROBLOX_CLIENT_ID')
    app.config['ROBLOX_CLIENT_SECRET'] = os.getenv('ROBLOX_CLIENT_SECRET')
    app.config['ROBLOX_REDIRECT_URI'] = os.getenv('ROBLOX_REDIRECT_URI', 'http://localhost:2121/auth/roblox/callback')
    app.config['ROBLOX_AUTH_URL'] = os.getenv('ROBLOX_AUTH_URL')
    app.config['ROBLOX_TOKEN_URL'] = os.getenv('ROBLOX_TOKEN_URL')
    app.config['ROBLOX_API_URL'] = os.getenv('ROBLOX_API_URL')

    # Конфигурация приложения
    app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
    app.config['PORT'] = int(os.getenv('PORT', 2121))
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'airline.db')

    # CORS конфигурация
    from flask_cors import CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://127.0.0.1:5000", "http://localhost:5000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    return app