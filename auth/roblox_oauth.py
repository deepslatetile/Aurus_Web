from flask import Blueprint, redirect, request, session, jsonify
import requests
from database import get_db
import secrets
from datetime import datetime
from urllib.parse import urlencode
from services.utils import login_required
from services.db_utils import handle_db_locks

roblox_bp = Blueprint('roblox', __name__)

@roblox_bp.route('/roblox')
@handle_db_locks(max_retries=5)
def auth_roblox():
    from app import app
    if not app.config['ROBLOX_CLIENT_ID'] or not app.config['ROBLOX_CLIENT_SECRET']:
        return jsonify({"error": "Roblox OAuth is not configured"}), 500

    params = {
        'client_id': app.config['ROBLOX_CLIENT_ID'],
        'redirect_uri': app.config['ROBLOX_REDIRECT_URI'],
        'response_type': 'code',
        'scope': 'openid profile',
        'state': secrets.token_urlsafe(16)
    }

    auth_url = f"{app.config['ROBLOX_AUTH_URL']}?{urlencode(params)}"
    return redirect(auth_url)

@roblox_bp.route('/roblox/callback')
@handle_db_locks(max_retries=5)
def auth_roblox_callback():
    from app import app
    if not app.config['ROBLOX_CLIENT_ID'] or not app.config['ROBLOX_CLIENT_SECRET']:
        return redirect('/profile?error=roblox_not_configured')

    try:
        code = request.args.get('code')
        if not code:
            return redirect('/profile?error=roblox_no_code')

        if 'user_id' not in session:
            return redirect('/login?redirect=/auth/roblox')

        user_id = session['user_id']

        token_data = {
            'client_id': app.config['ROBLOX_CLIENT_ID'],
            'client_secret': app.config['ROBLOX_CLIENT_SECRET'],
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': app.config['ROBLOX_REDIRECT_URI']
        }

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        ROBLOX_TOKEN_URL = 'https://apis.roblox.com/oauth/v1/token'
        token_response = requests.post(ROBLOX_TOKEN_URL, data=token_data, headers=headers)
        token_response.raise_for_status()
        token_json = token_response.json()

        access_token = token_json['access_token']
        refresh_token = token_json.get('refresh_token')
        expires_in = token_json.get('expires_in', 24 * 60 * 60)

        user_headers = {'Authorization': f'Bearer {access_token}'}
        ROBLOX_API_URL = 'https://apis.roblox.com/oauth/v1/userinfo'
        user_response = requests.get(ROBLOX_API_URL, headers=user_headers)
        user_response.raise_for_status()
        roblox_user = user_response.json()

        if not roblox_user.get('sub'):
            return redirect('/profile?error=roblox_no_user_id')

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('''
                  SELECT user_id
                  FROM oauth_connections
                  WHERE provider = %s
                    AND provider_user_id = %s
                    AND user_id != %s
                  ''', ('roblox', roblox_user['sub'], user_id))

        existing_connection = cursor.fetchone()
        if existing_connection:
            return redirect('/profile?error=roblox_already_linked')

        cursor.execute('''
                  SELECT id
                  FROM oauth_connections
                  WHERE user_id = %s
                    AND provider = 'roblox'
                  ''', (user_id,))

        current_connection = cursor.fetchone()

        if current_connection:
            cursor.execute('''
                      UPDATE oauth_connections
                      SET access_token  = %s,
                          refresh_token = %s,
                          expires_at    = %s
                      WHERE user_id = %s
                        AND provider = 'roblox'
                      ''', (
                          access_token,
                          refresh_token,
                          int(datetime.now().timestamp()) + expires_in,
                          user_id
                      ))
        else:
            cursor.execute('''
                      INSERT INTO oauth_connections (user_id, provider, provider_user_id, access_token, refresh_token,
                                                     expires_at, created_at)
                      VALUES (%s, %s, %s, %s, %s, %s, %s)
                      ''', (
                          user_id,
                          'roblox',
                          roblox_user['sub'],
                          access_token,
                          refresh_token,
                          int(datetime.now().timestamp()) + expires_in,
                          int(datetime.now().timestamp())
                      ))

        cursor.execute('''
                  UPDATE users
                  SET virtual_id = %s
                  WHERE id = %s
                  ''', (roblox_user['sub'], user_id))

        db.commit()
        return redirect('/profile?success=roblox_linked')

    except requests.RequestException as e:
        print(f"Roblox OAuth error: {e}")
        return redirect('/profile?error=roblox_auth_failed')
    except Exception as e:
        print(f"Unexpected error: {e}")
        return redirect('/profile?error=roblox_unexpected_error')

@roblox_bp.route('/roblox/connection', methods=['GET', 'DELETE'])
@login_required
@handle_db_locks(max_retries=5)
def roblox_connection():
    user_id = session['user_id']
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        if request.method == 'GET':
            cursor.execute('''
                      SELECT provider_user_id, created_at, expires_at
                      FROM oauth_connections
                      WHERE user_id = %s
                        AND provider = 'roblox'
                      ''', (user_id,))

            connection = cursor.fetchone()

            if connection:
                return jsonify({
                    "connected": True,
                    "provider_user_id": connection['provider_user_id'],
                    "connected_at": connection['created_at'],
                    "expires_at": connection['expires_at']
                }), 200
            else:
                return jsonify({"connected": False}), 200

        elif request.method == 'DELETE':
            cursor.execute('''
                      DELETE
                      FROM oauth_connections
                      WHERE user_id = %s
                        AND provider = 'roblox'
                      ''', (user_id,))

            deleted_count = cursor.rowcount
            db.commit()

            if deleted_count > 0:
                return jsonify({"message": "Roblox connection removed successfully"}), 200
            else:
                return jsonify({"error": "No Roblox connection found"}), 404

    except Exception as e:
        print(f"Roblox connection error: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@roblox_bp.route('/roblox/userinfo', methods=['GET'])
@login_required
@handle_db_locks(max_retries=5)
def roblox_userinfo():
    user_id = session['user_id']
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('''
                  SELECT access_token, expires_at
                  FROM oauth_connections
                  WHERE user_id = %s
                    AND provider = 'roblox'
                  ''', (user_id,))

        connection = cursor.fetchone()
        if not connection:
            return jsonify({"error": "Roblox account not connected"}), 404

        access_token, expires_at = connection['access_token'], connection['expires_at']
        if expires_at and expires_at < datetime.now().timestamp():
            return jsonify({"error": "Roblox token expired, please reconnect"}), 401

        headers = {'Authorization': f'Bearer {access_token}'}
        ROBLOX_API_URL = 'https://apis.roblox.com/oauth/v1/userinfo'
        user_response = requests.get(ROBLOX_API_URL, headers=headers)

        if user_response.status_code != 200:
            return jsonify({"error": "Failed to fetch Roblox user info"}), 500

        roblox_user = user_response.json()

        return jsonify({
            "roblox_user": {
                "id": roblox_user.get('sub'),
                "name": roblox_user.get('name'),
                "nickname": roblox_user.get('nickname'),
                "preferred_username": roblox_user.get('preferred_username'),
                "profile": roblox_user.get('profile')
            }
        }), 200

    except Exception as e:
        print(f"Roblox userinfo error: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@roblox_bp.route('/roblox/disconnect', methods=['POST'])
@login_required
@handle_db_locks(max_retries=5)
def roblox_disconnect():
    user_id = session['user_id']
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('''
                  DELETE
                  FROM oauth_connections
                  WHERE user_id = %s
                    AND provider = 'roblox'
                  ''', (user_id,))

        deleted_count = cursor.rowcount
        db.commit()

        if deleted_count > 0:
            return jsonify({"message": "Roblox account disconnected successfully"}), 200
        else:
            return jsonify({"error": "No Roblox connection found"}), 404

    except Exception as e:
        print(f"Roblox disconnect error: {e}")
        return jsonify({"error": "Failed to disconnect Roblox account"}), 500

def get_roblox_user_info(user_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('''
                  SELECT access_token, expires_at
                  FROM oauth_connections
                  WHERE user_id = %s
                    AND provider = 'roblox'
                  ''', (user_id,))

        connection = cursor.fetchone()

        if not connection:
            return None

        access_token, expires_at = connection['access_token'], connection['expires_at']
        if expires_at and expires_at < datetime.now().timestamp():
            return None

        headers = {'Authorization': f'Bearer {access_token}'}
        ROBLOX_API_URL = 'https://apis.roblox.com/oauth/v1/userinfo'
        user_response = requests.get(ROBLOX_API_URL, headers=headers)

        if user_response.status_code == 200:
            return user_response.json()
        else:
            return None

    except Exception as e:
        print(f"Error getting Roblox user info: {e}")
        return None

@roblox_bp.route('/api/internal/roblox_info', methods=['GET'])
@login_required
@handle_db_locks(max_retries=5)
def internal_roblox_info():
    user_id = session['user_id']
    roblox_info = get_roblox_user_info(user_id)

    if roblox_info:
        return jsonify({
            "success": True,
            "data": roblox_info
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": "Could not fetch Roblox user info"
        }), 400
        