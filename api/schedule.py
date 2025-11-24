from flask import Blueprint, request, jsonify, session
from database import get_db
from datetime import datetime
import json
import sqlite3
from services.utils import login_required

schedule_bp = Blueprint('schedule', __name__)


@schedule_bp.route('/get/schedule', methods=['GET'])
def get_schedule():
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute('''
            SELECT 
                s.*,
                COUNT(b.id) as flying_count
            FROM schedule s
            LEFT JOIN bookings b ON s.flight_number = b.flight_number
            GROUP BY s.id
            ORDER BY s.datetime ASC
        ''')
        schedule = c.fetchall()

        conn.close()

        schedule_list = []
        for flight in schedule:
            flight_info = {
                "id": flight[0],
                "flight_number": flight[1],
                "created_at": flight[2],
                "departure": flight[3],
                "arrival": flight[4],
                "datetime": flight[5],
                "enroute": flight[6],
                "status": flight[7],
                "seatmap": flight[8],
                "aircraft": flight[9],
                "meal": flight[10],
                "pax_service": flight[11],
                "boarding_pass_default": flight[12],
                "flying_count": flight[13]
            }
            schedule_list.append(flight_info)

        return jsonify(schedule_list), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@schedule_bp.route('/get/schedule/<flight_number>', methods=['GET'])
def get_flight(flight_number):
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute('''
            SELECT 
                s.*,
                COUNT(b.id) as flying_count
            FROM schedule s
            LEFT JOIN bookings b ON s.flight_number = b.flight_number
            WHERE s.flight_number = ?
            GROUP BY s.id
        ''', (flight_number,))
        flight = c.fetchone()

        conn.close()

        if not flight:
            return jsonify({"error": "Flight not found"}), 404

        flight_info = {
            "id": flight[0],
            "flight_number": flight[1],
            "created_at": flight[2],
            "departure": flight[3],
            "arrival": flight[4],
            "datetime": flight[5],
            "enroute": flight[6],
            "status": flight[7],
            "seatmap": flight[8],
            "aircraft": flight[9],
            "meal": flight[10],
            "pax_service": flight[11],
            "boarding_pass_default": flight[12],
            "flying_count": flight[13]
        }

        return jsonify(flight_info), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@schedule_bp.route('/post/schedule', methods=['POST'])
@login_required
def post_schedule():
    # Проверка прав доступа
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

        # Проверяем существование рейса
        existing_flight = db.execute(
            'SELECT id FROM schedule WHERE flight_number = ?',
            (data['flight_number'],)
        ).fetchone()

        if existing_flight:
            return jsonify({"error": "Flight with this number already exists"}), 409

        # Создаем рейс
        db.execute('''
                   INSERT INTO schedule (flight_number, created_at, departure, arrival, datetime,
                                         enroute, status, seatmap, aircraft, meal, pax_service, boarding_pass_default)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
def put_schedule(flight_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM schedule WHERE id = ?", (flight_id,))
        flight = c.fetchone()

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
                update_fields.append(f"{field} = ?")
                update_values.append(data[field])

        if not update_fields:
            return jsonify({"error": "No fields to update"}), 400

        if 'flight_number' in data:
            c.execute("SELECT * FROM schedule WHERE flight_number = ? AND id != ?", (data['flight_number'], flight_id))
            existing_flight = c.fetchone()
            if existing_flight:
                return jsonify({"error": "Flight with this number already exists"}), 409

        update_values.append(flight_id)

        update_query = f"UPDATE schedule SET {', '.join(update_fields)} WHERE id = ?"
        c.execute(update_query, update_values)

        conn.commit()
        conn.close()

        return jsonify({"message": f"Flight {flight_id} updated successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@schedule_bp.route('/delete/schedule/<int:flight_id>', methods=['DELETE'])
@login_required
def delete_schedule(flight_id):
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM schedule WHERE id = ?", (flight_id,))
        flight = c.fetchone()

        if not flight:
            return jsonify({"error": "Flight not found"}), 404

        c.execute("DELETE FROM schedule WHERE id = ?", (flight_id,))
        conn.commit()
        conn.close()

        return jsonify({"message": f"Flight {flight_id} deleted successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500