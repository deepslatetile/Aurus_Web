from flask import Blueprint, request, jsonify, session
from services.utils import login_required
from database import get_db
import sqlite3
import json
from services.db_utils import handle_db_locks

configs_bp = Blueprint('configs', __name__)


@configs_bp.route('/get/config/<int:config_id>', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_config(config_id):
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM configs WHERE id = ?", (config_id,))
        config = c.fetchone()

        conn.close()

        if not config:
            return jsonify({"error": "Config not found"}), 404

        config_info = {
            "id": config[0],
            "name": config[1],
            "description": config[2] if config[2] is not None else "",
            "image": config[3] if config[3] is not None else ""
        }

        return jsonify(config_info), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@configs_bp.route('/get/config/name/<config_name>', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_config_by_name(config_name):
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM configs WHERE name = ?", (config_name,))
        config = c.fetchone()

        conn.close()

        if not config:
            return jsonify({"error": "Config not found"}), 404

        config_info = {
            "id": config[0],
            "name": config[1],
            "description": config[2] if config[2] is not None else "",
            "image": config[3] if config[3] is not None else ""
        }

        return jsonify(config_info), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@configs_bp.route('/post/config', methods=['POST'])
@login_required
@handle_db_locks(max_retries=5)
def post_config():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        required_fields = ['name', 'description']

        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        image = data.get('image', None)

        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM configs WHERE name = ?", (data['name'],))
        existing_config = c.fetchone()

        if existing_config:
            return jsonify({"error": "Config with this name already exists"}), 409

        c.execute('''
                  INSERT INTO configs (name, description, image)
                  VALUES (?, ?, ?)
                  ''', (
                      data['name'],
                      data['description'],
                      image
                  ))

        config_id = c.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            "message": "Config created successfully",
            "config_id": config_id
        }), 201

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@configs_bp.route('/put/config/<int:config_id>', methods=['PUT'])
@login_required
@handle_db_locks(max_retries=5)
def put_config(config_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM configs WHERE id = ?", (config_id,))
        config = c.fetchone()

        if not config:
            return jsonify({"error": "Config not found"}), 404

        update_fields = []
        update_values = []

        updatable_fields = ['name', 'description', 'image']

        for field in updatable_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                update_values.append(data[field])

        if not update_fields:
            return jsonify({"error": "No fields to update"}), 400

        if 'name' in data:
            c.execute("SELECT * FROM configs WHERE name = ? AND id != ?", (data['name'], config_id))
            existing_config = c.fetchone()
            if existing_config:
                return jsonify({"error": "Config with this name already exists"}), 409

        update_values.append(config_id)

        update_query = f"UPDATE configs SET {', '.join(update_fields)} WHERE id = ?"
        c.execute(update_query, update_values)

        conn.commit()
        conn.close()

        return jsonify({"message": f"Config {config_id} updated successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@configs_bp.route('/delete/config/<int:config_id>', methods=['DELETE'])
@login_required
@handle_db_locks(max_retries=5)
def delete_config(config_id):
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM configs WHERE id = ?", (config_id,))
        config = c.fetchone()

        if not config:
            return jsonify({"error": "Config not found"}), 404

        c.execute("DELETE FROM configs WHERE id = ?", (config_id,))
        conn.commit()
        conn.close()

        return jsonify({"message": f"Config {config_id} deleted successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@configs_bp.route('/get/configs/seatmaps', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_seatmap_configs():
    try:
        db = get_db()

        configs = db.execute(
            'SELECT name, description, image FROM configs WHERE name LIKE ?',
            ('%seatmap%',)
        ).fetchall()

        result = []
        for config in configs:
            try:
                config_data = json.loads(config['image']) if config['image'] else {}
            except:
                config_data = {}

            result.append({
                'name': config['name'],
                'description': config['description'],
                'config': config_data
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@configs_bp.route('/get/pax_services', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_pax_services():
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute('''
                  SELECT name, description, price
                  FROM pax_service
                  WHERE price > 0
                  UNION
                  SELECT name, description, data ->>'$.price' as price
                  FROM flight_configs
                  WHERE type = 'service' AND is_active = 1 AND json_extract(data, '$.price') > 0
                  ORDER BY name
                  ''')

        services = c.fetchall()
        conn.close()

        result = []
        for service in services:
            result.append({
                'name': service[0],
                'description': service[1],
                'price': float(service[2]) if service[2] else 0.0
            })

        return jsonify(result), 200

    except Exception as e:
        print(f"Error getting PAX services: {e}")
        return jsonify({"error": str(e)}), 500


@configs_bp.route('/post/pax_service', methods=['POST'])
@login_required
@handle_db_locks(max_retries=5)
def create_pax_service():
    db = get_db()
    admin_user = db.execute(
        'SELECT user_group FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not admin_user or admin_user['user_group'] not in ['HQ', 'STF']:
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    required_fields = ['name', 'price']

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        db.execute('''
                   INSERT INTO pax_service (name, description, groupname, subgroupname, price)
                   VALUES (?, ?, ?, ?, ?)
                   ''', (
                       data['name'],
                       data.get('description', ''),
                       data.get('groupname', 'Custom Services'),
                       data.get('subgroupname', 'General'),
                       data['price']
                   ))

        db.commit()
        return jsonify({"message": "PAX service created successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500