#!/usr/bin/env python3
"""
Location-aware LocalLifeAssistant backend using real-time event fetching
"""

import logging
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our location-aware crawler
from location_aware_crawler import LocationAwareEventbriteCrawler, get_supported_cities

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="LocalLifeAssistant - Location Aware", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the location-aware crawler
location_crawler = LocationAwareEventbriteCrawler()

# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[ChatMessage] = []
    llm_provider: Optional[str] = None
    location: Optional[Dict[str, Any]] = None  # Add location to chat request

class ChatResponse(BaseModel):
    message: str
    recommendations: List[Dict[str, Any]] = []
    llm_provider_used: str

class GeocodeRequest(BaseModel):
    input_text: str

class GeocodeResponse(BaseModel):
    success: bool
    coordinates: Optional[Dict[str, Any]] = None
    formatted_address: Optional[str] = None
    error_message: Optional[str] = None

class LocationCoordinates(BaseModel):
    latitude: float
    longitude: float
    formatted_address: str

# Smart city mapping system
class SmartCityMapper:
    """
    Smart city mapping system that handles city aliases and regional groupings
    """
    
    def __init__(self):
        # Define major cities and their coordinates
        self.major_cities = {
            "san francisco": (37.7749, -122.4194),
            "new york": (40.7128, -74.0060),
            "los angeles": (34.0522, -118.2437),
            "chicago": (41.8781, -87.6298),
            "boston": (42.3601, -71.0589),
            "seattle": (47.6062, -122.3321),
            "austin": (30.2672, -97.7431),
            "denver": (39.7392, -104.9903),
            "miami": (25.7617, -80.1918),
            "atlanta": (33.7490, -84.3880),
            "london": (51.5074, -0.1278),
            "paris": (48.8566, 2.3522),
            "tokyo": (35.6762, 139.6503),
        }
        
        # Define city aliases and regional mappings
        self.city_mappings = {
            # San Francisco Bay Area
            "san francisco": ["san francisco", "sf", "bay area", "san fran", "palo alto", 
                             "mountain view", "sunnyvale", "santa clara", "cupertino", "san jose", 
                             "menlo park", "fremont", "hayward", "oakland", "berkeley", 
                             "daly city", "san mateo", "redwood city"],
            
            # New York Metro Area
            "new york": ["new york", "nyc", "manhattan", "brooklyn", "queens", "bronx", 
                        "staten island", "long island", "westchester", "nassau", "suffolk"],
            
            # Los Angeles Area
            "los angeles": ["los angeles", "la", "hollywood", "beverly hills", "santa monica",
                           "venice", "pasadena", "glendale", "burbank", "long beach", "anaheim"],
            
            # Chicago Area
            "chicago": ["chicago", "chicago loop", "lincoln park", "wicker park", "lakeview"],
            
            # Boston Area
            "boston": ["boston", "cambridge", "somerville", "brookline", "newton"],
            
            # Seattle Area
            "seattle": ["seattle", "bellevue", "redmond", "kirkland", "tacoma"],
            
            # Austin Area
            "austin": ["austin", "round rock", "cedar park", "pflugerville"],
            
            # Denver Area
            "denver": ["denver", "aurora", "lakewood", "westminster"],
            
            # Miami Area
            "miami": ["miami", "miami beach", "fort lauderdale", "west palm beach"],
            
            # Atlanta Area
            "atlanta": ["atlanta", "sandy springs", "roswell", "alpharetta"],
            
            # International cities
            "london": ["london", "greater london", "westminster", "camden", "islington"],
            "paris": ["paris", "ile de france", "paris arrondissement"],
            "tokyo": ["tokyo", "tokyo prefecture", "shibuya", "shinjuku", "harajuku"],
        }
        
        # Create reverse lookup for fast matching
        self.alias_to_city = {}
        for major_city, aliases in self.city_mappings.items():
            for alias in aliases:
                self.alias_to_city[alias.lower()] = major_city
    
    def extract_city_from_address(self, formatted_address: str) -> Optional[str]:
        """
        Extract major city from formatted address using smart mapping
        """
        if not formatted_address:
            return None
        
        address_lower = formatted_address.lower()
        
        # Direct alias matching
        for alias, major_city in self.alias_to_city.items():
            if alias in address_lower:
                return major_city
        
        # State-based fallback for US cities
        if 'california' in address_lower or 'ca' in address_lower:
            if any(bay_city in address_lower for bay_city in 
                   ['palo alto', 'mountain view', 'sunnyvale', 'santa clara', 'san jose']):
                return 'san francisco'
            elif any(la_city in address_lower for la_city in 
                     ['hollywood', 'beverly hills', 'santa monica', 'venice']):
                return 'los angeles'
        
        elif 'new york' in address_lower or 'ny' in address_lower:
            return 'new york'
        
        elif 'texas' in address_lower or 'tx' in address_lower:
            return 'austin'
        
        elif 'washington' in address_lower or 'wa' in address_lower:
            return 'seattle'
        
        elif 'massachusetts' in address_lower or 'ma' in address_lower:
            return 'boston'
        
        elif 'illinois' in address_lower or 'il' in address_lower:
            return 'chicago'
        
        elif 'colorado' in address_lower or 'co' in address_lower:
            return 'denver'
        
        elif 'florida' in address_lower or 'fl' in address_lower:
            return 'miami'
        
        elif 'georgia' in address_lower or 'ga' in address_lower:
            return 'atlanta'
        
        return None
    
    def extract_city_from_coordinates(self, lat: float, lng: float) -> Optional[str]:
        """
        Extract major city from coordinates using distance calculation
        """
        min_distance = float('inf')
        closest_city = None
        
        for city, (city_lat, city_lng) in self.major_cities.items():
            distance = ((lat - city_lat) ** 2 + (lng - city_lng) ** 2) ** 0.5
            if distance < min_distance and distance < 1.0:  # Within ~100km
                min_distance = distance
                closest_city = city
        
        return closest_city
    
    def get_city(self, location: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Smart city extraction from location data
        """
        if not location:
            return None
        
        # Try address-based extraction first
        formatted_address = location.get('formatted_address', '')
        if formatted_address:
            city = self.extract_city_from_address(formatted_address)
            if city:
                return city
        
        # Fallback to coordinate-based extraction
        lat = location.get('latitude', 0)
        lng = location.get('longitude', 0)
        
        if lat and lng:
            return self.extract_city_from_coordinates(lat, lng)
        
        return None
    
    def add_city_region(self, major_city: str, coordinates: tuple, aliases: list):
        """
        Add a new city region to the mapping system
        """
        self.major_cities[major_city] = coordinates
        self.city_mappings[major_city] = aliases
        
        # Update reverse lookup
        for alias in aliases:
            self.alias_to_city[alias.lower()] = major_city
    
    def get_supported_regions(self) -> dict:
        """
        Get all supported regions and their aliases
        """
        return {
            city: {
                "coordinates": coords,
                "aliases": self.city_mappings.get(city, []),
                "alias_count": len(self.city_mappings.get(city, []))
            }
            for city, coords in self.major_cities.items()
        }

# Global instance
city_mapper = SmartCityMapper()

def extract_city_from_location(location: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Extract city name from location coordinates or formatted address using smart mapping
    """
    return city_mapper.get_city(location)

# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "LocalLifeAssistant Location-Aware"}

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    supported_cities = get_supported_cities()
    return {
        "service": "location-aware",
        "supported_cities_count": len(supported_cities),
        "supported_cities": supported_cities[:10],  # Show first 10
        "features": ["real-time-events", "location-aware", "multi-city-support"]
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Location-aware chat endpoint that fetches events based on user location"""
    try:
        logger.info(f"Chat request: {request.message}")
        
        # Extract city from location if provided
        city = extract_city_from_location(request.location)
        logger.info(f"Extracted city from location: {city}")
        
        # Default to New York if no location provided
        if not city:
            city = "new york"
            logger.info("No location provided, defaulting to New York")
        
        # Fetch events for the city
        logger.info(f"Fetching events for city: {city}")
        events = location_crawler.fetch_events_by_city(city, max_pages=2)
        logger.info(f"Fetched {len(events)} events for {city}")
        
        # Simple keyword search in the fetched events
        query_words = request.message.lower().split()
        relevant_events = []
        
        for event in events:
            score = 0
            event_text = f"{event.get('title', '')} {event.get('description', '')} {' '.join(event.get('categories', []))}".lower()
            
            for word in query_words:
                if word in event_text:
                    score += 1
                if word in event.get('title', '').lower():
                    score += 2
                if word in event.get('venue_name', '').lower():
                    score += 1
            
            if score > 0:
                event['relevance_score'] = score
                relevant_events.append(event)
        
        # Sort by relevance and take top results
        relevant_events.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        top_events = relevant_events[:5]
        
        # Format response
        if top_events:
            response_message = f"🎉 Found {len(top_events)} events in {city.title()} that match your search! Check out the recommendations below ↓"
            
            formatted_recommendations = []
            for event in top_events:
                formatted_recommendations.append({
                    "type": "event",
                    "data": event,
                    "relevance_score": event.get('relevance_score', 0.5),
                    "explanation": f"This event in {city.title()} matches your search for '{request.message}' based on title, description, or categories."
                })
        else:
            response_message = f"😔 I couldn't find any events in {city.title()} matching your query. Try asking about 'fashion events', 'music concerts', 'halloween parties', or 'free events'."
            formatted_recommendations = []
        
        return ChatResponse(
            message=response_message,
            recommendations=formatted_recommendations,
            llm_provider_used="location-aware"
        )
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@app.post("/api/geocode", response_model=GeocodeResponse)
async def geocode_location(request: GeocodeRequest):
    """Geocode a location input including US zipcodes"""
    try:
        input_text = request.input_text.strip()
        logger.info(f"Geocoding location: {input_text}")
        
        # Check if input is a US zipcode (5 digits)
        import re
        if re.match(r'^\d{5}$', input_text):
            return await geocode_zipcode(input_text)
        
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
            "london": {"latitude": 51.5074, "longitude": -0.1278, "formatted_address": "London, UK"},
            "paris": {"latitude": 48.8566, "longitude": 2.3522, "formatted_address": "Paris, France"},
            "tokyo": {"latitude": 35.6762, "longitude": 139.6503, "formatted_address": "Tokyo, Japan"},
        }
        
        # Check for exact match first
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

async def geocode_zipcode(zipcode: str) -> GeocodeResponse:
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
        elif 2100 <= zip_int <= 2199:  # Boston area
            return GeocodeResponse(
                success=True,
                coordinates={"latitude": 42.3601, "longitude": -71.0589, "formatted_address": f"Boston, MA {zipcode}, USA"},
                formatted_address=f"Boston, MA {zipcode}, USA"
            )
        else:
            return GeocodeResponse(
                success=False,
                error_message=f"Zipcode {zipcode} not recognized. Please try a major city name or a known zipcode."
            )

@app.get("/api/events")
async def get_events(query: str, location: Optional[str] = None, category: Optional[str] = None, max_results: int = 5):
    """Get events by query and location"""
    try:
        # Use location if provided, otherwise default to New York
        city = location or "new york"
        
        logger.info(f"Fetching events for query: '{query}' in city: '{city}'")
        
        # Fetch events for the city
        events = location_crawler.fetch_events_by_city(city, max_pages=2)
        
        # Filter events based on query
        query_words = query.lower().split()
        relevant_events = []
        
        for event in events:
            score = 0
            event_text = f"{event.get('title', '')} {event.get('description', '')} {' '.join(event.get('categories', []))}".lower()
            
            for word in query_words:
                if word in event_text:
                    score += 1
                if word in event.get('title', '').lower():
                    score += 2
            
            if score > 0:
                relevant_events.append(event)
        
        # Sort and return top results
        relevant_events.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return {
            "query": query,
            "location": city,
            "events": relevant_events[:max_results],
            "total_found": len(relevant_events)
        }
        
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching events: {str(e)}")

@app.get("/api/supported-cities")
async def get_supported_cities_endpoint():
    """Get list of supported cities"""
    cities = get_supported_cities()
    return {
        "supported_cities": cities,
        "total_count": len(cities)
    }

@app.post("/api/debug/location")
async def debug_location_extraction(location: Dict[str, Any]):
    """Debug endpoint to test location extraction"""
    extracted_city = extract_city_from_location(location)
    return {
        "input_location": location,
        "extracted_city": extracted_city,
        "formatted_address": location.get('formatted_address', ''),
        "latitude": location.get('latitude', 0),
        "longitude": location.get('longitude', 0)
    }

@app.get("/api/regions")
async def get_supported_regions():
    """Get all supported regions and their aliases"""
    return {
        "regions": city_mapper.get_supported_regions(),
        "total_regions": len(city_mapper.major_cities),
        "total_aliases": len(city_mapper.alias_to_city)
    }

if __name__ == "__main__":
    logger.info("Starting LocalLifeAssistant (Location-Aware Version)...")
    logger.info("Supported cities: " + ", ".join(get_supported_cities()[:10]) + "...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
