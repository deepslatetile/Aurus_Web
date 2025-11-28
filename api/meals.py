from flask import Blueprint, request, jsonify
from services.utils import login_required
from database import get_db
from services.db_utils import handle_db_locks

meals_bp = Blueprint('meals', __name__)

@meals_bp.route('/get/meals/<serve_class>', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_meals_by_class(serve_class):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM meals WHERE serve_class = %s ORDER BY id", (serve_class,))
        meals = cursor.fetchall()

        if not meals:
            return jsonify([]), 200

        response = []
        for meal in meals:
            response.append({
                "id": meal['id'],
                "serve_class": meal['serve_class'],
                "serve_time": meal['serve_time'],
                "name": meal['name'],
                "description": meal['description'] if meal['description'] is not None else "",
                "image": meal['image']
            })

        return jsonify(response), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@meals_bp.route('/post/meal', methods=['POST'])
@login_required
@handle_db_locks(max_retries=5)
def post_meal():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    try:
        required_fields = [
            'serve_class',
            'serve_time',
            'name'
        ]

        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        description = data.get('description', '')
        image = data.get('image', None)

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('''
            INSERT INTO meals (
                serve_class, serve_time, name, description, image
            ) VALUES (%s, %s, %s, %s, %s)
        ''', (
            data['serve_class'],
            data['serve_time'],
            data['name'],
            description,
            image
        ))

        meal_id = cursor.lastrowid
        db.commit()

        return jsonify({
            "message": "Meal created successfully",
            "meal_id": meal_id
        }), 201

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@meals_bp.route('/delete/meal/<meal_id>', methods=['DELETE'])
@login_required
@handle_db_locks(max_retries=5)
def delete_meal(meal_id):
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
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@meals_bp.route('/get/all_meals', methods=['GET'])
@handle_db_locks(max_retries=5)
def get_all_meals():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM meals ORDER BY serve_class, serve_time, id")
        meals = cursor.fetchall()

        if not meals:
            return jsonify([]), 200

        response = []
        for meal in meals:
            response.append({
                "id": meal['id'],
                "serve_class": meal['serve_class'],
                "serve_time": meal['serve_time'],
                "name": meal['name'],
                "description": meal['description'] if meal['description'] is not None else "",
                "image": meal['image']
            })

        return jsonify(response), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500