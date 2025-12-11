from flask import Blueprint, send_file, jsonify
import io
from database import get_db, execute_with_retry
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
    try:
        class NoTextWriter(ImageWriter):
            def _paint_text(self, xpos, ypos):
                pass

        writer = NoTextWriter()
        writer.set_options({
            'module_width': 0.33,
            'module_height': height - 10,
            'quiet_zone': 4,
            'background': 'white',
            'foreground': 'black',
        })

        code128 = barcode.get_barcode_class('code128')
        barcode_obj = code128(data, writer=writer)

        buffer = BytesIO()
        barcode_obj.write(buffer)
        buffer.seek(0)

        barcode_img = Image.open(buffer)
        barcode_resized = barcode_img.resize((width, height), Image.Resampling.LANCZOS)

        return barcode_resized
    except Exception as e:
        print(f"Barcode generation error: {e}")
        return Image.new('RGB', (width, height), 'white')

def load_style_module(style_name: str):
    try:
        if style_name == 'default':
            return None

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
    base_image_path = f'bp_styles/default_{info["serve_class"].lower().replace(" ", "-")}.png'

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

    barcode_data = f"{info['booking_id']}_{info['flight_number']}_{info['passenger_name']}"
    barcode_img = generate_barcode(barcode_data)
    img.paste(barcode_img, (1075, 450))

    return img

def draw_boarding_pass(style, info):
    if isinstance(style, int) or (isinstance(style, str) and style.isdigit()):
        try:
            result = execute_with_retry('''
                                        SELECT data
                                        FROM flight_configs
                                        WHERE id = %s
                                          AND type = 'boarding_style'
                                          AND is_active = 1
                                        ''', (int(style),))

            config = result.fetchone()

            if config:
                config_data = json.loads(config['data'])
                style = config_data.get('draw_function', 'default')
        except Exception as e:
            print(f"Error loading boarding style config: {e}")
            style = 'default'

    if style == 'default':
        return draw_default_boarding_pass(info)
    else:
        style_module = load_style_module(style)
        if style_module and hasattr(style_module, 'draw_boarding_pass'):
            return style_module.draw_boarding_pass(info)
        else:
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
    try:
        result = execute_with_retry('''
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
                                    WHERE b.id = %s
                                    ''', (booking_id,))

        booking = result.fetchone()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        flight_number = booking['flight_number']
        seat = booking['seat']
        serve_class = booking['serve_class']
        departure = booking['departure']
        arrival = booking['arrival']
        flight_datetime = booking['datetime']
        note_data = booking['note']
        user_id = booking['user_id']
        passenger_name = booking['passenger_name'] or "unknown"

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
    try:
        result = execute_with_retry('''
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
                                    WHERE b.id = %s
                                    ''', (booking_id,))

        booking = result.fetchone()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        flight_number = booking['flight_number']
        seat = booking['seat']
        serve_class = booking['serve_class']
        departure = booking['departure']
        arrival = booking['arrival']
        flight_datetime = booking['datetime']
        note_data = booking['note']
        user_id = booking['user_id']
        passenger_name = booking['passenger_name']

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
        