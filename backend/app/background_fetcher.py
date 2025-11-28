#!/usr/bin/env python3
"""
Background event fetcher service for pre-caching events
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from .event_service import EventCrawler
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class BackgroundEventFetcher:
    """Background service to fetch and cache events for all supported cities and event types"""

    def __init__(self, cache_manager: CacheManager, event_crawler: EventCrawler):
        self.cache_manager = cache_manager
        self.event_crawler = event_crawler
        self.last_refresh_time: Dict[str, datetime] = {}
        logger.info("BackgroundEventFetcher initialized")


    def fetch_all_events(self) -> Dict[str, Any]:
        """
        Fetch events for all supported cities and event types.
        This is the main method called by the background scheduler.
        
        Returns:
            Dictionary with fetch results and statistics
        """
        start_time = datetime.now()
        logger.info("Starting background event fetch for all cities and event types")
        
        try:
            supported_cities = self.event_crawler.get_supported_cities()
            supported_event_types = self.event_crawler.get_supported_events()
            
            logger.info(f"Fetching events for {len(supported_cities)} cities and {len(supported_event_types)} event types")
            
            total_fetched = 0
            total_cached = 0
            errors = []
            
            for city in supported_cities:
                for event_type in supported_event_types:
                    try:
                        logger.info(f"Fetching {event_type} events for {city}")
                        
                        # Fetch events from all providers
                        events = self.event_crawler.fetch_events_by_city(
                            city, 
                            category=event_type, 
                            max_pages=3
                        )
                        
                        if events:
                            # Filter out past events using cache_manager's method
                            future_events = self.cache_manager.filter_past_events(events)
                            
                            if future_events:
                                # Cache the filtered events
                                success = self.cache_manager.cache_events(city, future_events, event_type)
                                if success:
                                    total_cached += len(future_events)
                                    logger.info(f"Cached {len(future_events)} future {event_type} events for {city}")
                                else:
                                    errors.append(f"Failed to cache events for {city}/{event_type}")
                            else:
                                logger.info(f"No future events found for {city}/{event_type}")
                            
                            total_fetched += len(events)
                        else:
                            logger.warning(f"No events fetched for {city}/{event_type}")
                            
                    except Exception as e:
                        error_msg = f"Error fetching {event_type} events for {city}: {e}"
                        logger.error(error_msg, exc_info=True)
                        errors.append(error_msg)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Update last refresh time
            self.last_refresh_time['all'] = end_time
            
            result = {
                'success': True,
                'duration_seconds': duration,
                'cities_processed': len(supported_cities),
                'event_types_processed': len(supported_event_types),
                'total_events_fetched': total_fetched,
                'total_events_cached': total_cached,
                'errors': errors,
                'last_refresh_time': end_time.isoformat()
            }
            
            logger.info(f"Background event fetch completed in {duration:.2f}s. "
                       f"Cached {total_cached} events across {len(supported_cities)} cities")
            
            return result
            
        except Exception as e:
            logger.error(f"Fatal error in background event fetch: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'last_refresh_time': datetime.now().isoformat()
            }

    def get_last_refresh_time(self, city: str = None) -> Dict[str, Any]:
        """Get the last refresh time for a specific city or all cities"""
        if city:
            return {
                'city': city,
                'last_refresh_time': self.last_refresh_time.get(city, {}).isoformat() if self.last_refresh_time.get(city) else None
            }
        else:
            return {
                'last_refresh_time': self.last_refresh_time.get('all', {}).isoformat() if self.last_refresh_time.get('all') else None,
                'all_refresh_times': {k: v.isoformat() if v else None for k, v in self.last_refresh_time.items()}
            }

