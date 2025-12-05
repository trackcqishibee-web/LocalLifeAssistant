import os
from .geocoding import GeocodingService
from .providers import EventbriteProvider, MeetupProvider, AllEventsProvider, TicketmasterProvider, SerpApiProvider, PredictHQProvider

class UnifiedEventService:
    def __init__(self):
        self.geocoder = GeocodingService()
        
        # Initialize providers with keys from environment
        self.eventbrite = EventbriteProvider(os.getenv("EVENTBRITE_TOKEN"))
        self.meetup = MeetupProvider(os.getenv("MEETUP_TOKEN"))
        self.allevents = AllEventsProvider(os.getenv("ALLEVENTS_KEY"))
        self.ticketmaster = TicketmasterProvider(os.getenv("TICKETMASTER_KEY"))
        self.serpapi = SerpApiProvider(os.getenv("SERPAPI_KEY"))
        self.predicthq = PredictHQProvider(os.getenv("PREDICTHQ_TOKEN"))
        
        # Supported event types
        self.supported_event_types = ['music', 'sports', 'nightlife', 'business', 'tech', 'dating']

    def get_supported_cities(self):
        """
        Get intersection of all providers' supported cities.
        Since most providers support any city via geocoding,
        we return Eventbrite's explicitly supported cities as the base set.
        """
        return self.eventbrite.get_supported_cities()
    
    def get_supported_events(self):
        """
        Get list of supported event types.
        """
        return self.supported_event_types

    def get_events(self, location_name, category="events"):
        all_events = []

        # 0. Preprocess location name
        # Convert location name from snake_case to title case
        location_name = location_name.lower().strip().replace("_", " ")
        location_name = location_name.title()
        
        # 1. Geocode the location
        lat, lon = self.geocoder.get_coordinates(location_name)
        
        # 2. Fetch from Eventbrite (uses city name, not lat/lon)
        print(f"Fetching Eventbrite for {location_name}...")
        all_events.extend(self.eventbrite.search(location_name, category))
        
        # 3. Fetch from Providers needing Lat/Lon
        if lat and lon:
            print(f"Fetching Meetup for {location_name} ({lat}, {lon})...")
            all_events.extend(self.meetup.search(lat, lon, category))
            
            print(f"Fetching PredictHQ for {location_name} ({lat}, {lon})...")
            all_events.extend(self.predicthq.search(lat, lon, category))
        else:
            print(f"Could not geocode {location_name}, skipping location-based providers.")

        # 4. Fetch from Providers needing City Name
        print(f"Fetching AllEvents for {location_name}...")
        all_events.extend(self.allevents.search(location_name, category, lat, lon))
        
        print(f"Fetching Ticketmaster for {location_name}...")
        all_events.extend(self.ticketmaster.search(location_name, category))
        
        print(f"Fetching SerpApi for {location_name}...")
        all_events.extend(self.serpapi.search(location_name, category))

        return all_events
