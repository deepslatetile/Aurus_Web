from flask import Blueprint, request, jsonify, session
from database import get_db
import json

admin_bookings_bp = Blueprint('admin_bookings', __name__)


def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        db = get_db()
        user = db.execute(
            'SELECT user_group FROM users WHERE id = ?',
            (session['user_id'],)
        ).fetchone()

        if not user or user['user_group'] not in ['HQ', 'STF']:
            return jsonify({'error': 'Forbidden'}), 403

        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


@admin_bookings_bp.route('/bookings', methods=['GET'])
@admin_required
def get_all_bookings():
    db = get_db()

    flight_filter = request.args.get('flight_number', '')

    query = '''
            SELECT b.*, u.nickname, u.virtual_id, s.flight_number as flight_number_full
            FROM bookings b
                     LEFT JOIN users u ON b.user_id = u.id
                     LEFT JOIN schedule s ON b.flight_number = s.flight_number
            WHERE 1 = 1 \
            '''
    params = []

    if flight_filter:
        query += ' AND b.flight_number LIKE ?'
        params.append(f'%{flight_filter}%')

    query += ' ORDER BY b.created_at DESC'

    bookings = db.execute(query, params).fetchall()

    result = []
    for booking in bookings:
        result.append({
            'id': booking['id'],
            'flight_number': booking['flight_number'],
            'created_at': booking['created_at'],
            'user_nickname': booking['nickname'],
            'user_virtual_id': booking['virtual_id'],
            'seat': booking['seat'],
            'serve_class': booking['serve_class'],
            'passenger_name': booking['passenger_name'],
            'valid': bool(booking['valid']),
            'note': booking['note']
        })

    return jsonify(result)


@admin_bookings_bp.route('/bookings/<booking_id>', methods=['GET'])
@admin_required
def get_booking_detail(booking_id):
    db = get_db()

    booking = db.execute('''
                         SELECT b.*,
                                u.nickname,
                                u.virtual_id,
                                u.user_group,
                                s.departure,
                                s.arrival,
                                s.datetime as flight_datetime
                         FROM bookings b
                                  LEFT JOIN users u ON b.user_id = u.id
                                  LEFT JOIN schedule s ON b.flight_number = s.flight_number
                         WHERE b.id = ?
                         ''', (booking_id,)).fetchone()

    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    pax_services = []
    pax_service_data = booking['pax_service']

    if pax_service_data:
        try:
            if isinstance(pax_service_data, str) and ',' in pax_service_data:
                service_names = [name.strip() for name in pax_service_data.split(',')]

                for service_name in service_names:
                    if service_name:
                        pax_info = db.execute(
                            'SELECT name, price FROM pax_service WHERE name = ?',
                            (service_name,)
                        ).fetchone()

                        if pax_info:
                            pax_services.append({
                                'name': pax_info['name'],
                                'price': pax_info['price']
                            })
                        else:
                            pax_services.append({
                                'name': service_name,
                                'price': 0
                            })

            elif isinstance(pax_service_data, str) and pax_service_data.strip():
                service_name = pax_service_data.strip()
                pax_info = db.execute(
                    'SELECT name, price FROM pax_service WHERE name = ?',
                    (service_name,)
                ).fetchone()

                if pax_info:
                    pax_services.append({
                        'name': pax_info['name'],
                        'price': pax_info['price']
                    })
                else:
                    pax_services.append({
                        'name': service_name,
                        'price': 0
                    })

        except Exception as e:
            print(f"Error parsing pax_service: {e}")
            pax_services = []

    return jsonify({
        'id': booking['id'],
        'flight_number': booking['flight_number'],
        'created_at': booking['created_at'],
        'user_id': booking['user_id'],
        'user_nickname': booking['nickname'],
        'user_virtual_id': booking['virtual_id'],
        'user_group': booking['user_group'],
        'seat': booking['seat'],
        'serve_class': booking['serve_class'],
        'pax_services': pax_services,
        'boarding_pass': booking['boarding_pass'],
        'note': booking['note'],
        'valid': bool(booking['valid']),
        'passenger_name': booking['passenger_name'],
        'departure': booking['departure'],
        'arrival': booking['arrival'],
        'flight_datetime': booking['flight_datetime']
    })


@admin_bookings_bp.route('/bookings/<booking_id>', methods=['PUT'])
@admin_required
def update_booking(booking_id):
    db = get_db()
    data = request.get_json()

    booking = db.execute(
        'SELECT id FROM bookings WHERE id = ?',
        (booking_id,)
    ).fetchone()

    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    update_fields = []
    params = []

    allowed_fields = ['seat', 'serve_class', 'note', 'passenger_name', 'valid']

    for field in allowed_fields:
        if field in data:
            update_fields.append(f'{field} = ?')
            params.append(data[field])

    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400

    params.append(booking_id)

    query = f'UPDATE bookings SET {", ".join(update_fields)} WHERE id = ?'

    try:
        db.execute(query, params)
        db.commit()
        return jsonify({'message': 'Booking updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        