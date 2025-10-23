#!/usr/bin/env python3
"""
Cache management for city-based event storage
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CacheManager:
    """Intelligent cache manager for city-based event storage"""
    
    def __init__(self, cache_dir: str = "./event_cache", ttl_hours: int = 6, max_size_mb: int = 100):
        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        self.max_size_mb = max_size_mb
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        logger.info(f"Cache manager initialized: {cache_dir}, TTL: {ttl_hours}h")
    
    def _get_cache_file(self, city: str) -> str:
        """Get cache file path for a city"""
        # Sanitize city name for filename
        safe_city = city.lower().replace(" ", "_").replace("/", "_")
        return os.path.join(self.cache_dir, f"{safe_city}.json")
    
    def _is_cache_valid(self, cache_file: str) -> bool:
        """Check if cache file is still valid (not expired)"""
        if not os.path.exists(cache_file):
            return False
        
        try:
            # Check file modification time
            mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            age = datetime.now() - mod_time
            
            return age < timedelta(hours=self.ttl_hours)
        except Exception as e:
            logger.warning(f"Error checking cache validity: {e}")
            return False
    
    def get_cached_events(self, city: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached events for a city if valid"""
        cache_file = self._get_cache_file(city)
        
        if not self._is_cache_valid(cache_file):
            logger.info(f"Cache for {city} is expired or doesn't exist")
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            events = cache_data.get('events', [])
            logger.info(f"Retrieved {len(events)} cached events for {city}")
            return events
            
        except Exception as e:
            logger.error(f"Error reading cache for {city}: {e}")
            return None
    
    def cache_events(self, city: str, events: List[Dict[str, Any]]) -> bool:
        """Cache events for a city"""
        cache_file = self._get_cache_file(city)
        
        try:
            cache_data = {
                'city': city,
                'events': events,
                'cached_at': datetime.now().isoformat(),
                'count': len(events)
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cached {len(events)} events for {city}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching events for {city}: {e}")
            return False
    
    def get_cache_age(self, city: str) -> Optional[float]:
        """Get cache age in hours for a city"""
        cache_file = self._get_cache_file(city)
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            age = datetime.now() - mod_time
            return age.total_seconds() / 3600  # Convert to hours
        except Exception:
            return None
    
    def cleanup_old_cache(self):
        """Remove expired cache files to save space"""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    if not self._is_cache_valid(cache_file):
                        os.remove(cache_file)
                        logger.info(f"Removed expired cache: {filename}")
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            total_files = 0
            total_size_mb = 0
            valid_files = 0
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    total_files += 1
                    total_size_mb += os.path.getsize(cache_file) / (1024 * 1024)
                    
                    if self._is_cache_valid(cache_file):
                        valid_files += 1
            
            return {
                'total_files': total_files,
                'valid_files': valid_files,
                'total_size_mb': round(total_size_mb, 2),
                'cache_dir': self.cache_dir,
                'ttl_hours': self.ttl_hours
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}
