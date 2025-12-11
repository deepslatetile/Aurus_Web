from flask import Blueprint, jsonify, request, session
from database import get_db
import time
import base64

about_us_bp = Blueprint('about_us', __name__)


@about_us_bp.route('/get/about_us', methods=['GET'])
def get_about_us():
    try:
        group_filter = request.args.get('group')
        subgroup_filter = request.args.get('subgroup')
        active_only = request.args.get('active', 'true').lower() == 'true'

        db = get_db()
        cursor = db.cursor(dictionary=True)

        query = "SELECT * FROM about_us"
        conditions = []
        params = []

        if group_filter:
            conditions.append("about_group = %s")
            params.append(group_filter)

        if subgroup_filter:
            conditions.append("subgroup = %s")
            params.append(subgroup_filter)

        if active_only:
            conditions.append("is_active = TRUE")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY display_order, name"

        cursor.execute(query, params)
        items = cursor.fetchall()

        for item in items:
            if item.get('image'):
                try:
                    if isinstance(item['image'], bytes):
                        item['image'] = base64.b64encode(item['image']).decode('utf-8')
                except:
                    item['image'] = None
            else:
                item['image'] = None

        return jsonify(items)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@about_us_bp.route('/get/about_us/<int:item_id>', methods=['GET'])
def get_about_us_item(item_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM about_us WHERE id = %s", (item_id,))
        item = cursor.fetchone()

        if not item:
            return jsonify({'error': 'Item not found'}), 404

        if item.get('image'):
            try:
                if isinstance(item['image'], bytes):
                    item['image'] = base64.b64encode(item['image']).decode('utf-8')
            except:
                item['image'] = None
        else:
            item['image'] = None

        return jsonify(item)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@about_us_bp.route('/post/about_us', methods=['POST'])
def create_about_us_item():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.json
        required_fields = ['name', 'about_group']

        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_group FROM users WHERE id = %s",
            (session['user_id'],)
        )
        user = cursor.fetchone()

        if not user or user['user_group'] not in ['HQ', 'STF']:
            return jsonify({'error': 'Insufficient permissions'}), 403

        image_data = None
        if data.get('image') and isinstance(data['image'], str) and data['image'].startswith('data:image'):
            if 'base64,' in data['image']:
                base64_str = data['image'].split('base64,')[1]
                image_data = base64.b64decode(base64_str)
        elif data.get('image') and isinstance(data['image'], str):
            image_data = data['image']

        cursor.execute('''
                       INSERT INTO about_us (name, description, image, about_group, subgroup, link,
                                             role, position, years_experience, fleet_type,
                                             registration_number, capacity, first_flight,
                                             display_order, is_active)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ''', (
                           data['name'],
                           data.get('description', ''),
                           image_data,
                           data['about_group'],
                           data.get('subgroup', ''),
                           data.get('link', ''),
                           data.get('role', ''),
                           data.get('position', ''),
                           data.get('years_experience'),
                           data.get('fleet_type', ''),
                           data.get('registration_number', ''),
                           data.get('capacity'),
                           data.get('first_flight'),
                           data.get('display_order', 0),
                           data.get('is_active', True)
                       ))

        db.commit()
        return jsonify({'message': 'Item created successfully', 'id': cursor.lastrowid}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@about_us_bp.route('/put/about_us/<int:item_id>', methods=['PUT'])
def update_about_us_item(item_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.json

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_group FROM users WHERE id = %s",
            (session['user_id'],)
        )
        user = cursor.fetchone()

        if not user or user['user_group'] not in ['HQ', 'STF']:
            return jsonify({'error': 'Insufficient permissions'}), 403

        cursor.execute("SELECT id FROM about_us WHERE id = %s", (item_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Item not found'}), 404

        image_data = None
        if 'image' in data:
            if data['image'] and isinstance(data['image'], str) and data['image'].startswith('data:image'):
                if 'base64,' in data['image']:
                    base64_str = data['image'].split('base64,')[1]
                    image_data = base64.b64decode(base64_str)
            elif data['image'] and isinstance(data['image'], str):
                image_data = data['image']

        update_fields = []
        params = []

        field_mapping = {
            'name': 'name',
            'description': 'description',
            'image': 'image',
            'about_group': 'about_group',
            'subgroup': 'subgroup',
            'link': 'link',
            'role': 'role',
            'position': 'position',
            'years_experience': 'years_experience',
            'fleet_type': 'fleet_type',
            'registration_number': 'registration_number',
            'capacity': 'capacity',
            'first_flight': 'first_flight',
            'display_order': 'display_order',
            'is_active': 'is_active'
        }

        for json_field, db_field in field_mapping.items():
            if json_field in data:
                if json_field == 'image' and image_data is not None:
                    update_fields.append(f"{db_field} = %s")
                    params.append(image_data)
                elif json_field != 'image':
                    update_fields.append(f"{db_field} = %s")
                    params.append(data[json_field])

        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400

        params.append(item_id)

        query = f"UPDATE about_us SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, params)
        db.commit()

        return jsonify({'message': 'Item updated successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@about_us_bp.route('/delete/about_us/<int:item_id>', methods=['DELETE'])
def delete_about_us_item(item_id):
    """Удалить запись"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_group FROM users WHERE id = %s",
            (session['user_id'],)
        )
        user = cursor.fetchone()

        if not user or user['user_group'] not in ['HQ', 'STF']:
            return jsonify({'error': 'Insufficient permissions'}), 403

        cursor.execute("DELETE FROM about_us WHERE id = %s", (item_id,))
        db.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Item not found'}), 404

        return jsonify({'message': 'Item deleted successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@about_us_bp.route('/get/about_us/groups', methods=['GET'])
def get_about_us_groups():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT about_group FROM about_us WHERE is_active = TRUE ORDER BY about_group")
        groups = [row['about_group'] for row in cursor.fetchall()]
        return jsonify(groups)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@about_us_bp.route('/get/about_us/types', methods=['GET'])
def get_about_us_types():
    try:
        group_filter = request.args.get('group')

        db = get_db()
        cursor = db.cursor(dictionary=True)

        query = "SELECT DISTINCT fleet_type FROM about_us WHERE fleet_type IS NOT NULL AND fleet_type != ''"

        if group_filter:
            query += " AND about_group = %s"
            cursor.execute(query, (group_filter,))
        else:
            cursor.execute(query)

        types = [row['fleet_type'] for row in cursor.fetchall()]
        return jsonify(types)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@about_us_bp.route('/get/about_us/departments', methods=['GET'])
def get_about_us_departments():
    try:
        group_filter = request.args.get('group')

        db = get_db()
        cursor = db.cursor(dictionary=True)

        query = "SELECT DISTINCT subgroup FROM about_us WHERE subgroup IS NOT NULL AND subgroup != ''"

        if group_filter:
            query += " AND about_group = %s"
            cursor.execute(query, (group_filter,))
        else:
            cursor.execute(query)

        departments = [row['subgroup'] for row in cursor.fetchall()]
        return jsonify(departments)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
        