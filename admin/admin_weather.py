from flask import Blueprint, jsonify, request, session
import requests
import os
import time
import sqlite3
import json
from datetime import datetime, timedelta

admin_weather_bp = Blueprint('admin_weather', __name__)

# API ключ для checkwx.com
CHECKWX_API_KEY = os.getenv('CHECKWX_API_KEY', '2da1148c40ec422d965fe7757444d715')
CHECKWX_API_URL = 'https://api.checkwx.com/metar'

# Конфигурация кэширования
CACHE_DURATION = 300  # 5 минут в секундах
MAX_CACHE_ENTRIES = 100


def check_admin_access():
    """Проверка прав доступа администратора"""
    if 'user_id' not in session:
        return False

    try:
        conn = sqlite3.connect(os.getenv('DATABASE_URL', 'airline.db'))
        cursor = conn.cursor()

        cursor.execute(
            'SELECT user_group FROM users WHERE id = ?',
            (session['user_id'],)
        )

        user = cursor.fetchone()
        conn.close()

        return user and user[0] in ['HQ', 'STF']

    except Exception:
        return False


def cleanup_old_cache():
    """Очистка устаревших записей кэша"""
    conn = sqlite3.connect(os.getenv('DATABASE_URL', 'airline.db'))
    cursor = conn.cursor()

    current_time = int(time.time())
    cursor.execute('DELETE FROM weather_cache WHERE expires_at < ?', (current_time,))

    # Если записей слишком много, удаляем самые старые
    cursor.execute('SELECT COUNT(*) FROM weather_cache')
    count = cursor.fetchone()[0]

    if count > MAX_CACHE_ENTRIES:
        cursor.execute('''
                       DELETE
                       FROM weather_cache
                       WHERE icao_code IN (SELECT icao_code
                                           FROM weather_cache
                                           ORDER BY created_at ASC
                           LIMIT ?
                           )
                       ''', (count - MAX_CACHE_ENTRIES,))

    conn.commit()
    conn.close()


def get_cached_weather(icao_code):
    """Получение данных из кэша"""
    conn = sqlite3.connect(os.getenv('DATABASE_URL', 'airline.db'))
    cursor = conn.cursor()

    current_time = int(time.time())
    cursor.execute(
        'SELECT data FROM weather_cache WHERE icao_code = ? AND expires_at > ?',
        (icao_code.upper(), current_time)
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]  # Возвращаем JSON строку
    return None


def set_cached_weather(icao_code, data):
    """Сохранение данных в кэш"""
    conn = sqlite3.connect(os.getenv('DATABASE_URL', 'airline.db'))
    cursor = conn.cursor()

    current_time = int(time.time())
    expires_at = current_time + CACHE_DURATION

    cursor.execute('''
        INSERT OR REPLACE INTO weather_cache 
        (icao_code, data, created_at, expires_at) 
        VALUES (?, ?, ?, ?)
    ''', (icao_code.upper(), json.dumps(data), current_time, expires_at))

    conn.commit()
    conn.close()


def fetch_weather_from_api(icao_code):
    """Получение погоды из внешнего API"""
    headers = {
        'X-API-Key': CHECKWX_API_KEY
    }

    url = f"{CHECKWX_API_URL}/{icao_code}/decoded"
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        raise Exception('Invalid API key')
    elif response.status_code == 404:
        raise Exception('Station not found')
    else:
        raise Exception(f'Weather API error: {response.status_code}')


@admin_weather_bp.route('/get/weather/<icao_code>', methods=['GET'])
def get_weather(icao_code):
    """
    Get METAR weather data for specified ICAO code with caching
    """
    if not icao_code or len(icao_code) != 4:
        return jsonify({'error': 'Invalid ICAO code'}), 400

    try:
        # Очищаем старый кэш перед каждым запросом
        cleanup_old_cache()

        # Пытаемся получить данные из кэша
        cached_data = get_cached_weather(icao_code)

        if cached_data:
            # Возвращаем данные из кэша
            data = json.loads(cached_data)
            from_cache = True
        else:
            # Получаем данные из API
            data = fetch_weather_from_api(icao_code)
            from_cache = False

            # Сохраняем в кэш, если данные получены успешно
            if data.get('results', 0) > 0:
                set_cached_weather(icao_code, data)

        # Добавляем информацию о кэше в ответ
        response_data = data.copy()
        response_data['cache_info'] = {
            'from_cache': from_cache,
            'cache_duration': CACHE_DURATION,
            'cached_until': int(time.time()) + CACHE_DURATION if from_cache else None
        }

        return jsonify(response_data)

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Weather API timeout'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Cannot connect to weather service'}), 503
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@admin_weather_bp.route('/get/weather/multiple', methods=['GET'])
def get_multiple_weather():
    """
    Get METAR weather data for multiple ICAO codes with caching
    """
    stations = request.args.get('stations', '')

    if not stations:
        return jsonify({'error': 'No stations provided'}), 400

    station_list = [s.strip().upper() for s in stations.split(',') if len(s.strip()) == 4]

    if not station_list:
        return jsonify({'error': 'No valid ICAO codes provided'}), 400

    if len(station_list) > 10:
        return jsonify({'error': 'Maximum 10 stations allowed'}), 400

    try:
        # Очищаем старый кэш
        cleanup_old_cache()

        results = []
        from_cache_count = 0

        for station in station_list:
            # Пытаемся получить из кэша
            cached_data = get_cached_weather(station)

            if cached_data:
                # Данные из кэша
                station_data = json.loads(cached_data)
                station_data['cache_info'] = {
                    'from_cache': True,
                    'cache_duration': CACHE_DURATION
                }
                results.append(station_data)
                from_cache_count += 1
            else:
                # Получаем из API
                try:
                    station_data = fetch_weather_from_api(station)
                    if station_data.get('results', 0) > 0:
                        # Сохраняем в кэш
                        set_cached_weather(station, station_data)
                        station_data['cache_info'] = {
                            'from_cache': False,
                            'cache_duration': CACHE_DURATION
                        }
                        results.append(station_data)
                except Exception as e:
                    # Пропускаем станции с ошибками
                    print(f"Error fetching weather for {station}: {e}")
                    continue

        # Формируем общий ответ
        combined_data = {
            'results': len(results),
            'data': [item for result in results for item in result.get('data', [])],
            'cache_info': {
                'total_stations': len(station_list),
                'from_cache': from_cache_count,
                'from_api': len(results) - from_cache_count,
                'cache_duration': CACHE_DURATION
            }
        }

        return jsonify(combined_data)

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@admin_weather_bp.route('/weather/cache/clear', methods=['POST'])
def clear_weather_cache():
    """
    Clear weather cache (admin only)
    """
    # Проверка прав доступа
    if not check_admin_access():
        return jsonify({'error': 'Unauthorized access'}), 403

    try:
        conn = sqlite3.connect(os.getenv('DATABASE_URL', 'airline.db'))
        cursor = conn.cursor()

        cursor.execute('DELETE FROM weather_cache')
        deleted_count = cursor.rowcount

        conn.commit()
        conn.close()

        return jsonify({
            'message': f'Weather cache cleared successfully',
            'deleted_entries': deleted_count
        })

    except Exception as e:
        return jsonify({'error': f'Error clearing cache: {str(e)}'}), 500


@admin_weather_bp.route('/weather/cache/status', methods=['GET'])
def get_cache_status():
    """
    Get weather cache status (admin only)
    """
    # Проверка прав доступа
    if not check_admin_access():
        return jsonify({'error': 'Unauthorized access'}), 403

    try:
        conn = sqlite3.connect(os.getenv('DATABASE_URL', 'airline.db'))
        cursor = conn.cursor()

        # Общее количество записей
        cursor.execute('SELECT COUNT(*) FROM weather_cache')
        total_entries = cursor.fetchone()[0]

        # Количество активных записей (не истекших)
        current_time = int(time.time())
        cursor.execute('SELECT COUNT(*) FROM weather_cache WHERE expires_at > ?', (current_time,))
        active_entries = cursor.fetchone()[0]

        # Самые старые и новые записи
        cursor.execute('SELECT icao_code, created_at FROM weather_cache ORDER BY created_at ASC LIMIT 5')
        oldest_entries = cursor.fetchall()

        cursor.execute('SELECT icao_code, created_at FROM weather_cache ORDER BY created_at DESC LIMIT 5')
        newest_entries = cursor.fetchall()

        conn.close()

        return jsonify({
            'cache_status': {
                'total_entries': total_entries,
                'active_entries': active_entries,
                'expired_entries': total_entries - active_entries,
                'max_entries': MAX_CACHE_ENTRIES,
                'cache_duration_seconds': CACHE_DURATION,
                'cache_duration_minutes': CACHE_DURATION // 60,
                'oldest_entries': [
                    {'icao': entry[0], 'created_at': entry[1]}
                    for entry in oldest_entries
                ],
                'newest_entries': [
                    {'icao': entry[0], 'created_at': entry[1]}
                    for entry in newest_entries
                ]
            }
        })

    except Exception as e:
        return jsonify({'error': f'Error getting cache status: {str(e)}'}), 500