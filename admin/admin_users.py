from flask import Blueprint, request, jsonify, session
from database import get_db
from services.utils import login_required

admin_users_bp = Blueprint('admin_users', __name__)


@admin_users_bp.route('/users', methods=['GET'])
@login_required
def get_all_users():
    """Get all users with pagination and filtering"""
    db = get_db()

    # Check admin permissions
    admin_user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not admin_user or admin_user['user_group'] not in ['HQ', 'STF']:
        return jsonify({"error": "Admin access required"}), 403

    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    group_filter = request.args.get('group', '')
    status_filter = request.args.get('status', '')

    # Build query
    query = '''
            SELECT id, \
                   nickname, \
                   created_at, \
                   virtual_id, \
                   social_id, \
                   miles,
                   user_group, \
                   subgroup, \
                   status, \
                   pending
            FROM users
            WHERE 1 = 1 \
            '''
    params = []

    if search:
        query += ' AND (nickname LIKE ? OR virtual_id LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])

    if group_filter:
        query += ' AND user_group = ?'
        params.append(group_filter)

    if status_filter:
        query += ' AND status = ?'
        params.append(status_filter)

    # Count total
    count_query = f'SELECT COUNT(*) as total FROM ({query})'
    total = db.execute(count_query, params).fetchone()['total']

    # Add pagination
    query += ' ORDER BY id DESC LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])

    # Execute query
    users = db.execute(query, params).fetchall()

    return jsonify({
        'users': [dict(user) for user in users],
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })


@admin_users_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user_details(user_id):
    """Get detailed user information"""
    db = get_db()

    # Check admin permissions
    admin_user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not admin_user or admin_user['user_group'] not in ['HQ', 'STF']:
        return jsonify({"error": "Admin access required"}), 403

    user = db.execute(
        'SELECT * FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(dict(user))


@admin_users_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """Update user information"""
    db = get_db()

    # Check admin permissions
    admin_user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not admin_user or admin_user['user_group'] not in ['HQ', 'STF']:
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Get current user data
    current_user = db.execute(
        'SELECT * FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()

    if not current_user:
        return jsonify({"error": "User not found"}), 404

    # Prepare update fields
    update_fields = []
    update_values = []

    # Define allowed fields to update
    allowed_fields = [
        'nickname', 'virtual_id', 'social_id', 'miles', 'bonuses',
        'user_group', 'subgroup', 'link', 'metadata', 'pending', 'status'
    ]

    for field in allowed_fields:
        if field in data:
            update_fields.append(f"{field} = ?")
            update_values.append(data[field])

    if not update_fields:
        return jsonify({"error": "No valid fields to update"}), 400

    update_values.append(user_id)

    # Execute update
    try:
        db.execute(
            f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?",
            update_values
        )
        db.commit()

        return jsonify({"message": "User updated successfully"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500


@admin_users_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """Delete a user"""
    db = get_db()

    # Check admin permissions
    admin_user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not admin_user or admin_user['user_group'] not in ['HQ', 'STF']:
        return jsonify({"error": "Admin access required"}), 403

    # Prevent self-deletion
    if user_id == session['user_id']:
        return jsonify({"error": "Cannot delete your own account"}), 400

    user = db.execute(
        'SELECT * FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()

    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        # Delete user's bookings first (if needed)
        db.execute('DELETE FROM bookings WHERE user_id = ?', (user_id,))
        # Delete user's transactions
        db.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
        # Delete user
        db.execute('DELETE FROM users WHERE id = ?', (user_id,))

        db.commit()
        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500


@admin_users_bp.route('/users/stats', methods=['GET'])
@login_required
def get_user_stats():
    """Get user statistics for admin dashboard"""
    db = get_db()

    # Check admin permissions
    admin_user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not admin_user or admin_user['user_group'] not in ['HQ', 'STF']:
        return jsonify({"error": "Admin access required"}), 403

    stats = db.execute('''
                       SELECT COUNT(*)                                        as total_users,
                              COUNT(CASE WHEN status = 'active' THEN 1 END)   as active_users,
                              COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_users,
                              COUNT(CASE WHEN user_group = 'HQ' THEN 1 END)   as hq_users,
                              COUNT(CASE WHEN user_group = 'STF' THEN 1 END)  as staff_users,
                              COUNT(CASE WHEN user_group = 'PAX' THEN 1 END)  as passenger_users,
                              SUM(miles)                                      as total_miles
                       FROM users
                       ''').fetchone()

    return jsonify(dict(stats))
