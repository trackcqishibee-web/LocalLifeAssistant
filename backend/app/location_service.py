#!/usr/bin/env python3
"""
Zipcode-aware location resolver that maps US postal codes to supported cities.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

logger = logging.getLogger(__name__)


class LocationResolver:
    """Utility for detecting and resolving US zip codes to supported cities."""

    ZIP_REGEX = re.compile(r"\b\d{5}(?:-\d{4})?\b")
    CACHE_TTL_HOURS = 24

    # Map suburbs/neighborhoods to their primary metro areas
    CITY_ALIASES = {
        # New York metro
        "new york": "new york",
        "new york city": "new york",
        "nyc": "new york",
        "manhattan": "new york",
        "brooklyn": "new york",
        "queens": "new york",
        "bronx": "new york",
        "staten island": "new york",
        "jersey city": "new york",
        "hoboken": "new york",
        "long island city": "new york",
        "williamsburg": "new york",
        "prospect heights": "new york",
        "astoria": "new york",

        # Los Angeles metro
        "los angeles": "los angeles",
        "la": "los angeles",
        "hollywood": "los angeles",
        "santa monica": "los angeles",
        "pasadena": "los angeles",
        "burbank": "los angeles",
        "glendale": "los angeles",
        "west hollywood": "los angeles",
        "beverly hills": "los angeles",

        # San Francisco / Bay Area
        "san francisco": "san francisco",
        "sf": "san francisco",
        "palo alto": "san francisco",
        "mountain view": "san francisco",
        "sunnyvale": "san francisco",
        "san jose": "san francisco",
        "cupertino": "san francisco",
        "redwood city": "san francisco",
        "menlo park": "san francisco",
        "fremont": "san francisco",
        "hayward": "san francisco",
        "oakland": "san francisco",
        "berkeley": "san francisco",
        "daly city": "san francisco",
        "santa clara": "san francisco",

        # Other metros
        "chicago": "chicago",
        "boston": "boston",
        "cambridge": "boston",
        "somerville": "boston",
        "seattle": "seattle",
        "bellevue": "seattle",
        "redmond": "seattle",
        "miami": "miami",
        "austin": "austin",
        "denver": "denver",
        "portland": "portland",
        "phoenix": "phoenix",
        "las vegas": "las vegas",
        "atlanta": "atlanta",
    }

    def __init__(self):
        self.geolocator = Nominatim(user_agent="local_life_assistant")
        self.zip_cache: Dict[str, Dict[str, Any]] = {}

    def extract_zip_from_text(self, text: str) -> Optional[str]:
        """Return the first US zip code found in the text."""
        if not text:
            return None

        match = self.ZIP_REGEX.search(text)
        if not match:
            return None

        zip_code = match.group(0)
        # Normalize 9-digit zips (#####-####) down to 5 digits for geocoder
        return zip_code[:5]

    def resolve_zip(self, zip_code: str) -> Optional[Dict[str, Any]]:
        """Resolve a zip code to location metadata and canonical city."""
        if not zip_code:
            return None

        zip_code = zip_code[:5]
        cached = self.zip_cache.get(zip_code)
        if cached and self._is_cache_valid(cached["cached_at"]):
            return cached["data"]

        try:
            location = self.geolocator.geocode(
                {"postalcode": zip_code, "country": "United States"},
                addressdetails=True,
                timeout=10,
            )
        except (GeocoderTimedOut, GeocoderUnavailable) as exc:
            logger.warning(f"Geocoding failed for zip {zip_code}: {exc}")
            return cached["data"] if cached else None
        except Exception as exc:  # pragma: no cover - safety net
            logger.error(f"Unexpected geocoding error for zip {zip_code}: {exc}")
            return cached["data"] if cached else None

        if not location:
            logger.info(f"No geocoding result for zip {zip_code}")
            return None

        address = location.raw.get("address", {})
        resolved_city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("county")
        )
        state = address.get("state")
        canonical_city = self._normalize_city(resolved_city)

        data = {
            "zip_code": zip_code,
            "city": resolved_city,
            "state": state,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "canonical_city": canonical_city,
        }

        self.zip_cache[zip_code] = {
            "cached_at": datetime.utcnow(),
            "data": data,
        }

        logger.info(
            f"Resolved zip {zip_code} to {canonical_city or resolved_city} "
            f"({location.latitude}, {location.longitude})"
        )
        return data

    def _normalize_city(self, city: Optional[str]) -> Optional[str]:
        """Map suburb/neighborhood names to supported canonical cities."""
        if not city:
            return None

        return self.CITY_ALIASES.get(city.lower(), city.lower())

    def _is_cache_valid(self, cached_at: datetime) -> bool:
        """Check whether cached metadata is still valid."""
        age = datetime.utcnow() - cached_at
        return age < timedelta(hours=self.CACHE_TTL_HOURS)

