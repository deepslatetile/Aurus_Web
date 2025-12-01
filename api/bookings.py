from flask import Blueprint, request, jsonify, session
from database import get_db
from services.utils import login_required, generate_booking_id
from datetime import datetime
from services.db_utils import handle_db_locks

bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('/get/booking/<id>', methods=['GET'])
@login_required
@handle_db_locks(max_retries=5)
def get_booking(id):
    try:
        user_id = session['user_id']
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM bookings WHERE id = %s AND user_id = %s", (id, user_id))
        booking = cursor.fetchone()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        booking_info = {
            "id": str(booking['id']),
            "flight_number": str(booking['flight_number']),
            "created_at": int(booking['created_at']),
            "user_id": str(booking['user_id']),
            "seat": str(booking['seat']),
            "serve_class": str(booking['serve_class']),
            "pax_service": str(booking['pax_service']) if booking['pax_service'] is not None else "",
            "boarding_pass": str(booking['boarding_pass']),
            "note": str(booking['note']) if booking['note'] is not None else "",
            "valid": int(booking['valid'])
        }

        return jsonify(booking_info), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@bookings_bp.route('/get/bookings/<flight_number>', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_bookings_by_flight(flight_number):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM bookings WHERE flight_number = %s ORDER BY id",
            (flight_number,)
        )
        bookings = cursor.fetchall()

        if not bookings:
            return jsonify([]), 200

        response = []
        for booking in bookings:
            response.append({
                "id": str(booking['id']),
                "flight_number": str(booking['flight_number']),
                "created_at": int(booking['created_at']),
                "user_id": str(booking['user_id']),
                "seat": str(booking['seat']),
                "serve_class": str(booking['serve_class']),
                "pax_service": str(booking['pax_service']) if booking['pax_service'] is not None else "",
                "boarding_pass": str(booking['boarding_pass']),
                "note": str(booking['note']) if booking['note'] is not None else "",
                "valid": int(booking['valid'])
            })

        return jsonify(response), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@bookings_bp.route('/post/booking/', methods=['POST'])
@handle_db_locks(max_retries=5)
def create_booking():
    try:
        data = request.get_json()

        flight_number = data.get('flight_number')
        seat = data.get('seat')
        serve_class = data.get('serve_class')
        user_id = data.get('user_id', '-1')
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
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            'SELECT id FROM bookings WHERE flight_number = %s AND seat = %s AND valid = %s',
            (flight_number, seat, valid)
        )
        existing_booking = cursor.fetchone()

        if existing_booking:
            return jsonify({'error': 'Seat already taken'}), 400

        cursor.execute('''
                   INSERT INTO bookings
                   (id, flight_number, created_at, user_id, seat, serve_class,
                    pax_service, boarding_pass, note, valid, passenger_name)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
@handle_db_locks(max_retries=5)
def delete_booking(booking_id):
    try:
        user_id = session['user_id']
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM bookings WHERE id = %s AND user_id = %s", (booking_id, user_id))
        booking = cursor.fetchone()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        cursor.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
        db.commit()

        return jsonify({"message": f"Booking {booking_id} deleted successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500
