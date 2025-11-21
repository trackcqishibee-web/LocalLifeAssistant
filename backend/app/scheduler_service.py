#!/usr/bin/env python3
"""
Background scheduler for proactively fetching events from all cities every 6 hours
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CityEventsScheduler:
    """Background scheduler that fetches events for all cities every 6 hours"""

    def __init__(self, event_crawler, cache_manager):
        self.event_crawler = event_crawler
        self.cache_manager = cache_manager
        self.running = False
        self._task: Optional[asyncio.Task] = None

    def _get_supported_cities(self) -> List[str]:
        """Get list of all supported cities"""
        return self.event_crawler.eventbrite_crawler.get_supported_cities()

    def _calculate_next_interval(self) -> float:
        """Calculate seconds until next 6-hour interval (00:00, 06:00, 12:00, 18:00 UTC)"""
        now = datetime.utcnow()
        current_hour = now.hour
        
        # Determine next interval hour
        if current_hour < 6:
            next_hour = 6
        elif current_hour < 12:
            next_hour = 12
        elif current_hour < 18:
            next_hour = 18
        else:
            next_hour = 24  # Next day 00:00
        
        # Calculate next interval datetime
        if next_hour == 24:
            next_datetime = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            next_datetime = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
        
        # If we're past the hour, move to next interval
        if next_datetime <= now:
            next_datetime += timedelta(hours=6)
        
        seconds_until_next = (next_datetime - now).total_seconds()
        logger.info(f"Next crawl scheduled at {next_datetime.isoformat()} UTC ({seconds_until_next/3600:.1f} hours from now)")
        return seconds_until_next

    async def _crawl_all_cities(self) -> Dict[str, Any]:
        """Fetch events for all supported cities and cache them"""
        start_time = datetime.utcnow()
        cities = self._get_supported_cities()
        logger.info(f"🔄 Starting scheduled crawl for {len(cities)} cities")
        
        city_results = {}
        popular_events = []
        
        for city in cities:
            try:
                logger.info(f"📅 Fetching events for {city}...")
                events = self.event_crawler.fetch_events_by_city(city, max_pages=3)
                
                if events and len(events) > 0:
                    # Cache events for this city
                    self.cache_manager.cache_events(city, events)
                    city_results[city] = len(events)
                    
                    # Take top 1 event for popular events cache
                    top_event = events[0]
                    popular_events.append(top_event)
                    logger.info(f"✅ {city}: {len(events)} events cached, top event: {top_event.get('title', 'N/A')[:50]}")
                else:
                    city_results[city] = 0
                    logger.warning(f"⚠️ {city}: No events found")
                    
            except Exception as e:
                logger.error(f"❌ Failed to fetch events for {city}: {e}")
                city_results[city] = None
        
        # Cache popular events (top 1 per city)
        if popular_events:
            successful_cities = [city for city, count in city_results.items() if count and count > 0]
            self.cache_manager.cache_popular_events(popular_events, cities_crawled=successful_cities)
            logger.info(f"⭐ Cached {len(popular_events)} popular events from {len(successful_cities)} cities")
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"✅ Crawl completed in {duration:.1f}s. Cities: {city_results}")
        
        return {
            "cities_processed": len(cities),
            "cities_successful": sum(1 for v in city_results.values() if v is not None and v > 0),
            "total_events": sum(v for v in city_results.values() if v and v > 0),
            "popular_events_count": len(popular_events),
            "duration_seconds": duration,
            "city_results": city_results
        }

    async def _run_scheduler_loop(self):
        """Main scheduler loop that runs every 6 hours"""
        while self.running:
            try:
                # Calculate time until next interval
                sleep_seconds = self._calculate_next_interval()
                
                # Wait until next interval
                logger.info(f"⏰ Scheduler sleeping for {sleep_seconds/3600:.1f} hours until next crawl")
                await asyncio.sleep(sleep_seconds)
                
                # Run crawl
                if self.running:  # Check if still running after sleep
                    await self._crawl_all_cities()
                    
            except asyncio.CancelledError:
                logger.info("Scheduler task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                # Continue running even if one cycle fails
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    def start(self):
        """Start the scheduler as a background task"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._run_scheduler_loop())
        logger.info("🚀 City events scheduler started (runs every 6 hours)")

    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return
        
        self.running = False
        if self._task:
            self._task.cancel()
        logger.info("🛑 City events scheduler stopped")

