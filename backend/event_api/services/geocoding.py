import ssl
import certifi
from geopy.geocoders import Nominatim
from functools import lru_cache

class GeocodingService:
    def __init__(self, user_agent="event_api_service"):
        ctx = ssl.create_default_context(cafile=certifi.where())
        self.geolocator = Nominatim(user_agent=user_agent, ssl_context=ctx)

    @lru_cache(maxsize=100)
    def get_coordinates(self, city_name):
        """
        Get (latitude, longitude) for a city name.
        Uses caching to avoid hitting the API too often.
        """
        try:
            location = self.geolocator.geocode(city_name)
            if location:
                return location.latitude, location.longitude
            return None, None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None, None
