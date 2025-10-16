from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..models import RecommendationRequest, EventType
from ..rag_engine import RAGEngine
from ..database import get_db_manager

router = APIRouter(prefix="/api", tags=["recommendations"])

# Initialize RAG engine
rag_engine = RAGEngine()

@router.get("/recommendations")
async def get_recommendations(
    query: str = Query(..., description="Search query for recommendations"),
    type: Optional[str] = Query(None, description="Type: 'event' or 'restaurant'"),
    location: Optional[str] = Query(None, description="Location filter"),
    category: Optional[str] = Query(None, description="Category filter"),
    max_results: int = Query(5, description="Maximum number of results"),
    llm_provider: str = Query("openai", description="LLM provider to use")
):
    """
    Direct recommendations endpoint with query parameters
    """
    try:
        # Create recommendation request
        request = RecommendationRequest(
            query=query,
            type=EventType(type) if type else None,
            location=location,
            category=category,
            max_results=max_results
        )
        
        # Get recommendations using RAG
        response, recommendations = await rag_engine.get_recommendations(
            query=query,
            llm_provider=llm_provider,
            max_results=max_results
        )
        
        return {
            "query": query,
            "message": response,
            "recommendations": [
                {
                    "type": rec.type,
                    "data": rec.data.dict(),
                    "relevance_score": rec.relevance_score,
                    "explanation": rec.explanation
                }
                for rec in recommendations
            ],
            "total_results": len(recommendations),
            "llm_provider_used": llm_provider
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@router.get("/events")
async def get_events(
    query: str = Query(..., description="Search query for events"),
    location: Optional[str] = Query(None, description="Location filter"),
    category: Optional[str] = Query(None, description="Category filter"),
    max_results: int = Query(5, description="Maximum number of results")
):
    """
    Get events only
    """
    try:
        db_manager = get_db_manager()
        
        # Create filters
        filters = {}
        if location:
            # Simple location filtering (would need more sophisticated matching)
            pass
        
        # Search events
        results = db_manager.search_events(
            query=query,
            n_results=max_results,
            where=filters
        )
        
        return {
            "query": query,
            "events": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting events: {str(e)}")

@router.get("/restaurants")
async def get_restaurants(
    query: str = Query(..., description="Search query for restaurants"),
    location: Optional[str] = Query(None, description="Location filter"),
    cuisine: Optional[str] = Query(None, description="Cuisine filter"),
    max_results: int = Query(5, description="Maximum number of results")
):
    """
    Get restaurants only
    """
    try:
        db_manager = get_db_manager()
        
        # Create filters
        filters = {}
        if cuisine:
            filters["cuisine_type"] = cuisine
        
        # Search restaurants
        results = db_manager.search_restaurants(
            query=query,
            n_results=max_results,
            where=filters
        )
        
        return {
            "query": query,
            "restaurants": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting restaurants: {str(e)}")

@router.get("/search")
async def search_all(
    query: str = Query(..., description="Search query"),
    max_results: int = Query(5, description="Maximum number of results per type")
):
    """
    Search both events and restaurants
    """
    try:
        db_manager = get_db_manager()
        
        # Search both
        results = db_manager.search_all(
            query=query,
            n_results=max_results
        )
        
        return {
            "query": query,
            "events": results["events"],
            "restaurants": results["restaurants"],
            "total_events": len(results["events"]),
            "total_restaurants": len(results["restaurants"])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching: {str(e)}")
