#!/usr/bin/env python3
"""
Comprehensive extraction service for user preferences and location
Consolidates location extraction from geocoding.py with new preference extraction
"""

import os
import openai
import re
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class UserPreferences(BaseModel):
    location: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    event_type: Optional[str] = None

class ExtractionService:
    """Service for extracting user preferences and location from natural language"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
    
    def extract_user_preferences(self, user_message: str) -> UserPreferences:
        """
        Extract all user preferences from a single message using LLM
        """
        try:
            # Create comprehensive prompt for all preference extraction
            prompt = f"""
You are a preference extraction assistant. Extract the following information from the user's message:

User message: "{user_message}"

Extract and return a JSON object with these fields:
1. "location": City name (e.g., "New York", "Los Angeles", "Chicago") or "none" if not mentioned
2. "date": Specific date, relative date, or "none" (e.g., "today", "tomorrow", "this weekend", "next Friday", "December 15th")
3. "time": Time preference or "none" (e.g., "morning", "afternoon", "evening", "night", "7pm", "lunch time")
4. "event_type": Type of event or "none" (e.g., "music", "food", "art", "sports", "networking", "comedy", "theater")

Guidelines:
- Only extract information that is clearly mentioned
- For neighborhoods like "Brooklyn", "Manhattan", return the main city (e.g., "New York")
- For relative dates, keep the natural language (e.g., "this weekend", "tomorrow")
- For event types, use broad categories (music, food, art, sports, etc.)
- Return "none" for any field not mentioned
- Return only valid JSON, no other text

Examples:
- "Find me jazz concerts in Brooklyn this weekend" → {{"location": "New York", "date": "this weekend", "time": "none", "event_type": "music"}}
- "What restaurants are good for dinner tonight?" → {{"location": "none", "date": "today", "time": "evening", "event_type": "food"}}
- "Show me art galleries in San Francisco" → {{"location": "San Francisco", "date": "none", "time": "none", "event_type": "art"}}
- "I want to try something new" → {{"location": "none", "date": "none", "time": "none", "event_type": "none"}}

Return only the JSON object:
"""

            # Call OpenAI API for preference extraction
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a precise preference extraction assistant. Return only valid JSON objects."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            extracted_text = response.choices[0].message.content.strip()
            logger.info(f"LLM extraction response: {extracted_text}")
            
            # Parse JSON response
            import json
            if "{" in extracted_text and "}" in extracted_text:
                json_start = extracted_text.find("{")
                json_end = extracted_text.rfind("}") + 1
                json_str = extracted_text[json_start:json_end]
                extracted_data = json.loads(json_str)
                
                # Create UserPreferences object
                preferences = UserPreferences(
                    location=self._normalize_location(extracted_data.get("location", "none")),
                    date=self._normalize_date(extracted_data.get("date", "none")),
                    time=self._normalize_time(extracted_data.get("time", "none")),
                    event_type=self._normalize_event_type(extracted_data.get("event_type", "none"))
                )
                
                logger.info(f"LLM extracted preferences: {preferences}")
                return preferences
            else:
                logger.warning("Failed to parse LLM response as JSON, using fallback")
                return self._fallback_extraction(user_message)
                
        except Exception as e:
            logger.error(f"LLM preference extraction failed: {e}")
            return self._fallback_extraction(user_message)
    
    def extract_location_from_query(self, query: str) -> Optional[str]:
        """
        Extract city name from user query (migrated from geocoding.py)
        """
        # Try LLM extraction first
        llm_result = self._extract_city_from_query_llm(query)
        if llm_result:
            return llm_result
        
        # Fallback to regex-based extraction
        logger.info(f"LLM extraction failed, trying regex fallback for: '{query}'")
        
        # Common city patterns (migrated from geocoding.py)
        city_patterns = {
            r'\bbrooklyn\b': 'new york',
            r'\bmanhattan\b': 'new york', 
            r'\bqueens\b': 'new york',
            r'\bbronx\b': 'new york',
            r'\bnyc\b': 'new york',
            r'\bnew york city\b': 'new york',
            r'\blos angeles\b': 'los angeles',
            r'\bla\b': 'los angeles',
            r'\bsan francisco\b': 'san francisco',
            r'\bsf\b': 'san francisco',
            r'\bchicago\b': 'chicago',
            r'\bboston\b': 'boston',
            r'\bseattle\b': 'seattle',
            r'\bmiami\b': 'miami',
            r'\baustin\b': 'austin',
            r'\bdenver\b': 'denver',
            r'\bportland\b': 'portland',
            r'\bphoenix\b': 'phoenix',
            r'\blas vegas\b': 'las vegas',
            r'\batlanta\b': 'atlanta'
        }
        
        query_lower = query.lower()
        for pattern, city in city_patterns.items():
            if re.search(pattern, query_lower):
                logger.info(f"Regex found city '{city}' in query: '{query}'")
                return city
        
        logger.info(f"No city found in query (regex): '{query}'")
        return None
    
    def _extract_city_from_query_llm(self, query: str) -> Optional[str]:
        """
        Extract city name from user query using LLM (migrated from geocoding.py)
        """
        try:
            prompt = f"""
You are a location extraction assistant. Your task is to identify if the user's query mentions a specific US city or location.

User query: "{query}"

Instructions:
1. Look for explicit city names, neighborhoods, or regions in the query
2. Only return a city name if it's clearly mentioned
3. If no specific location is mentioned, return "none"
4. Return the city name in lowercase format
5. For neighborhoods like "Brooklyn", "Manhattan", "Queens", return "new york"
6. For regions like "Bay Area", return "san francisco"

Examples:
- "Show me free events in Brooklyn" → "new york"
- "Find restaurants in Los Angeles" → "los angeles" 
- "What's happening in Miami this weekend?" → "miami"
- "Find me a chinese place to eat nearby" → "none"
- "Show me events in Chicago" → "chicago"
- "What restaurants are good for a date night?" → "none"

Return only the city name or "none", nothing else.
"""

            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a precise location extraction assistant. Return only city names or 'none'."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            extracted_city = response.choices[0].message.content.strip().lower()
            
            if extracted_city == "none" or not extracted_city:
                logger.info(f"No city found in query (LLM): '{query}'")
                return None
            
            # Map common variations to standard city names (migrated from geocoding.py)
            city_mapping = {
                'brooklyn': 'New York',
                'manhattan': 'New York', 
                'queens': 'New York',
                'bronx': 'New York',
                'nyc': 'New York',
                'new york city': 'New York',
                'los angeles': 'Los Angeles',
                'la': 'Los Angeles',
                'san francisco': 'San Francisco',
                'sf': 'San Francisco',
                'chicago': 'Chicago',
                'boston': 'Boston',
                'seattle': 'Seattle',
                'miami': 'Miami',
                'austin': 'Austin',
                'denver': 'Denver',
                'portland': 'Portland',
                'phoenix': 'Phoenix',
                'las vegas': 'Las Vegas',
                'atlanta': 'Atlanta'
            }
            final_city = city_mapping.get(extracted_city.lower(), extracted_city)
            
            logger.info(f"LLM extracted city '{final_city}' from query: '{query}'")
            return final_city
            
        except Exception as e:
            logger.error(f"LLM city extraction failed: {e}")
            return None
    
    def _fallback_extraction(self, user_message: str) -> UserPreferences:
        """
        Fallback extraction using regex patterns when LLM fails
        """
        logger.info(f"Using fallback extraction for: '{user_message}'")
        
        # Extract location using existing method
        location = self.extract_location_from_query(user_message)
        
        # Extract date using regex patterns
        date = self._extract_date_regex(user_message)
        
        # Extract time using regex patterns
        time = self._extract_time_regex(user_message)
        
        # Extract event type using regex patterns
        event_type = self._extract_event_type_regex(user_message)
        
        return UserPreferences(
            location=location,
            date=date,
            time=time,
            event_type=event_type
        )
    
    def _extract_date_regex(self, text: str) -> Optional[str]:
        """Extract date using regex patterns"""
        text_lower = text.lower()
        
        # Today/tomorrow patterns
        if re.search(r'\btoday\b', text_lower):
            return "today"
        elif re.search(r'\btomorrow\b', text_lower):
            return "tomorrow"
        elif re.search(r'\bthis weekend\b', text_lower):
            return "this weekend"
        elif re.search(r'\bnext weekend\b', text_lower):
            return "next weekend"
        elif re.search(r'\bthis week\b', text_lower):
            return "this week"
        elif re.search(r'\bnext week\b', text_lower):
            return "next week"
        
        # Day of week patterns
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days:
            if re.search(rf'\b{day}\b', text_lower):
                return day
        
        return None
    
    def _extract_time_regex(self, text: str) -> Optional[str]:
        """Extract time using regex patterns"""
        text_lower = text.lower()
        
        # Time of day patterns
        if re.search(r'\bmorning\b', text_lower):
            return "morning"
        elif re.search(r'\bafternoon\b', text_lower):
            return "afternoon"
        elif re.search(r'\bevening\b', text_lower):
            return "evening"
        elif re.search(r'\bnight\b', text_lower):
            return "night"
        elif re.search(r'\blunch\b', text_lower):
            return "lunch time"
        elif re.search(r'\bdinner\b', text_lower):
            return "dinner time"
        
        # Specific time patterns (e.g., "7pm", "2:30")
        time_pattern = r'\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b'
        match = re.search(time_pattern, text_lower)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_event_type_regex(self, text: str) -> Optional[str]:
        """Extract event type using regex patterns"""
        text_lower = text.lower()
        
        # Event type patterns
        event_patterns = {
            r'\bmusic\b|\bconcert\b|\bjazz\b|\bconcert\b': 'music',
            r'\bfood\b|\brestaurant\b|\bdining\b|\bcuisine\b': 'food',
            r'\bart\b|\bgallery\b|\bexhibition\b|\bmuseum\b': 'art',
            r'\bsports\b|\bfitness\b|\bgym\b|\bworkout\b': 'sports',
            r'\bnetworking\b|\bbusiness\b|\bprofessional\b': 'networking',
            r'\bcomedy\b|\bstandup\b|\bfunny\b': 'comedy',
            r'\btheater\b|\bplay\b|\bshow\b': 'theater',
            r'\bfestival\b|\bfair\b|\bmarket\b': 'festival',
            r'\bparty\b|\bcelebration\b|\bclub\b': 'party'
        }
        
        for pattern, event_type in event_patterns.items():
            if re.search(pattern, text_lower):
                return event_type
        
        return None
    
    def _normalize_location(self, location: str) -> Optional[str]:
        """Normalize location string"""
        if location == "none" or not location:
            return None
        return location
    
    def _normalize_date(self, date: str) -> Optional[str]:
        """Normalize date string"""
        if date == "none" or not date:
            return None
        return date
    
    def _normalize_time(self, time: str) -> Optional[str]:
        """Normalize time string"""
        if time == "none" or not time:
            return None
        return time
    
    def _normalize_event_type(self, event_type: str) -> Optional[str]:
        """Normalize event type string"""
        if event_type == "none" or not event_type:
            return None
        return event_type
