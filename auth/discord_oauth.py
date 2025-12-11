from flask import Blueprint, redirect, request, session, jsonify
import requests
from database import get_db
import secrets
from datetime import datetime
from urllib.parse import urlencode
from services.utils import login_required
from services.db_utils import handle_db_locks

discord_bp = Blueprint('discord', __name__)

@discord_bp.route('/discord')
@handle_db_locks(max_retries=5)
def auth_discord():
    from app import app
    if not app.config['DISCORD_CLIENT_ID'] or not app.config['DISCORD_CLIENT_SECRET']:
        return jsonify({"error": "Discord OAuth is not configured"}), 500

    params = {
        'client_id': app.config['DISCORD_CLIENT_ID'],
        'redirect_uri': app.config['DISCORD_REDIRECT_URI'],
        'response_type': 'code',
        'scope': 'identify guilds',
        'state': secrets.token_urlsafe(16)
    }

    auth_url = f"{app.config['DISCORD_AUTH_URL']}?{urlencode(params)}"
    return redirect(auth_url)

@discord_bp.route('/discord/callback')
@handle_db_locks(max_retries=5)
def auth_discord_callback():
    from app import app
    if not app.config['DISCORD_CLIENT_ID'] or not app.config['DISCORD_CLIENT_SECRET']:
        return redirect('/profile?error=discord_not_configured')

    try:
        code = request.args.get('code')
        if not code:
            return redirect('/profile?error=discord_no_code')

        if 'user_id' not in session:
            return redirect('/login?redirect=/auth/discord')

        user_id = session['user_id']

        token_data = {
            'client_id': app.config['DISCORD_CLIENT_ID'],
            'client_secret': app.config['DISCORD_CLIENT_SECRET'],
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': app.config['DISCORD_REDIRECT_URI']
        }

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        DISCORD_TOKEN_URL = 'https://discord.com/api/oauth2/token'
        token_response = requests.post(DISCORD_TOKEN_URL, data=token_data, headers=headers)
        token_response.raise_for_status()
        token_json = token_response.json()

        access_token = token_json['access_token']
        refresh_token = token_json.get('refresh_token')
        expires_in = token_json.get('expires_in', 24 * 60 * 60)

        user_headers = {'Authorization': f'Bearer {access_token}'}
        DISCORD_API_URL = 'https://discord.com/api/v10'
        user_response = requests.get(f'{DISCORD_API_URL}/users/@me', headers=user_headers)
        user_response.raise_for_status()
        discord_user = user_response.json()

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('''
                  SELECT user_id
                  FROM oauth_connections
                  WHERE provider = %s
                    AND provider_user_id = %s
                    AND user_id != %s
                  ''', ('discord', discord_user['id'], user_id))

        existing_connection = cursor.fetchone()
        if existing_connection:
            return redirect('/profile?error=discord_already_linked')

        cursor.execute('''
                  SELECT id
                  FROM oauth_connections
                  WHERE user_id = %s
                    AND provider = 'discord'
                  ''', (user_id,))

        current_connection = cursor.fetchone()

        if current_connection:
            cursor.execute('''
                      UPDATE oauth_connections
                      SET access_token  = %s,
                          refresh_token = %s,
                          expires_at    = %s
                      WHERE user_id = %s
                        AND provider = 'discord'
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
                          'discord',
                          discord_user['id'],
                          access_token,
                          refresh_token,
                          int(datetime.now().timestamp()) + expires_in,
                          int(datetime.now().timestamp())
                      ))

        cursor.execute('''
                  UPDATE users
                  SET social_id = %s
                  WHERE id = %s
                  ''', (discord_user['id'], user_id))

        db.commit()
        return redirect('/profile?success=discord_linked')

    except requests.RequestException as e:
        print(f"Discord OAuth error: {e}")
        return redirect('/profile?error=discord_auth_failed')
    except Exception as e:
        print(f"Unexpected error: {e}")
        return redirect('/profile?error=discord_unexpected_error')

@discord_bp.route('/discord/connection', methods=['GET', 'DELETE'])
@login_required
@handle_db_locks(max_retries=5)
def discord_connection():
    user_id = session['user_id']
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        if request.method == 'GET':
            cursor.execute('''
                      SELECT provider_user_id, created_at, expires_at
                      FROM oauth_connections
                      WHERE user_id = %s
                        AND provider = 'discord'
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
                        AND provider = 'discord'
                      ''', (user_id,))

            cursor.execute('''
                      UPDATE users 
                      SET social_id = NULL 
                      WHERE id = %s
                      ''', (user_id,))

            deleted_count = cursor.rowcount
            db.commit()

            if deleted_count > 0:
                return jsonify({"message": "Discord connection removed successfully"}), 200
            else:
                return jsonify({"error": "No Discord connection found"}), 404

    except Exception as e:
        print(f"Discord connection error: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@discord_bp.route('/discord/userinfo', methods=['GET'])
@login_required
@handle_db_locks(max_retries=5)
def discord_userinfo():
    user_id = session['user_id']
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('''
                  SELECT access_token, expires_at
                  FROM oauth_connections
                  WHERE user_id = %s
                    AND provider = 'discord'
                  ''', (user_id,))

        connection = cursor.fetchone()
        if not connection:
            return jsonify({"error": "Discord account not connected"}), 404

        access_token, expires_at = connection['access_token'], connection['expires_at']
        if expires_at and expires_at < datetime.now().timestamp():
            return jsonify({"error": "Discord token expired, please reconnect"}), 401

        headers = {'Authorization': f'Bearer {access_token}'}
        DISCORD_API_URL = 'https://discord.com/api/v10'
        user_response = requests.get(f'{DISCORD_API_URL}/users/@me', headers=headers)

        if user_response.status_code != 200:
            return jsonify({"error": "Failed to fetch Discord user info"}), 500

        discord_user = user_response.json()

        return jsonify({
            "discord_user": {
                "id": discord_user.get('id'),
                "username": discord_user.get('username'),
                "avatar": discord_user.get('avatar'),
                "global_name": discord_user.get('global_name')
            }
        }), 200

    except Exception as e:
        print(f"Discord userinfo error: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@discord_bp.route('/discord/disconnect', methods=['POST'])
@login_required
@handle_db_locks(max_retries=5)
def discord_disconnect():
    user_id = session['user_id']
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('''
                  DELETE
                  FROM oauth_connections
                  WHERE user_id = %s
                    AND provider = 'discord'
                  ''', (user_id,))

        cursor.execute('''
                  UPDATE users 
                  SET social_id = 0 
                  WHERE id = %s
                  ''', (user_id,))

        deleted_count = cursor.rowcount
        db.commit()

        if deleted_count > 0:
            return jsonify({"message": "Discord account disconnected successfully"}), 200
        else:
            return jsonify({"error": "No Discord connection found"}), 404

    except Exception as e:
        print(f"Discord disconnect error: {e}")
        return jsonify({"error": "Failed to disconnect Discord account"}), 500

def get_discord_user_roles(user_id, guild_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('''
                  SELECT access_token, expires_at
                  FROM oauth_connections
                  WHERE user_id = %s
                    AND provider = 'discord'
                  ''', (user_id,))

        connection = cursor.fetchone()

        if not connection:
            print(f"No Discord connection found for user {user_id}")
            return None

        access_token, expires_at = connection['access_token'], connection['expires_at']
        if expires_at and expires_at < datetime.now().timestamp():
            print(f"Discord token expired for user {user_id}")
            return None

        headers = {'Authorization': f'Bearer {access_token}'}
        DISCORD_API_URL = 'https://discord.com/api/v10'

        member_response = requests.get(
            f'{DISCORD_API_URL}/users/@me/guilds/{guild_id}/member',
            headers=headers
        )

        if member_response.status_code == 200:
            member_data = member_response.json()
            user_role_ids = member_data.get('roles', [])

            guild_roles_response = requests.get(
                f'{DISCORD_API_URL}/guilds/{guild_id}/roles',
                headers=headers
            )

            if guild_roles_response.status_code == 200:
                all_roles = guild_roles_response.json()
                user_roles = []
                for role_id in user_role_ids:
                    role_detail = next((role for role in all_roles if role['id'] == role_id), None)
                    if role_detail:
                        user_roles.append({
                            'id': role_detail['id'],
                            'name': role_detail['name'],
                            'color': role_detail.get('color', 0),
                            'position': role_detail.get('position', 0),
                            'permissions': role_detail.get('permissions', '0')
                        })

                user_roles.sort(key=lambda x: x['position'], reverse=True)

                result = {
                    'guild_id': guild_id,
                    'user_id': user_id,
                    'roles': user_roles,
                    'highest_role': user_roles[0] if user_roles else None,
                    'role_ids': user_role_ids
                }

                return result
            else:
                print(f"Failed to fetch guild roles: {guild_roles_response.status_code}")
                return None
        else:
            print(f"User {user_id} not in guild {guild_id} or no access")
            return None

    except Exception as e:
        print(f"Error getting Discord roles: {e}")
        return None

@discord_bp.route('/api/internal/discord_roles/<guild_id>', methods=['GET'])
@login_required
@handle_db_locks(max_retries=5)
def internal_discord_roles(guild_id):
    user_id = session['user_id']
    roles_data = get_discord_user_roles(user_id, guild_id)

    if roles_data:
        return jsonify({
            "success": True,
            "data": roles_data
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": "Could not fetch Discord roles"
        }), 400
        