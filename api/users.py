from datetime import datetime
from flask import Blueprint, request, jsonify, session
from database import get_db
from services.utils import login_required
import sqlite3
import hashlib

users_bp = Blueprint('users', __name__)


@users_bp.route('/get/user/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()

        conn.close()

        if not user:
            return jsonify({"error": "User not found"}), 404

        user_info = {
            "id": user[0],
            "nickname": user[1],
            "created_at": user[2],
            "virtual_id": user[3],
            "social_id": user[4],
            "miles": user[5],
            "bonuses": user[6] if user[6] is not None else "",
            "user_group": user[7],
            "subgroup": user[8],
            "link": user[9] if user[9] is not None else "",
            "pfp": user[10] if user[10] is not None else "",
            "metadata": user[11] if user[11] is not None else "",
            "pending": user[12] if user[12] is not None else "",
            "status": user[13] if user[13] is not None else ""
        }

        return jsonify(user_info), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@users_bp.route('/put/user/<int:user_id>', methods=['PUT'])
@login_required
def put_user(user_id):
    db = get_db()
    admin_user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not admin_user or admin_user['user_group'] not in ['HQ', 'STF']:
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        user = db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

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
                update_fields.append(f"{field} = ?")
                update_values.append(data[field])

        if not update_fields:
            return jsonify({"error": "No fields to update"}), 400

        update_values.append(user_id)

        update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        db.execute(update_query, update_values)

        if 'miles' in data and data['miles'] != user['miles']:
            amount_change = data['miles'] - user['miles']
            transaction_type = 'payment' if amount_change > 0 else 'refund'

            db.execute('''
                       INSERT INTO transactions (user_id, amount, description, type, admin_user_id, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ''', (
                           user_id,
                           amount_change,
                           data.get('transaction_description', 'Manual adjustment'),
                           transaction_type,
                           session['user_id'],
                           int(datetime.now().timestamp())
                       ))

        db.commit()
        return jsonify({"message": f"User {user_id} updated successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@users_bp.route('/delete/user/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    db = get_db()
    admin_user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not admin_user or admin_user['user_group'] not in ['HQ', 'STF']:
        return jsonify({"error": "Admin access required"}), 403

    try:
        user = db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()

        return jsonify({"message": f"User {user_id} deleted successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@users_bp.route('/post/user', methods=['POST'])
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

        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE nickname = ?", (data['nickname'],))
        existing_user = c.fetchone()

        if existing_user:
            return jsonify({"error": "Username already exists"}), 409

        c.execute('''
                  INSERT INTO users (nickname, created_at, virtual_id, social_id, miles, bonuses,
                                     user_group, subgroup, link, pfp, metadata, pending, status, password_hash)
                  VALUES (?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

        user_id = c.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            "message": "User created successfully",
            "user_id": user_id
        }), 201

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@users_bp.route('/get/users/virtual/<virtual_id>', methods=['GET'])
def get_user_by_virtual_id(virtual_id):
    try:
        db = get_db()

        user = db.execute(
            'SELECT id, nickname, virtual_id, user_group FROM users WHERE virtual_id = ?',
            (virtual_id,)
        ).fetchone()

        if user:
            return jsonify({
                'id': user['id'],
                'nickname': user['nickname'],
                'virtual_id': user['virtual_id'],
                'user_group': user['user_group']
            })
        else:
            return jsonify({'error': 'User not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500