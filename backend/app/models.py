from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    EVENT = "event"
    RESTAURANT = "restaurant"

class Event(BaseModel):
    event_id: str
    title: str
    description: str
    start_datetime: str
    end_datetime: str
    timezone: str
    venue_name: str
    venue_city: str
    venue_country: str
    latitude: float
    longitude: float
    organizer_name: str
    organizer_id: str
    ticket_min_price: str
    ticket_max_price: str
    is_free: bool
    categories: List[str]
    image_url: str
    event_url: str
    attendee_count: int
    source: str

class Restaurant(BaseModel):
    restaurant_id: str
    name: str
    description: str
    cuisine_type: str
    price_range: str  # $, $$, $$$, $$$$
    rating: float
    venue_name: str
    venue_city: str
    venue_country: str
    latitude: float
    longitude: float
    phone: str
    website: str
    categories: List[str]
    image_url: str
    is_open_now: bool
    source: str

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[ChatMessage] = []
    llm_provider: Optional[str] = None

class RecommendationItem(BaseModel):
    type: EventType
    data: Union[Event, Restaurant]
    relevance_score: float
    explanation: str

class ChatResponse(BaseModel):
    message: str
    recommendations: List[RecommendationItem] = []
    llm_provider_used: str

class RecommendationRequest(BaseModel):
    query: str
    type: Optional[EventType] = None
    location: Optional[str] = None
    category: Optional[str] = None
    max_results: int = 5
