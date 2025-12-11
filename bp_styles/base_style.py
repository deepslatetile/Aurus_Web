from abc import ABC, abstractmethod
from PIL import Image, ImageDraw

class BaseBoardingPassStyle(ABC):
    @abstractmethod
    def draw_boarding_pass(self, info: dict) -> Image.Image:
        pass

    @abstractmethod
    def get_required_fields(self) -> list:
        return ['booking_id', 'flight_number', 'seat', 'serve_class',
                'departure', 'arrival', 'flight_datetime', 'passenger_name']
                