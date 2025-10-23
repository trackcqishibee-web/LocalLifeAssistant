#!/usr/bin/env python3
"""
Intelligent search and LLM integration for event recommendations
"""

import os
import json
import openai
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SearchService:
    """Service for intelligent event search using LLM"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
    
    async def intelligent_event_search(self, query: str, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
            client = openai.OpenAI(api_key=self.openai_api_key)
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
