from flask import Blueprint, request, jsonify, session
from database import get_db
from datetime import datetime
from services.utils import login_required
from services.db_utils import handle_db_locks

schedule_bp = Blueprint('schedule', __name__)


@schedule_bp.route('/get/schedule', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_schedule():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('''
                       SELECT s.*,
                              COUNT(b.id) as flying_count
                       FROM schedule s
                                LEFT JOIN bookings b ON s.flight_number = b.flight_number
                       GROUP BY s.id
                       ORDER BY s.datetime ASC
                       ''')
        schedule = cursor.fetchall()

        schedule_list = []
        for flight in schedule:
            flight_info = {
                "id": flight['id'],
                "flight_number": flight['flight_number'],
                "created_at": flight['created_at'],
                "departure": flight['departure'],
                "arrival": flight['arrival'],
                "datetime": flight['datetime'],
                "enroute": flight['enroute'],
                "status": flight['status'],
                "seatmap": flight['seatmap'],
                "aircraft": flight['aircraft'],
                "meal": flight['meal'],
                "pax_service": flight['pax_service'],
                "boarding_pass_default": flight['boarding_pass_default'],
                "flying_count": flight['flying_count']
            }
            schedule_list.append(flight_info)

        return jsonify(schedule_list), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@schedule_bp.route('/get/schedule/<flight_number>', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_flight(flight_number):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('''
                       SELECT s.*,
                              COUNT(b.id) as flying_count
                       FROM schedule s
                                LEFT JOIN bookings b ON s.flight_number = b.flight_number
                       WHERE s.flight_number = %s
                       GROUP BY s.id
                       ''', (flight_number,))
        flight = cursor.fetchone()

        if not flight:
            return jsonify({"error": "Flight not found"}), 404

        flight_info = {
            "id": flight['id'],
            "flight_number": flight['flight_number'],
            "created_at": flight['created_at'],
            "departure": flight['departure'],
            "arrival": flight['arrival'],
            "datetime": flight['datetime'],
            "enroute": flight['enroute'],
            "status": flight['status'],
            "seatmap": flight['seatmap'],
            "aircraft": flight['aircraft'],
            "meal": flight['meal'],
            "pax_service": flight['pax_service'],
            "boarding_pass_default": flight['boarding_pass_default'],
            "flying_count": flight['flying_count']
        }

        return jsonify(flight_info), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@schedule_bp.route('/post/schedule', methods=['POST'])
@login_required
@handle_db_locks(max_retries=5)
def post_schedule():
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
        required_fields = [
            'flight_number',
            'departure',
            'arrival',
            'datetime',
            'enroute',
            'seatmap',
            'aircraft'
        ]

        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        cursor.execute(
            'SELECT id FROM schedule WHERE flight_number = %s',
            (data['flight_number'],)
        )
        existing_flight = cursor.fetchone()

        if existing_flight:
            return jsonify({"error": "Flight with this number already exists"}), 409

        cursor.execute('''
                       INSERT INTO schedule (flight_number, created_at, departure, arrival, datetime,
                                             enroute, status, seatmap, aircraft, meal, pax_service,
                                             boarding_pass_default)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ''', (
                           data['flight_number'],
                           int(datetime.now().timestamp()),
                           data['departure'],
                           data['arrival'],
                           data['datetime'],
                           data['enroute'],
                           data.get('status', 'Scheduled'),
                           data['seatmap'],
                           data['aircraft'],
                           data.get('meal', 'Standard Meal Service'),
                           data.get('pax_service', '[]'),
                           data.get('boarding_pass_default', 'default')
                       ))

        db.commit()

        return jsonify({
            "message": "Flight created successfully",
            "flight_number": data['flight_number']
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@schedule_bp.route('/put/schedule/<int:flight_id>', methods=['PUT'])
@login_required
@handle_db_locks(max_retries=5)
def put_schedule(flight_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM schedule WHERE id = %s", (flight_id,))
        flight = cursor.fetchone()

        if not flight:
            return jsonify({"error": "Flight not found"}), 404

        update_fields = []
        update_values = []

        updatable_fields = [
            'flight_number', 'departure', 'arrival', 'datetime', 'enroute',
            'status', 'seatmap', 'aircraft', 'meal', 'pax_service', 'boarding_pass_default'
        ]

        for field in updatable_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                update_values.append(data[field])

        if not update_fields:
            return jsonify({"error": "No fields to update"}), 400

        if 'flight_number' in data:
            cursor.execute("SELECT * FROM schedule WHERE flight_number = %s AND id != %s",
                           (data['flight_number'], flight_id))
            existing_flight = cursor.fetchone()
            if existing_flight:
                return jsonify({"error": "Flight with this number already exists"}), 409

        update_values.append(flight_id)

        update_query = f"UPDATE schedule SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(update_query, update_values)

        db.commit()
        return jsonify({"message": f"Flight {flight_id} updated successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@schedule_bp.route('/delete/schedule/<int:flight_id>', methods=['DELETE'])
@login_required
@handle_db_locks(max_retries=5)
def delete_schedule(flight_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM schedule WHERE id = %s", (flight_id,))
        flight = cursor.fetchone()

        if not flight:
            return jsonify({"error": "Flight not found"}), 404

        cursor.execute("DELETE FROM schedule WHERE id = %s", (flight_id,))
        db.commit()

        return jsonify({"message": f"Flight {flight_id} deleted successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500
        