import firebase_admin
from firebase_admin import credentials, messaging
import os
import json
from database import get_db


class FirebaseAdmin:
    _initialized = False

    @classmethod
    def initialize(cls):
        if cls._initialized:
            return

        try:
            # Для PythonAnywhere используем переменные окружения
            service_account_info = {
                "type": "service_account",
                "project_id": "aurus-pwa",
                "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                "private_key": os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
                "client_email": os.getenv('FIREBASE_CLIENT_EMAIL',
                                          'firebase-adminsdk-fbsdk@aurus-pwa.iam.gserviceaccount.com'),
                "client_id": os.getenv('FIREBASE_CLIENT_ID'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }

            # Если нет приватного ключа в переменных окружения, попробуем файл
            if not service_account_info['private_key']:
                cred = credentials.Certificate('firebase-service-account.json')
            else:
                cred = credentials.Certificate(service_account_info)

            firebase_admin.initialize_app(cred)
            cls._initialized = True
            print("✅ Firebase Admin SDK initialized successfully")

        except Exception as e:
            print(f"❌ Firebase Admin SDK initialization failed: {e}")
            cls._initialized = False

    @classmethod
    def send_to_token(cls, token, title, body, data=None):
        if not cls._initialized:
            cls.initialize()
            if not cls._initialized:
                raise Exception("Firebase Admin not initialized")

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=token,
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            badge=1,
                            sound='default'
                        )
                    )
                )
            )

            response = messaging.send(message)
            print(f"✅ Notification sent successfully: {response}")
            return response

        except Exception as e:
            print(f"❌ Error sending notification: {e}")
            raise e

    @classmethod
    def send_to_topic(cls, topic, title, body, data=None):
        if not cls._initialized:
            cls.initialize()
            if not cls._initialized:
                raise Exception("Firebase Admin not initialized")

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                topic=topic
            )

            response = messaging.send(message)
            print(f"✅ Notification to topic {topic} sent: {response}")
            return response

        except Exception as e:
            print(f"❌ Error sending topic notification: {e}")
            raise e

    @classmethod
    def send_to_user(cls, user_id, title, body, data=None):
        """Отправляет уведомление всем устройствам пользователя"""
        if not cls._initialized:
            cls.initialize()

        try:
            db = get_db()
            tokens = db.execute(
                'SELECT fcm_token FROM push_subscriptions WHERE user_id = ?',
                (user_id,)
            ).fetchall()

            if not tokens:
                print(f"⚠️ No tokens found for user {user_id}")
                return None

            results = []
            for token_row in tokens:
                try:
                    result = cls.send_to_token(token_row['fcm_token'], title, body, data)
                    results.append(result)
                except Exception as e:
                    print(f"❌ Failed to send to token {token_row['fcm_token']}: {e}")
                    # Удаляем невалидный токен
                    db.execute(
                        'DELETE FROM push_subscriptions WHERE fcm_token = ?',
                        (token_row['fcm_token'],)
                    )
                    db.commit()

            return results

        except Exception as e:
            print(f"❌ Error sending to user {user_id}: {e}")
            raise e

    @classmethod
    def send_broadcast(cls, title, body, data=None):
        """Отправляет уведомление всем подписанным пользователям"""
        if not cls._initialized:
            cls.initialize()

        try:
            db = get_db()
            tokens = db.execute(
                'SELECT fcm_token FROM push_subscriptions WHERE fcm_token IS NOT NULL'
            ).fetchall()

            if not tokens:
                print("⚠️ No tokens found for broadcast")
                return None

            results = []
            invalid_tokens = []

            for token_row in tokens:
                try:
                    result = cls.send_to_token(token_row['fcm_token'], title, body, data)
                    results.append(result)
                except Exception as e:
                    print(f"❌ Failed to send to token {token_row['fcm_token']}: {e}")
                    invalid_tokens.append(token_row['fcm_token'])

            # Удаляем невалидные токены
            if invalid_tokens:
                db.execute(
                    f'DELETE FROM push_subscriptions WHERE fcm_token IN ({",".join(["?"] * len(invalid_tokens))})',
                    invalid_tokens
                )
                db.commit()
                print(f"🗑️ Removed {len(invalid_tokens)} invalid tokens")

            return results

        except Exception as e:
            print(f"❌ Error sending broadcast: {e}")
            raise e

    @classmethod
    def subscribe_to_topic(cls, tokens, topic):
        if not cls._initialized:
            cls.initialize()

        try:
            response = messaging.subscribe_to_topic(tokens, topic)
            print(f"✅ Subscribed {response.success_count} tokens to topic {topic}")
            return response
        except Exception as e:
            print(f"❌ Error subscribing to topic: {e}")
            raise e

    @classmethod
    def unsubscribe_from_topic(cls, tokens, topic):
        if not cls._initialized:
            cls.initialize()

        try:
            response = messaging.unsubscribe_from_topic(tokens, topic)
            print(f"✅ Unsubscribed {response.success_count} tokens from topic {topic}")
            return response
        except Exception as e:
            print(f"❌ Error unsubscribing from topic: {e}")
            raise e



FirebaseAdmin.initialize()