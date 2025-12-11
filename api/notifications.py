from flask import Blueprint, request, jsonify, session
from database import get_db
import time
from services.firebase_admin import FirebaseAdmin

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/push/subscribe', methods=['POST'])
def push_subscribe():
    try:
        data = request.get_json()
        token = data.get('token')
        user_id = data.get('user_id')

        if not token:
            return jsonify({'error': 'Token is required'}), 400

        db = get_db()

        # Если пользователь авторизован в сессии, используем его ID
        if 'user_id' in session and not user_id:
            user_id = session['user_id']

        # Проверяем, существует ли уже токен
        existing = db.execute(
            'SELECT id FROM push_subscriptions WHERE fcm_token = ?',
            (token,)
        ).fetchone()

        if existing:
            return jsonify({'message': 'Token already exists'}), 200

        # Сохраняем токен
        db.execute(
            '''INSERT INTO push_subscriptions
                   (user_id, fcm_token, created_at)
               VALUES (?, ?, ?)''',
            (user_id, token, int(time.time()))
        )
        db.commit()

        # Подписываем на общие темы
        try:
            FirebaseAdmin.subscribe_to_topic([token], 'all_users')
            if user_id:
                FirebaseAdmin.subscribe_to_topic([token], f'user_{user_id}')
        except Exception as e:
            print(f"Topic subscription warning: {e}")

        return jsonify({'message': 'Token saved successfully'}), 200

    except Exception as e:
        print(f"Error in push_subscribe: {e}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/push/unsubscribe', methods=['POST'])
def push_unsubscribe():
    try:
        data = request.get_json()
        token = data.get('token')

        if not token:
            return jsonify({'error': 'Token is required'}), 400

        db = get_db()

        # Отписываем от тем перед удалением
        try:
            subscription = db.execute(
                'SELECT user_id FROM push_subscriptions WHERE fcm_token = ?',
                (token,)
            ).fetchone()

            if subscription:
                user_id = subscription['user_id']
                FirebaseAdmin.unsubscribe_from_topic([token], 'all_users')
                if user_id:
                    FirebaseAdmin.unsubscribe_from_topic([token], f'user_{user_id}')
        except Exception as e:
            print(f"Topic unsubscription warning: {e}")

        db.execute(
            'DELETE FROM push_subscriptions WHERE fcm_token = ?',
            (token,)
        )
        db.commit()

        return jsonify({'message': 'Token removed successfully'}), 200

    except Exception as e:
        print(f"Error in push_unsubscribe: {e}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/push/tokens', methods=['GET'])
def get_user_tokens():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        db = get_db()

        tokens = db.execute(
            'SELECT fcm_token, created_at FROM push_subscriptions WHERE user_id = ?',
            (session['user_id'],)
        ).fetchall()

        return jsonify({
            'tokens': [dict(token) for token in tokens]
        }), 200

    except Exception as e:
        print(f"Error in get_user_tokens: {e}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/push/test', methods=['POST'])
def send_test_notification():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.get_json()
        test_type = data.get('type', 'personal')  # personal, broadcast

        title = "🧪 Тестовое уведомление"
        body = f"Это тестовое уведомление от Aurus. Время: {time.strftime('%H:%M:%S')}"

        if test_type == 'personal':
            # Отправляем текущему пользователю
            result = FirebaseAdmin.send_to_user(
                session['user_id'],
                title,
                body,
                data={'url': '/', 'type': 'test'}
            )
            message = "Тестовое уведомление отправлено вам"

        elif test_type == 'broadcast':
            # Отправляем всем пользователям (только для админов)
            db = get_db()
            user = db.execute(
                'SELECT user_group FROM users WHERE id = ?',
                (session['user_id'],)
            ).fetchone()

            if not user or user['user_group'] not in ['HQ', 'STF']:
                return jsonify({'error': 'Admin access required'}), 403

            result = FirebaseAdmin.send_broadcast(
                title,
                body,
                data={'url': '/', 'type': 'test_broadcast'}
            )
            message = f"Тестовое уведомление отправлено всем пользователям ({len(result) if result else 0} получателей)"

        else:
            return jsonify({'error': 'Invalid test type'}), 400

        return jsonify({
            'message': message,
            'result': result
        }), 200

    except Exception as e:
        print(f"Error in send_test_notification: {e}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/push/send', methods=['POST'])
def send_custom_notification():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        # Проверяем права админа
        db = get_db()
        user = db.execute(
            'SELECT user_group FROM users WHERE id = ?',
            (session['user_id'],)
        ).fetchone()

        if not user or user['user_group'] not in ['HQ', 'STF']:
            return jsonify({'error': 'Admin access required'}), 403

        data = request.get_json()
        title = data.get('title')
        body = data.get('body')
        target = data.get('target', 'all')  # all, user, topic
        target_id = data.get('target_id')
        url = data.get('url', '/')

        if not title or not body:
            return jsonify({'error': 'Title and body are required'}), 400

        notification_data = {
            'url': url,
            'type': 'custom',
            'sent_by': str(session['user_id']),
            'timestamp': str(int(time.time()))
        }

        if target == 'all':
            result = FirebaseAdmin.send_broadcast(title, body, notification_data)
            message = f"Уведомление отправлено всем пользователям"

        elif target == 'user':
            if not target_id:
                return jsonify({'error': 'target_id required for user target'}), 400
            result = FirebaseAdmin.send_to_user(target_id, title, body, notification_data)
            message = f"Уведомление отправлено пользователю {target_id}"

        elif target == 'topic':
            if not target_id:
                return jsonify({'error': 'target_id required for topic target'}), 400
            result = FirebaseAdmin.send_to_topic(target_id, title, body, notification_data)
            message = f"Уведомление отправлено в тему {target_id}"

        else:
            return jsonify({'error': 'Invalid target'}), 400

        # Логируем отправку уведомления
        db.execute(
            '''INSERT INTO notification_logs
                   (admin_user_id, title, body, target, target_id, sent_at)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (session['user_id'], title, body, target, target_id, int(time.time()))
        )
        db.commit()

        return jsonify({
            'message': message,
            'sent_count': len(result) if result else 0
        }), 200

    except Exception as e:
        print(f"Error in send_custom_notification: {e}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/push/stats', methods=['GET'])
def get_notification_stats():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        # Проверяем права админа
        db = get_db()
        user = db.execute(
            'SELECT user_group FROM users WHERE id = ?',
            (session['user_id'],)
        ).fetchone()

        if not user or user['user_group'] not in ['HQ', 'STF']:
            return jsonify({'error': 'Admin access required'}), 403

        # Статистика по подпискам
        stats = db.execute('''
                           SELECT COUNT(*)                as total_subscriptions,
                                  COUNT(DISTINCT user_id) as unique_users,
                                  COUNT(*)                as active_tokens
                           FROM push_subscriptions
                           WHERE fcm_token IS NOT NULL
                           ''').fetchone()

        return jsonify({
            'stats': dict(stats)
        }), 200

    except Exception as e:
        print(f"Error in get_notification_stats: {e}")
        return jsonify({'error': str(e)}), 500