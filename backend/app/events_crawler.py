"""
Eventbrite Events Crawler for LocalLifeAssistant
Enhanced version of the original crawler with better error handling and data normalization
"""

import requests
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import os

logger = logging.getLogger(__name__)

class EventbriteCrawler:
    def __init__(self):
        self.base_url = "https://www.eventbrite.com/api/v3/destination/search/"
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with headers and cookies"""
        # These headers and cookies may need to be updated periodically
        # Consider using environment variables for sensitive data
        self.session.headers.update({
            "referer": "https://www.eventbrite.com/d/ny--new-york/all-events/?page=1&lang=en",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "x-csrftoken": "d104f5aaa1ff11f091e53b19e64a90d8",
            "x-requested-with": "XMLHttpRequest",
        })
        
        self.session.cookies.update({
            "stableId": "c1a4e01b-eec8-4b21-87d5-480c9f1204c6",
            "mgrefby": "",
            "guest": "identifier%3D962a4002-d8b7-4bb2-a5e3-7147aa5f4c56%26a%3D1497%26s%3D4107b7da86213116d63285f1fae37350db161fd1400d4a3cf1e2dcff65684ed9",
            "csrftoken": "d104f5aaa1ff11f091e53b19e64a90d8",
        })
    
    def _create_search_payload(self, location_id: str = "85977539", page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Create search payload for Eventbrite API"""
        return {
            "event_search": {
                "dates": "current_future",
                "dedup": True,
                "places": [location_id],  # Default to NYC, can be changed
                "page": page,
                "page_size": page_size,
                "aggs": [
                    "places_borough",
                    "places_neighborhood",
                ],
                "online_events_only": False,
                "languages": ["en"],
            },
            "expand.destination_event": [
                "primary_venue",
                "image",
                "ticket_availability",
                "saves",
                "event_sales_status",
                "primary_organizer",
                "public_collections",
            ],
            "browse_surface": "search",
        }
    
    def _get_address(self, venue: Dict[str, Any]) -> Dict[str, Any]:
        """Extract address information from venue data"""
        addr = venue.get("address") or {}
        return {
            "address_1": addr.get("address_1"),
            "address_2": addr.get("address_2"),
            "city": addr.get("city"),
            "region": addr.get("region"),
            "postal_code": addr.get("postal_code"),
            "country": addr.get("country"),
            "latitude": addr.get("latitude"),
            "longitude": addr.get("longitude"),
            "display": addr.get("localized_address_display") or addr.get("localized_multi_line_address_display"),
        }
    
    def _normalize_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize event data to match LocalLifeAssistant schema"""
        venue = event.get("primary_venue") or {}
        organizer = event.get("primary_organizer") or {}
        ticket = event.get("ticket_availability") or {}
        image = event.get("image") or {}
        
        # Extract start and end times
        start_date = event.get("start_date")
        end_date = event.get("end_date")
        
        # Parse dates if they exist
        start_datetime = None
        end_datetime = None
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00')).isoformat()
            except:
                start_datetime = start_date
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00')).isoformat()
            except:
                end_datetime = end_date
        
        return {
            "event_id": str(event.get("id") or event.get("eventbrite_event_id", "")),
            "title": event.get("name", ""),
            "description": event.get("summary", ""),
            "start_datetime": start_datetime or "",
            "end_datetime": end_datetime or "",
            "timezone": event.get("timezone", "America/New_York"),
            "venue_name": venue.get("name", ""),
            "venue_city": venue.get("address", {}).get("city", ""),
            "venue_country": venue.get("address", {}).get("country", "United States"),
            "latitude": venue.get("address", {}).get("latitude", 0.0),
            "longitude": venue.get("address", {}).get("longitude", 0.0),
            "organizer_name": organizer.get("name", ""),
            "organizer_id": str(organizer.get("id", "")),
            "ticket_min_price": str((ticket.get("minimum_ticket_price") or {}).get("display", "0.00 USD")),
            "ticket_max_price": str((ticket.get("maximum_ticket_price") or {}).get("display", "0.00 USD")),
            "is_free": ticket.get("is_free", False),
            "categories": [tag.get("display_name") for tag in (event.get("tags") or []) if isinstance(tag, dict)],
            "image_url": (image.get("original") or {}).get("url") or image.get("url", ""),
            "event_url": event.get("url", ""),
            "attendee_count": 0,  # Not available in Eventbrite API
            "source": "eventbrite"
        }
    
    def fetch_events(self, location_id: str = "85977539", max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch events from Eventbrite API
        
        Args:
            location_id: Eventbrite location ID (85977539 for NYC, 85922351 for Palo Alto)
            max_pages: Maximum number of pages to fetch
        
        Returns:
            List of normalized event dictionaries
        """
        all_events = []
        
        try:
            for page in range(1, max_pages + 1):
                logger.info(f"Fetching Eventbrite events - page {page}")
                
                payload = self._create_search_payload(location_id, page, 20)
                params = {"stable_id": "3eff2ab4-0f8b-48c5-bae5-fa33a68f2342"}
                
                response = self.session.post(
                    self.base_url,
                    params=params,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                events = (data.get("events", {}).get("results")) or []
                
                if not events:
                    logger.info(f"No more events found on page {page}")
                    break
                
                # Normalize events
                normalized_events = [self._normalize_event(event) for event in events]
                all_events.extend(normalized_events)
                
                logger.info(f"Fetched {len(normalized_events)} events from page {page}")
                
                # Small delay to be respectful to the API
                import time
                time.sleep(1)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching events from Eventbrite: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching events: {e}")
            raise
        
        logger.info(f"Total events fetched: {len(all_events)}")
        return all_events
    
    def fetch_events_by_coordinates(self, latitude: float, longitude: float, radius_km: float = 10.0) -> List[Dict[str, Any]]:
        """
        Fetch events near specific coordinates
        Note: Eventbrite API doesn't directly support coordinate-based search,
        so this uses the NYC location ID by default
        """
        # For now, we'll use NYC as the default location
        # In a full implementation, you'd need to map coordinates to Eventbrite location IDs
        logger.info(f"Fetching events near coordinates: {latitude}, {longitude}")
        return self.fetch_events(location_id="85977539")  # NYC location ID

def fetch_events(location_id: str = "85977539", max_pages: int = 5) -> List[Dict[str, Any]]:
    """Convenience function to fetch events"""
    crawler = EventbriteCrawler()
    return crawler.fetch_events(location_id, max_pages)

def fetch_events_by_location(latitude: float, longitude: float, radius_km: float = 10.0) -> List[Dict[str, Any]]:
    """Convenience function to fetch events by coordinates"""
    crawler = EventbriteCrawler()
    return crawler.fetch_events_by_coordinates(latitude, longitude, radius_km)

if __name__ == "__main__":
    # Test the crawler
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Eventbrite crawler...")
    events = fetch_events(max_pages=2)  # Test with just 2 pages
    
    print(f"Fetched {len(events)} events")
    if events:
        print("Sample event:")
        print(json.dumps(events[0], indent=2))
    
    # Save to file for inspection
    with open("test_events.json", "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    print("Events saved to test_events.json")
