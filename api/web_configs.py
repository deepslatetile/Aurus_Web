from flask import Blueprint, request, jsonify
from services.utils import login_required
from datetime import datetime
import sqlite3
from services.db_utils import handle_db_locks

web_configs_bp = Blueprint('web_configs', __name__)

@web_configs_bp.route('/get/web_config/id/<int:config_id>', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_web_config_by_id(config_id):
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM web_configs WHERE id = ?", (config_id,))
        config = c.fetchone()

        conn.close()

        if not config:
            return jsonify({"error": "Web config not found"}), 404

        config_info = {
            "id": config[0],
            "page_name": config[1],
            "page_display": config[2],
            "state": config[3]
        }

        return jsonify(config_info), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@web_configs_bp.route('/get/web_config/state/<state>', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_web_configs_by_state(state):
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        if state == '-1':
            c.execute("SELECT * FROM web_configs ORDER BY id")
        else:
            state = int(state)
            c.execute("SELECT * FROM web_configs WHERE state = ? ORDER BY id", (state,))

        configs = c.fetchall()
        conn.close()

        if not configs:
            return jsonify([]), 200

        response = []
        for config in configs:
            response.append({
                "id": config[0],
                "page_name": config[1],
                "page_display": config[2],
                "state": config[3]
            })

        return jsonify(response), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@web_configs_bp.route('/post/web_config/', methods=['POST'])
@login_required
@handle_db_locks(max_retries=5)
def create_web_config():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        required_fields = ['page_name', 'page_display']

        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        state = data.get('state', 0)

        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM web_configs WHERE page_name = ?", (data['page_name'],))
        existing_config = c.fetchone()

        if existing_config:
            return jsonify({"error": "Web config with this page_name already exists"}), 409

        c.execute('''
            INSERT INTO web_configs (page_name, page_display, state)
            VALUES (?, ?, ?)
        ''', (
            data['page_name'],
            data['page_display'],
            state
        ))

        config_id = c.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            "message": "Web config created successfully",
            "config_id": config_id
        }), 201

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@web_configs_bp.route('/delete/web_config/<int:config_id>', methods=['DELETE'])
@login_required
@handle_db_locks(max_retries=5)
def delete_web_config(config_id):
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM web_configs WHERE id = ?", (config_id,))
        config = c.fetchone()

        if not config:
            return jsonify({"error": "Web config not found"}), 404

        c.execute("DELETE FROM web_configs WHERE id = ?", (config_id,))
        conn.commit()
        conn.close()

        return jsonify({"message": f"Web config {config_id} deleted successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@web_configs_bp.route('/put/web_config/<int:config_id>/<int:state>', methods=['PUT'])
@login_required
@handle_db_locks(max_retries=5)
def update_web_config_state(config_id, state):
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM web_configs WHERE id = ?", (config_id,))
        config = c.fetchone()

        if not config:
            return jsonify({"error": "Web config not found"}), 404

        c.execute("UPDATE web_configs SET state = ? WHERE id = ?", (state, config_id))
        conn.commit()
        conn.close()

        return jsonify({
            "message": f"Web config {config_id} state updated to {state}",
            "config_id": config_id,
            "new_state": state
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@web_configs_bp.route('/get/page_content/<page_name>', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_page_content(page_name):
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM web_configs WHERE page_name = ?", (page_name,))
        page_config = c.fetchone()

        conn.close()

        if not page_config:
            return jsonify({"error": "Page not found"}), 404

        page_info = {
            "id": page_config[0],
            "page_name": page_config[1],
            "page_display": page_config[2],
            "state": page_config[3],
            "content": page_config[4] if len(page_config) > 4 else "",
            "last_updated": page_config[5] if len(page_config) > 5 else int(datetime.now().timestamp())
        }

        return jsonify(page_info), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@web_configs_bp.route('/put/page_content/<page_name>', methods=['PUT'])
@login_required
@handle_db_locks(max_retries=5)
def update_page_content(page_name):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM web_configs WHERE page_name = ?", (page_name,))
        existing_page = c.fetchone()

        if not existing_page:
            return jsonify({"error": "Page not found"}), 404

        update_fields = []
        update_values = []

        if 'content' in data:
            update_fields.append("content = ?")
            update_values.append(data['content'])

        if 'page_display' in data:
            update_fields.append("page_display = ?")
            update_values.append(data['page_display'])

        if 'state' in data:
            update_fields.append("state = ?")
            update_values.append(data['state'])

        update_fields.append("last_updated = ?")
        update_values.append(int(datetime.now().timestamp()))

        update_values.append(page_name)

        if update_fields:
            update_query = f"UPDATE web_configs SET {', '.join(update_fields)} WHERE page_name = ?"
            c.execute(update_query, update_values)

        conn.commit()
        conn.close()

        return jsonify({"message": f"Page {page_name} updated successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500