from flask import Blueprint, jsonify, request, session
import requests
import os
import time
import json
from datetime import datetime, timedelta
from database import get_db

admin_weather_bp = Blueprint('admin_weather', __name__)

CHECKWX_API_KEY = os.getenv('CHECKWX_API_KEY', '2da1148c40ec422d965fe7757444d715')
CHECKWX_API_URL = 'https://api.checkwx.com/metar'

CACHE_DURATION = 300
MAX_CACHE_ENTRIES = 100

def check_admin_access():
    if 'user_id' not in session:
        return False

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            'SELECT user_group FROM users WHERE id = %s',
            (session['user_id'],)
        )

        user = cursor.fetchone()
        return user and user['user_group'] in ['HQ', 'STF']

    except Exception:
        return False

def cleanup_old_cache():
    db = get_db()
    cursor = db.cursor()

    current_time = int(time.time())
    cursor.execute('DELETE FROM weather_cache WHERE expires_at < %s', (current_time,))

    cursor.execute('SELECT COUNT(*) FROM weather_cache')
    count_result = cursor.fetchone()
    count = count_result[0] if count_result else 0

    if count > MAX_CACHE_ENTRIES:
        cursor.execute('''
                       DELETE
                       FROM weather_cache
                       WHERE icao_code IN (SELECT icao_code
                                           FROM weather_cache
                                           ORDER BY created_at ASC
                           LIMIT %s
                           )
                       ''', (count - MAX_CACHE_ENTRIES,))

    db.commit()

def get_cached_weather(icao_code):
    """Получение данных из кэша"""
    db = get_db()
    cursor = db.cursor(dictionary=True)

    current_time = int(time.time())
    cursor.execute(
        'SELECT data FROM weather_cache WHERE icao_code = %s AND expires_at > %s',
        (icao_code.upper(), current_time)
    )

    result = cursor.fetchone()
    if result:
        return result['data']
    return None

def set_cached_weather(icao_code, data):
    db = get_db()
    cursor = db.cursor()

    current_time = int(time.time())
    expires_at = current_time + CACHE_DURATION

    cursor.execute('''
        INSERT INTO weather_cache 
        (icao_code, data, created_at, expires_at) 
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        data = VALUES(data), 
        created_at = VALUES(created_at), 
        expires_at = VALUES(expires_at)
    ''', (icao_code.upper(), json.dumps(data), current_time, expires_at))

    db.commit()

def fetch_weather_from_api(icao_code):
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
    if not icao_code or len(icao_code) != 4:
        return jsonify({'error': 'Invalid ICAO code'}), 400

    try:
        cleanup_old_cache()

        cached_data = get_cached_weather(icao_code)

        if cached_data:
            data = json.loads(cached_data)
            from_cache = True
        else:
            data = fetch_weather_from_api(icao_code)
            from_cache = False

            if data.get('results', 0) > 0:
                set_cached_weather(icao_code, data)

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
        print(f"Weather API error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@admin_weather_bp.route('/get/weather/multiple', methods=['GET'])
def get_multiple_weather():
    stations = request.args.get('stations', '')

    if not stations:
        return jsonify({'error': 'No stations provided'}), 400

    station_list = [s.strip().upper() for s in stations.split(',') if len(s.strip()) == 4]

    if not station_list:
        return jsonify({'error': 'No valid ICAO codes provided'}), 400

    if len(station_list) > 10:
        return jsonify({'error': 'Maximum 10 stations allowed'}), 400

    try:
        cleanup_old_cache()

        results = []
        from_cache_count = 0

        for station in station_list:
            cached_data = get_cached_weather(station)

            if cached_data:
                station_data = json.loads(cached_data)
                station_data['cache_info'] = {
                    'from_cache': True,
                    'cache_duration': CACHE_DURATION
                }
                results.append(station_data)
                from_cache_count += 1
            else:
                try:
                    station_data = fetch_weather_from_api(station)
                    if station_data.get('results', 0) > 0:
                        set_cached_weather(station, station_data)
                        station_data['cache_info'] = {
                            'from_cache': False,
                            'cache_duration': CACHE_DURATION
                        }
                        results.append(station_data)
                except Exception as e:
                    print(f"Error fetching weather for {station}: {e}")
                    continue

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
        print(f"Multiple weather API error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@admin_weather_bp.route('/weather/cache/clear', methods=['POST'])
def clear_weather_cache():

    if not check_admin_access():
        return jsonify({'error': 'Unauthorized access'}), 403

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute('DELETE FROM weather_cache')
        deleted_count = cursor.rowcount

        db.commit()

        return jsonify({
            'message': f'Weather cache cleared successfully',
            'deleted_entries': deleted_count
        })

    except Exception as e:
        return jsonify({'error': f'Error clearing cache: {str(e)}'}), 500

@admin_weather_bp.route('/weather/cache/status', methods=['GET'])
def get_cache_status():
    if not check_admin_access():
        return jsonify({'error': 'Unauthorized access'}), 403

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('SELECT COUNT(*) as total FROM weather_cache')
        total_result = cursor.fetchone()
        total_entries = total_result['total'] if total_result else 0

        current_time = int(time.time())
        cursor.execute('SELECT COUNT(*) as active FROM weather_cache WHERE expires_at > %s', (current_time,))
        active_result = cursor.fetchone()
        active_entries = active_result['active'] if active_result else 0

        cursor.execute('SELECT icao_code, created_at FROM weather_cache ORDER BY created_at ASC LIMIT 5')
        oldest_entries = cursor.fetchall()

        cursor.execute('SELECT icao_code, created_at FROM weather_cache ORDER BY created_at DESC LIMIT 5')
        newest_entries = cursor.fetchall()

        return jsonify({
            'cache_status': {
                'total_entries': total_entries,
                'active_entries': active_entries,
                'expired_entries': total_entries - active_entries,
                'max_entries': MAX_CACHE_ENTRIES,
                'cache_duration_seconds': CACHE_DURATION,
                'cache_duration_minutes': CACHE_DURATION // 60,
                'oldest_entries': oldest_entries,
                'newest_entries': newest_entries
            }
        })

    except Exception as e:
        return jsonify({'error': f'Error getting cache status: {str(e)}'}), 500
        