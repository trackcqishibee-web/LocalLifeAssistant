#!/usr/bin/env python3
"""
Firebase-based cache management for city-based event storage
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from firebase_admin import firestore
from .firebase_config import db

logger = logging.getLogger(__name__)

class CacheManager:
    """Firebase-based cache manager for city-based event storage"""

    def __init__(self, ttl_hours: int = 6):
        self.ttl_hours = ttl_hours
        self.db = db
        logger.info(f"Firebase Cache manager initialized, TTL: {ttl_hours}h")

    def _is_cache_valid(self, cached_at: str) -> bool:
        """Check if cache entry is still valid (not expired)"""
        try:
            cache_time = datetime.fromisoformat(cached_at)
            age = datetime.now() - cache_time
            return age < timedelta(hours=self.ttl_hours)
        except Exception as e:
            logger.warning(f"Error checking cache validity: {e}")
            return False

    def get_cached_events(self, city: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached events for a city if valid"""
        try:
            # Sanitize city name for document ID
            safe_city = city.lower().replace(" ", "_").replace("/", "_")

            cache_doc = self.db.collection('event_cache').document(safe_city).get()

            if not cache_doc.exists:
                logger.info(f"Cache for {city} doesn't exist")
                return None

            cache_data = cache_doc.to_dict()

            if not self._is_cache_valid(cache_data.get('cached_at', '')):
                logger.info(f"Cache for {city} is expired")
                return None

            events = cache_data.get('events', [])
            logger.info(f"Retrieved {len(events)} cached events for {city}")
            return events

        except Exception as e:
            logger.error(f"Error reading cache for {city}: {e}")
            return None

    def cache_events(self, city: str, events: List[Dict[str, Any]]) -> bool:
        """Cache events for a city"""
        try:
            # Sanitize city name for document ID
            safe_city = city.lower().replace(" ", "_").replace("/", "_")

            cache_data = {
                'city': city,
                'events': events,
                'cached_at': datetime.now().isoformat(),
                'count': len(events)
            }

            self.db.collection('event_cache').document(safe_city).set(cache_data)

            logger.info(f"Cached {len(events)} events for {city}")
            return True

        except Exception as e:
            logger.error(f"Error caching events for {city}: {e}")
            return False

    def get_cache_age(self, city: str) -> Optional[float]:
        """Get cache age in hours for a city"""
        try:
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
        """Remove expired cache entries to save space"""
        try:
            # Get all cache documents
            cache_docs = self.db.collection('event_cache').get()

            for doc in cache_docs:
                cache_data = doc.to_dict()
                if not self._is_cache_valid(cache_data.get('cached_at', '')):
                    doc.reference.delete()
                    logger.info(f"Removed expired cache: {doc.id}")

        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            total_files = 0
            valid_files = 0

            # Get all cache documents
            cache_docs = self.db.collection('event_cache').get()

            for doc in cache_docs:
                total_files += 1
                cache_data = doc.to_dict()
                if self._is_cache_valid(cache_data.get('cached_at', '')):
                    valid_files += 1

            return {
                'total_files': total_files,
                'valid_files': valid_files,
                'ttl_hours': self.ttl_hours,
                'storage_type': 'firestore'
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}
