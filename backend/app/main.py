"""
Simplified LocalLifeAssistant backend for testing events integration
This version works without ChromaDB dependencies
"""

from dotenv import load_dotenv
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Load environment variables
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .events_crawler import EventbriteCrawler
from .external_data_service import ExternalDataService
from .geocoding import geocoding_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Local Life Assistant API (Simplified)",
    description="AI-powered local life assistant for events and restaurant recommendations - Events Only Version",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
events_crawler = EventbriteCrawler()
external_service = ExternalDataService()

# In-memory storage for events (instead of ChromaDB)
events_cache: List[Dict[str, Any]] = []
cache_timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, Any]] = []
    llm_provider: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    recommendations: List[Dict[str, Any]] = []
    llm_provider_used: str

class RecommendationRequest(BaseModel):
    query: str
    type: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = None
    max_results: int = 5

def load_events():
    """Load events into cache"""
    global events_cache, cache_timestamp
    
    try:
        logger.info("Loading events from Eventbrite...")
        events = events_crawler.fetch_events(max_pages=3)
        events_cache = events
        cache_timestamp = datetime.now()
        logger.info(f"Loaded {len(events)} events into cache")
        return True
    except Exception as e:
        logger.error(f"Error loading events: {e}")
        return False

def search_events(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Simple text-based event search"""
    if not events_cache:
        logger.info("No events in cache")
        return []
    
    query_lower = query.lower()
    # Split query into individual words for better matching
    query_words = query_lower.split()
    logger.info(f"Searching for words {query_words} in {len(events_cache)} events")
    results = []
    
    for event in events_cache:
        score = 0
        
        # Check each word in the query
        for word in query_words:
            # Check title
            if word in event.get('title', '').lower():
                score += 3
            
            # Check description
            if word in event.get('description', '').lower():
                score += 2
            
            # Check categories
            for category in event.get('categories', []):
                if word in category.lower():
                    score += 1
            
            # Check venue
            if word in event.get('venue_name', '').lower():
                score += 1
            
            # Special handling for common terms
            if word == "free" and event.get('is_free'):
                score += 2
            elif word == "free" and "free" in event.get('title', '').lower():
                score += 2
        
        if score > 0:
            results.append((score, event))
    
    # Sort by score and return top results
    results.sort(key=lambda x: x[0], reverse=True)
    logger.info(f"Found {len(results)} events with scores: {[score for score, _ in results[:5]]}")
    return [event for score, event in results[:max_results]]

@app.on_event("startup")
async def startup_event():
    """Load events on startup"""
    logger.info("Starting LocalLifeAssistant (Simplified Version)...")
    load_events()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Local Life Assistant API (Simplified)", 
        "status": "running",
        "version": "1.0.0",
        "features": ["events", "geocoding"],
        "note": "This is a simplified version for testing events integration"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "in-memory cache",
        "events_count": len(events_cache),
        "cache_timestamp": cache_timestamp.isoformat() if cache_timestamp else None,
        "services": {
            "events": "active",
            "geocoding": "active",
            "chromadb": "disabled (simplified version)"
        }
    }

@app.get("/stats")
async def get_stats():
    """Get database statistics"""
    return {
        "events_count": len(events_cache),
        "restaurants_count": 0,
        "cache_timestamp": cache_timestamp.isoformat() if cache_timestamp else None,
        "note": "Restaurants not available in simplified version"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Simplified chat endpoint"""
    try:
        # Simple keyword-based responses
        message_lower = request.message.lower()
        
        # Always try to search for events first
        logger.info(f"Searching for events with query: {request.message}")
        recommendations = search_events(request.message, max_results=5)
        logger.info(f"Found {len(recommendations)} recommendations")
        
        if recommendations:
            # Simple, clean message for the chat
            response_message = f"🎉 I found {len(recommendations)} events that match your search! Check out the recommendations below ↓"
            
            # Format recommendations for frontend
            formatted_recommendations = []
            for event in recommendations:
                formatted_recommendations.append({
                    "type": "event",
                    "data": event,
                    "relevance_score": 0.9,  # High relevance since they matched the search
                    "explanation": f"This event matches your search for '{request.message}' based on title, description, or categories."
                })
        else:
            response_message = "😔 I couldn't find any events matching your query. Try asking about 'fashion events', 'music concerts', 'halloween parties', or 'free events'."
            formatted_recommendations = []
        
        return ChatResponse(
            message=response_message,
            recommendations=formatted_recommendations,
            llm_provider_used="simplified"
        )
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@app.post("/api/chat/simple")
async def simple_chat(message: str, llm_provider: str = "simplified"):
    """Simplified chat endpoint"""
    request = ChatRequest(message=message, llm_provider=llm_provider)
    response = await chat(request)
    return {
        "message": response.message,
        "recommendations": response.recommendations,
        "llm_provider_used": response.llm_provider_used
    }

@app.get("/api/recommendations")
async def get_recommendations(
    query: str,
    type: Optional[str] = None,
    location: Optional[str] = None,
    category: Optional[str] = None,
    max_results: int = 5
):
    """Get event recommendations"""
    try:
        if not events_cache:
            load_events()
        
        recommendations = search_events(query, max_results)
        
        return {
            "query": query,
            "recommendations": recommendations,
            "total_found": len(recommendations),
            "source": "eventbrite"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@app.get("/api/events")
async def get_events(query: str = "", max_results: int = 10):
    """Get events only"""
    try:
        if not events_cache:
            load_events()
        
        if query:
            events = search_events(query, max_results)
        else:
            events = events_cache[:max_results]
        
        return {
            "events": events,
            "total_found": len(events),
            "query": query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting events: {str(e)}")

@app.get("/api/restaurants")
async def get_restaurants(query: str = "", max_results: int = 10):
    """Restaurants not available in simplified version"""
    return {
        "restaurants": [],
        "total_found": 0,
        "message": "Restaurants not available in simplified version. Full version with ChromaDB required."
    }

@app.get("/api/test-search")
async def test_search(query: str = "fashion"):
    """Test search function directly"""
    try:
        recommendations = search_events(query, max_results=5)
        return {
            "query": query,
            "recommendations": recommendations,
            "total_found": len(recommendations),
            "events_cache_size": len(events_cache)
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/geocode")
async def geocode_location(request: dict):
    """Geocode a location input"""
    try:
        input_text = request.get("input_text")
        if not input_text:
            raise HTTPException(status_code=400, detail="input_text is required")

        result = geocoding_service.geocode_location(input_text)
        
        if result:
            latitude, longitude, formatted_address = result
            return {
                "success": True,
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "formatted_address": formatted_address
                },
                "error_message": None
            }
        else:
            return {
                "success": False,
                "coordinates": None,
                "error_message": f"Could not geocode location: '{input_text}'"
            }
            
    except Exception as e:
        return {
            "success": False,
            "coordinates": None,
            "error_message": f"Error geocoding location: {str(e)}"
        }

@app.post("/api/refresh-events")
async def refresh_events():
    """Manually refresh events cache"""
    try:
        success = load_events()
        if success:
            return {
                "success": True,
                "message": f"Refreshed {len(events_cache)} events",
                "timestamp": cache_timestamp.isoformat() if cache_timestamp else None
            }
        else:
            return {
                "success": False,
                "message": "Failed to refresh events"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing events: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
