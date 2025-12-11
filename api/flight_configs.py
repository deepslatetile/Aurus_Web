from flask import Blueprint, request, jsonify, session
from services.utils import login_required
from database import get_db
import json
from datetime import datetime
from services.db_utils import handle_db_locks

flight_configs_bp = Blueprint('flight_configs', __name__)

@flight_configs_bp.route('/get/flight_configs/<config_type>', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_flight_configs_by_type(config_type):
    try:
        valid_types = ['cabin_layout', 'service', 'boarding_style']
        if config_type not in valid_types:
            return jsonify({"error": "Invalid config type"}), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('''
                  SELECT id, name, type, data, description, created_at, updated_at
                  FROM flight_configs
                  WHERE type = %s
                    AND is_active = 1
                  ORDER BY name
                  ''', (config_type,))

        configs = cursor.fetchall()

        result_configs = []
        for config in configs:
            try:
                data = json.loads(config['data']) if config['data'] else {}
            except:
                data = {}

            result_configs.append({
                'id': config['id'],
                'name': config['name'],
                'type': config['type'],
                'data': data,
                'description': config['description'],
                'created_at': config['created_at'],
                'updated_at': config['updated_at']
            })

        return jsonify({
            'success': True,
            'type': config_type,
            'configs': result_configs
        }), 200

    except Exception as e:
        print(f"Error getting flight configs: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load configurations'
        }), 500

@flight_configs_bp.route('/post/flight_config', methods=['POST'])
@login_required
@handle_db_locks(max_retries=5)
def create_flight_config():
    if session.get('user_group') not in ['HQ', 'STF']:
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        required_fields = ['name', 'type', 'data']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        valid_types = ['cabin_layout', 'service', 'boarding_style']
        if data['type'] not in valid_types:
            return jsonify({"error": "Invalid config type"}), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('''
                  SELECT id
                  FROM flight_configs
                  WHERE name = %s
                    AND type = %s
                    AND is_active = 1
                  ''', (data['name'], data['type']))

        if cursor.fetchone():
            return jsonify({"error": "Config with this name and type already exists"}), 409

        timestamp = int(datetime.now().timestamp())

        cursor.execute('''
                  INSERT INTO flight_configs (name, type, data, description, created_at, updated_at)
                  VALUES (%s, %s, %s, %s, %s, %s)
                  ''', (
                      data['name'],
                      data['type'],
                      json.dumps(data['data']),
                      data.get('description', ''),
                      timestamp,
                      timestamp
                  ))

        config_id = cursor.lastrowid
        db.commit()

        return jsonify({
            "success": True,
            "message": "Config created successfully",
            "config_id": config_id
        }), 201

    except Exception as e:
        print(f"Error creating flight config: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@flight_configs_bp.route('/put/flight_config/<int:config_id>', methods=['PUT'])
@login_required
@handle_db_locks(max_retries=5)
def update_flight_config(config_id):
    if session.get('user_group') not in ['HQ', 'STF']:
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('SELECT id FROM flight_configs WHERE id = %s AND is_active = 1', (config_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Config not found"}), 404

        update_fields = []
        update_values = []
        timestamp = int(datetime.now().timestamp())

        if 'name' in data:
            cursor.execute('''
                      SELECT id
                      FROM flight_configs
                      WHERE name = %s
                        AND type = (SELECT type FROM flight_configs WHERE id = %s)
                        AND id != %s AND is_active = 1
                      ''', (data['name'], config_id, config_id))

            if cursor.fetchone():
                return jsonify({"error": "Config with this name already exists for this type"}), 409

            update_fields.append("name = %s")
            update_values.append(data['name'])

        if 'data' in data:
            update_fields.append("data = %s")
            update_values.append(json.dumps(data['data']))

        if 'description' in data:
            update_fields.append("description = %s")
            update_values.append(data['description'])

        update_fields.append("updated_at = %s")
        update_values.append(timestamp)

        if update_fields:
            update_values.append(config_id)
            update_query = f"UPDATE flight_configs SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(update_query, update_values)

        db.commit()
        return jsonify({
            "success": True,
            "message": "Config updated successfully"
        }), 200

    except Exception as e:
        print(f"Error updating flight config: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@flight_configs_bp.route('/delete/flight_config/<int:config_id>', methods=['DELETE'])
@login_required
@handle_db_locks(max_retries=5)
def delete_flight_config(config_id):
    if session.get('user_group') not in ['HQ', 'STF']:
        return jsonify({"error": "Admin access required"}), 403

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('SELECT id FROM flight_configs WHERE id = %s AND is_active = 1', (config_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Config not found"}), 404

        cursor.execute('UPDATE flight_configs SET is_active = 0 WHERE id = %s', (config_id,))
        db.commit()

        return jsonify({
            "success": True,
            "message": "Config deleted successfully"
        }), 200

    except Exception as e:
        print(f"Error deleting flight config: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@flight_configs_bp.route('/get/flight_configs', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_all_flight_configs():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('''
                  SELECT id, name, type, data, description, created_at, updated_at
                  FROM flight_configs
                  WHERE is_active = 1
                  ORDER BY type, name
                  ''')

        configs = cursor.fetchall()

        result_configs = []
        for config in configs:
            try:
                data = json.loads(config['data']) if config['data'] else {}
            except:
                data = {}

            result_configs.append({
                'id': config['id'],
                'name': config['name'],
                'type': config['type'],
                'data': data,
                'description': config['description'],
                'created_at': config['created_at'],
                'updated_at': config['updated_at']
            })

        return jsonify({
            'success': True,
            'configs': result_configs
        }), 200

    except Exception as e:
        print(f"Error getting all flight configs: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load configurations'
        }), 500

@flight_configs_bp.route('/get/boarding_styles', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_boarding_styles():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('''
                  SELECT id, name, type, data, description
                  FROM flight_configs
                  WHERE type = 'boarding_style'
                    AND is_active = 1
                  ORDER BY name
                  ''')

        db_styles = cursor.fetchall()

        styles = []

        styles.append({
            'id': 'default',
            'name': 'Default Style',
            'type': 'builtin',
            'description': 'default style',
            'draw_function': 'default'
        })

        for style in db_styles:
            try:
                data = json.loads(style['data']) if style['data'] else {}
                styles.append({
                    'id': style['id'],
                    'name': style['name'],
                    'type': 'custom',
                    'description': style['description'] or '',
                    'draw_function': data.get('draw_function', 'default'),
                    'background_image': data.get('background_image', ''),
                    'background_url': data.get('background_url', ''),
                    'config_data': data
                })
            except:
                continue

        return jsonify({
            'success': True,
            'styles': styles
        }), 200

    except Exception as e:
        print(f"Error getting boarding styles: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load boarding styles'
        }), 500
