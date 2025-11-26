from flask import Blueprint, request, jsonify, session
from database import get_db
from services.utils import login_required, generate_booking_id
from datetime import datetime
import sqlite3


bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('/get/booking/<id>', methods=['GET'])
@login_required
def get_booking(id):
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM bookings WHERE id = ? AND user_id = ?", (id, user_id))
        booking = c.fetchone()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        booking_info = {
            "id": str(booking[0]),
            "flight_number": str(booking[1]),
            "created_at": int(booking[2]),
            "user_id": str(booking[3]),
            "seat": str(booking[4]),
            "serve_class": str(booking[5]),
            "pax_service": str(booking[6]) if booking[6] is not None else "",
            "boarding_pass": str(booking[7]),
            "note": str(booking[8]) if booking[8] is not None else "",
            "valid": int(booking[9])
        }

        conn.close()
        return jsonify(booking_info), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@bookings_bp.route('/get/bookings/<flight_number>', methods=['GET'])
def get_bookings_by_flight(flight_number):
    try:
        db = get_db()

        bookings = db.execute(
            "SELECT * FROM bookings WHERE flight_number = ? ORDER BY id",
            (flight_number,)
        ).fetchall()

        if not bookings:
            return jsonify([]), 200

        response = []
        for booking in bookings:
            response.append({
                "id": str(booking[0]),
                "flight_number": str(booking[1]),
                "created_at": int(booking[2]),
                "user_id": str(booking[3]),
                "seat": str(booking[4]),
                "serve_class": str(booking[5]),
                "pax_service": str(booking[6]) if booking[6] is not None else "",
                "boarding_pass": str(booking[7]),
                "note": str(booking[8]) if booking[8] is not None else "",
                "valid": int(booking[9])
            })

        return jsonify(response), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@bookings_bp.route('/post/booking/', methods=['POST'])
def create_booking():
    try:
        data = request.get_json()

        flight_number = data.get('flight_number')
        seat = data.get('seat')
        serve_class = data.get('serve_class')
        user_id = data.get('user_id')
        passenger_name = data.get('passenger_name')

        if not all([flight_number, seat, serve_class, passenger_name]):
            return jsonify({'error': 'Missing required fields'}), 400

        booking_id = generate_booking_id()
        created_at = int(datetime.now().timestamp())
        note = data.get('note', '')
        passenger_name = data['passenger_name']
        valid = 1
        pax_service = data.get('pax_service', '')
        boarding_pass = data.get('boarding_pass', 'default')
        social_id = data.get('social_id', '')
        virtual_id = data.get('virtual_id', '')

        db = get_db()

        existing_booking = db.execute(
            'SELECT id FROM bookings WHERE flight_number = ? AND seat = ? AND valid = 1',
            (flight_number, seat)
        ).fetchone()

        if existing_booking:
            return jsonify({'error': 'Seat already taken'}), 400

        db.execute('''
                   INSERT INTO bookings
                   (id, flight_number, created_at, user_id, seat, serve_class,
                    pax_service, boarding_pass, note, valid, passenger_name)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ''', (booking_id, flight_number, created_at, user_id, seat, serve_class,
                         pax_service, boarding_pass, note, valid, passenger_name))

        db.commit()

        return jsonify({
            'booking_id': booking_id,
            'message': 'Booking created successfully'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bookings_bp.route('/delete/booking/<booking_id>', methods=['DELETE'])
@login_required
def delete_booking(booking_id):
    try:
        user_id = session['user_id']
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM bookings WHERE id = ? AND user_id = ?", (booking_id, user_id))
        booking = c.fetchone()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        c.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        conn.commit()
        conn.close()

        return jsonify({"message": f"Booking {booking_id} deleted successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500
