import requests
from datetime import datetime
import os

class EventProvider:
    def search(self, **kwargs):
        raise NotImplementedError

class EventbriteProvider(EventProvider):
    """Eventbrite crawler using destination search API"""
    
    def __init__(self, api_key=None):
        self.base_url = "https://www.eventbrite.com/api/v3/destination/search/"
        self.session = requests.Session()
        self._setup_session()
        
        # Verified location IDs for major cities
        self.location_ids = {
            "san_francisco": "85922583",
            "new_york": "85977539",
            "los_angeles": "85923517",
            "miami": "85933669",
            "chicago": "85940195",
            "seattle": "101730401",
            "boston": "85950361",
        }
    
    def _setup_session(self):
        """Setup session with required headers"""
        self.session.headers.update({
            "referer": "https://www.eventbrite.com/d/ny--new-york/all-events/?page=1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "x-csrftoken": "d104f5aaa1ff11f091e53b19e64a90d8",
            "x-requested-with": "XMLHttpRequest",
        })
        self.session.cookies.update({
            "csrftoken": "d104f5aaa1ff11f091e53b19e64a90d8",
        })
    
    def _get_location_id(self, city_name: str) -> str:
        """Get Eventbrite location ID for a city"""
        city_key = city_name.lower().strip().replace(" ", "_")
        return self.location_ids.get(city_key)

    def get_supported_cities(self):
        """Get list of supported city names"""
        return list(self.location_ids.keys())
    
    def _format_price(self, price_str: str, is_free: bool) -> str:
        """Format price string"""
        if is_free or not price_str:
            return "Free"
        clean_price = price_str.replace("USD", "").strip()
        try:
            price_float = float(clean_price)
            if price_float == 0.0:
                return "Free"
            return f"{price_float:g}"
        except:
            return clean_price or "Free"
    
    def search(self, city, category=None):
        """Search events by city"""
        location_id = self._get_location_id(city)
        if not location_id:
            print(f"Eventbrite: City '{city}' not supported")
            return []
        
        payload = {
            "event_search": {
                "dates": "current_future",
                "dedup": True,
                "places": [location_id],
                "page": 1,
                "page_size": 20,
                "online_events_only": False,
            },
            "expand.destination_event": [
                "primary_venue", "image", "ticket_availability",
                "primary_organizer", "event_sales_status"
            ],
        }
        
        # Add category filter if provided
        if category:
            payload["event_search"]["q"] = category
        
        
        try:
            response = self.session.post(self.base_url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            events = []
            for item in data.get("events", {}).get("results", []):
                venue = item.get("primary_venue") or {}
                venue_addr = venue.get("address") or {}
                ticket = item.get("ticket_availability") or {}
                image = item.get("image") or {}
                organizer = item.get("primary_organizer") or {}
                
                # Price formatting
                is_free = ticket.get("is_free", False)
                min_price = "Free"
                max_price = "Free"
                if not is_free:
                    min_ticket = ticket.get("minimum_ticket_price") or {}
                    max_ticket = ticket.get("maximum_ticket_price") or {}
                    min_price = self._format_price(min_ticket.get("display", ""), is_free)
                    max_price = self._format_price(max_ticket.get("display", ""), is_free)
                
                events.append({
                    "event_id": str(item.get("id", "")),
                    "title": item.get("name", ""),
                    "description": item.get("summary", ""),
                    "start_datetime": item.get("start_date", ""),
                    "end_datetime": item.get("end_date", ""),
                    "timezone": item.get("timezone", "UTC"),
                    "venue_name": venue.get("name", ""),
                    "venue_city": venue_addr.get("city", ""),
                    "venue_country": venue_addr.get("country", ""),
                    "latitude": venue_addr.get("latitude", 0.0),
                    "longitude": venue_addr.get("longitude", 0.0),
                    "organizer_name": organizer.get("name", ""),
                    "ticket_min_price": min_price,
                    "ticket_max_price": max_price,
                    "is_free": is_free,
                    "categories": [tag.get("display_name", "") for tag in (item.get("tags") or [])],
                    "image_url": (image.get("original") or {}).get("url", ""),
                    "event_url": item.get("url", ""),
                    "source": "eventbrite"
                })
            return events
        except Exception as e:
            print(f"Eventbrite error: {e}")
            return []


class MeetupProvider(EventProvider):
    def __init__(self, token):
        self.token = token
        self.url = "https://api.meetup.com/gql-ext"

    def search(self, lat, lon, query="events", radius=50):
        if not self.token:
            print("Meetup token missing")
            return []

        gql_query = """
        query ($lat: Float!, $lon: Float!, $query: String!) {
          keywordSearch(filter: { lat: $lat, lon: $lon, query: $query, source: EVENTS }) {
            edges {
              node {
                id
                title
                eventUrl
                dateTime
                description
                venue {
                  name
                  city
                }
              }
            }
          }
        }
        """
        
        variables = {
            "lat": float(lat),
            "lon": float(lon),
            "query": query
        }

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.url, headers=headers, json={'query': gql_query, 'variables': variables})
            response.raise_for_status()
            data = response.json()
            
            events = []
            edges = data.get("data", {}).get("keywordSearch", {}).get("edges", [])
            for edge in edges:
                node = edge["node"]
                venue = node.get("venue") or {}
                events.append({
                    "event_id": str(node.get("id", "")),
                    "title": node.get("title", ""),
                    "description": node.get("description", ""),
                    "start_datetime": node.get("dateTime", ""),
                    "end_datetime": "",
                    "timezone": "UTC",
                    "venue_name": venue.get("name", ""),
                    "venue_city": venue.get("city", ""),
                    "venue_country": "",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "organizer_name": "",
                    "ticket_min_price": "Free",
                    "ticket_max_price": "Free",
                    "is_free": True,
                    "categories": [],
                    "image_url": "",
                    "event_url": node.get("eventUrl", ""),
                    "source": "meetup"
                })
            return events
        except Exception as e:
            print(f"Meetup error: {e}")
            return []

class AllEventsProvider(EventProvider):
    def __init__(self, api_key=None):
        # API key not required for this endpoint; kept for compatibility
        self.api_key = api_key
        self.url = "https://allevents.in/api/index.php/events/web/qs/search_v1"

    def search(self, city, category="events", lat=None, lon=None):

        # Use provided coordinates or geocode city to improve accuracy
        if lat is None or lon is None:
            print(f"AllEvents: Could not geocode city '{city}'")
            return []
        cookies = {
            "FPID": "FPID2.2.eboPeLs04b9qsXo1MCpRek3XeCf%2F4q7lCGF86c9eaUk%3D.1760280802",
        }

        headers = {
            "referer": "https://allevents.in/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        }
        
        json_data = {
            "query": category if category != "events" else "",
            "latitude": str(lat),
            "longitude": str(lon),
            "city": city,
            'region_code': 'US',
            "search_scope": "city",
        }

        try:
            response = requests.post(self.url, headers=headers, json=json_data, cookies=cookies)
            response.raise_for_status()
            # Guard against empty or non-JSON responses for better debugging
            if not response.text.strip():
                print(f"AllEvents: empty response body (status {response.status_code}) for city={city}, category={category}")
                return []
            try:
                data = response.json()
            except Exception as parse_err:
                preview = response.text[:200].replace("\n", " ")
                print(f"AllEvents: non-JSON response ({parse_err}), status {response.status_code}, preview: {preview!r}")
                return []
            
            events = []
            items = data.get("events") or data.get("global_events") or []
            for item in items:
                venue = item.get("venue", {})
                ticket = item.get("ticket", {})
                
                # Parse ticket pricing
                min_price = "Free"
                max_price = "Free"
                is_free = True
                if ticket.get("has_tickets", False):
                    min_val = ticket.get("min_ticket_price", "0.00")
                    max_val = ticket.get("max_ticket_price", "0.00")
                    try:
                        min_float = float(min_val) if min_val else 0.0
                        max_float = float(max_val) if max_val else 0.0
                        if min_float > 0 or max_float > 0:
                            is_free = False
                            currency = ticket.get("ticket_currency", "")
                            min_price = f"{currency} {min_float:g}" if currency else f"{min_float:g}"
                            max_price = f"{currency} {max_float:g}" if currency else f"{max_float:g}"
                    except (ValueError, TypeError):
                        pass
                
                # Parse start time (Unix timestamp)
                start_time = item.get("start_time", "")
                start_datetime = ""
                if start_time:
                    try:
                        start_datetime = datetime.fromtimestamp(int(start_time)).isoformat()
                    except (ValueError, TypeError):
                        start_datetime = item.get("start_time_display", "")
                
                # Get venue coordinates
                venue_lat = 0.0
                venue_lon = 0.0
                try:
                    venue_lat = float(venue.get("latitude", 0)) if venue.get("latitude") else 0.0
                    venue_lon = float(venue.get("longitude", 0)) if venue.get("longitude") else 0.0
                except (ValueError, TypeError):
                    pass
                
                events.append({
                    "event_id": str(item.get("event_id", "")),
                    "title": item.get("eventname", ""),
                    "description": venue.get("full_address", ""),
                    "start_datetime": start_datetime or item.get("start_time_display", ""),
                    "end_datetime": "",
                    "timezone": "UTC",
                    "venue_name": item.get("location", ""),
                    "venue_city": venue.get("city", city),
                    "venue_country": venue.get("country", ""),
                    "latitude": venue_lat,
                    "longitude": venue_lon,
                    "organizer_name": "",
                    "ticket_min_price": min_price,
                    "ticket_max_price": max_price,
                    "is_free": is_free,
                    "categories": [],
                    "image_url": item.get("banner_url", item.get("thumb_url", "")),
                    "event_url": item.get("event_url", ""),
                    "source": "allevents"
                })
            # Keep only events matching the requested city
            target_city = city.strip().lower()
            events = [
                e for e in events
                if str(e.get("venue_city", "")).strip().lower() == target_city
            ]
            # Cap at 20 events for consistency
            events = events[:20]
            return events
        except Exception as e:
            print(f"AllEvents error: {e}")
            return []

class TicketmasterProvider(EventProvider):
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://app.ticketmaster.com/discovery/v2/events.json"

    def search(self, city, category="music"):
        if not self.api_key:
            print("Ticketmaster key missing")
            return []

        params = {
            "apikey": self.api_key,
            "city": city,
            "classificationName": category,
            "sort": "date,asc",
            "size": 20
        }

        try:
            response = requests.get(self.url, params=params)
            response.raise_for_status()
            data = response.json()
            
            events = []
            embedded = data.get("_embedded", {})
            for item in embedded.get("events", []):
                venue = item.get("_embedded", {}).get("venues", [{}])[0]
                venue_location = venue.get("location", {})
                images = item.get("images", [])
                image_url = images[0].get("url", "") if images else ""
                price_ranges = item.get("priceRanges", [])
                
                min_price = "Free"
                max_price = "Free"
                is_free = True
                if price_ranges:
                    min_val = price_ranges[0].get("min", 0)
                    max_val = price_ranges[0].get("max", 0)
                    if min_val > 0:
                        is_free = False
                        min_price = f"{min_val:g}"
                        max_price = f"{max_val:g}"
                
                events.append({
                    "event_id": str(item.get("id", "")),
                    "title": item.get("name", ""),
                    "description": item.get("info", ""),
                    "start_datetime": item.get("dates", {}).get("start", {}).get("localDate", ""),
                    "end_datetime": "",
                    "timezone": item.get("dates", {}).get("timezone", "UTC"),
                    "venue_name": venue.get("name", ""),
                    "venue_city": venue.get("city", {}).get("name", ""),
                    "venue_country": venue.get("country", {}).get("countryCode", ""),
                    "latitude": float(venue_location.get("latitude", 0.0)),
                    "longitude": float(venue_location.get("longitude", 0.0)),
                    "organizer_name": "",
                    "ticket_min_price": min_price,
                    "ticket_max_price": max_price,
                    "is_free": is_free,
                    "categories": [c.get("name", "") for c in item.get("classifications", [])],
                    "image_url": image_url,
                    "event_url": item.get("url", ""),
                    "source": "ticketmaster"
                })
            return events
        except Exception as e:
            print(f"Ticketmaster error: {e}")
            return []

class SerpApiProvider(EventProvider):
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://serpapi.com/search"

    def search(self, city, category="events"):
        if not self.api_key:
            print("SerpApi key missing")
            return []

        params = {
            "api_key": self.api_key,
            "engine": "google_events",
            "q": f"{category} in {city}",
            "hl": "en",
            "gl": "us"
        }

        try:
            response = requests.get(self.url, params=params)
            response.raise_for_status()
            data = response.json()
            
            events = []
            for item in data.get("events_results", []):
                date_info = item.get("date", {})
                address = item.get("address", [])
                events.append({
                    "event_id": str(item.get("link", "")),
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "start_datetime": date_info.get("start_date", ""),
                    "end_datetime": date_info.get("end_date", ""),
                    "timezone": "UTC",
                    "venue_name": item.get("venue", {}).get("name", ""),
                    "venue_city": address[0] if len(address) > 0 else "",
                    "venue_country": "",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "organizer_name": "",
                    "ticket_min_price": "Free",
                    "ticket_max_price": "Free",
                    "is_free": True,
                    "categories": [],
                    "image_url": item.get("thumbnail", ""),
                    "event_url": item.get("link", ""),
                    "source": "serpapi"
                })
            return events
        except Exception as e:
            print(f"SerpApi error: {e}")
            return []

class PredictHQProvider(EventProvider):
    def __init__(self, token):
        self.token = token
        self.url = "https://api.predicthq.com/v1/events/"

    def search(self, lat, lon, category=None, radius="10km"):
        if not self.token:
            print("PredictHQ token missing")
            return []

        headers = {"Authorization": f"Bearer {self.token}"}
        params = {
            "q": category if category else "events",
            "within": f"{radius}@{lat},{lon}",
            "sort": "start",
            "limit": 20
        }

        try:
            response = requests.get(self.url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            events = []
            for item in data.get("results", []):
                location = item.get("location", [])
                events.append({
                    "event_id": str(item.get("id", "")),
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "start_datetime": item.get("start", ""),
                    "end_datetime": item.get("end", ""),
                    "timezone": item.get("timezone", "UTC"),
                    "venue_name": "",
                    "venue_city": "",
                    "venue_country": item.get("country", ""),
                    "latitude": location[1] if len(location) > 1 else 0.0,
                    "longitude": location[0] if len(location) > 0 else 0.0,
                    "organizer_name": "",
                    "ticket_min_price": "Free",
                    "ticket_max_price": "Free",
                    "is_free": True,
                    "categories": item.get("category", "").split(",") if item.get("category") else [],
                    "image_url": "",
                    "event_url": "https://www.predicthq.com",
                    "source": "predicthq"
                })
            return events
        except Exception as e:
            print(f"PredictHQ error: {e}")
            return []
