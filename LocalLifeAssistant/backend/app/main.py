from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
from .routers import chat, recommendations
from .database import get_db_manager
from .models import Event, Restaurant

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
    """Load mock data into ChromaDB on startup"""
    try:
        db_manager = get_db_manager()
        
        # Check if data is already loaded
        stats = db_manager.get_collection_stats()
        if stats["events_count"] > 0 and stats["restaurants_count"] > 0:
            print("Data already loaded in ChromaDB")
            return
        
        # Load events
        events_file = os.path.join(os.path.dirname(__file__), "..", "data", "mock_events.json")
        if os.path.exists(events_file):
            with open(events_file, "r") as f:
                events_data = json.load(f)
            
            events = [Event(**event) for event in events_data]
            db_manager.add_events(events)
            print(f"Loaded {len(events)} events into ChromaDB")
        
        # Load restaurants
        restaurants_file = os.path.join(os.path.dirname(__file__), "..", "data", "mock_restaurants.json")
        if os.path.exists(restaurants_file):
            with open(restaurants_file, "r") as f:
                restaurants_data = json.load(f)
            
            restaurants = [Restaurant(**restaurant) for restaurant in restaurants_data]
            db_manager.add_restaurants(restaurants)
            print(f"Loaded {len(restaurants)} restaurants into ChromaDB")
        
        print("Mock data loaded successfully!")
        
    except Exception as e:
        print(f"Error loading mock data: {str(e)}")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
