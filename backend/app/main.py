#!/usr/bin/env python3
"""
Smart Cached RAG Local Life Assistant
Combines real-time fetching with intelligent city-based caching
"""

import logging
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from .event_service import EventbriteCrawler
from .cache_manager import CacheManager
from .geocoding import GeocodingService, GeocodeRequest, GeocodeResponse, LocationCoordinates
from .search_service import SearchService
from .extraction_service import ExtractionService, UserPreferences
from .usage_tracker import UsageTracker

# Load environment variables from .env file
load_dotenv('../.env') or load_dotenv('.env') or load_dotenv('/app/.env')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Cached RAG Local Life Assistant", version="2.1.0")

# Add CORS middleware
domain_name = os.getenv("DOMAIN_NAME")
render_frontend_url = os.getenv("RENDER_FRONTEND_URL")
logger.info(f"DOMAIN_NAME environment variable: '{domain_name}'")


if domain_name and domain_name not in ["your-domain.com", "localhost", ""]:
    # Production: Allow the actual domain and www subdomain
    allow_origins = [
        f"http://{domain_name}",
        f"https://{domain_name}",
        f"https://www.{domain_name}",
    ]
    logger.info(f"Production CORS configured for domain: {domain_name}")
elif render_frontend_url:
    # Render deployment: Allow the frontend URL
    allow_origins = [render_frontend_url]
else:
    # Development: Allow localhost and common dev ports
    allow_origins = [
        "http://localhost:3000", 
        "http://localhost:8000", 
        "http://127.0.0.1:3000", 
        "http://127.0.0.1:8000", 
        "http://localhost:5173", 
        "http://127.0.0.1:5173"
    ]

# Log CORS configuration for debugging
logger.info(f"DOMAIN_NAME environment variable: '{domain_name}'")
logger.info(f"RENDER_FRONTEND_URL environment variable: '{render_frontend_url}'")
logger.info(f"Allowed origins: {allow_origins}")


logger.info(f"Allowed origins: {allow_origins}")

# Manual CORS middleware - simplified and more explicit
@app.middleware("http")
async def cors_middleware(request, call_next):
    origin = request.headers.get("origin")
    logger.info(f"CORS middleware - Origin: {origin}, Allowed origins: {allow_origins}")
    
    # Handle preflight requests
    if request.method == "OPTIONS":
        response = Response()
        # Set the origin header if it's in the allowed origins
        if origin in allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            logger.info(f"OPTIONS: Set Access-Control-Allow-Origin to {origin}")
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "600"
        return response
    
    # Handle actual requests
    response = await call_next(request)
    # Set the origin header if it's in the allowed origins
    if origin in allow_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        logger.info(f"GET/POST: Set Access-Control-Allow-Origin to {origin}")
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Add middleware to log CORS requests for debugging
@app.middleware("http")
async def log_cors_requests(request: Request, call_next):
    origin = request.headers.get("origin")
    logger.info(f"CORS middleware - Origin: {origin}, Allowed origins: {allow_origins}")
    response = await call_next(request)
    return response

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, Any]] = []
    llm_provider: str = "openai"
    location: Optional[LocationCoordinates] = None
    user_preferences: Optional[UserPreferences] = None
    is_initial_response: bool = False  # Flag for welcome message response
    user_id: str  # NEW - Required anonymous user ID

class ChatResponse(BaseModel):
    message: str
    recommendations: List[Dict[str, Any]] = []
    llm_provider_used: str
    cache_used: bool = False
    cache_age_hours: Optional[float] = None
    extracted_preferences: Optional[UserPreferences] = None  # NEW
    extraction_summary: Optional[str] = None  # NEW
    usage_stats: Optional[Dict[str, Any]] = None  # NEW - Trial info
    trial_exceeded: bool = False  # NEW - Flag to show registration prompt

# Initialize services
event_crawler = EventbriteCrawler()
cache_manager = CacheManager()
geocoding_service = GeocodingService()
search_service = SearchService()
extraction_service = ExtractionService()
usage_tracker = UsageTracker()

# Cache configuration
CACHE_TTL_HOURS = 6  # Cache events for 6 hours

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
        user_id = request.user_id
        
        # Check trial limit for anonymous users
        if user_id.startswith("user_"):  # Anonymous user
            if usage_tracker.check_trial_limit(user_id):
                # Trial exceeded - return prompt to register
                trial_limit = usage_tracker.trial_limit
                return ChatResponse(
                    message=f"🔒 You've reached your free trial limit of {trial_limit} interactions! Please register to continue using our service and keep your conversation history.",
                    recommendations=[],
                    llm_provider_used=request.llm_provider,
                    cache_used=False,
                    trial_exceeded=True,
                    usage_stats=usage_tracker.get_usage(user_id),
                    conversation_id="temp"
                )
        
        # Increment usage for anonymous users
        if user_id.startswith("user_"):
            usage_stats = usage_tracker.increment_usage(user_id)
        else:
            usage_stats = None
        
        # Step 1: Extract user preferences if this is an initial response
        extracted_preferences = None
        if request.is_initial_response:
            logger.info("Initial response detected, extracting user preferences")
            extracted_preferences = extraction_service.extract_user_preferences(request.message)
            logger.info(f"Extracted preferences: {extracted_preferences}")
        
        # Step 2: Determine city to use (prioritize extracted preferences)
        city = None
        location_provided = False
        
        # Priority 1: Use extracted location from preferences
        if extracted_preferences and extracted_preferences.location and extracted_preferences.location != "none":
            city = extracted_preferences.location.lower()
            location_provided = True
            logger.info(f"Using city from extracted preferences: {city}")
        
        # Priority 2: Try to extract city from query using existing method
        if not city:
            query_city = extraction_service.extract_location_from_query(request.message)
            if query_city:
                city = query_city.lower()
                location_provided = True
                logger.info(f"Using city from query extraction: {city}")
        
        # Priority 3: Extract city from location coordinates (fallback)
        if not city and request.location:
            address = request.location.formatted_address
            if address:
                parts = address.split(',')
                if len(parts) >= 1:
                    city = parts[0].strip().lower()
                    location_provided = True
                    logger.info(f"Using city from location coordinates: {city}")
        
        # Step 3: Handle missing location for initial responses
        if request.is_initial_response and not location_provided:
            logger.info("No location provided in initial response, asking user for location")
            return ChatResponse(
                message="I'd be happy to help you find events! To give you the best recommendations, could you please tell me which city or area you're interested in? (e.g., 'New York', 'Los Angeles', 'Chicago', or a zipcode)",
                recommendations=[],
                llm_provider_used=request.llm_provider,
                cache_used=False,
                cache_age_hours=None,
                extracted_preferences=extracted_preferences,
                extraction_summary=None
            )
        
        # Step 4: Default fallback for non-initial responses or when location still missing
        if not city:
            city = "new york"
            logger.info("No city found, defaulting to New York")
            # If this is not an initial response and we're defaulting, inform the user
            if not request.is_initial_response:
                logger.info("Informing user that we're defaulting to New York")
        
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
            events = event_crawler.fetch_events_by_city(city, max_pages=2)
            logger.info(f"Fetched {len(events)} fresh events for {city}")
            
            # Step 3: Cache the fresh events
            cache_manager.cache_events(city, events)
            cache_used = False
            cache_age_hours = 0
        
        # Step 4: LLM-powered intelligent event search with preferences
        logger.info(f"Starting LLM search for query: '{request.message}' with {len(events)} events")
        
        # Convert UserPreferences object to dict for search service
        user_preferences_dict = None
        if extracted_preferences:
            user_preferences_dict = {
                'location': extracted_preferences.location,
                'date': extracted_preferences.date,
                'time': extracted_preferences.time,
                'event_type': extracted_preferences.event_type
            }
        
        top_events = await search_service.intelligent_event_search(
            request.message, 
            events, 
            user_preferences=user_preferences_dict
        )
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
        location_note = ""
        if not location_provided and city == "new york":
            location_note = " (I couldn't determine your location, so I'm defaulting to New York)"
        
        if top_events:
            response_message = f"🎉 Found {len(top_events)} events in {city.title()} that match your search!{location_note} Check out the recommendations below ↓"
        else:
            response_message = f"😔 I couldn't find any events in {city.title()} matching your query.{location_note} Try asking about 'fashion events', 'music concerts', 'halloween parties', or 'free events'."
        
        # Step 7: Create extraction summary if preferences were extracted
        extraction_summary = None
        if extracted_preferences:
            summary_parts = []
            if extracted_preferences.location and extracted_preferences.location != "none":
                summary_parts.append(f"📍 {extracted_preferences.location}")
            if extracted_preferences.date and extracted_preferences.date != "none":
                summary_parts.append(f"📅 {extracted_preferences.date}")
            if extracted_preferences.time and extracted_preferences.time != "none":
                summary_parts.append(f"🕐 {extracted_preferences.time}")
            if extracted_preferences.event_type and extracted_preferences.event_type != "none":
                summary_parts.append(f"🎭 {extracted_preferences.event_type}")
            
            if summary_parts:
                extraction_summary = " • ".join(summary_parts)
        
        return ChatResponse(
            message=response_message,
            recommendations=formatted_recommendations,
            llm_provider_used=request.llm_provider,
            cache_used=cache_used,
            cache_age_hours=cache_age_hours,
            extracted_preferences=extracted_preferences,
            extraction_summary=extraction_summary,
            usage_stats=usage_stats,  # NEW
            trial_exceeded=False
        )
        
    except Exception as e:
        logger.error(f"Error in smart cached chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@app.get("/api/usage/{user_id}")
async def get_user_usage(user_id: str):
    """Get usage statistics for a user"""
    usage = usage_tracker.get_usage(user_id)
    return usage

@app.post("/api/users/register")
async def register_user(
    anonymous_user_id: str,
    email: str,
    password: str,
    name: Optional[str] = None
):
    """
    Register a new user and migrate their anonymous data
    
    This is a placeholder - you'll want to add:
    - Password hashing (bcrypt)
    - Email validation
    - Real user database (SQLite, PostgreSQL, etc.)
    """
    # TODO: Implement real user registration
    # 1. Validate email format
    # 2. Hash password
    # 3. Create user in database
    # 4. Generate real user ID
    # 5. Migrate conversations from anonymous_user_id to real_user_id
    # 6. Mark anonymous user as registered
    
    # Placeholder response
    from datetime import datetime
    real_user_id = f"registered_{datetime.now().timestamp()}"
    
    # Mark as registered
    usage_tracker.mark_registered(anonymous_user_id, real_user_id)
    
    return {
        "success": True,
        "user_id": real_user_id,
        "message": "Registration successful! Your conversation history has been preserved."
    }

@app.post("/api/users/login")
async def login_user(email: str, password: str):
    """
    User login endpoint
    
    This is a placeholder - you'll want to add:
    - Password verification
    - JWT token generation
    - Session management
    """
    # TODO: Implement real login
    # 1. Find user by email
    # 2. Verify password
    # 3. Generate JWT token
    # 4. Return token and user info
    
    return {
        "success": True,
        "user_id": "registered_user_123",
        "token": "jwt_token_here",
        "message": "Login successful!"
    }

@app.post("/api/users/migrate-conversations")
async def migrate_conversations(
    anonymous_user_id: str,
    real_user_id: str
):
    """Migrate conversations from anonymous user to registered user"""
    # This will be used by the file storage system
    # Move all conversations from anonymous folder to registered user folder
    
    import shutil
    anonymous_dir = os.path.join("backend/conversations", anonymous_user_id)
    registered_dir = os.path.join("backend/conversations", real_user_id)
    
    if os.path.exists(anonymous_dir):
        os.makedirs(registered_dir, exist_ok=True)
        
        # Copy all conversations
        for filename in os.listdir(anonymous_dir):
            src = os.path.join(anonymous_dir, filename)
            dst = os.path.join(registered_dir, filename)
            shutil.copy2(src, dst)
        
        return {
            "success": True,
            "migrated_conversations": len(os.listdir(anonymous_dir))
        }
    
    return {"success": False, "error": "No conversations to migrate"}

@app.post("/api/geocode", response_model=GeocodeResponse)
async def geocode_location(request: GeocodeRequest):
    """Geocode a location input including US zipcodes"""
    return await geocoding_service.geocode_location(request)

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
    logger.info(f"Cache directory: {cache_manager.cache_dir}")
    
    # Clean up old cache on startup
    cache_manager.cleanup_old_cache()
    
    # Use PORT environment variable for Render deployment, fallback to 8000 for local development
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)