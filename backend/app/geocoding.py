import logging
import requests
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class GeocodingService:
    """Service for geocoding location inputs to coordinates"""
    
    def __init__(self):
        # Use HTTP instead of HTTPS to avoid SSL issues
        self.base_url = "http://nominatim.openstreetmap.org/search"
        self.headers = {
            'User-Agent': 'local_life_assistant'
        }
    
    def geocode_location(self, location_input: str) -> Optional[Tuple[float, float, str]]:
        """
        Geocode a location input (zipcode or "city, state") to coordinates
        Defaults to US context for better results
        
        Args:
            location_input: Either a zipcode (e.g., "10001") or "city, state" (e.g., "New York, NY")
            
        Returns:
            Tuple of (latitude, longitude, formatted_address) or None if geocoding fails
        """
        try:
            # Clean the input
            location_input = location_input.strip()
            
            # Make direct HTTP request to Nominatim with US bias
            params = {
                'q': location_input,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'us',  # Bias results toward US
                'addressdetails': 1    # Get detailed address information
            }
            
            response = requests.get(
                self.base_url, 
                params=params, 
                headers=self.headers, 
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data and len(data) > 0:
                result = data[0]
                lat = float(result['lat'])
                lon = float(result['lon'])
                address = result.get('display_name', f'{lat}, {lon}')
                
                logger.info(f"Successfully geocoded '{location_input}' to {lat}, {lon}")
                return (lat, lon, address)
            else:
                logger.warning(f"Could not geocode location: '{location_input}'")
                return None
                
        except Exception as e:
            logger.error(f"Error geocoding location '{location_input}': {e}")
            return None
    
    def is_valid_zipcode(self, input_text: str) -> bool:
        """Check if input looks like a US zipcode"""
        import re
        # US zipcode pattern: 5 digits or 5+4 format
        zipcode_pattern = r'^\d{5}(-\d{4})?$'
        return bool(re.match(zipcode_pattern, input_text.strip()))
    
    def is_valid_city_state(self, input_text: str) -> bool:
        """Check if input looks like "city, state" format"""
        import re
        # Basic pattern: word(s), comma, word(s)
        city_state_pattern = r'^[a-zA-Z\s]+,\s*[a-zA-Z\s]+$'
        return bool(re.match(city_state_pattern, input_text.strip()))

# Global instance
geocoding_service = GeocodingService()