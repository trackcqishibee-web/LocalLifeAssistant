#!/usr/bin/env python3
"""
Event Service - Direct wrapper for event_api UnifiedEventService
"""

import logging
from typing import Dict, Any, List, Optional
import sys
import os

# Add parent directory to path so we can import event_api
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from event_api.services.scraper import UnifiedEventService

logger = logging.getLogger(__name__)

class EventCrawler:
    """
    Unified event crawler using event_api UnifiedEventService
    """
    
    def __init__(self):
        self.unified_service = UnifiedEventService()

    def get_supported_cities(self) -> List[str]:
        """Get list of supported city names"""
        return self.unified_service.get_supported_cities()
    
    def get_supported_events(self) -> List[str]:
        """Get list of supported event types"""
        return self.unified_service.get_supported_events()
    
    def fetch_events_by_city(
        self, 
        city_name: str, 
        sources: List[str] = None, 
        max_pages: int = 3,
        category: str = "events"
    ) -> List[Dict[str, Any]]:
        """
        Fetch and normalize events from multiple sources using UnifiedEventService
        
        Args:
            city_name: City name (e.g., "new york", "san francisco")
            sources: List of sources (ignored, kept for compatibility - uses all available providers)
            max_pages: Max pages (ignored, kept for compatibility)
            category: Event category/type (e.g., "music", "sports", "nightlife", "business", "tech", "dating")
        
        Returns:
            List of normalized event dictionaries
        """
        logger.info(f"🔍 Starting unified event search for '{city_name}' with category '{category}' using event_api")
        
        try:
            normalized_city = city_name.lower().strip()
            all_events = self.unified_service.get_events(normalized_city, category=category)
            logger.info(f"📊 Total events collected: {len(all_events)} from event_api providers for {city_name}/{category}")
        return all_events
        except Exception as e:
            logger.error(f"Error fetching events from event_api: {e}", exc_info=True)
            return []


# Convenience function for backward compatibility
def fetch_events_by_city(city_name: str, max_pages: int = 3) -> List[Dict[str, Any]]:
    """Convenience function - fetch from all sources"""
    event_crawler = EventCrawler()
    return event_crawler.fetch_events_by_city(city_name, max_pages=max_pages)
