#!/usr/bin/env python3
"""
Smart Cached RAG Local Life Assistant
Combines real-time fetching with intelligent city-based caching
"""

import asyncio
import logging
import json
import os
import openai
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
# Try multiple locations for flexibility (local dev vs Docker)
load_dotenv('../.env') or load_dotenv('.env') or load_dotenv('/app/.env')

# Initialize OpenAI client with API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Import our existing components
import sys
sys.path.append('..')
from location_aware_crawler import LocationAwareEventbriteCrawler
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug: Log the API key being used
logger.info(f"OpenAI API key loaded: {openai.api_key[:20]}..." if openai.api_key else "None")

app = FastAPI(title="Smart Cached RAG Local Life Assistant", version="2.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://localhost:3001", "http://localhost:3002", 
        "http://localhost:3003", "http://localhost:3004", "http://localhost:3005",
        "https://locomoco.lijietu.com", "https://www.locomoco.lijietu.com"
    ],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class LocationCoordinates(BaseModel):
    latitude: float
    longitude: float
    formatted_address: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, Any]] = []
    llm_provider: str = "openai"
    location: Optional[LocationCoordinates] = None

class ChatResponse(BaseModel):
    message: str
    recommendations: List[Dict[str, Any]] = []
    llm_provider_used: str
    cache_used: bool = False
    cache_age_hours: Optional[float] = None

class GeocodeRequest(BaseModel):
    input_text: str

class GeocodeResponse(BaseModel):
    success: bool
    coordinates: Optional[LocationCoordinates] = None
    formatted_address: Optional[str] = None
    error_message: Optional[str] = None

# Initialize components
location_crawler = LocationAwareEventbriteCrawler()

# Cache configuration
CACHE_DIR = "./event_cache"
CACHE_TTL_HOURS = 6  # Cache events for 6 hours
MAX_CACHE_SIZE_MB = 100  # Maximum cache size in MB

class CacheManager:
    """Intelligent cache manager for city-based event storage"""
    
    def __init__(self, cache_dir: str = CACHE_DIR, ttl_hours: int = CACHE_TTL_HOURS):
        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        self.max_size_mb = MAX_CACHE_SIZE_MB
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        logger.info(f"Cache manager initialized: {cache_dir}, TTL: {ttl_hours}h")
    
    def _get_cache_file(self, city: str) -> str:
        """Get cache file path for a city"""
        # Sanitize city name for filename
        safe_city = city.lower().replace(" ", "_").replace("/", "_")
        return os.path.join(self.cache_dir, f"{safe_city}.json")
    
    def _is_cache_valid(self, cache_file: str) -> bool:
        """Check if cache file is still valid (not expired)"""
        if not os.path.exists(cache_file):
            return False
        
        try:
            # Check file modification time
            mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            age = datetime.now() - mod_time
            
            return age < timedelta(hours=self.ttl_hours)
        except Exception as e:
            logger.warning(f"Error checking cache validity: {e}")
            return False
    
    def get_cached_events(self, city: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached events for a city if valid"""
        cache_file = self._get_cache_file(city)
        
        if not self._is_cache_valid(cache_file):
            logger.info(f"Cache for {city} is expired or doesn't exist")
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            events = cache_data.get('events', [])
            logger.info(f"Retrieved {len(events)} cached events for {city}")
            return events
            
        except Exception as e:
            logger.error(f"Error reading cache for {city}: {e}")
            return None
    
    def cache_events(self, city: str, events: List[Dict[str, Any]]) -> bool:
        """Cache events for a city"""
        cache_file = self._get_cache_file(city)
        
        try:
            cache_data = {
                'city': city,
                'events': events,
                'cached_at': datetime.now().isoformat(),
                'count': len(events)
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cached {len(events)} events for {city}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching events for {city}: {e}")
            return False
    
    def get_cache_age(self, city: str) -> Optional[float]:
        """Get cache age in hours for a city"""
        cache_file = self._get_cache_file(city)
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            age = datetime.now() - mod_time
            return age.total_seconds() / 3600  # Convert to hours
        except Exception:
            return None
    
    def cleanup_old_cache(self):
        """Remove expired cache files to save space"""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    if not self._is_cache_valid(cache_file):
                        os.remove(cache_file)
                        logger.info(f"Removed expired cache: {filename}")
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            total_files = 0
            total_size_mb = 0
            valid_files = 0
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    total_files += 1
                    total_size_mb += os.path.getsize(cache_file) / (1024 * 1024)
                    
                    if self._is_cache_valid(cache_file):
                        valid_files += 1
            
            return {
                'total_files': total_files,
                'valid_files': valid_files,
                'total_size_mb': round(total_size_mb, 2),
                'cache_dir': self.cache_dir,
                'ttl_hours': self.ttl_hours
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}

# Initialize cache manager
cache_manager = CacheManager()

def extract_city_from_query_llm(query: str) -> Optional[str]:
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
            'brooklyn': 'new york',
            'manhattan': 'new york', 
            'queens': 'new york',
            'bronx': 'new york',
            'staten island': 'new york',
            'nyc': 'new york',
            'la': 'los angeles',
            'sf': 'san francisco',
            'bay area': 'san francisco',
            'dc': 'washington',
            'washington dc': 'washington',
            'vegas': 'las vegas',
            'nola': 'new orleans',
            'philly': 'philadelphia',
            'chi': 'chicago'
        }
        
        # Apply city mapping (simplified)
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

def extract_city_from_query(query: str) -> Optional[str]:
    """
    Extract city name from user query using LLM with regex fallback.
    Returns the city name if found, None otherwise.
    """
    # Try LLM extraction first
    llm_result = extract_city_from_query_llm(query)
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

# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "version": "2.1.0", 
        "features": ["smart_caching", "real_time_events", "city_based_cache"]
    }

@app.get("/stats")
async def get_stats():
    """Get system statistics including cache info"""
    try:
        cache_stats = cache_manager.get_cache_stats()
        
        return {
            "status": "active",
            "cache_stats": cache_stats,
            "features": ["smart_caching", "real_time_events", "city_based_cache", "llm_city_extraction"]
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/chat", response_model=ChatResponse)
async def smart_cached_chat(request: ChatRequest):
    """
    Smart cached chat endpoint
    Uses cache when available, fetches fresh data when needed
    """
    try:
        logger.info(f"Smart cached chat request: {request.message}")
        
        # Step 1: Try to extract city from query first (highest priority)
        query_city = extract_city_from_query(request.message)
        logger.info(f"Extracted city from query: '{query_city}'")
        
        # Step 2: Extract city from location (fallback)
        location_city = None
        if request.location:
            # Simple fallback: try to extract city from formatted address
            address = request.location.formatted_address
            if address:
                # Extract city from "City, State, Country" format
                parts = address.split(',')
                if len(parts) >= 1:
                    location_city = parts[0].strip()
        
        # Step 3: Determine which city to use
        logger.info(f"Query city: '{query_city}', Location city: '{location_city}'")
        if query_city:
            city = query_city
            logger.info(f"Using city from query: {city}")
        elif location_city:
            city = location_city
            logger.info(f"Using city from location: {city}")
        else:
            city = "new york"  # Default fallback
            logger.info("No city found in query or location, defaulting to New York")
        
        logger.info(f"Final city decision: {city}")
        
        # Step 1: Try to get cached events
        cached_events = cache_manager.get_cached_events(city)
        cache_age_hours = cache_manager.get_cache_age(city)
        
        if cached_events:
            logger.info(f"Using cached events for {city} (age: {cache_age_hours:.1f}h)")
            events = cached_events
            cache_used = True
        else:
            logger.info(f"No valid cache for {city}, fetching fresh events")
            # Step 2: Fetch fresh events if no cache
            events = location_crawler.fetch_events_by_city(city, max_pages=2)
            logger.info(f"Fetched {len(events)} fresh events for {city}")
            
            # Step 3: Cache the fresh events
            cache_manager.cache_events(city, events)
            cache_used = False
            cache_age_hours = 0
        
        # Step 4: LLM-powered intelligent event search
        logger.info(f"Starting LLM search for query: '{request.message}' with {len(events)} events")
        top_events = await intelligent_event_search(request.message, events)
        logger.info(f"LLM search returned {len(top_events)} events")
        
        # Debug: Check if events have LLM scores
        if top_events:
            first_event = top_events[0]
            logger.info(f"First event has llm_scores: {first_event.get('llm_scores', 'None')}")
            logger.info(f"First event relevance_score: {first_event.get('relevance_score', 'None')}")
        
        # Step 5: Format recommendations
        formatted_recommendations = []
        for event in top_events:
            formatted_recommendations.append({
                "type": "event",
                "data": {
                    **event,  # This includes llm_scores and relevance_score
                    "source": "cached" if cache_used else "realtime"
                },
                "relevance_score": event.get('relevance_score', 0.5),  # Keep for backward compatibility
                "explanation": f"Event in {city.title()}: {event.get('title', 'Unknown Event')}"
            })
        
        # Step 6: Generate response message
        if top_events:
            response_message = f"🎉 Found {len(top_events)} events in {city.title()} that match your search! Check out the recommendations below ↓"
        else:
            response_message = f"😔 I couldn't find any events in {city.title()} matching your query. Try asking about 'fashion events', 'music concerts', 'halloween parties', or 'free events'."
        
        return ChatResponse(
            message=response_message,
            recommendations=formatted_recommendations,
            llm_provider_used=request.llm_provider,
            cache_used=cache_used,
            cache_age_hours=cache_age_hours
        )
        
    except Exception as e:
        logger.error(f"Error in smart cached chat: {e}", exc_info=True)
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

async def intelligent_event_search(query: str, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Use LLM to intelligently search and rank events based on user query
    """
    logger.info(f"intelligent_event_search called with query: '{query}' and {len(events)} events")
    
    if not events:
        logger.info("No events provided, returning empty list")
        return []
    
    # Prepare event summaries for LLM
    event_summaries = []
    for i, event in enumerate(events[:20]):  # Limit to top 20 for performance
        summary = {
            "id": i,
            "title": event.get("title", ""),
            "description": event.get("description", "")[:200] + "..." if len(event.get("description", "")) > 200 else event.get("description", ""),
            "venue": event.get("venue_name", ""),
            "date": event.get("start_datetime", ""),
            "price": event.get("ticket_min_price", ""),
            "categories": ", ".join(event.get("categories", [])),
            "is_free": event.get("is_free", False)
        }
        event_summaries.append(summary)
    
    # Create enhanced prompt for LLM with detailed scoring
    prompt = f"""
You are an expert event recommendation system. Given a user query and a list of events, analyze and score each event.

User Query: "{query}"

Available Events:
{json.dumps(event_summaries, indent=2)}

Please analyze each event and return a JSON object with:
1. "selected_events": Array of event IDs (0-19) ranked by relevance (max 5 events)
2. "scores": Object with event_id as key and detailed scoring as value

For each selected event, provide a score breakdown:
- relevance_score: 1-10 (how well it matches the query)
- title_match: 1-5 (title relevance)
- description_match: 1-5 (description relevance) 
- category_match: 1-5 (category relevance)
- venue_appropriateness: 1-5 (venue suitability)
- price_consideration: 1-5 (price appropriateness)
- user_intent_match: 1-5 (matches user intent)
- overall_quality: 1-5 (event quality/popularity)

Return format:
{{
  "selected_events": [id1, id2, id3, id4, id5],
  "scores": {{
    "id1": {{"relevance_score": 9, "title_match": 5, "description_match": 4, "category_match": 5, "venue_appropriateness": 4, "price_consideration": 3, "user_intent_match": 5, "overall_quality": 4}},
    "id2": {{"relevance_score": 8, "title_match": 4, "description_match": 4, "category_match": 4, "venue_appropriateness": 5, "price_consideration": 4, "user_intent_match": 4, "overall_quality": 4}}
  }}
}}
"""
    
    try:
        logger.info(f"Calling OpenAI API with prompt length: {len(prompt)}")
        
        # Call OpenAI API (updated for v1.0+)
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful event recommendation assistant. Always return valid JSON objects with selected_events and scores."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        logger.info(f"OpenAI API call successful")
        
        # Parse LLM response
        llm_response = response.choices[0].message.content.strip()
        logger.info(f"LLM search response: {llm_response}")
        
        # Parse enhanced LLM response with detailed scoring
        try:
            # Clean the response to extract JSON object
            if "{" in llm_response and "}" in llm_response:
                json_start = llm_response.find("{")
                json_end = llm_response.rfind("}") + 1
                json_str = llm_response[json_start:json_end]
                llm_data = json.loads(json_str)
                
                selected_ids = llm_data.get("selected_events", [])
                scores = llm_data.get("scores", {})
                
                logger.info(f"LLM selected events: {selected_ids}")
                logger.info(f"LLM scores: {scores}")
                
            else:
                # Fallback: try to extract numbers from old format
                import re
                numbers = re.findall(r'\d+', llm_response)
                selected_ids = [int(n) for n in numbers[:5]]
                scores = {}
                logger.warning("Using fallback parsing - no detailed scores available")
            
            # Get selected events with enhanced scoring
            selected_events = []
            for event_id in selected_ids:
                if 0 <= event_id < len(events):
                    event = events[event_id].copy()
                    
                    # Get detailed scores from LLM or use fallback
                    if str(event_id) in scores:
                        event_scores = scores[str(event_id)]
                        event['relevance_score'] = event_scores.get('relevance_score', 10 - selected_ids.index(event_id))
                        event['llm_scores'] = event_scores
                        logger.info(f"Event {event_id} scores: {event_scores}")
                    else:
                        # Fallback scoring
                        event['relevance_score'] = 10 - selected_ids.index(event_id)
                        event['llm_scores'] = {
                            'relevance_score': event['relevance_score'],
                            'title_match': 3,
                            'description_match': 3,
                            'category_match': 3,
                            'venue_appropriateness': 3,
                            'price_consideration': 3,
                            'user_intent_match': 3,
                            'overall_quality': 3
                        }
                    
                    selected_events.append(event)
            
            logger.info(f"LLM selected {len(selected_events)} events with detailed scoring")
            return selected_events
            
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            logger.warning(f"Failed to parse LLM response: {e}, falling back to keyword search")
            logger.warning(f"Raw LLM response was: {llm_response}")
            return fallback_keyword_search(query, events)
            
    except Exception as e:
        logger.error(f"LLM search failed: {e}, falling back to keyword search")
        return fallback_keyword_search(query, events)


def fallback_keyword_search(query: str, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enhanced fallback keyword search with semantic expansion
    """
    query_words = query.lower().split()
    relevant_events = []
    
    # Enhanced semantic keyword expansion
    semantic_expansions = {
        "events": ["event", "show", "concert", "performance", "festival", "conference", "meeting", "gathering", "celebration", "party", "exhibition", "fair", "market", "workshop", "seminar", "talk", "presentation"],
        "nearby": ["local", "close", "near", "around", "in the area", "this area", "here", "local events", "area events"],
        "entertainment": ["fun", "exciting", "enjoyable", "amusing", "lively", "music", "art", "show", "concert", "performance", "comedy", "theater"],
        "fun": ["entertainment", "exciting", "enjoyable", "amusing", "lively", "party", "celebration", "festival"],
        "music": ["concert", "band", "singer", "musical", "live music", "jazz", "rock", "pop", "classical", "acoustic"],
        "art": ["artistic", "gallery", "exhibition", "creative", "visual", "painting", "sculpture", "museum"],
        "food": ["restaurant", "dining", "cuisine", "meal", "culinary", "wine", "tasting", "cooking", "chef"],
        "free": ["complimentary", "no cost", "gratis", "zero cost", "ticket", "admission"],
        "romantic": ["intimate", "couple", "date", "dinner", "wine", "valentine", "love"],
        "family": ["kids", "children", "family-friendly", "all ages", "parent", "child"],
        "night": ["evening", "nighttime", "late", "after dark", "sunset"],
        "weekend": ["saturday", "sunday", "weekend", "saturday", "sunday"],
        "business": ["professional", "networking", "corporate", "meeting", "conference", "tech"],
        "sports": ["athletic", "fitness", "game", "match", "tournament", "running", "cycling"],
        "culture": ["cultural", "heritage", "tradition", "community", "local", "history"]
    }
    
    # Special case: if query is just "events" or "nearby events", return more diverse results
    if query.lower() in ["events", "nearby events", "local events", "what events", "show me events"]:
        logger.info("General events query - returning diverse results")
        # Return top 5 events with some variety
        diverse_events = []
        seen_categories = set()
        
        for event in events:
            categories = event.get('categories', [])
            category_key = tuple(sorted(categories[:3]))  # Use first 3 categories as key
            
            if len(diverse_events) < 5:
                if category_key not in seen_categories or len(diverse_events) < 3:
                    event['relevance_score'] = 5  # High score for general queries
                    diverse_events.append(event)
                    seen_categories.add(category_key)
        
        # Fill remaining slots if we have less than 5
        for event in events:
            if len(diverse_events) >= 5:
                break
            if event not in diverse_events:
                event['relevance_score'] = 3
                diverse_events.append(event)
        
        logger.info(f"Returning {len(diverse_events)} diverse events for general query")
        return diverse_events
    
    # Expand query with semantic synonyms
    expanded_words = set(query_words)
    for word in query_words:
        if word in semantic_expansions:
            expanded_words.update(semantic_expansions[word])
    
    logger.info(f"Enhanced search using {len(expanded_words)} keywords: {list(expanded_words)[:10]}")
    
    for event in events:
        score = 0
        event_text = f"{event.get('title', '')} {event.get('description', '')} {' '.join(event.get('categories', []))}".lower()
        
        # Score based on expanded keywords
        for word in expanded_words:
            if word in event_text:
                score += 1
            if word in event.get('title', '').lower():
                score += 3  # Higher weight for title matches
            if word in event.get('venue_name', '').lower():
                score += 2
            if word in ' '.join(event.get('categories', [])).lower():
                score += 2
        
        if score > 0:
            event['relevance_score'] = score
            relevant_events.append(event)
    
    relevant_events.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    logger.info(f"Found {len(relevant_events)} relevant events with enhanced search")
    return relevant_events[:5]


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

@app.post("/api/cache/cleanup")
async def cleanup_cache():
    """Manually clean up expired cache files"""
    try:
        cache_manager.cleanup_old_cache()
        stats = cache_manager.get_cache_stats()
        return {
            "success": True,
            "message": "Cache cleanup completed",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error cleaning up cache: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get detailed cache statistics"""
    try:
        stats = cache_manager.get_cache_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    logger.info("Starting Smart Cached RAG Local Life Assistant...")
    logger.info("Features: City-based caching + Real-time events + Rate limit protection")
    logger.info(f"Cache TTL: {CACHE_TTL_HOURS} hours")
    logger.info(f"Cache directory: {CACHE_DIR}")
    
    # Clean up old cache on startup
    cache_manager.cleanup_old_cache()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
