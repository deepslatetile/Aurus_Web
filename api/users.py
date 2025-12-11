from datetime import datetime
from flask import Blueprint, request, jsonify, session
from database import get_db
from services.utils import login_required
import hashlib
from services.db_utils import handle_db_locks

users_bp = Blueprint('users', __name__)

@users_bp.route('/get/user/<int:user_id>', methods=['GET'])
@login_required
@handle_db_locks(max_retries=5)
def get_user(user_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        user_info = {
            "id": user['id'],
            "nickname": user['nickname'],
            "created_at": user['created_at'],
            "virtual_id": user['virtual_id'],
            "social_id": user['social_id'],
            "miles": user['miles'],
            "bonuses": user['bonuses'] if user['bonuses'] is not None else "",
            "user_group": user['user_group'],
            "subgroup": user['subgroup'],
            "link": user['link'] if user['link'] is not None else "",
            "pfp": user['pfp'] if user['pfp'] is not None else "",
            "metadata": user['metadata'] if user['metadata'] is not None else "",
            "pending": user['pending'] if user['pending'] is not None else "",
            "status": user['status'] if user['status'] is not None else ""
        }

        return jsonify(user_info), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@users_bp.route('/put/user/<int:user_id>', methods=['PUT'])
@login_required
@handle_db_locks(max_retries=5)
def put_user(user_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        'SELECT user_group FROM users WHERE id = %s',
        (session['user_id'],)
    )
    admin_user = cursor.fetchone()

    if not admin_user or admin_user['user_group'] not in ['HQ', 'STF']:
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        cursor.execute(
            "SELECT * FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        update_fields = []
        update_values = []

        updatable_fields = [
            'nickname', 'virtual_id', 'social_id', 'miles', 'bonuses',
            'user_group', 'subgroup', 'link', 'pfp', 'metadata', 'pending', 'status'
        ]

        for field in updatable_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                update_values.append(data[field])

        if not update_fields:
            return jsonify({"error": "No fields to update"}), 400

        update_values.append(user_id)

        update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(update_query, update_values)

        db.commit()
        return jsonify({"message": f"User {user_id} updated successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@users_bp.route('/delete/user/<int:user_id>', methods=['DELETE'])
@login_required
@handle_db_locks(max_retries=5)
def delete_user(user_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        'SELECT user_group FROM users WHERE id = %s',
        (session['user_id'],)
    )
    admin_user = cursor.fetchone()

    if not admin_user or admin_user['user_group'] not in ['HQ', 'STF']:
        return jsonify({"error": "Admin access required"}), 403

    try:
        cursor.execute(
            "SELECT * FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db.commit()

        return jsonify({"message": f"User {user_id} deleted successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@users_bp.route('/post/user', methods=['POST'])
@handle_db_locks(max_retries=5)
def post_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        required_fields = [
            'nickname',
            'password',
            'user_group',
            'subgroup'
        ]

        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        password_hash = hashlib.sha256(data['password'].encode()).hexdigest()

        miles = 0
        bonuses = ''
        link = data.get('link', '')
        pfp = data.get('pfp', '')
        metadata = ''
        pending = ''
        status = data.get('status', 'active')
        created_at = int(datetime.now().timestamp())

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE nickname = %s", (data['nickname'],))
        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({"error": "Username already exists"}), 409

        cursor.execute('''
                  INSERT INTO users (nickname, created_at, virtual_id, social_id, miles, bonuses,
                                     user_group, subgroup, link, pfp, metadata, pending, status, password_hash)
                  VALUES (%s, %s, NULL, NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                  ''', (
                      data['nickname'],
                      created_at,
                      miles,
                      bonuses,
                      data['user_group'],
                      data['subgroup'],
                      link,
                      pfp,
                      metadata,
                      pending,
                      status,
                      password_hash
                  ))

        user_id = cursor.lastrowid
        db.commit()

        return jsonify({
            "message": "User created successfully",
            "user_id": user_id
        }), 201

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@users_bp.route('/get/users/virtual/<virtual_id>', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_user_by_virtual_id(virtual_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            'SELECT id, nickname, virtual_id, user_group, miles FROM users WHERE virtual_id = %s',
            (virtual_id,)
        )
        user = cursor.fetchone()

        if user:
            return jsonify({
                'id': user['id'],
                'nickname': user['nickname'],
                'virtual_id': user['virtual_id'],
                'user_group': user['user_group'],
                'miles': user['miles']
            })
        else:
            return jsonify({'error': 'User not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
        