from flask import Blueprint, request, jsonify, session
from database import get_db, execute_with_retry
from services.utils import login_required
from datetime import datetime
import time

transactions_bp = Blueprint('transactions', __name__)

def check_admin_permissions():
    user_id = session.get('user_id')
    if not user_id:
        return False, "Not authenticated"

    try:
        result = execute_with_retry(
            'SELECT user_group FROM users WHERE id = %s',
            (user_id,)
        )

        if not result:
            return False, "User not found"

        user_group = result.fetchone()['user_group']

        if user_group not in ['HQ', 'STF']:
            return False, f"Admin access required. Your group: {user_group}"

        return True, user_group

    except Exception as e:
        return False, f"Permission check failed: {str(e)}"

@transactions_bp.route('/post/transaction', methods=['POST'])
@login_required
def create_transaction():
    has_permission, message = check_admin_permissions()
    if not has_permission:
        return jsonify({"error": message}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    required_fields = ['user_id', 'amount', 'description', 'type']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        user_result = execute_with_retry(
            'SELECT id, nickname, miles FROM users WHERE id = %s',
            (data['user_id'],)
        )
        user = user_result.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        if data.get('booking_id'):
            booking_result = execute_with_retry(
                'SELECT id, flight_number FROM bookings WHERE id = %s',
                (data['booking_id'],)
            )
            booking = booking_result.fetchone()

            if not booking:
                return jsonify({"error": "Booking not found"}), 404

        amount = data['amount']
        if not isinstance(amount, (int, float)) or abs(amount) > 1000000:
            return jsonify({"error": "Invalid amount"}), 400

        execute_with_retry(''' \
                           INSERT INTO transactions (user_id, booking_id, amount, description, type, admin_user_id,
                                                     created_at)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)
                           ''', (
                               data['user_id'],
                               data.get('booking_id'),
                               amount,
                               data['description'],
                               data['type'],
                               session['user_id'],
                               int(datetime.now().timestamp())
                           ))

        new_balance = user['miles'] + amount
        execute_with_retry(
            'UPDATE users SET miles = %s WHERE id = %s',
            (new_balance, data['user_id'])
        )

        print(f"Transaction created: user_id={data['user_id']}, amount={amount}, new_balance={new_balance}, admin={session['user_id']}")

        return jsonify({
            "message": "Transaction created successfully",
            "transaction": {
                "user_id": data['user_id'],
                "amount": amount,
                "description": data['description'],
                "type": data['type'],
                "new_balance": new_balance
            }
        }), 201

    except Exception as e:
        print(f"Transaction creation error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@transactions_bp.route('/get/transactions/user/<int:user_id>', methods=['GET'])
@login_required
def get_user_transactions(user_id):
    try:
        current_user_id = session.get('user_id')
        current_user_group = session.get('user_group')

        if user_id != current_user_id and current_user_group not in ['HQ', 'STF']:
            return jsonify({"error": "Access denied"}), 403

        result = execute_with_retry(''' \
                                    SELECT t.*, u.nickname as admin_nickname
                                    FROM transactions t
                                             LEFT JOIN users u ON t.admin_user_id = u.id
                                    WHERE t.user_id = %s
                                    ORDER BY t.created_at DESC
                                    ''', (user_id,))

        transactions = result.fetchall()

        result_list = []
        for transaction in transactions:
            amount = float(transaction['amount'])

            result_list.append({
                'id': transaction['id'],
                'user_id': transaction['user_id'],
                'booking_id': transaction['booking_id'],
                'amount': amount,
                'description': transaction['description'],
                'type': transaction['type'],
                'admin_user_id': transaction['admin_user_id'],
                'admin_nickname': transaction['admin_nickname'],
                'created_at': transaction['created_at'],
                'created_at_formatted': datetime.fromtimestamp(transaction['created_at']).strftime('%Y-%m-%d %H:%M:%S')
            })

        return jsonify(result_list), 200

    except Exception as e:
        print(f"Get transactions error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@transactions_bp.route('/get/transactions/booking/<booking_id>', methods=['GET'])
@login_required
def get_booking_transactions(booking_id):
    try:
        has_permission, message = check_admin_permissions()
        if not has_permission:
            return jsonify({"error": message}), 403

        result = execute_with_retry(''' \
                                    SELECT t.*, u.nickname as admin_nickname
                                    FROM transactions t
                                             LEFT JOIN users u ON t.admin_user_id = u.id
                                    WHERE t.booking_id = %s
                                    ORDER BY t.created_at DESC
                                    ''', (booking_id,))

        transactions = result.fetchall()

        result_list = []
        for transaction in transactions:
            result_list.append({
                'id': transaction['id'],
                'user_id': transaction['user_id'],
                'booking_id': transaction['booking_id'],
                'amount': float(transaction['amount']),
                'description': transaction['description'],
                'type': transaction['type'],
                'admin_user_id': transaction['admin_user_id'],
                'admin_nickname': transaction['admin_nickname'],
                'created_at': transaction['created_at'],
                'created_at_formatted': datetime.fromtimestamp(transaction['created_at']).strftime('%Y-%m-%d %H:%M:%S')
            })

        return jsonify(result_list), 200

    except Exception as e:
        print(f"Get booking transactions error: {e}")
        return jsonify({"error": "Internal server error"}), 500
        