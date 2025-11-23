#!/usr/bin/env python3
"""
Intelligent search and LLM integration for event recommendations
"""

import os
import json
import openai
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class SearchService:
    """Service for intelligent event search using LLM"""
    
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openrouter_api_key:
            self.client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.openrouter_api_key)
        elif self.openai_api_key:
            self.client = openai.OpenAI(api_key=self.openai_api_key)
        else:
            raise ValueError("Either OPENROUTER_API_KEY or OPENAI_API_KEY environment variable is required")

    async def intelligent_event_search(self, query: str, events: List[Dict[str, Any]], user_preferences: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Use LLM to intelligently search and rank events based on user query
        """
        logger.info(f"intelligent_event_search called with query: '{query}' and {len(events)} events")
        
        if user_preferences:
            logger.info(f"User preferences received in search_service: {user_preferences}")
        else:
            logger.warning("No user preferences received in search_service - user_preferences is None")
        
        if not events:
            logger.info("No events provided, returning empty list")
            return []
        
        # Prepare event summaries for LLM
        event_summaries = []
        for i, event in enumerate(events):
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
        
        # Create enhanced prompt for LLM with detailed scoring and user preferences
        preferences_text = ""
        if user_preferences:
            location = user_preferences.get('location', 'Not specified')
            date = user_preferences.get('date', 'Not specified')
            time = user_preferences.get('time', 'Not specified')
            event_type = user_preferences.get('event_type', 'Not specified')
            
            preferences_text = f"""
User Preferences:
- Location: {location}
- Date: {date}
- Time: {time}
- Event Type: {event_type}

IMPORTANT: Consider these preferences when ranking events. Give higher scores to events that match the user's preferences, especially:
1. Events matching the specified event type ({event_type}) should receive higher category_match scores
2. Events in the specified location ({location}) should be prioritized
3. Events matching the date/time preferences ({date}, {time}) should receive higher scores
4. Overall relevance_score should reflect how well the event matches ALL user preferences, not just the query text
"""
            logger.info(f"User preferences included in prompt: Location={location}, Date={date}, Time={time}, Event Type={event_type}")
        else:
            logger.warning("No user preferences to include in prompt")
        
        prompt = f"""
You are an expert event recommendation system. Given a user query and a list of events, analyze and score each event.

**PRIMARY FOCUS: User's Actual Query**
The user's actual query is: "{query}"

This is the MOST IMPORTANT input - it represents what the user is actually asking for. Pay close attention to:
- The specific words and phrases in the query
- The user's intent and what they're looking for
- Any specific requests or preferences mentioned in the query text

{preferences_text}
Available Events:
{json.dumps(event_summaries, indent=2, ensure_ascii=False)}

**Scoring Guidelines:**
1. **relevance_score (1-10)**: This is the MOST IMPORTANT score. It should reflect how well the event matches the user's ACTUAL QUERY ("{query}"). Consider:
   - Does the event match what the user is asking for in their query?
   - Does it fulfill the user's intent expressed in the query?
   - How relevant is the event to the specific request in the query?

2. **title_match (1-5)**: How well does the event title match keywords or concepts from the user's query?

3. **description_match (1-5)**: How well does the event description match the user's query?

4. **category_match (1-5)**: How well does the event category match the user's preferences (especially event_type from preferences)

5. **venue_appropriateness (1-5)**: Is the venue suitable for the type of event the user is looking for?

6. **price_consideration (1-5)**: Is the price appropriate for what the user is seeking?

7. **user_intent_match (1-5)**: Does the event match the user's intent as expressed in their query?

8. **overall_quality (1-5)**: Event quality/popularity

**IMPORTANT**: The user's actual query ("{query}") should be the PRIMARY factor in determining relevance_score. User preferences (location, event_type, etc.) are secondary filters that help narrow down the results, but the query text itself is what the user is actively asking for.

Please analyze each event and return a JSON object with:
1. "selected_events": Array of event IDs (0-19) ranked by relevance (max 5 events)
2. "scores": Object with event_id as key and detailed scoring as value

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
            if self.openrouter_api_key:
                # Use google/gemini-2.5-flash-lite if OPENROUTER_API_KEY is set because it has the best performance for this task.
                response = self.client.chat.completions.create(
                    model = "google/gemini-2.5-flash-lite",
                    messages=[
                        {"role": "system", "content": "You are a helpful event recommendation assistant. Always return valid JSON objects with selected_events and scores."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.1
                )
            elif self.openai_api_key:
                response = self.client.chat.completions.create(
                    model = "gpt-4.1-nano",
                    messages=[
                        {"role": "system", "content": "You are a helpful event recommendation assistant. Always return valid JSON objects with selected_events and scores."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.1
                )
            else:
                raise ValueError("No LLM API key found")

            # logger.info(f"OpenAI API call with {prompt} successful")
            
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
                return self.fallback_keyword_search(query, events)
                
        except Exception as e:
            logger.error(f"LLM search failed: {e}, falling back to keyword search")
            return self.fallback_keyword_search(query, events)

    def fallback_keyword_search(self, query: str, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
