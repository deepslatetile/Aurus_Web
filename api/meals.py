from flask import Blueprint, request, jsonify, session
from services.utils import login_required
from database import get_db
from services.db_utils import handle_db_locks

meals_bp = Blueprint('meals', __name__)


def check_admin_access():
    if 'user_id' not in session:
        return False
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT user_group FROM users WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()
        return user and user['user_group'] in ['HQ', 'STF']
    except Exception as e:
        print(f"Admin check error: {e}")
        return False


def safe_get_image(image_data):
    if image_data is None:
        return None
    return str(image_data)


@meals_bp.route('/get/meals/<serve_class>', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_meals_by_class(serve_class):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, serve_class, serve_time, name, description, image FROM meals WHERE serve_class = %s ORDER BY id",
            (serve_class,))
        meals = cursor.fetchall()

        response = []
        for meal in meals:
            response.append({
                "id": meal['id'],
                "serve_class": meal['serve_class'],
                "serve_time": meal['serve_time'],
                "name": meal['name'],
                "description": meal['description'] or "",
                "image": safe_get_image(meal['image'])
            })
        return jsonify(response), 200
    except Exception as e:
        print(f"Error getting meals by class: {e}")
        return jsonify({"error": "Something went wrong"}), 500


@meals_bp.route('/post/meal', methods=['POST'])
@login_required
@handle_db_locks(max_retries=5)
def post_meal():
    if not check_admin_access():
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        required_fields = ['serve_class', 'serve_time', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        image_url = str(data.get('image')) if data.get('image') else None

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute('''
                       INSERT INTO meals (serve_class, serve_time, name, description, image)
                       VALUES (%s, %s, %s, %s, %s)
                       ''', (
                           data['serve_class'],
                           data['serve_time'],
                           data['name'],
                           data.get('description', ''),
                           image_url
                       ))

        meal_id = cursor.lastrowid
        db.commit()
        return jsonify({"message": "Meal created successfully", "meal_id": meal_id}), 201

    except Exception as e:
        print(f"Error creating meal: {e}")
        return jsonify({"error": "Something went wrong"}), 500


@meals_bp.route('/delete/meal/<meal_id>', methods=['DELETE'])
@login_required
@handle_db_locks(max_retries=5)
def delete_meal(meal_id):
    if not check_admin_access():
        return jsonify({"error": "Admin access required"}), 403

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM meals WHERE id = %s", (meal_id,))
        meal = cursor.fetchone()

        if not meal:
            return jsonify({"error": "Meal not found"}), 404

        cursor.execute("DELETE FROM meals WHERE id = %s", (meal_id,))
        db.commit()
        return jsonify({"message": f"Meal {meal_id} deleted successfully"}), 200

    except Exception as e:
        print(f"Error deleting meal: {e}")
        return jsonify({"error": "Something went wrong"}), 500


@meals_bp.route('/get/all_meals', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_all_meals():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, serve_class, serve_time, name, description, image FROM meals ORDER BY serve_class, serve_time, id")
        meals = cursor.fetchall()

        response = []
        for meal in meals:
            response.append({
                "id": meal['id'],
                "serve_class": meal['serve_class'],
                "serve_time": meal['serve_time'],
                "name": meal['name'],
                "description": meal['description'] or "",
                "image": safe_get_image(meal['image'])
            })
        return jsonify(response), 200

    except Exception as e:
        print(f"Error getting all meals: {e}")
        return jsonify({"error": "Something went wrong"}), 500


@meals_bp.route('/put/meal/<meal_id>', methods=['PUT'])
@login_required
@handle_db_locks(max_retries=5)
def update_meal(meal_id):
    if not check_admin_access():
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM meals WHERE id = %s", (meal_id,))
        meal = cursor.fetchone()

        if not meal:
            return jsonify({"error": "Meal not found"}), 404

        update_fields = []
        update_values = []
        updatable_fields = ['serve_class', 'serve_time', 'name', 'description', 'image']

        for field in updatable_fields:
            if field in data:
                if field == 'image':
                    update_values.append(str(data[field]))
                else:
                    update_values.append(data[field])
                update_fields.append(f"{field} = %s")

        if not update_fields:
            return jsonify({"error": "No fields to update"}), 400

        update_values.append(meal_id)
        update_query = f"UPDATE meals SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(update_query, update_values)
        db.commit()

        return jsonify({"message": "Meal updated successfully", "meal_id": meal_id}), 200

    except Exception as e:
        print(f"Error updating meal: {e}")
        return jsonify({"error": "Something went wrong"}), 500
        