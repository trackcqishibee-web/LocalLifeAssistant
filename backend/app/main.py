#!/usr/bin/env python3
"""
Smart Cached RAG Local Life Assistant
Combines real-time fetching with intelligent city-based caching
"""

import logging
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from .event_service import EventbriteCrawler
from .cache_manager import CacheManager
from .geocoding import GeocodingService, GeocodeRequest, GeocodeResponse, LocationCoordinates
from .search_service import SearchService

# Load environment variables from .env file
load_dotenv('../.env') or load_dotenv('.env') or load_dotenv('/app/.env')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Cached RAG Local Life Assistant", version="2.1.0")

# Add CORS middleware
domain_name = os.getenv("DOMAIN_NAME")
logger.info(f"DOMAIN_NAME environment variable: '{domain_name}'")

if domain_name and domain_name not in ["your-domain.com", "localhost", ""]:
    # Production: Allow the actual domain and www subdomain
    allow_origins = [
        f"http://{domain_name}",
        f"https://{domain_name}",
        f"https://www.{domain_name}",
    ]
    logger.info(f"Production CORS configured for domain: {domain_name}")
else:
    # Development: Allow localhost origins (cannot use * with credentials)
    allow_origins = [
        "http://localhost:3000",
        "http://localhost:8000", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:5173"
    ]
    logger.info("Development CORS configured for localhost")

logger.info(f"Allowed origins: {allow_origins}")

# Manual CORS middleware - simplified and more explicit
@app.middleware("http")
async def cors_middleware(request, call_next):
    origin = request.headers.get("origin")
    logger.info(f"CORS middleware - Origin: {origin}, Allowed origins: {allow_origins}")
    
    # Handle preflight requests
    if request.method == "OPTIONS":
        response = Response()
        # Always set the origin header for localhost:3000 in development
        if origin == "http://localhost:3000":
            response.headers["Access-Control-Allow-Origin"] = origin
            logger.info(f"OPTIONS: Set Access-Control-Allow-Origin to {origin}")
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "600"
        return response
    
    # Handle actual requests
    response = await call_next(request)
    # Always set the origin header for localhost:3000 in development
    if origin == "http://localhost:3000":
        response.headers["Access-Control-Allow-Origin"] = origin
        logger.info(f"GET/POST: Set Access-Control-Allow-Origin to {origin}")
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Pydantic models
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

# Initialize services
event_crawler = EventbriteCrawler()
cache_manager = CacheManager()
geocoding_service = GeocodingService()
search_service = SearchService()

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
        
        # Step 1: Try to extract city from query first (highest priority)
        query_city = geocoding_service.extract_city_from_query(request.message)
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
            events = event_crawler.fetch_events_by_city(city, max_pages=2)
            logger.info(f"Fetched {len(events)} fresh events for {city}")
            
            # Step 3: Cache the fresh events
            cache_manager.cache_events(city, events)
            cache_used = False
            cache_age_hours = 0
        
        # Step 4: LLM-powered intelligent event search
        logger.info(f"Starting LLM search for query: '{request.message}' with {len(events)} events")
        top_events = await search_service.intelligent_event_search(request.message, events)
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
    
    uvicorn.run(app, host="0.0.0.0", port=8000)