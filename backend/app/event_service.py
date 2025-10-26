#!/usr/bin/env python3
"""
Unified Event Crawler supporting multiple sources (Eventbrite, Sohu) with AI normalization
"""

import requests
import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import time
from openai import OpenAI
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class EventbriteCrawler:
    """
    Enhanced Eventbrite crawler that supports multiple locations
    """
    
    def __init__(self):
        self.base_url = "https://www.eventbrite.com/api/v3/destination/search/"
        self.session = requests.Session()
        self._setup_session()
        
        # Common Eventbrite location IDs for major cities
        self.location_ids = {
            # US Cities
            "new_york": "85977539",
            "los_angeles": "85975577", 
            "san_francisco": "85922351",
            "chicago": "85977485",
            "boston": "85977482",
            "seattle": "85977488",
            "austin": "85977481",
            "denver": "85977483",
            "miami": "85977484",
            "atlanta": "85977480",
            "philadelphia": "85977486",
            "phoenix": "85977487",
            "las_vegas": "85977489",
            "san_diego": "85977490",
            "portland": "85977491",
            "nashville": "85977492",
            "orlando": "85977493",
            "houston": "85977494",
            "dallas": "85977495",
            "detroit": "85977496",
            
            # International Cities
            "london": "85977501",
            "paris": "85977502", 
            "tokyo": "85977503",
            "sydney": "85977504",
            "toronto": "85977505",
            "berlin": "85977506",
            "amsterdam": "85977507",
            "dublin": "85977508",
            "madrid": "85977509",
            "rome": "85977510",
            "singapore": "85977511",
            "hong_kong": "85977512",
            "mumbai": "85977513",
            "sao_paulo": "85977514",
            "mexico_city": "85977515",
        }
        
        # City name mappings for user-friendly input
        self.city_aliases = {
            "nyc": "new_york",
            "new york": "new_york",
            "ny": "new_york",
            "la": "los_angeles",
            "los angeles": "los_angeles",
            "sf": "san_francisco",
            "san francisco": "san_francisco",
            "bay area": "san_francisco",
            "chicago": "chicago",
            "boston": "boston",
            "seattle": "seattle",
            "austin": "austin",
            "denver": "denver",
            "miami": "miami",
            "atlanta": "atlanta",
            "philadelphia": "philadelphia",
            "philly": "philadelphia",
            "phoenix": "phoenix",
            "las vegas": "las_vegas",
            "vegas": "las_vegas",
            "san diego": "san_diego",
            "portland": "portland",
            "nashville": "nashville",
            "orlando": "orlando",
            "houston": "houston",
            "dallas": "dallas",
            "detroit": "detroit",
            "london": "london",
            "paris": "paris",
            "tokyo": "tokyo",
            "sydney": "sydney",
            "toronto": "toronto",
            "berlin": "berlin",
            "amsterdam": "amsterdam",
            "dublin": "dublin",
            "madrid": "madrid",
            "rome": "rome",
            "singapore": "singapore",
            "hong kong": "hong_kong",
            "mumbai": "mumbai",
            "sao paulo": "sao_paulo",
            "mexico city": "mexico_city",
        }
    
    def _setup_session(self):
        """Setup session with headers and cookies"""
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
    
    def get_location_id(self, city_name: str) -> Optional[str]:
        """
        Get Eventbrite location ID for a city
        
        Args:
            city_name: City name (e.g., "new york", "nyc", "san francisco")
            
        Returns:
            Eventbrite location ID or None if not found
        """
        # Normalize city name
        city_key = city_name.lower().strip()
        
        # Check aliases first
        if city_key in self.city_aliases:
            city_key = self.city_aliases[city_key]
        
        # Return location ID
        return self.location_ids.get(city_key)
    
    def _format_price(self, price_str: str, is_free: bool) -> str:
        """
        Format price string to remove USD suffix and trailing zeros
        
        Args:
            price_str: Raw price string from Eventbrite (e.g., "22.48 USD", "0.00 USD")
            is_free: Whether the event is free
            
        Returns:
            Formatted price string (e.g., "Free", "22.48", "15")
        """
        if is_free or not price_str:
            return "Free"
        
        # Remove USD suffix and whitespace
        clean_price = price_str.replace("USD", "").strip()
        
        try:
            # Convert to float to remove trailing zeros, then back to string
            price_float = float(clean_price)
            
            # If it's zero, return Free
            if price_float == 0.0:
                return "Free"
            
            # Format without trailing zeros
            if price_float == int(price_float):
                return str(int(price_float))  # e.g., 15.00 -> 15
            else:
                return f"{price_float:g}"  # e.g., 22.48 -> 22.48, 15.50 -> 15.5
                
        except (ValueError, TypeError):
            # If parsing fails, return the original string cleaned up
            return clean_price or "Free"

    def get_supported_cities(self) -> List[str]:
        """Get list of supported city names"""
        return list(self.city_aliases.keys())
    
    def _create_search_payload(self, location_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Create search payload for Eventbrite API"""
        return {
            "event_search": {
                "dates": "current_future",
                "dedup": True,
                "places": [location_id],
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
    
    def _normalize_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize event data"""
        venue = event.get("primary_venue") or {}
        organizer = event.get("primary_organizer") or {}
        ticket = event.get("ticket_availability") or {}
        image = event.get("image") or {}
        
        # Extract dates
        start_date = event.get("start_date")
        end_date = event.get("end_date")
        
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
        
        # Safely handle ticket pricing
        min_price = "0.00"
        max_price = "0.00"
        is_free = False
        
        if ticket:
            min_ticket = ticket.get("minimum_ticket_price")
            max_ticket = ticket.get("maximum_ticket_price")
            is_free = ticket.get("is_free", False)
            
            if min_ticket:
                min_price_raw = min_ticket.get("display", "0.00")
                # Clean up price formatting - remove USD suffix and trailing zeros
                min_price = self._format_price(min_price_raw, is_free)
                # Update is_free based on formatted price
                if min_price == "Free":
                    is_free = True
            
            if max_ticket:
                max_price_raw = max_ticket.get("display", "0.00")
                max_price = self._format_price(max_price_raw, is_free)
        
        # Safely handle venue address
        venue_address = venue.get("address") or {}
        
        return {
            "event_id": str(event.get("id", "")),
            "title": event.get("name", ""),
            "description": event.get("summary", ""),
            "start_datetime": start_datetime or "",
            "end_datetime": end_datetime or "",
            "timezone": event.get("timezone", "UTC"),
            "venue_name": venue.get("name", ""),
            "venue_city": venue_address.get("city", ""),
            "venue_country": venue_address.get("country", ""),
            "latitude": venue_address.get("latitude", 0.0),
            "longitude": venue_address.get("longitude", 0.0),
            "organizer_name": organizer.get("name", ""),
            "organizer_id": str(organizer.get("id", "")),
            "ticket_min_price": min_price,
            "ticket_max_price": max_price,
            "is_free": is_free,
            "categories": [tag.get("display_name") for tag in (event.get("tags") or []) if isinstance(tag, dict)],
            "image_url": (image.get("original") or {}).get("url") or image.get("url", "") if image else "",
            "event_url": event.get("url", ""),
            "attendee_count": 0,
            "source": "eventbrite"
        }
    
    def fetch_events_by_city(self, city_name: str, max_pages: int = 3) -> List[Dict[str, Any]]:
        """
        Fetch events for a specific city using real Eventbrite API

        Args:
            city_name: City name (e.g., "san francisco", "nyc", "london")
            max_pages: Maximum number of pages to fetch

        Returns:
            List of normalized event dictionaries
        """
        logger.info(f"📅 EventbriteCrawler: Starting to fetch events for '{city_name}'")

        # Map city name to Eventbrite location ID
        location_id = self._get_eventbrite_location_id(city_name)
        logger.info(f"📅 EventbriteCrawler: Mapped '{city_name}' to location ID {location_id}")

        real_events = self.fetch_events(location_id=location_id, max_pages=max_pages)

        if real_events and len(real_events) > 0:
            logger.info(f"📅 EventbriteCrawler: Retrieved {len(real_events)} real events for {city_name}")
        else:
            logger.warning(f"📅 EventbriteCrawler: No events found for {city_name}")

        return real_events
    
    def _get_eventbrite_location_id(self, city_name: str) -> str:
        """
        Map city name to Eventbrite location ID
        
        Args:
            city_name: City name (e.g., "san francisco", "nyc", "london")
            
        Returns:
            Eventbrite location ID
        """
        # Eventbrite location ID mapping - US Cities with real location IDs
        location_mapping = {
            # Major US Cities with actual location IDs
            "new york": "85977539",           # NYC
            "nyc": "85977539",               # NYC
            "brooklyn": "85977605",          # Brooklyn, NY
            "queens": "85977601",            # Queens, NY
            "manhattan": "85977539",         # Manhattan (using NYC)
            
            "san francisco": "85922351",     # Palo Alto (closest to SF)
            "santa clara": "85922355",       # Santa Clara, CA
            "sacramento": "85922413",        # Sacramento, CA
            "davis": "85922405",             # Davis, CA
            "burlingame": "85922509",        # Burlingame, CA
            "morgan hill": "85922359",       # Morgan Hill, CA
            
            # NY State cities
            "syracuse": "85977803",          # Syracuse, NY
            "greenwich": "85977609",         # Greenwich, NY
            "melville": "85977611",          # Melville, NY
            "hudson": "85977813",            # Hudson, NY
            "poughkeepsie": "85977817",      # Poughkeepsie, NY
            "catskill": "85977807",          # Catskill, NY
            "kinderhook": "85977811",        # Kinderhook, NY
            "gowanda": "85977541",           # Gowanda, NY
            "olean": "85977543",             # Olean, NY
            
            # Major cities that don't have specific IDs yet (fallback to NYC)
            "los angeles": "85977539",       # NYC events for now
            "chicago": "85977539",           # NYC events for now
            "boston": "85977539",            # NYC events for now
            "seattle": "85977539",           # NYC events for now
            "austin": "85977539",            # NYC events for now
            "miami": "85977539",             # NYC events for now
            "denver": "85977539",            # NYC events for now
            "atlanta": "85977539",           # NYC events for now
            "phoenix": "85977539",           # NYC events for now
            "detroit": "85977539",           # NYC events for now
        }
        
        # Clean city name
        clean_city = city_name.lower().strip().replace('_', ' ')
        
        # Return mapped ID or default to NYC
        return location_mapping.get(clean_city, "85977539")

    def fetch_events_multiple_cities(self, cities: List[str], max_pages_per_city: int = 2) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch events from multiple cities
        
        Args:
            cities: List of city names
            max_pages_per_city: Maximum pages to fetch per city
            
        Returns:
            Dictionary mapping city names to their events
        """
        results = {}
        
        for city in cities:
            try:
                events = self.fetch_events_by_city(city, max_pages_per_city)
                results[city] = events
                logger.info(f"Successfully fetched {len(events)} events for {city}")
            except Exception as e:
                logger.error(f"Failed to fetch events for {city}: {e}")
                results[city] = []
        
        return results
    
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

class SohuCrawler:
    """Sohu article crawler with AI normalization"""

    def __init__(self):
        # City profiles for Sohu articles - using same format as EventbriteCrawler
        self.city_profiles = {
            "new_york": "https://mp.sohu.com/profile?xpt=aGFvY2hpYnVueUBzb2h1LmNvbQ==",
        }

    def fetch_events_by_city(self, city_name: str) -> List[Dict[str, Any]]:
        """Fetch and normalize Sohu articles for a city"""
        logger.info(f"📰 SohuCrawler: Starting to fetch articles for '{city_name}'")
        try:
            profile_url = self._get_city_profile(city_name)
            if not profile_url:
                logger.warning(f"📰 SohuCrawler: No Sohu profile found for {city_name}")
                return []

            logger.info(f"📰 SohuCrawler: Found profile URL for {city_name}")
            html = self._fetch_sohu_profile(profile_url)
            articles = self._parse_sohu_articles(html)
            logger.info(f"📰 SohuCrawler: Parsed {len(articles)} articles from profile")

            # Enhance each article with full content
            enhanced_articles = []
            for i, article in enumerate(articles[:10]):  # Limit to 10 articles
                if article.get('article_url'):
                    try:
                        logger.debug(f"📰 SohuCrawler: Fetching content for article {i+1}/{min(len(articles), 10)}")
                        article_html = self._fetch_sohu_article(article['article_url'])
                        content_data = self._parse_sohu_article_content(article_html)
                        article.update(content_data)
                        enhanced_articles.append(article)
                    except Exception as e:
                        logger.error(f"📰 SohuCrawler: Failed to fetch article content: {e}")
                        enhanced_articles.append(article)

            logger.info(f"📰 SohuCrawler: Enhanced {len(enhanced_articles)} articles with full content")

            # Normalize articles to event format
            normalized_events = []
            for article in enhanced_articles:
                normalized = self._normalize_sohu_event(article)
                normalized_events.append(normalized)

            logger.info(f"📰 SohuCrawler: Successfully normalized {len(normalized_events)} Sohu articles to events")
            return normalized_events

        except Exception as e:
            logger.error(f"📰 SohuCrawler: Error fetching Sohu events for {city_name}: {e}")
            return []

    def _get_city_profile(self, city_name: str) -> Optional[str]:
        """Get Sohu profile URL for a city"""
        city_key = city_name.lower().strip().replace(' ', '_').replace('-', '_')
        return self.city_profiles.get(city_key)

    def _fetch_sohu_profile(self, profile_url: str) -> str:
        """Fetch Sohu profile HTML with cookies"""
        cookies = {
            'SUV': '1761456502828odinqfcO',
            'reqtype': 'pc',
            'gidinf': 'x099980107ee1b829c17bac31000396b6596aefaa33b',
            '_dfp': 'tgWd/PeOqyhBKzfqD5Rx5QL5+GI0g1J11Z0srNbBlIk=',
            'clt': '1761456516',
            'cld': '20251026132836',
            't': '1761463759249',
        }

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        }

        response = requests.get(profile_url, cookies=cookies, headers=headers)
        return response.text

    def _fetch_sohu_article(self, article_url: str) -> str:
        """Fetch individual Sohu article"""
        cookies = {
            'SUV': '1761456502828odinqfcO',
            'reqtype': 'pc',
            'gidinf': 'x099980107ee1b829c17bac31000396b6596aefaa33b',
            '_dfp': 'tgWd/PeOqyhBKzfqD5Rx5QL5+GI0g1J11Z0srNbBlIk=',
            'clt': '1761456516',
            'cld': '20251026132836',
            '_ga': 'GA1.1.756759890.1761461989',
            '_ym_uid': '1761461990920399414',
        }

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Referer': 'https://mp.sohu.com/profile?xpt=aGFvY2hpYnVueUBzb2h1LmNvbQ==',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        }

        response = requests.get(article_url, cookies=cookies, headers=headers)
        return response.text

    def _parse_sohu_articles(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse Sohu articles from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        articles = []

        article_items = soup.find_all('div', class_='TPLImageTextFeedItem')

        for item in article_items:
            try:
                article_data = {}

                # Extract title
                title_elem = item.find('div', class_='item-text-content-title')
                article_data['title'] = title_elem.get_text(strip=True) if title_elem else "No title"

                # Extract description
                desc_elem = item.find('div', class_='item-text-content-description')
                article_data['description'] = desc_elem.get_text(strip=True) if desc_elem else "No description"

                # Extract article URL
                link_elem = item.find('a', class_='tpl-image-text-feed-item-content')
                if link_elem and link_elem.get('href'):
                    article_url = link_elem['href']
                    if article_url.startswith('//'):
                        article_url = 'https:' + article_url
                    elif article_url.startswith('/'):
                        article_url = 'https://www.sohu.com' + article_url
                    article_data['article_url'] = article_url

                articles.append(article_data)

            except Exception as e:
                logger.error(f"Error parsing article: {e}")
                continue

        return articles

    def _parse_sohu_article_content(self, html_content: str) -> Dict[str, Any]:
        """Parse individual Sohu article content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        article_data = {}

        # Extract title
        title_meta = soup.find('meta', property='og:title')
        if title_meta and title_meta.get('content'):
            article_data['title'] = title_meta['content']
        else:
            title_tag = soup.find('title')
            article_data['title'] = title_tag.get_text(strip=True) if title_tag else "No title"

        # Extract description
        desc_meta = soup.find('meta', {'name': 'description'})
        if desc_meta and desc_meta.get('content'):
            article_data['description'] = desc_meta['content']
        else:
            og_desc = soup.find('meta', property='og:description')
            article_data['description'] = og_desc['content'] if og_desc and og_desc.get('content') else ""

        # Extract publish time
        time_meta = soup.find('meta', {'name': 'datePublished'}) or soup.find('meta', property='article:published_time')
        if time_meta and time_meta.get('content'):
            article_data['publish_time'] = time_meta['content']

        # Extract content paragraphs
        article_element = soup.find('article', {'class': 'article', 'id': 'mp-editor'})
        content_paragraphs = []

        if article_element:
            for element in article_element.find_all(['p', 'div']):
                if element.get('class') and ('lookall' in element.get('class') or 'hidden-content' in element.get('class')):
                    continue

                if element.name == 'p':
                    text = element.get_text(strip=True)
                    if text and not text.startswith('返回搜狐'):
                        content_paragraphs.append(text)

        article_data['content_paragraphs'] = content_paragraphs

        # Extract author
        author_meta = soup.find('meta', {'name': 'author'})
        if author_meta and author_meta.get('content'):
            article_data['author'] = author_meta['content']
        else:
            media_meta = soup.find('meta', {'name': 'mediaid'})
            article_data['author'] = media_meta['content'] if media_meta and media_meta.get('content') else "Unknown author"

        return article_data

    def _normalize_sohu_event(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to normalize Sohu article to standard event format"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")

            client = OpenAI(api_key=api_key)

            prompt = f"""
            Normalize this Sohu article into a standard event format.

            Raw article data: {json.dumps(article, indent=2)}

            Return JSON with these exact fields:
            {{
                "event_id": "sohu_unique_identifier",
                "title": "article title",
                "description": "brief description under 200 chars",
                "start_datetime": "ISO format datetime or empty string",
                "end_datetime": "ISO format datetime or empty string",
                "venue_name": "Online or location name",
                "venue_city": "city name if detectable",
                "organizer_name": "article author or Sohu",
                "ticket_min_price": "Free",
                "ticket_max_price": "Free",
                "is_free": true,
                "categories": ["Article", "News", "relevant topics"],
                "event_url": "article URL",
                "source": "sohu",
                "attendee_count": 0
            }}

            For articles about events, extract event details. For news articles, treat as informational content.
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.1
            )

            result = json.loads(response.choices[0].message.content.strip())

            # Ensure required fields
            required_fields = [
                "event_id", "title", "description", "start_datetime", "end_datetime",
                "venue_name", "venue_city", "organizer_name", "ticket_min_price",
                "ticket_max_price", "is_free", "categories", "event_url", "source"
            ]

            for field in required_fields:
                if field not in result:
                    if field in ["event_id"]:
                        result[field] = f"sohu_{hash(str(article))}"
                    elif field in ["start_datetime", "end_datetime", "venue_city"]:
                        result[field] = ""
                    elif field == "event_url":
                        result[field] = article.get('article_url', '')
                    elif field == "source":
                        result[field] = "sohu"
                    elif field == "is_free":
                        result[field] = True
                    elif field == "categories":
                        result[field] = ["Article", "News"]
                    elif field == "ticket_min_price":
                        result[field] = "Free"
                    elif field == "ticket_max_price":
                        result[field] = "Free"
                    elif field == "attendee_count":
                        result[field] = 0
                    else:
                        result[field] = f"Unknown {field}"

            return result

        except Exception as e:
            logger.error(f"Error normalizing Sohu event: {e}")
            # Return basic normalized event on error
            return {
                "event_id": f"sohu_{hash(str(article))}",
                "title": article.get("title", "Unknown Article"),
                "description": article.get("description", "No description available"),
                "start_datetime": article.get("publish_time", ""),
                "end_datetime": "",
                "venue_name": "Online",
                "venue_city": "",
                "organizer_name": article.get("author", "Sohu"),
                "ticket_min_price": "Free",
                "ticket_max_price": "Free",
                "is_free": True,
                "categories": ["Article", "News"],
                "event_url": article.get("article_url", ""),
                "source": "sohu",
                "attendee_count": 0
            }


class EventCrawler:
    """Unified event crawler orchestrating multiple sources"""

    def __init__(self):
        self.eventbrite_crawler = EventbriteCrawler()
        self.sohu_crawler = SohuCrawler()

    def fetch_events_by_city(self, city_name: str, sources: List[str] = None, max_pages: int = 3) -> List[Dict[str, Any]]:
        """
        Fetch and normalize events from multiple sources

        Args:
            city_name: City name (e.g., "new york", "san francisco")
            sources: List of sources ["eventbrite", "sohu"]
            max_pages: Max pages for Eventbrite

        Returns:
            List of normalized events
        """
        if sources is None:
            sources = ["eventbrite", "sohu"]

        all_events = []
        logger.info(f"🔍 Starting unified event search for '{city_name}' using sources: {sources}")

        # Fetch from Eventbrite
        if "eventbrite" in sources:
            logger.info(f"📅 Fetching events from Eventbrite for {city_name}...")
            try:
                events = self.eventbrite_crawler.fetch_events_by_city(city_name, max_pages)
                all_events.extend(events)
                logger.info(f"✅ Eventbrite: {len(events)} events found")
            except Exception as e:
                logger.error(f"❌ Eventbrite crawler failed: {e}")

        # Fetch from Sohu
        if "sohu" in sources:
            logger.info(f"📰 Fetching articles from Sohu for {city_name}...")
            try:
                articles = self.sohu_crawler.fetch_events_by_city(city_name)
                all_events.extend(articles)
                logger.info(f"✅ Sohu: {len(articles)} articles normalized to events")
            except Exception as e:
                logger.error(f"❌ Sohu crawler failed: {e}")

        logger.info(f"📊 Total events/articles collected: {len(all_events)} from {len(sources)} sources")
        return all_events


# Global instance for backward compatibility
event_crawler = EventCrawler()


def fetch_events_by_city(city_name: str, max_pages: int = 3) -> List[Dict[str, Any]]:
    """Convenience function - fetch from all sources"""
    return event_crawler.fetch_events_by_city(city_name, max_pages=max_pages)


def get_supported_cities() -> List[str]:
    """Get list of supported cities across all crawlers"""
    return list(event_crawler.eventbrite_crawler.city_aliases.keys())


if __name__ == "__main__":
    # Test the unified crawler
    logging.basicConfig(level=logging.INFO)

    print("Testing Unified Event Crawler")
    print("=" * 50)

    # Test Eventbrite
    print("\nFetching Eventbrite events...")
    eb_events = event_crawler.fetch_events_by_city("san francisco", sources=["eventbrite"], max_pages=1)
    print(f"Eventbrite: {len(eb_events)} events")

    # Test Sohu
    print("\nFetching Sohu articles...")
    sohu_events = event_crawler.fetch_events_by_city("new york", sources=["sohu"])
    print(f"Sohu: {len(sohu_events)} articles")

    # Test unified
    print("\nFetching from both sources...")
    all_events = event_crawler.fetch_events_by_city("new york", sources=["eventbrite", "sohu"], max_pages=1)
    print(f"Total: {len(all_events)} events/articles")

    if all_events:
        sample = all_events[0]
        print(f"\nSample event: {sample['title']}")
        print(f"Source: {sample['source']}")