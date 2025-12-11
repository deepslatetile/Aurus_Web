from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone
import barcode
from barcode.writer import ImageWriter
from io import BytesIO


def unix_to_readable(n):
    dt = datetime.fromtimestamp(int(n), tz=timezone.utc)
    date_str = str(dt.strftime('%d %b')).upper()
    time_str = dt.strftime('%H:%M')
    return [date_str, time_str]


def serve_class_to_printable(s):
    words = s.split()
    r = ''
    for w in words:
        r += w[:2]
    return r[:5]


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


def draw_boarding_pass(info):
    base_image_path = f'bp_styles/kja_bp.png'
    img = Image.open(base_image_path)
    draw = ImageDraw.Draw(img)

    fontB = ImageFont.truetype("static/fonts/kja.ttf", 32)
    font = ImageFont.truetype("static/fonts/kja.ttf", 30)

    carrier, number = info['flight_number'][:2], info['flight_number'][2:]
    date_str, time_str = unix_to_readable(info['flight_datetime'])

    draw.text((192, 340), str(info['passenger_name']).upper(), fill='#000', font=font)
    draw.text((1524, 309), str(info['passenger_name']).upper(), fill='#000', font=font)
    draw.text((192, 485), str(info['departure']).upper(), fill='#000', font=font)
    draw.text((1664, 372), str(info['departure']).upper(), fill='#000', font=font)
    draw.text((192, 603), str(info['arrival']).upper(), fill='#000', font=font)
    draw.text((1664, 433), str(info['arrival']).upper(), fill='#000', font=font)
    draw.text((616, 750), str(serve_class_to_printable(info['serve_class']).upper()), fill='#000', font=font)
    draw.text((1685, 576), str(serve_class_to_printable(info['serve_class']).upper()), fill='#000', font=font)
    draw.text((620, 513), str(carrier).upper(), fill='#000', font=font)
    draw.text((832, 513), str(number).upper(), fill='#000', font=font)
    draw.text((1523, 576), str(carrier).upper() + ' ' + str(number).upper(), fill='#000', font=font)
    draw.text((1044, 513), str(date_str).upper(), fill='#000', font=font)
    draw.text((1259, 513), str(time_str).upper(), fill='#000', font=font)
    draw.text((1798, 576), str(date_str).upper(), fill='#000', font=font)
    draw.text((1935, 576), str(time_str).upper(), fill='#000', font=font)
    draw.text((832, 752), str(info['seat']).upper(), fill='#000', font=font)
    draw.text((1937, 722), str(info['seat']).upper(), fill='#000', font=font)
    draw.text((191, 750), str(info.get('gate', '')).upper(), fill='#000', font=font)
    draw.text((1523, 722), str(info.get('gate', '')).upper(), fill='#000', font=font)
    draw.text((403, 750), str(info.get('boarding_till', '')).upper(), fill='#000', font=font)
    draw.text((1726, 722), str(info.get('boarding_till', '')).upper(), fill='#000', font=font)
    draw.text((1980, 252), str(info['booking_id']).upper(), fill='#000', font=fontB)

    barcode_data = f"{info['booking_id']}_{info['flight_number']}_{info['passenger_name']}"
    barcode_img = generate_barcode(barcode_data)
    img.paste(barcode_img, (660, 190))

    return img
    