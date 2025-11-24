from flask import Flask, render_template, session, redirect, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

# Импорт модулей
from config import init_app
from database import init_db, get_db
from auth.routes import auth_bp
from auth.discord_oauth import discord_bp
from auth.roblox_oauth import roblox_bp
from api.schedule import schedule_bp
from api.bookings import bookings_bp
from api.users import users_bp
from api.meals import meals_bp
from api.configs import configs_bp
from api.web_configs import web_configs_bp
from services.boarding_pass import boarding_bp
from admin.bookings import admin_bookings_bp
from api.transactions import transactions_bp
from api.flight_configs import flight_configs_bp

app = Flask(__name__)
app = init_app(app)

# Инициализация базы данных
init_db()

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(discord_bp, url_prefix='/auth')
app.register_blueprint(roblox_bp, url_prefix='/auth')
app.register_blueprint(schedule_bp, url_prefix='/api')
app.register_blueprint(bookings_bp, url_prefix='/api')
app.register_blueprint(users_bp, url_prefix='/api')
app.register_blueprint(meals_bp, url_prefix='/api')
app.register_blueprint(configs_bp, url_prefix='/api')
app.register_blueprint(web_configs_bp, url_prefix='/api')
app.register_blueprint(boarding_bp, url_prefix='/api')
app.register_blueprint(admin_bookings_bp, url_prefix='/admin/api')
app.register_blueprint(transactions_bp, url_prefix='/api')
app.register_blueprint(flight_configs_bp, url_prefix='/api')


@app.route('/static/fonts/<path:filename>')
def serve_fonts(filename):
    return send_from_directory('static/fonts', filename)

@app.route('/static/images/<path:filename>')
def serve_images(filename):
    return send_from_directory('static/images', filename)

@app.route('/static/styles/<path:filename>')
def serve_styles(filename):
    return send_from_directory('static/styles', filename)


@app.route('/auth/discord')
def discord_auth_redirect():
    if 'user_id' not in session:
        return redirect('/login?redirect=/auth/discord')
    return redirect('/auth/discord')


@app.route('/auth/roblox')
def roblox_auth_redirect():
    if 'user_id' not in session:
        return redirect('/login?redirect=/auth/roblox')
    return redirect('/auth/roblox')


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/schedule', methods=['GET'])
def schedule():
    return render_template('schedule.html')


@app.route('/tos', methods=['GET'])
def tos():
    return render_template('tos.html')


@app.route('/privacy-policy', methods=['GET'])
def privacy_policy():
    return render_template('privacy-policy.html')


@app.route('/profile')
def profile_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('profile.html')


@app.route('/book', methods=['GET'])
def book_page():
    return render_template('book.html')


@app.route('/admin/bookings', methods=['GET'])
def admin_bookings():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not user or user['user_group'] not in ['HQ', 'STF']:
        return redirect('/')

    return render_template('admin_bookings.html')


@app.route('/admin/payments', methods=['GET'])
def admin_payments():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not user or user['user_group'] not in ['HQ', 'STF']:
        return redirect('/')

    return render_template('admin_payments.html')


@app.route('/admin/create_flight', methods=['GET'])
def admin_create_flight():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not user or user['user_group'] not in ['HQ', 'STF']:
        return redirect('/')

    return render_template('admin_create_flight.html')


@app.route('/admin/flight_configs', methods=['GET'])
def admin_flight_configs():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not user or user['user_group'] not in ['HQ', 'STF']:
        return redirect('/')

    return render_template('admin_flight_configs.html')


@app.route('/admin/meals', methods=['GET'])
def admin_meals():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not user or user['user_group'] not in ['HQ', 'STF']:
        return redirect('/')

    return render_template('admin_meals.html')


@app.route('/admin/edit_flight', methods=['GET'])
def admin_edit_flight():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not user or user['user_group'] not in ['HQ', 'STF']:
        return redirect('/')

    return render_template('admin_edit_flight.html')


@app.route('/menu', methods=['GET'])
def menu():
    return render_template('menu.html')


@app.route('/admin', methods=['GET'])
def admin_dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not user or user['user_group'] not in ['HQ', 'STF']:
        return redirect('/')

    return render_template('admin_dashboard.html')


@app.route('/admin/web_configs', methods=['GET'])
def admin_web_configs():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not user or user['user_group'] not in ['HQ', 'STF']:
        return redirect('/')

    return render_template('admin_web_configs.html')


def check_environment():
    # TODO
    return True

if __name__ == '__main__':
    if check_environment():
        app.run(debug=app.config['DEBUG'], port=app.config['PORT'], host='127.0.0.1')
    else:
        print("❌ Application cannot start due to missing configuration")