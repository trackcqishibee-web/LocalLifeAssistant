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

    def _get_cache_key(self, city: str) -> str:
        """Generate cache key from city name"""
        return city.lower().replace(" ", "_").replace("/", "_")

    def _get_cache_file_path(self, city: str) -> str:
        """Get file path for city cache"""
        cache_key = self._get_cache_key(city)
        return os.path.join(self.cache_dir, f"{cache_key}.json")

    def _save_cache_to_disk(self, city: str, cache_data: Dict[str, Any]):
        """Save cache data to disk"""
        try:
            file_path = self._get_cache_file_path(city)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache to disk for {city}: {e}")

    def get_cached_events(self, city: str, event_crawler=None) -> Optional[List[Dict[str, Any]]]:
        """Get cached events for a city - checks local cache first, then Firebase, then fetches fresh if provided"""
        try:
            cache_key = self._get_cache_key(city)

            # Check local memory cache first (fastest)
            if cache_key in self.memory_cache:
                cache_data = self.memory_cache[cache_key]
                if self._is_cache_valid(cache_data.get('cached_at', '')):
                    events = cache_data.get('events', [])
                    logger.info(f"Retrieved {len(events)} events for {city} from local memory cache")
                    return events
                else:
                    # Remove expired entry from memory
                    del self.memory_cache[cache_key]
                    logger.debug(f"Removed expired cache from memory: {city}")

            # Check local file cache
            file_path = self._get_cache_file_path(city)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)

                    if self._is_cache_valid(cache_data.get('cached_at', '')):
                        # Load into memory cache for faster future access
                        self.memory_cache[cache_key] = cache_data
                        events = cache_data.get('events', [])
                        logger.info(f"Retrieved {len(events)} events for {city} from local file cache")
                        return events
                    else:
                        # Remove expired file
                        os.remove(file_path)
                        logger.debug(f"Removed expired cache file: {city}")
                except Exception as e:
                    logger.warning(f"Error reading cache file for {city}: {e}")

            # Fallback to Firebase (slower)
            safe_city = city.lower().replace(" ", "_").replace("/", "_")
            cache_doc = self.db.collection('event_cache').document(safe_city).get()

            if not cache_doc.exists:
                logger.info(f"Cache for {city} doesn't exist in Firebase")
                # If no cache found and event_crawler provided, fetch fresh events
                if event_crawler:
                    return self._fetch_and_cache_fresh_events(city, event_crawler)
                return None

            cache_data = cache_doc.to_dict()

            if not self._is_cache_valid(cache_data.get('cached_at', '')):
                logger.info(f"Cache for {city} is expired in Firebase")
                # If cache expired and event_crawler provided, fetch fresh events
                if event_crawler:
                    return self._fetch_and_cache_fresh_events(city, event_crawler)
                return None

            # Cache in local memory and disk for future use
            events = cache_data.get('events', [])
            self.memory_cache[cache_key] = cache_data
            self._save_cache_to_disk(city, cache_data)

            logger.info(f"Retrieved {len(events)} events for {city} from Firebase (cached locally)")
            return events

        except Exception as e:
            logger.error(f"Error reading cache for {city}: {e}")
            return None

    def _fetch_and_cache_fresh_events(self, city: str, event_crawler) -> Optional[List[Dict[str, Any]]]:
        """Fetch fresh events for a specific city and cache them"""
        try:
            logger.info(f"Fetching fresh events for {city} due to expired/missing cache")
            fresh_events = event_crawler.fetch_events_by_city(city, max_pages=3)

            if fresh_events:
                logger.info(f"Fetched {len(fresh_events)} fresh events for {city}")
                # Cache the fresh events
                self.cache_events(city, fresh_events)
                return fresh_events
            else:
                logger.warning(f"Failed to fetch fresh events for {city}")
                return None

        except Exception as e:
            logger.error(f"Error fetching fresh events for {city}: {e}")
            return None

    def cache_events(self, city: str, events: List[Dict[str, Any]]) -> bool:
        """Cache events for a city - saves locally first, then to Firebase in background"""
        try:
            cache_data = {
                'city': city,
                'events': events,
                'cached_at': datetime.now().isoformat(),
                'count': len(events)
            }

            # Cache in local memory (fastest access)
            cache_key = self._get_cache_key(city)
            self.memory_cache[cache_key] = cache_data

            # Cache to local disk (persistence)
            self._save_cache_to_disk(city, cache_data)

            # Cache in Firebase (distributed backup) - in background to not block
            asyncio.create_task(self._cache_events_to_firebase_async(city, cache_data))

            logger.info(f"Cached {len(events)} events for {city} locally and in Firebase (async)")
            return True

        except Exception as e:
            logger.error(f"Error caching events for {city}: {e}")
            return False

    async def _cache_events_to_firebase_async(self, city: str, cache_data: Dict[str, Any]):
        """Async method to save cache data to Firebase in the background"""
        try:
            safe_city = city.lower().replace(" ", "_").replace("/", "_")
            self.db.collection('event_cache').document(safe_city).set(cache_data)
            logger.debug(f"Successfully cached {cache_data['count']} events for {city} to Firebase")
        except Exception as e:
            logger.error(f"Error caching events for {city} to Firebase: {e}")

    def get_cache_age(self, city: str) -> Optional[float]:
        """Get cache age in hours for a city - checks local cache first"""
        try:
            cache_key = self._get_cache_key(city)

            # Check local memory cache first
            if cache_key in self.memory_cache:
                cache_data = self.memory_cache[cache_key]
                cached_at = cache_data.get('cached_at')
                if cached_at:
                    cache_time = datetime.fromisoformat(cached_at)
                    age = datetime.now() - cache_time
                    return age.total_seconds() / 3600  # Convert to hours

            # Check local file cache
            file_path = self._get_cache_file_path(city)
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
            safe_city = city.lower().replace(" ", "_").replace("/", "_")
            cache_doc = self.db.collection('event_cache').document(safe_city).get()

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
