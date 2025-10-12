import re
from typing import List, Dict, Any, Optional, Tuple
from .models import Event, Restaurant, RecommendationItem, EventType, ChatMessage
from .database import get_db_manager
from .llm_provider import MultiLLMProvider

class IntentParser:
    """Parse user intent from natural language queries"""
    
    def __init__(self):
        self.event_keywords = [
            "event", "events", "activity", "activities", "concert", "show", "performance",
            "workshop", "class", "meeting", "conference", "festival", "party", "gathering",
            "networking", "social", "music", "art", "sports", "comedy", "theater"
        ]
        self.restaurant_keywords = [
            "restaurant", "food", "dining", "eat", "lunch", "dinner", "breakfast", "brunch",
            "cuisine", "meal", "cafe", "bar", "pub", "bistro", "cafe", "eatery"
        ]
        self.location_keywords = [
            "in", "near", "around", "close to", "downtown", "uptown", "midtown", "brooklyn",
            "queens", "manhattan", "bronx", "hoboken", "jersey city"
        ]
        self.price_keywords = {
            "cheap": ["cheap", "affordable", "budget", "inexpensive", "low-cost"],
            "expensive": ["expensive", "upscale", "fine dining", "premium", "high-end"],
            "free": ["free", "no cost", "complimentary"]
        }
        self.time_keywords = [
            "today", "tomorrow", "this week", "next week", "weekend", "evening", "morning",
            "afternoon", "night", "tonight"
        ]

    def parse_intent(self, query: str) -> Dict[str, Any]:
        """Parse user query to extract intent and preferences"""
        query_lower = query.lower()
        
        intent = {
            "type": None,  # "event" or "restaurant"
            "location": None,
            "price_preference": None,
            "time_preference": None,
            "categories": [],
            "keywords": []
        }
        
        # Determine if looking for events or restaurants
        event_score = sum(1 for keyword in self.event_keywords if keyword in query_lower)
        restaurant_score = sum(1 for keyword in self.restaurant_keywords if keyword in query_lower)
        
        if event_score > restaurant_score:
            intent["type"] = "event"
        elif restaurant_score > event_score:
            intent["type"] = "restaurant"
        else:
            # Ambiguous - will search both
            intent["type"] = "both"
        
        # Extract location
        for keyword in self.location_keywords:
            if keyword in query_lower:
                # Extract location after the keyword
                pattern = rf"{keyword}\s+([a-zA-Z\s]+)"
                match = re.search(pattern, query_lower)
                if match:
                    intent["location"] = match.group(1).strip()
                    break
        
        # Extract price preference
        for price_level, keywords in self.price_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    intent["price_preference"] = price_level
                    break
        
        # Extract time preference
        for keyword in self.time_keywords:
            if keyword in query_lower:
                intent["time_preference"] = keyword
                break
        
        # Extract categories (basic keyword matching)
        category_mapping = {
            "music": ["music", "concert", "band", "jazz", "rock", "classical"],
            "food": ["food", "cooking", "culinary", "wine", "tasting"],
            "sports": ["sports", "basketball", "football", "soccer", "tennis"],
            "art": ["art", "gallery", "exhibition", "museum", "painting"],
            "technology": ["tech", "startup", "coding", "programming", "AI"],
            "wellness": ["yoga", "fitness", "meditation", "wellness", "health"],
            "networking": ["networking", "professional", "business", "career"],
            "comedy": ["comedy", "stand-up", "humor", "laugh"],
            "italian": ["italian", "pasta", "pizza", "trattoria"],
            "japanese": ["japanese", "sushi", "ramen", "sashimi"],
            "mexican": ["mexican", "taco", "burrito", "margarita"],
            "chinese": ["chinese", "dim sum", "wok", "noodles"],
            "indian": ["indian", "curry", "spicy", "tandoor"],
            "french": ["french", "bistro", "wine", "escargot"],
            "vegan": ["vegan", "vegetarian", "plant-based", "organic"]
        }
        
        for category, keywords in category_mapping.items():
            for keyword in keywords:
                if keyword in query_lower:
                    intent["categories"].append(category)
        
        # Extract general keywords
        words = query_lower.split()
        intent["keywords"] = [word for word in words if len(word) > 3]
        
        return intent

class RAGEngine:
    """Retrieval-Augmented Generation engine for recommendations"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.llm_provider = MultiLLMProvider()
        self.intent_parser = IntentParser()

    def _create_search_filters(self, intent: Dict[str, Any]) -> Optional[Dict]:
        """Create ChromaDB filters based on parsed intent"""
        filters = {}
        
        if intent.get("location"):
            # This would need more sophisticated location matching
            # For now, we'll use the location in the search query
            pass
        
        if intent.get("price_preference") == "free":
            filters["is_free"] = True
        elif intent.get("price_preference") == "cheap":
            # Would need to implement price range filtering
            pass
        
        return filters if filters else None

    def _format_context_for_llm(self, results: List[Dict], intent: Dict) -> str:
        """Format search results into context for LLM"""
        context_parts = []
        
        if results:
            context_parts.append("Here are some relevant recommendations based on your query:")
            
            for i, result in enumerate(results[:5], 1):  # Limit to top 5
                metadata = result.get("metadata", {})
                distance = result.get("distance", 0)
                relevance_score = 1 - distance  # Convert distance to relevance
                
                if metadata.get("type") == "event":
                    context_parts.append(f"""
{i}. {metadata.get('title', 'Unknown Event')}
   Description: {metadata.get('description', 'No description available')}
   Date: {metadata.get('start_datetime', 'TBD')}
   Location: {metadata.get('venue_name', 'TBD')}, {metadata.get('venue_city', 'TBD')}
   Price: {'Free' if metadata.get('is_free') else f"${metadata.get('ticket_min_price', 'TBD')}"}
   Categories: {', '.join(metadata.get('categories', []))}
   Relevance: {relevance_score:.2f}
""")
                else:  # restaurant
                    context_parts.append(f"""
{i}. {metadata.get('name', 'Unknown Restaurant')}
   Description: {metadata.get('description', 'No description available')}
   Cuisine: {metadata.get('cuisine_type', 'Unknown')}
   Price Range: {metadata.get('price_range', 'TBD')}
   Rating: {metadata.get('rating', 'N/A')}/5
   Location: {metadata.get('venue_name', 'TBD')}, {metadata.get('venue_city', 'TBD')}
   Categories: {', '.join(metadata.get('categories', []))}
   Relevance: {relevance_score:.2f}
""")
        
        return "\n".join(context_parts)

    def _create_recommendation_items(self, results: List[Dict]) -> List[RecommendationItem]:
        """Convert search results to RecommendationItem objects"""
        items = []
        
        for result in results:
            metadata = result.get("metadata", {})
            distance = result.get("distance", 0)
            relevance_score = 1 - distance
            
            if metadata.get("type") == "event":
                # Convert metadata back to Event object
                event_data = {
                    "event_id": metadata.get("id", ""),
                    "title": metadata.get("title", ""),
                    "description": metadata.get("description", ""),
                    "start_datetime": metadata.get("start_datetime", ""),
                    "end_datetime": metadata.get("end_datetime", ""),
                    "timezone": "America/New_York",
                    "venue_name": metadata.get("venue_name", ""),
                    "venue_city": metadata.get("venue_city", ""),
                    "venue_country": metadata.get("venue_country", ""),
                    "latitude": metadata.get("latitude", 0.0),
                    "longitude": metadata.get("longitude", 0.0),
                    "organizer_name": metadata.get("organizer_name", ""),
                    "organizer_id": metadata.get("organizer_id", ""),
                    "ticket_min_price": metadata.get("ticket_min_price", ""),
                    "ticket_max_price": metadata.get("ticket_max_price", ""),
                    "is_free": metadata.get("is_free", False),
                    "categories": metadata.get("categories", []),
                    "image_url": metadata.get("image_url", ""),
                    "event_url": metadata.get("event_url", ""),
                    "attendee_count": metadata.get("attendee_count", 0),
                    "source": metadata.get("source", "")
                }
                
                event = Event(**event_data)
                items.append(RecommendationItem(
                    type=EventType.EVENT,
                    data=event,
                    relevance_score=relevance_score,
                    explanation=f"Relevant event matching your interests"
                ))
            else:  # restaurant
                restaurant_data = {
                    "restaurant_id": metadata.get("id", ""),
                    "name": metadata.get("name", ""),
                    "description": metadata.get("description", ""),
                    "cuisine_type": metadata.get("cuisine_type", ""),
                    "price_range": metadata.get("price_range", ""),
                    "rating": metadata.get("rating", 0.0),
                    "venue_name": metadata.get("venue_name", ""),
                    "venue_city": metadata.get("venue_city", ""),
                    "venue_country": metadata.get("venue_country", ""),
                    "latitude": metadata.get("latitude", 0.0),
                    "longitude": metadata.get("longitude", 0.0),
                    "phone": metadata.get("phone", ""),
                    "website": metadata.get("website", ""),
                    "categories": metadata.get("categories", []),
                    "image_url": metadata.get("image_url", ""),
                    "is_open_now": metadata.get("is_open_now", True),
                    "source": metadata.get("source", "")
                }
                
                restaurant = Restaurant(**restaurant_data)
                items.append(RecommendationItem(
                    type=EventType.RESTAURANT,
                    data=restaurant,
                    relevance_score=relevance_score,
                    explanation=f"Restaurant matching your preferences"
                ))
        
        return items

    async def get_recommendations(
        self, 
        query: str, 
        conversation_history: List[ChatMessage] = None,
        llm_provider: str = None,
        max_results: int = 5
    ) -> Tuple[str, List[RecommendationItem]]:
        """Get recommendations using RAG approach"""
        
        # Parse user intent
        intent = self.intent_parser.parse_intent(query)
        
        # Create search filters
        filters = self._create_search_filters(intent)
        
        # Search in database
        search_results = []
        
        if intent["type"] in ["event", "both"]:
            event_results = self.db_manager.search_events(
                query=query, 
                n_results=max_results, 
                where=filters
            )
            search_results.extend(event_results)
        
        if intent["type"] in ["restaurant", "both"]:
            restaurant_results = self.db_manager.search_restaurants(
                query=query, 
                n_results=max_results, 
                where=filters
            )
            search_results.extend(restaurant_results)
        
        # Sort by relevance score
        search_results.sort(key=lambda x: 1 - x.get("distance", 1), reverse=True)
        search_results = search_results[:max_results]
        
        # Format context for LLM
        context = self._create_context_for_llm(search_results, intent)
        
        # Create LLM prompt
        prompt = f"""
Based on the user's query: "{query}"

{context}

Please provide a helpful response that:
1. Acknowledges what the user is looking for
2. Explains why these recommendations are relevant
3. Provides additional helpful information or suggestions
4. Asks if they need more specific information

Be conversational and helpful. If no relevant results were found, suggest alternative search terms or ask for clarification.
"""
        
        # Generate response using LLM
        try:
            response = await self.llm_provider.generate_response(
                prompt=prompt,
                context="",
                provider_name=llm_provider
            )
        except Exception as e:
            response = f"I found some recommendations for you, but I'm having trouble generating a detailed response. Here are the results I found: {context}"
        
        # Convert results to RecommendationItem objects
        recommendations = self._create_recommendation_items(search_results)
        
        return response, recommendations

    async def chat_with_context(
        self, 
        message: str, 
        conversation_history: List[ChatMessage] = None,
        llm_provider: str = None
    ) -> Tuple[str, List[RecommendationItem]]:
        """Handle chat with conversation context"""
        
        # Build conversation context
        context_parts = []
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages
                context_parts.append(f"{msg.role}: {msg.content}")
        
        # Add current message
        context_parts.append(f"user: {message}")
        
        # Get recommendations
        response, recommendations = await self.get_recommendations(
            query=message,
            conversation_history=conversation_history,
            llm_provider=llm_provider
        )
        
        return response, recommendations
