import os

def init_app(app):
    app.secret_key = os.getenv('SECRET_KEY')

    app.config['DISCORD_CLIENT_ID'] = os.getenv('DISCORD_CLIENT_ID')
    app.config['DISCORD_CLIENT_SECRET'] = os.getenv('DISCORD_CLIENT_SECRET')
    app.config['DISCORD_REDIRECT_URI'] = os.getenv('DISCORD_REDIRECT_URI')
    app.config['DISCORD_AUTH_URL'] = os.getenv('DISCORD_AUTH_URL')

    app.config['ROBLOX_CLIENT_ID'] = os.getenv('ROBLOX_CLIENT_ID')
    app.config['ROBLOX_CLIENT_SECRET'] = os.getenv('ROBLOX_CLIENT_SECRET')
    app.config['ROBLOX_REDIRECT_URI'] = os.getenv('ROBLOX_REDIRECT_URI')
    app.config['ROBLOX_AUTH_URL'] = os.getenv('ROBLOX_AUTH_URL')
    app.config['ROBLOX_TOKEN_URL'] = os.getenv('ROBLOX_TOKEN_URL')
    app.config['ROBLOX_API_URL'] = os.getenv('ROBLOX_API_URL')

    app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
    app.config['PORT'] = int(os.getenv('PORT', 2121))
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')

    from flask_cors import CORS
    CORS(app, resources={
        r"/*": {
            "origins": ["http://127.0.0.1:2121", "http://localhost:2121", "https://aurus.pythonanywhere.com"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    return app
