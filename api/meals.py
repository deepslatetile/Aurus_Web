from flask import Blueprint, request, jsonify
from services.utils import login_required
import sqlite3

meals_bp = Blueprint('meals', __name__)

@meals_bp.route('/get/meals/<serve_class>', methods=['GET'])
def get_meals_by_class(serve_class):
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM meals WHERE serve_class = ? ORDER BY id", (serve_class,))
        meals = c.fetchall()

        conn.close()

        if not meals:
            return jsonify([]), 200

        response = []
        for meal in meals:
            response.append({
                "id": meal[0],
                "serve_class": meal[1],
                "serve_time": meal[2],
                "name": meal[3],
                "description": meal[4] if meal[4] is not None else "",
                "image": meal[5]
            })

        return jsonify(response), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@meals_bp.route('/post/meal', methods=['POST'])
@login_required
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

        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute('''
            INSERT INTO meals (
                serve_class, serve_time, name, description, image
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            data['serve_class'],
            data['serve_time'],
            data['name'],
            description,
            image
        ))

        meal_id = c.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            "message": "Meal created successfully",
            "meal_id": meal_id
        }), 201

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500

@meals_bp.route('/delete/meal/<meal_id>', methods=['DELETE'])
@login_required
def delete_meal(meal_id):
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM meals WHERE id = ?", (meal_id,))
        meal = c.fetchone()

        if not meal:
            return jsonify({"error": "Meal not found"}), 404

        c.execute("DELETE FROM meals WHERE id = ?", (meal_id,))
        conn.commit()
        conn.close()

        return jsonify({"message": f"Meal {meal_id} deleted successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500


@meals_bp.route('/get/all_meals', methods=['GET'])
def get_all_meals():
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute("SELECT * FROM meals ORDER BY serve_class, serve_time, id")
        meals = c.fetchall()

        conn.close()

        if not meals:
            return jsonify([]), 200

        response = []
        for meal in meals:
            response.append({
                "id": meal[0],
                "serve_class": meal[1],
                "serve_time": meal[2],
                "name": meal[3],
                "description": meal[4] if meal[4] is not None else "",
                "image": meal[5]
            })

        return jsonify(response), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Something went wrong"}), 500