from flask import Blueprint, send_file, jsonify
import io
import sqlite3
import json
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import importlib.util
import os


def unix_to_readable(n):
    dt = datetime.fromtimestamp(n, tz=timezone.utc)
    return dt.strftime('%d.%m %H:%M')


def generate_barcode(data, width=730, height=220):
    """
    Генерирует штрихкод Code128 с размерами 730x190 без текста
    """
    try:
        # Создаем кастомный writer без текста
        class NoTextWriter(ImageWriter):
            def _paint_text(self, xpos, ypos):
                # Переопределяем метод отрисовки текста - ничего не делаем
                pass

        writer = NoTextWriter()
        writer.set_options({
            'module_width': 0.33,
            'module_height': height - 10,  # Оставляем немного места
            'quiet_zone': 4,
            'background': 'white',
            'foreground': 'black',
        })

        code128 = barcode.get_barcode_class('code128')
        barcode_obj = code128(data, writer=writer)

        # Сохраняем в память
        buffer = BytesIO()
        barcode_obj.write(buffer)
        buffer.seek(0)

        # Открываем и ресайзим до точных размеров
        barcode_img = Image.open(buffer)
        barcode_resized = barcode_img.resize((width, height), Image.Resampling.LANCZOS)

        return barcode_resized
    except Exception as e:
        print(f"Barcode generation error: {e}")
        # Возвращаем пустое изображение в случае ошибки
        return Image.new('RGB', (width, height), 'white')


def load_style_module(style_name: str):
    """Динамически загружает модуль стиля"""
    try:
        # Если это default, используем встроенную функцию
        if style_name == 'default':
            return None

        # Ищем файл в bp_styles
        module_path = f'bp_styles/{style_name}.py'
        if not os.path.exists(module_path):
            raise FileNotFoundError(f"Style module {module_path} not found")

        spec = importlib.util.spec_from_file_location(style_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    except Exception as e:
        print(f"Error loading style module {style_name}: {e}")
        return None


def draw_default_boarding_pass(info):
    """Стандартная функция рисования посадочного талона"""
    base_image_path = f'bp_styles/default_{info["serve_class"].lower().replace(" ", "-")}.png'

    # Если файл не существует, используем дефолтный
    if not os.path.exists(base_image_path):
        base_image_path = 'bp_styles/default_economy.png'

    img = Image.open(base_image_path)
    draw = ImageDraw.Draw(img)

    fontBB = ImageFont.truetype("static/fonts/kja.ttf", 216)
    fontB = ImageFont.truetype("static/fonts/kja.ttf", 128)
    font = ImageFont.truetype("static/fonts/kja.ttf", 64)
    fontS = ImageFont.truetype("static/fonts/kja.ttf", 24)

    draw.text((30, 30), info['flight_number'], fill='#fff', font=fontBB)
    draw.text((30, 300), 'Seat', fill='#fff', font=fontS)
    draw.text((30, 330), info['seat'], fill='#fff', font=font)
    draw.text((400, 300), 'Date/time', fill='#fff', font=fontS)
    draw.text((400, 400), '* time in UTC', fill='#9ec5ff', font=fontS)
    draw.text((400, 330), unix_to_readable(info['flight_datetime']), fill='#fff', font=font)
    draw.text((1080, 300), 'Passenger name', fill='#fff', font=fontS)
    draw.text((1080, 330), info['passenger_name'], fill='#fff', font=font)
    draw.text((1080, 30), f'From {" ".join(info["departure"].split(" ")[:-1])}', fill='#fff', font=fontS)
    draw.text((1080, 60), info['departure'].split(' ')[-1], fill='#fff', font=fontB)
    draw.text((1580, 30), f'To {" ".join(info["arrival"].split(" ")[:-1])}', fill='#fff', font=fontS)
    draw.text((1580, 60), info['arrival'].split(' ')[-1], fill='#fff', font=fontB)
    draw.text((30, 450), 'Additional info', fill='#9ec5ff', font=fontS)
    draw.text((30, 480), info['note'] or '--', fill='#9ec5ff', font=fontS)
    draw.text((1580, 300), 'Booking ID', fill='#fff', font=fontS)
    draw.text((1580, 330), info['booking_id'], fill='#fff', font=font)

    # Добавляем штрихкод
    barcode_data = f"{info['booking_id']}_{info['flight_number']}_{info['passenger_name']}"
    barcode_img = generate_barcode(barcode_data)
    img.paste(barcode_img, (1075, 450))

    return img


def draw_boarding_pass(style, info):
    """Основная функция рисования посадочного талона"""
    # Если style - это ID конфига из БД (число), загружаем конфиг
    if isinstance(style, int) or (isinstance(style, str) and style.isdigit()):
        try:
            conn = sqlite3.connect('airline.db')
            c = conn.cursor()
            c.execute('''
                      SELECT data
                      FROM flight_configs
                      WHERE id = ?
                        AND type = 'boarding_style'
                        AND is_active = 1
                      ''', (int(style),))
            config = c.fetchone()
            conn.close()

            if config:
                config_data = json.loads(config[0])
                style = config_data.get('draw_function', 'default')
        except Exception as e:
            print(f"Error loading boarding style config: {e}")
            style = 'default'

    # Обрабатываем строковые стили
    if style == 'default':
        return draw_default_boarding_pass(info)
    else:
        # Загружаем кастомный стиль из файла
        style_module = load_style_module(style)
        if style_module and hasattr(style_module, 'draw_boarding_pass'):
            return style_module.draw_boarding_pass(info)
        else:
            # Fallback to default
            print(f"Style {style} not found, using default")
            return draw_default_boarding_pass(info)


boarding_bp = Blueprint('boarding', __name__)


def boarding_pass_to_pdf(image):
    pdf_bytes = io.BytesIO()

    if image.mode != 'RGB':
        image = image.convert('RGB')

    image.save(pdf_bytes, format='PDF')
    pdf_bytes.seek(0)

    return pdf_bytes


@boarding_bp.route('/get/boarding_pass/<booking_id>/<style>', methods=['GET'])
def get_boarding_pass(booking_id, style):
    """Get boarding pass as PNG"""
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        # Получаем информацию о бронировании включая passenger_name
        c.execute('''
                  SELECT b.flight_number,
                         b.seat,
                         b.serve_class,
                         s.departure,
                         s.arrival,
                         s.datetime,
                         b.note,
                         b.user_id,
                         b.passenger_name
                  FROM bookings b
                           JOIN schedule s ON b.flight_number = s.flight_number
                  WHERE b.id = ?
                  ''', (booking_id,))

        booking = c.fetchone()
        conn.close()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        flight_number = booking[0]
        seat = booking[1]
        serve_class = booking[2]
        departure = booking[3]
        arrival = booking[4]
        flight_datetime = booking[5]
        note_data = booking[6]
        user_id = booking[7]
        passenger_name = booking[8] or "unknown"

        info = {
            'booking_id': booking_id,
            'flight_number': flight_number,
            'seat': seat,
            'serve_class': serve_class,
            'departure': departure,
            'arrival': arrival,
            'flight_datetime': flight_datetime,
            'passenger_name': passenger_name,
            'user_id': user_id,
            'note': note_data,
        }

        boarding_pass_image = draw_boarding_pass(style, info)

        img_bytes = io.BytesIO()
        boarding_pass_image.save(img_bytes, format='PNG', quality=100)
        img_bytes.seek(0)

        return send_file(img_bytes, mimetype='image/png',
                         download_name=f'boarding_pass_{booking_id}.png')

    except Exception as e:
        print(f"Boarding pass generation error: {e}")
        return jsonify({"error": f"Failed to generate boarding pass: {str(e)}"}), 500


@boarding_bp.route('/get/boarding_pass_pdf/<booking_id>/<style>', methods=['GET'])
def get_boarding_pass_pdf(booking_id, style):
    """Get boarding pass as PDF"""
    try:
        conn = sqlite3.connect('airline.db')
        c = conn.cursor()

        c.execute('''
                  SELECT b.flight_number,
                         b.seat,
                         b.serve_class,
                         s.departure,
                         s.arrival,
                         s.datetime,
                         b.note,
                         b.user_id,
                         b.passenger_name
                  FROM bookings b
                           JOIN schedule s ON b.flight_number = s.flight_number
                  WHERE b.id = ?
                  ''', (booking_id,))

        booking = c.fetchone()
        conn.close()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        flight_number = booking[0]
        seat = booking[1]
        serve_class = booking[2]
        departure = booking[3]
        arrival = booking[4]
        flight_datetime = booking[5]
        note_data = booking[6]
        user_id = booking[7]
        passenger_name = booking[8]

        info = {
            'booking_id': booking_id,
            'flight_number': flight_number,
            'seat': seat,
            'serve_class': serve_class,
            'departure': departure,
            'arrival': arrival,
            'flight_datetime': flight_datetime,
            'passenger_name': passenger_name,
            'user_id': user_id,
            'note': note_data,
        }

        boarding_pass_image = draw_boarding_pass(style, info)
        pdf_bytes = boarding_pass_to_pdf(boarding_pass_image)

        return send_file(pdf_bytes, mimetype='application/pdf',
                         download_name=f'boarding_pass_{booking_id}.pdf')

    except Exception as e:
        print(f"Boarding pass PDF generation error: {e}")
        return jsonify({"error": f"Failed to generate PDF boarding pass: {str(e)}"}), 500