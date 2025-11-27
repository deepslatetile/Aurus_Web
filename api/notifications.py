import json
import time
from flask import Blueprint, request, jsonify
from database import get_db
import jwt
import requests
from base64 import urlsafe_b64encode
import os

# Создаем blueprint для уведомлений
notifications_bp = Blueprint('notifications', __name__)


class NotificationManager:
    def __init__(self):
        self.vapid_private_key = os.getenv('VAPID_PRIVATE_KEY', '')
        self.vapid_public_key = os.getenv('VAPID_PUBLIC_KEY', '')
        self.vapid_claims = {
            "sub": "mailto:deepslatework@mail.ru"
        }

    def save_subscription(self, subscription_data, user_id=None):
        """Сохраняет подписку в БД"""
        db = get_db()

        subscription = json.loads(subscription_data) if isinstance(subscription_data, str) else subscription_data

        try:
            db.execute('''
                INSERT OR REPLACE INTO push_subscriptions 
                (user_id, endpoint, p256dh, auth, created_at) 
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                subscription['endpoint'],
                subscription['keys']['p256dh'],
                subscription['keys']['auth'],
                int(time.time())
            ))
            db.commit()
            return True
        except Exception as e:
            print(f"Error saving subscription: {e}")
            return False

    def get_user_subscriptions(self, user_id):
        """Получает подписки пользователя"""
        db = get_db()
        cursor = db.execute('''
                            SELECT endpoint, p256dh, auth
                            FROM push_subscriptions
                            WHERE user_id = ?
                            ''', (user_id,))

        subscriptions = []
        for row in cursor.fetchall():
            subscriptions.append({
                'endpoint': row['endpoint'],
                'keys': {
                    'p256dh': row['p256dh'],
                    'auth': row['auth']
                }
            })
        return subscriptions

    def get_all_subscriptions(self):
        """Получает все подписки"""
        db = get_db()
        cursor = db.execute('''
                            SELECT endpoint, p256dh, auth, user_id
                            FROM push_subscriptions
                            ''')

        subscriptions = []
        for row in cursor.fetchall():
            subscriptions.append({
                'endpoint': row['endpoint'],
                'keys': {
                    'p256dh': row['p256dh'],
                    'auth': row['auth']
                },
                'user_id': row['user_id']
            })
        return subscriptions

    def delete_subscription(self, endpoint):
        """Удаляет подписку"""
        db = get_db()
        db.execute('DELETE FROM push_subscriptions WHERE endpoint = ?', (endpoint,))
        db.commit()

    def send_push_notification(self, subscription, title, body, url=None, icon=None):
        """Отправляет push-уведомление"""
        try:
            # Подготовка payload
            payload = {
                'title': title,
                'body': body,
                'icon': icon or '/static/icons/icon-192x192.png',
                'url': url or '/'
            }

            # Создание JWT токена
            expiration = int(time.time()) + 43200  # 12 часов
            jwt_payload = {
                "aud": "https://fcm.googleapis.com",
                "exp": expiration,
                "sub": self.vapid_claims["sub"]
            }

            jwt_token = jwt.encode(jwt_payload, self.vapid_private_key, algorithm="ES256")
            if isinstance(jwt_token, bytes):
                jwt_token = jwt_token.decode('utf-8')

            # Заголовки
            headers = {
                'Authorization': f'vapid t={jwt_token}, k={self.vapid_public_key}',
                'Content-Type': 'application/json',
                'TTL': '86400'
            }

            # Отправка
            response = requests.post(
                subscription['endpoint'],
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )

            return response.status_code == 201

        except Exception as e:
            print(f"Error sending push notification: {e}")
            return False

    def send_to_user(self, user_id, title, body, url=None):
        """Отправляет уведомление конкретному пользователю"""
        subscriptions = self.get_user_subscriptions(user_id)
        results = []

        for subscription in subscriptions:
            success = self.send_push_notification(subscription, title, body, url)
            results.append({'endpoint': subscription['endpoint'], 'success': success})

        return results

    def broadcast(self, title, body, url=None):
        """Отправляет уведомление всем подписчикам"""
        subscriptions = self.get_all_subscriptions()
        results = []

        for subscription in subscriptions:
            success = self.send_push_notification(subscription, title, body, url)
            results.append({'endpoint': subscription['endpoint'], 'success': success})

        return results


# Создаем глобальный экземпляр
notification_manager = NotificationManager()


# Эндпоинты для уведомлений
@notifications_bp.route('/push/subscribe', methods=['POST'])
def push_subscribe():
    """Сохраняет подписку пользователя"""
    try:
        data = request.json
        subscription = data.get('subscription')
        user_id = data.get('user_id')  # Опционально

        if not subscription:
            return jsonify({'error': 'Subscription data required'}), 400

        success = notification_manager.save_subscription(subscription, user_id)

        if success:
            return jsonify({'status': 'success', 'message': 'Subscribed to push notifications'})
        else:
            return jsonify({'error': 'Failed to save subscription'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/push/unsubscribe', methods=['POST'])
def push_unsubscribe():
    """Удаляет подписку"""
    try:
        data = request.json
        endpoint = data.get('endpoint')

        if not endpoint:
            return jsonify({'error': 'Endpoint required'}), 400

        notification_manager.delete_subscription(endpoint)
        return jsonify({'status': 'success', 'message': 'Unsubscribed'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/push/send', methods=['POST'])
def push_send():
    """Отправляет уведомление (для админов)"""
    try:
        data = request.json
        title = data.get('title', 'Уведомление')
        body = data.get('body', '')
        url = data.get('url')
        user_id = data.get('user_id')

        if user_id:
            results = notification_manager.send_to_user(user_id, title, body, url)
        else:
            results = notification_manager.broadcast(title, body, url)

        return jsonify({
            'status': 'success',
            'message': f'Sent {len(results)} notifications',
            'results': results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/push/test', methods=['POST'])
def push_test():
    """Тестовое уведомление"""
    try:
        results = notification_manager.broadcast(
            'Тест PWA',
            'Привет! Это тестовое уведомление от твоего приложения! 🎉',
            '/'
        )

        return jsonify({
            'status': 'success',
            'message': f'Test notification sent to {len(results)} subscribers',
            'results': results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500