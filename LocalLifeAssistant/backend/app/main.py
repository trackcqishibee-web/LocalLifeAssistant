from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
from .routers import chat, recommendations
from .database import get_db_manager
from .models import Event, Restaurant
from .geocoding import geocoding_service
from .external_data_service import external_data_service

# Create FastAPI app
app = FastAPI(
    title="Local Life Assistant API",
    description="AI-powered local life assistant for events and restaurant recommendations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(recommendations.router)

@app.on_event("startup")
async def startup_event():
    """Load data into ChromaDB on startup - real events + mock restaurants"""
    try:
        db_manager = get_db_manager()
        
        # Check if data is already loaded
        stats = db_manager.get_collection_stats()
        if stats["events_count"] > 0 and stats["restaurants_count"] > 0:
            print("Data already loaded in ChromaDB")
            return
        
        # Load real events from Eventbrite
        print("Fetching real events from Eventbrite...")
        from .events_crawler import fetch_events
        
        try:
            events_data = fetch_events(max_pages=3)  # Fetch 3 pages of events
            events = [Event(**event) for event in events_data]
            db_manager.add_events(events)
            print(f"Loaded {len(events)} real events from Eventbrite into ChromaDB")
        except Exception as e:
            print(f"Error fetching real events, falling back to mock data: {e}")
            # Fallback to mock events
            events_file = os.path.join(os.path.dirname(__file__), "..", "data", "mock_events.json")
            if os.path.exists(events_file):
                with open(events_file, "r") as f:
                    events_data = json.load(f)
                events = [Event(**event) for event in events_data]
                db_manager.add_events(events)
                print(f"Loaded {len(events)} mock events into ChromaDB")
        
        # Load restaurants (still using mock data for now)
        restaurants_file = os.path.join(os.path.dirname(__file__), "..", "data", "mock_restaurants.json")
        if os.path.exists(restaurants_file):
            with open(restaurants_file, "r") as f:
                restaurants_data = json.load(f)
            
            restaurants = [Restaurant(**restaurant) for restaurant in restaurants_data]
            db_manager.add_restaurants(restaurants)
            print(f"Loaded {len(restaurants)} mock restaurants into ChromaDB")
        
        print("Data loaded successfully!")
        
    except Exception as e:
        print(f"Error loading data: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Local Life Assistant API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_manager = get_db_manager()
        stats = db_manager.get_collection_stats()
        
        return {
            "status": "healthy",
            "database": "connected",
            "events_count": stats["events_count"],
            "restaurants_count": stats["restaurants_count"]
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/stats")
async def get_stats():
    """Get database statistics"""
    try:
        db_manager = get_db_manager()
        stats = db_manager.get_collection_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.post("/api/geocode")
async def geocode_location(request: dict):
    """Geocode a location input (zipcode or city, state) to coordinates"""
    try:
        input_text = request.get("input_text")
        if not input_text:
            raise HTTPException(status_code=400, detail="input_text is required")

        # Geocode the location
        result = geocoding_service.geocode_location(input_text)
        
        if result:
            latitude, longitude, formatted_address = result
            #print(f"Latitude: {latitude}, Longitude: {longitude}")
            # Call external data service with coordinates (placeholder)
            await external_data_service.get_location_data(
                latitude=latitude,
                longitude=longitude,
                location_context=formatted_address
            )
            
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
