#!/usr/bin/env python3
"""
Geocoding and location extraction functionality
"""

import os
import openai
import re
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class LocationCoordinates(BaseModel):
    latitude: float
    longitude: float
    formatted_address: str

class GeocodeRequest(BaseModel):
    input_text: str

class GeocodeResponse(BaseModel):
    success: bool
    coordinates: Optional[LocationCoordinates] = None
    formatted_address: Optional[str] = None
    error_message: Optional[str] = None

class GeocodingService:
    """Service for geocoding and location extraction"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
    
    def extract_city_from_query_llm(self, query: str) -> Optional[str]:
        """
        Extract city name from user query using LLM.
        Returns the city name if found, None otherwise.
        """
        try:
            # Create a focused prompt for city extraction
            prompt = f"""
You are a location extraction assistant. Your task is to identify if the user's query mentions a specific US city or location.

User query: "{query}"

Instructions:
1. Look for explicit city names, neighborhoods, or regions in the query
2. Only return a city name if it's clearly mentioned
3. If no specific location is mentioned, return "none"
4. Return the city name in lowercase format
5. For neighborhoods like "Brooklyn", "Manhattan", "Queens", return "new york"
6. For regions like "Bay Area", return "san francisco"

Examples:
- "Show me free events in Brooklyn" → "new york"
- "Find restaurants in Los Angeles" → "los angeles" 
- "What's happening in Miami this weekend?" → "miami"
- "Find me a chinese place to eat nearby" → "none"
- "Show me events in Chicago" → "chicago"
- "What restaurants are good for a date night?" → "none"

Return only the city name or "none", nothing else.
"""

            # Call OpenAI API for city extraction
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a precise location extraction assistant. Return only city names or 'none'."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            extracted_city = response.choices[0].message.content.strip().lower()
            
            # Validate the response
            if extracted_city == "none" or not extracted_city:
                logger.info(f"No city found in query (LLM): '{query}'")
                return None
            
            # Map common variations to standard city names
            city_mapping = {
                'brooklyn': 'New York',
                'manhattan': 'New York', 
                'queens': 'New York',
                'bronx': 'New York',
                'nyc': 'New York',
                'new york city': 'New York',
                'los angeles': 'Los Angeles',
                'la': 'Los Angeles',
                'san francisco': 'San Francisco',
                'sf': 'San Francisco',
                'chicago': 'Chicago',
                'boston': 'Boston',
                'seattle': 'Seattle',
                'miami': 'Miami',
                'austin': 'Austin',
                'denver': 'Denver',
                'portland': 'Portland',
                'phoenix': 'Phoenix',
                'las vegas': 'Las Vegas',
                'atlanta': 'Atlanta'
            }
            final_city = city_mapping.get(extracted_city.lower(), extracted_city)
            
            logger.info(f"LLM extracted city '{final_city}' from query: '{query}'")
            return final_city
            
        except Exception as e:
            logger.error(f"LLM city extraction failed: {e}")
            return None

    def extract_city_from_query(self, query: str) -> Optional[str]:
        """
        Extract city name from user query using LLM with regex fallback.
        Returns the city name if found, None otherwise.
        """
        # Try LLM extraction first
        llm_result = self.extract_city_from_query_llm(query)
        if llm_result:
            return llm_result
        
        # Fallback to regex-based extraction
        logger.info(f"LLM extraction failed, trying regex fallback for: '{query}'")
        
        # Common city patterns
        city_patterns = {
            r'\bbrooklyn\b': 'new york',
            r'\bmanhattan\b': 'new york', 
            r'\bqueens\b': 'new york',
            r'\bbronx\b': 'new york',
            r'\bnyc\b': 'new york',
            r'\bnew york city\b': 'new york',
            r'\blos angeles\b': 'los angeles',
            r'\bla\b': 'los angeles',
            r'\bsan francisco\b': 'san francisco',
            r'\bsf\b': 'san francisco',
            r'\bchicago\b': 'chicago',
            r'\bboston\b': 'boston',
            r'\bseattle\b': 'seattle',
            r'\bmiami\b': 'miami',
            r'\baustin\b': 'austin',
            r'\bdenver\b': 'denver',
            r'\bportland\b': 'portland',
            r'\bphoenix\b': 'phoenix',
            r'\blas vegas\b': 'las vegas',
            r'\batlanta\b': 'atlanta'
        }
        
        query_lower = query.lower()
        for pattern, city in city_patterns.items():
            if re.search(pattern, query_lower):
                logger.info(f"Regex found city '{city}' in query: '{query}'")
                return city
        
        logger.info(f"No city found in query (regex): '{query}'")
        return None

    async def geocode_location(self, request: GeocodeRequest) -> GeocodeResponse:
        """Geocode a location input including US zipcodes"""
        try:
            input_text = request.input_text.strip()
            logger.info(f"Geocoding location: {input_text}")
            
            # Check if input is a US zipcode (5 digits)
            if re.match(r'^\d{5}$', input_text):
                return await self.geocode_zipcode(input_text)
            
            # Simple geocoding logic for city names
            location_mapping = {
                "new york": {"latitude": 40.7128, "longitude": -74.0060, "formatted_address": "New York, NY, USA"},
                "nyc": {"latitude": 40.7128, "longitude": -74.0060, "formatted_address": "New York, NY, USA"},
                "san francisco": {"latitude": 37.7749, "longitude": -122.4194, "formatted_address": "San Francisco, CA, USA"},
                "sf": {"latitude": 37.7749, "longitude": -122.4194, "formatted_address": "San Francisco, CA, USA"},
                "los angeles": {"latitude": 34.0522, "longitude": -118.2437, "formatted_address": "Los Angeles, CA, USA"},
                "la": {"latitude": 34.0522, "longitude": -118.2437, "formatted_address": "Los Angeles, CA, USA"},
                "chicago": {"latitude": 41.8781, "longitude": -87.6298, "formatted_address": "Chicago, IL, USA"},
                "boston": {"latitude": 42.3601, "longitude": -71.0589, "formatted_address": "Boston, MA, USA"},
                "seattle": {"latitude": 47.6062, "longitude": -122.3321, "formatted_address": "Seattle, WA, USA"},
                "austin": {"latitude": 30.2672, "longitude": -97.7431, "formatted_address": "Austin, TX, USA"},
                "denver": {"latitude": 39.7392, "longitude": -104.9903, "formatted_address": "Denver, CO, USA"},
                "miami": {"latitude": 25.7617, "longitude": -80.1918, "formatted_address": "Miami, FL, USA"},
                "atlanta": {"latitude": 33.7490, "longitude": -84.3880, "formatted_address": "Atlanta, GA, USA"},
            }
            
            if input_text.lower() in location_mapping:
                coords = location_mapping[input_text.lower()]
                return GeocodeResponse(
                    success=True,
                    coordinates=coords,
                    formatted_address=coords["formatted_address"]
                )
            
            # Check for partial matches
            for location, coords in location_mapping.items():
                if input_text.lower() in location or location in input_text.lower():
                    return GeocodeResponse(
                        success=True,
                        coordinates=coords,
                        formatted_address=coords["formatted_address"]
                    )
            
            # If no match found
            return GeocodeResponse(
                success=False,
                error_message=f"Location '{input_text}' not found. Try: New York, San Francisco, or a US zipcode like 10001."
            )
            
        except Exception as e:
            logger.error(f"Error geocoding location: {e}")
            return GeocodeResponse(
                success=False,
                error_message=f"Error geocoding location: {str(e)}"
            )

    async def geocode_zipcode(self, zipcode: str) -> GeocodeResponse:
        """Geocode a US zipcode using a simple mapping"""
        
        # Major US zipcode mappings (sample of common zipcodes)
        zipcode_mapping = {
            # New York
            "10001": {"latitude": 40.7505, "longitude": -73.9934, "formatted_address": "New York, NY 10001, USA"},
            "10002": {"latitude": 40.7157, "longitude": -73.9878, "formatted_address": "New York, NY 10002, USA"},
            "10003": {"latitude": 40.7336, "longitude": -73.9905, "formatted_address": "New York, NY 10003, USA"},
            "10011": {"latitude": 40.7407, "longitude": -73.9986, "formatted_address": "New York, NY 10011, USA"},
            "10012": {"latitude": 40.7254, "longitude": -73.9972, "formatted_address": "New York, NY 10012, USA"},
            
            # San Francisco
            "94102": {"latitude": 37.7849, "longitude": -122.4094, "formatted_address": "San Francisco, CA 94102, USA"},
            "94103": {"latitude": 37.7712, "longitude": -122.4127, "formatted_address": "San Francisco, CA 94103, USA"},
            "94105": {"latitude": 37.7885, "longitude": -122.3985, "formatted_address": "San Francisco, CA 94105, USA"},
            "94107": {"latitude": 37.7666, "longitude": -122.3931, "formatted_address": "San Francisco, CA 94107, USA"},
            "94110": {"latitude": 37.7484, "longitude": -122.4156, "formatted_address": "San Francisco, CA 94110, USA"},
            
            # Los Angeles
            "90210": {"latitude": 34.0901, "longitude": -118.4065, "formatted_address": "Beverly Hills, CA 90210, USA"},
            "90028": {"latitude": 34.1022, "longitude": -118.3268, "formatted_address": "Hollywood, CA 90028, USA"},
            "90046": {"latitude": 34.0983, "longitude": -118.3617, "formatted_address": "West Hollywood, CA 90046, USA"},
            "90048": {"latitude": 34.0736, "longitude": -118.3726, "formatted_address": "Los Angeles, CA 90048, USA"},
            
            # Chicago
            "60601": {"latitude": 41.8781, "longitude": -87.6298, "formatted_address": "Chicago, IL 60601, USA"},
            "60602": {"latitude": 41.8819, "longitude": -87.6274, "formatted_address": "Chicago, IL 60602, USA"},
            "60603": {"latitude": 41.8805, "longitude": -87.6281, "formatted_address": "Chicago, IL 60603, USA"},
            "60611": {"latitude": 41.8961, "longitude": -87.6234, "formatted_address": "Chicago, IL 60611, USA"},
            
            # Boston
            "02101": {"latitude": 42.3601, "longitude": -71.0589, "formatted_address": "Boston, MA 02101, USA"},
            "02108": {"latitude": 42.3581, "longitude": -71.0636, "formatted_address": "Boston, MA 02108, USA"},
            "02109": {"latitude": 42.3599, "longitude": -71.0539, "formatted_address": "Boston, MA 02109, USA"},
            
            # Seattle
            "98101": {"latitude": 47.6062, "longitude": -122.3321, "formatted_address": "Seattle, WA 98101, USA"},
            "98102": {"latitude": 47.6256, "longitude": -122.3205, "formatted_address": "Seattle, WA 98102, USA"},
            "98103": {"latitude": 47.6604, "longitude": -122.3427, "formatted_address": "Seattle, WA 98103, USA"},
            
            # Austin
            "78701": {"latitude": 30.2672, "longitude": -97.7431, "formatted_address": "Austin, TX 78701, USA"},
            "78702": {"latitude": 30.2672, "longitude": -97.7431, "formatted_address": "Austin, TX 78702, USA"},
            "78703": {"latitude": 30.2755, "longitude": -97.7628, "formatted_address": "Austin, TX 78703, USA"},
            
            # Miami
            "33101": {"latitude": 25.7617, "longitude": -80.1918, "formatted_address": "Miami, FL 33101, USA"},
            "33109": {"latitude": 25.7831, "longitude": -80.1301, "formatted_address": "Miami, FL 33109, USA"},
            "33132": {"latitude": 25.7889, "longitude": -80.2264, "formatted_address": "Miami, FL 33132, USA"},
            
            # Denver
            "80201": {"latitude": 39.7392, "longitude": -104.9903, "formatted_address": "Denver, CO 80201, USA"},
            "80202": {"latitude": 39.7392, "longitude": -104.9903, "formatted_address": "Denver, CO 80202, USA"},
            "80203": {"latitude": 39.7392, "longitude": -104.9903, "formatted_address": "Denver, CO 80203, USA"},
            
            # Atlanta
            "30301": {"latitude": 33.7490, "longitude": -84.3880, "formatted_address": "Atlanta, GA 30301, USA"},
            "30302": {"latitude": 33.7490, "longitude": -84.3880, "formatted_address": "Atlanta, GA 30302, USA"},
            "30303": {"latitude": 33.7490, "longitude": -84.3880, "formatted_address": "Atlanta, GA 30303, USA"},
        }
        
        if zipcode in zipcode_mapping:
            coords = zipcode_mapping[zipcode]
            return GeocodeResponse(
                success=True,
                coordinates=coords,
                formatted_address=coords["formatted_address"]
            )
        else:
            # For unknown zipcodes, try to map to nearest major city based on zipcode ranges
            zip_int = int(zipcode)
            
            if 10000 <= zip_int <= 14999:  # New York area
                return GeocodeResponse(
                    success=True,
                    coordinates={"latitude": 40.7128, "longitude": -74.0060, "formatted_address": f"New York, NY {zipcode}, USA"},
                    formatted_address=f"New York, NY {zipcode}, USA"
                )
            elif 94000 <= zip_int <= 94999:  # San Francisco Bay Area (check this first to avoid overlap)
                return GeocodeResponse(
                    success=True,
                    coordinates={"latitude": 37.7749, "longitude": -122.4194, "formatted_address": f"San Francisco, CA {zipcode}, USA"},
                    formatted_address=f"San Francisco, CA {zipcode}, USA"
                )
            elif 90000 <= zip_int <= 93999:  # Los Angeles area (reduced range to avoid overlap)
                return GeocodeResponse(
                    success=True,
                    coordinates={"latitude": 34.0522, "longitude": -118.2437, "formatted_address": f"Los Angeles, CA {zipcode}, USA"},
                    formatted_address=f"Los Angeles, CA {zipcode}, USA"
                )
            elif 60600 <= zip_int <= 60699:  # Chicago area
                return GeocodeResponse(
                    success=True,
                    coordinates={"latitude": 41.8781, "longitude": -87.6298, "formatted_address": f"Chicago, IL {zipcode}, USA"},
                    formatted_address=f"Chicago, IL {zipcode}, USA"
                )
            elif 2000 <= zip_int <= 2999:  # Boston area
                return GeocodeResponse(
                    success=True,
                    coordinates={"latitude": 42.3601, "longitude": -71.0589, "formatted_address": f"Boston, MA {zipcode}, USA"},
                    formatted_address=f"Boston, MA {zipcode}, USA"
                )
            elif 98000 <= zip_int <= 98999:  # Seattle area
                return GeocodeResponse(
                    success=True,
                    coordinates={"latitude": 47.6062, "longitude": -122.3321, "formatted_address": f"Seattle, WA {zipcode}, USA"},
                    formatted_address=f"Seattle, WA {zipcode}, USA"
                )
            elif 78700 <= zip_int <= 78799:  # Austin area
                return GeocodeResponse(
                    success=True,
                    coordinates={"latitude": 30.2672, "longitude": -97.7431, "formatted_address": f"Austin, TX {zipcode}, USA"},
                    formatted_address=f"Austin, TX {zipcode}, USA"
                )
            elif 80200 <= zip_int <= 80299:  # Denver area
                return GeocodeResponse(
                    success=True,
                    coordinates={"latitude": 39.7392, "longitude": -104.9903, "formatted_address": f"Denver, CO {zipcode}, USA"},
                    formatted_address=f"Denver, CO {zipcode}, USA"
                )
            elif 33100 <= zip_int <= 33199:  # Miami area
                return GeocodeResponse(
                    success=True,
                    coordinates={"latitude": 25.7617, "longitude": -80.1918, "formatted_address": f"Miami, FL {zipcode}, USA"},
                    formatted_address=f"Miami, FL {zipcode}, USA"
                )
            elif 30300 <= zip_int <= 30399:  # Atlanta area
                return GeocodeResponse(
                    success=True,
                    coordinates={"latitude": 33.7490, "longitude": -84.3880, "formatted_address": f"Atlanta, GA {zipcode}, USA"},
                    formatted_address=f"Atlanta, GA {zipcode}, USA"
                )
            else:
                return GeocodeResponse(
                    success=False,
                    error_message=f"Zipcode {zipcode} not supported. Please try a major US city zipcode."
                )
