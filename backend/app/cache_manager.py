#!/usr/bin/env python3
"""
Local-first cache management with Firebase fallback for city-based event storage
"""

import logging
import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from firebase_admin import firestore
from .firebase_config import db

logger = logging.getLogger(__name__)

class CacheManager:
    """Local-first cache manager with Firebase fallback for city-based event storage"""

    def __init__(self, ttl_hours: int = 6, cache_dir: str = "./cache"):
        self.ttl_hours = ttl_hours
        self.db = db
        self.cache_dir = cache_dir
        self.memory_cache: Dict[str, Dict[str, Any]] = {}

        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)

        logger.info(f"Local-first cache manager initialized, TTL: {ttl_hours}h, cache_dir: {cache_dir}")

    def _is_cache_valid(self, cached_at: str) -> bool:
        """Check if cache entry is still valid (not expired)"""
        try:
            cache_time = datetime.fromisoformat(cached_at)
            age = datetime.now() - cache_time
            return age < timedelta(hours=self.ttl_hours)
        except Exception as e:
            logger.warning(f"Error checking cache validity: {e}")
            return False

    def _get_cache_key(self, city: str, event_type: str = "events") -> str:
        """Generate cache key from city name and event type"""
        city_key = city.lower().replace(" ", "_").replace("/", "_")
        event_key = event_type.lower().replace(" ", "_")
        return f"{city_key}_{event_key}"

    def _get_cache_file_path(self, city: str, event_type: str = "events") -> str:
        """Get file path for city and event type cache"""
        cache_key = self._get_cache_key(city, event_type)
        return os.path.join(self.cache_dir, f"{cache_key}.json")

    def _save_cache_to_disk(self, city: str, cache_data: Dict[str, Any], event_type: str = "events"):
        """Save cache data to disk"""
        try:
            file_path = self._get_cache_file_path(city, event_type)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache to disk for {city}/{event_type}: {e}")

    def filter_past_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out events where start_datetime is before current time (public method for use by other services)"""
        if not events:
            return []
        
        current_time = datetime.now()
        future_events = []
        
        for event in events:
            start_datetime_str = event.get('start_datetime', '')
            if not start_datetime_str:
                # If no start_datetime, keep the event (let it pass through)
                future_events.append(event)
                continue
            
            try:
                # Try to parse the datetime string
                # Handle various formats: ISO format, date only, etc.
                if 'T' in start_datetime_str:
                    # ISO format with time
                    event_time = datetime.fromisoformat(start_datetime_str.replace('Z', '+00:00'))
                else:
                    # Date only format - assume start of day
                    event_time = datetime.fromisoformat(start_datetime_str)
                    # If it's just a date, compare dates only
                    if event_time.date() < current_time.date():
                        continue
                    elif event_time.date() == current_time.date():
                        # Same day - keep it (might be later today)
                        future_events.append(event)
                        continue
                    else:
                        # Future date
                        future_events.append(event)
                        continue
                
                # Compare with current time (accounting for timezone if needed)
                if event_time >= current_time:
                    future_events.append(event)
            except (ValueError, TypeError) as e:
                # If parsing fails, keep the event (better to show than hide)
                logger.warning(f"Could not parse start_datetime '{start_datetime_str}' for event '{event.get('title', 'Unknown')}': {e}")
                future_events.append(event)
        
        filtered_count = len(events) - len(future_events)
        if filtered_count > 0:
            logger.debug(f"Filtered out {filtered_count} past events, kept {len(future_events)} future events")
        
        return future_events

    def get_cached_events(self, city: str, event_type: str = "events", event_crawler=None) -> Optional[List[Dict[str, Any]]]:
        """Get cached events for a city and event type - checks local cache first, then Firebase, then fetches fresh if provided"""
        try:
            cache_key = self._get_cache_key(city, event_type)

            # Check local memory cache first (fastest)
            if cache_key in self.memory_cache:
                cache_data = self.memory_cache[cache_key]
                if self._is_cache_valid(cache_data.get('cached_at', '')):
                    events = cache_data.get('events', [])
                    # Filter out past events
                    events = self.filter_past_events(events)
                    logger.info(f"Retrieved {len(events)} events for {city}/{event_type} from local memory cache")
                    return events
                else:
                    # Cache expired but exists - return it immediately and trigger background refresh (stale-while-revalidate)
                    events = cache_data.get('events', [])
                    # Filter out past events
                    events = self.filter_past_events(events)
                    logger.info(f"Retrieved {len(events)} expired events for {city}/{event_type} from local memory cache (stale-while-revalidate)")
                    # Trigger background refresh if event_crawler is provided
                    if event_crawler:
                        asyncio.create_task(self._refresh_cache_async(city, event_type, event_crawler))
                    return events

            # Check local file cache
            file_path = self._get_cache_file_path(city, event_type)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)

                    if self._is_cache_valid(cache_data.get('cached_at', '')):
                        # Load into memory cache for faster future access
                        self.memory_cache[cache_key] = cache_data
                        events = cache_data.get('events', [])
                        # Filter out past events
                        events = self.filter_past_events(events)
                        logger.info(f"Retrieved {len(events)} events for {city}/{event_type} from local file cache")
                        return events
                    else:
                        # Cache expired but exists - return it immediately and trigger background refresh (stale-while-revalidate)
                        events = cache_data.get('events', [])
                        # Filter out past events
                        events = self.filter_past_events(events)
                        logger.info(f"Retrieved {len(events)} expired events for {city}/{event_type} from local file cache (stale-while-revalidate)")
                        # Trigger background refresh if event_crawler is provided
                        if event_crawler:
                            asyncio.create_task(self._refresh_cache_async(city, event_type, event_crawler))
                        return events
                except Exception as e:
                    logger.warning(f"Error reading cache file for {city}/{event_type}: {e}")

            # Fallback to Firebase (slower)
            safe_cache_key = cache_key
            cache_doc = self.db.collection('event_cache').document(safe_cache_key).get()

            if not cache_doc.exists:
                logger.info(f"Cache for {city}/{event_type} doesn't exist in Firebase")
                # If no cache found and event_crawler provided, fetch fresh events
                if event_crawler:
                    return self._fetch_and_cache_fresh_events(city, event_type, event_crawler)
                return None

            cache_data = cache_doc.to_dict()

            if not self._is_cache_valid(cache_data.get('cached_at', '')):
                logger.info(f"Cache for {city}/{event_type} is expired in Firebase")
                # Cache expired but exists - return it immediately and trigger background refresh (stale-while-revalidate)
                events = cache_data.get('events', [])
                # Filter out past events
                events = self._filter_past_events(events)
                logger.info(f"Retrieved {len(events)} expired events for {city}/{event_type} from Firebase (stale-while-revalidate)")
                # Cache in local memory and disk for faster access
                self.memory_cache[cache_key] = cache_data
                self._save_cache_to_disk(city, cache_data, event_type)
                # Trigger background refresh if event_crawler is provided
                if event_crawler:
                    asyncio.create_task(self._refresh_cache_async(city, event_type, event_crawler))
                return events

            # Cache in local memory and disk for future use
            events = cache_data.get('events', [])
            # Filter out past events
            events = self._filter_past_events(events)
            self.memory_cache[cache_key] = cache_data
            self._save_cache_to_disk(city, cache_data, event_type)

            logger.info(f"Retrieved {len(events)} events for {city}/{event_type} from Firebase (cached locally)")
            return events

        except Exception as e:
            logger.error(f"Error reading cache for {city}/{event_type}: {e}")
            return None

    def _fetch_and_cache_fresh_events(self, city: str, event_type: str, event_crawler) -> Optional[List[Dict[str, Any]]]:
        """Fetch fresh events for a specific city and event type, then cache them"""
        try:
            logger.info(f"Fetching fresh events for {city}/{event_type} due to expired/missing cache")
            fresh_events = event_crawler.fetch_events_by_city(city, category=event_type, max_pages=3)

            if fresh_events:
                # Filter out past events before caching
                future_events = self.filter_past_events(fresh_events)
                logger.info(f"Fetched {len(fresh_events)} events for {city}/{event_type}, {len(future_events)} are future events")
                # Cache the filtered events
                self.cache_events(city, future_events, event_type)
                return future_events
            else:
                logger.warning(f"Failed to fetch fresh events for {city}/{event_type}")
                return None

        except Exception as e:
            logger.error(f"Error fetching fresh events for {city}/{event_type}: {e}")
            return None

    async def _refresh_cache_async(self, city: str, event_type: str, event_crawler):
        """Async method to refresh cache in the background (stale-while-revalidate pattern)"""
        try:
            logger.info(f"Background refresh: Fetching fresh events for {city}/{event_type}")
            fresh_events = event_crawler.fetch_events_by_city(city, category=event_type, max_pages=3)
            
            if fresh_events:
                # Filter out past events before caching
                future_events = self.filter_past_events(fresh_events)
                logger.info(f"Background refresh: Fetched {len(fresh_events)} events for {city}/{event_type}, {len(future_events)} are future events")
                # Cache the filtered events
                self.cache_events(city, future_events, event_type)
                logger.info(f"Background refresh: Successfully updated cache for {city}/{event_type}")
            else:
                logger.warning(f"Background refresh: No events fetched for {city}/{event_type}")
        except Exception as e:
            logger.error(f"Background refresh: Error refreshing cache for {city}/{event_type}: {e}", exc_info=True)
    
    def cache_all_event_types_for_city(self, city: str, event_crawler) -> Dict[str, List[Dict[str, Any]]]:
        """
        Pre-cache all supported event types for a city.
        This allows frontend to show event type buttons and retrieve cached events instantly.
        
        Returns:
            Dictionary mapping event_type -> list of events
        """
        try:
            supported_event_types = event_crawler.get_supported_events()
            logger.info(f"Pre-caching all event types for {city}: {supported_event_types}")
            
            cached_results = {}
            for event_type in supported_event_types:
                try:
                    # Check if already cached and valid
                    cached = self.get_cached_events(city, event_type=event_type, event_crawler=None)
                    if cached:
                        logger.info(f"Event type {event_type} already cached for {city}")
                        cached_results[event_type] = cached
                    else:
                        # Fetch and cache
                        logger.info(f"Fetching and caching {event_type} events for {city}")
                        fresh_events = event_crawler.fetch_events_by_city(city, category=event_type, max_pages=3)
                        if fresh_events:
                            self.cache_events(city, fresh_events, event_type)
                            cached_results[event_type] = fresh_events
                        else:
                            cached_results[event_type] = []
                except Exception as e:
                    logger.error(f"Error caching {event_type} for {city}: {e}")
                    cached_results[event_type] = []
            
            logger.info(f"Pre-cached {len(cached_results)} event types for {city}")
            return cached_results
            
        except Exception as e:
            logger.error(f"Error pre-caching all event types for {city}: {e}")
            return {}

    def cache_events(self, city: str, events: List[Dict[str, Any]], event_type: str = "events") -> bool:
        """Cache events for a city and event type - saves locally first, then to Firebase in background"""
        try:
            cache_data = {
                'city': city,
                'event_type': event_type,
                'events': events,
                'cached_at': datetime.now().isoformat(),
                'count': len(events)
            }

            # Cache in local memory (fastest access)
            cache_key = self._get_cache_key(city, event_type)
            self.memory_cache[cache_key] = cache_data

            # Cache to local disk (persistence)
            self._save_cache_to_disk(city, cache_data, event_type)

            # Cache in Firebase (distributed backup) - in background to not block
            asyncio.create_task(self._cache_events_to_firebase_async(city, event_type, cache_data))

            logger.info(f"Cached {len(events)} events for {city}/{event_type} locally and in Firebase (async)")
            return True

        except Exception as e:
            logger.error(f"Error caching events for {city}/{event_type}: {e}")
            return False

    async def _cache_events_to_firebase_async(self, city: str, event_type: str, cache_data: Dict[str, Any]):
        """Async method to save cache data to Firebase in the background"""
        try:
            cache_key = self._get_cache_key(city, event_type)
            self.db.collection('event_cache').document(cache_key).set(cache_data)
            logger.debug(f"Successfully cached {cache_data['count']} events for {city}/{event_type} to Firebase")
        except Exception as e:
            logger.error(f"Error caching events for {city}/{event_type} to Firebase: {e}")

    def get_cache_age(self, city: str, event_type: str = "events") -> Optional[float]:
        """Get cache age in hours for a city and event type - checks local cache first"""
        try:
            cache_key = self._get_cache_key(city, event_type)

            # Check local memory cache first
            if cache_key in self.memory_cache:
                cache_data = self.memory_cache[cache_key]
                cached_at = cache_data.get('cached_at')
                if cached_at:
                    cache_time = datetime.fromisoformat(cached_at)
                    age = datetime.now() - cache_time
                    return age.total_seconds() / 3600  # Convert to hours

            # Check local file cache
            file_path = self._get_cache_file_path(city, event_type)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    cached_at = cache_data.get('cached_at')
                    if cached_at:
                        cache_time = datetime.fromisoformat(cached_at)
                        age = datetime.now() - cache_time
                        return age.total_seconds() / 3600  # Convert to hours
                except Exception:
                    pass

            # Fallback to Firebase
            cache_doc = self.db.collection('event_cache').document(cache_key).get()

            if not cache_doc.exists:
                return None

            cache_data = cache_doc.to_dict()
            cached_at = cache_data.get('cached_at')

            if not cached_at:
                return None

            cache_time = datetime.fromisoformat(cached_at)
            age = datetime.now() - cache_time
            return age.total_seconds() / 3600  # Convert to hours

        except Exception:
            return None

    def cleanup_old_cache(self):
        """Remove expired cache entries from local storage and Firebase"""
        try:
            # Clean up local memory cache
            expired_keys = []
            for cache_key, cache_data in self.memory_cache.items():
                if not self._is_cache_valid(cache_data.get('cached_at', '')):
                    expired_keys.append(cache_key)

            for cache_key in expired_keys:
                del self.memory_cache[cache_key]
                logger.debug(f"Removed expired cache from memory: {cache_key}")

            # Clean up local disk cache files
            if os.path.exists(self.cache_dir):
                for filename in os.listdir(self.cache_dir):
                    if not filename.endswith('.json'):
                        continue

                    file_path = os.path.join(self.cache_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)

                        if not self._is_cache_valid(cache_data.get('cached_at', '')):
                            os.remove(file_path)
                            logger.debug(f"Removed expired cache file: {filename}")
                    except Exception as e:
                        logger.warning(f"Error checking cache file {filename}: {e}")

            # Clean up Firebase cache
            cache_docs = self.db.collection('event_cache').get()
            for doc in cache_docs:
                cache_data = doc.to_dict()
                if not self._is_cache_valid(cache_data.get('cached_at', '')):
                    doc.reference.delete()
                    logger.info(f"Removed expired cache from Firebase: {doc.id}")

            logger.info(f"Cache cleanup completed. Removed {len(expired_keys)} expired entries")

        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for local and Firebase storage"""
        try:
            # Local cache stats
            local_memory_total = len(self.memory_cache)
            local_memory_valid = sum(1 for cache_data in self.memory_cache.values()
                                   if self._is_cache_valid(cache_data.get('cached_at', '')))

            # Local disk cache stats
            local_disk_total = 0
            local_disk_valid = 0
            if os.path.exists(self.cache_dir):
                for filename in os.listdir(self.cache_dir):
                    if not filename.endswith('.json'):
                        continue
                    local_disk_total += 1
                    file_path = os.path.join(self.cache_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        if self._is_cache_valid(cache_data.get('cached_at', '')):
                            local_disk_valid += 1
                    except Exception:
                        pass

            # Firebase cache stats
            firebase_total = 0
            firebase_valid = 0
            cache_docs = self.db.collection('event_cache').get()
            for doc in cache_docs:
                firebase_total += 1
                cache_data = doc.to_dict()
                if self._is_cache_valid(cache_data.get('cached_at', '')):
                    firebase_valid += 1

            return {
                'local_memory': {
                    'total': local_memory_total,
                    'valid': local_memory_valid
                },
                'local_disk': {
                    'total': local_disk_total,
                    'valid': local_disk_valid
                },
                'firebase': {
                    'total': firebase_total,
                    'valid': firebase_valid
                },
                'ttl_hours': self.ttl_hours,
                'cache_dir': self.cache_dir,
                'storage_type': 'hybrid_local_firebase'
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}
