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
            "new_york": "85977539",
            # "los_angeles": "85975577", 
            "san_francisco": "85922583",
            # "palo_alto": "85922351",
            # "chicago": "85977485",
            # "boston": "85977482",
            # "seattle": "85977488",
            # "austin": "85977481",
            # "denver": "85977483",
            # "miami": "85977484",
            # "atlanta": "85977480",
            # "philadelphia": "85977486",
            # "phoenix": "85977487",
            # "las_vegas": "85977489",
            # "san_diego": "85977490",
            # "portland": "85977491",
            # "nashville": "85977492",
            # "orlando": "85977493",
            # "houston": "85977494",
            # "dallas": "85977495",
            # "detroit": "85977496",
            
            # International Cities
            # "london": "85977501",
            # "paris": "85977502", 
            # "tokyo": "85977503",
            # "sydney": "85977504",
            # "toronto": "85977505",
            # "berlin": "85977506",
            # "amsterdam": "85977507",
            # "dublin": "85977508",
            # "madrid": "85977509",
            # "rome": "85977510",
            # "singapore": "85977511",
            # "hong_kong": "85977512",
            # "mumbai": "85977513",
            # "sao_paulo": "85977514",
            # "mexico_city": "85977515",
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
            # "chicago": "chicago",
            # "boston": "boston",
            # "seattle": "seattle",
            # "austin": "austin",
            # "denver": "denver",
            # "miami": "miami",
            # "atlanta": "atlanta",
            # "philadelphia": "philadelphia",
            # "philly": "philadelphia",
            # "phoenix": "phoenix",
            # "las vegas": "las_vegas",
            # "vegas": "las_vegas",
            # "san diego": "san_diego",
            # "portland": "portland",
            # "nashville": "nashville",
            # "orlando": "orlando",
            # "houston": "houston",
            # "dallas": "dallas",
            # "detroit": "detroit",
            # "london": "london",
            # "paris": "paris",
            # "tokyo": "tokyo",
            # "sydney": "sydney",
            # "toronto": "toronto",
            # "berlin": "berlin",
            # "amsterdam": "amsterdam",
            # "dublin": "dublin",
            # "madrid": "madrid",
            # "rome": "rome",
            # "singapore": "singapore",
            # "hong kong": "hong_kong",
            # "mumbai": "mumbai",
            # "sao paulo": "sao_paulo",
            # "mexico city": "mexico_city",
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
        return list(self.location_ids.keys())
    
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
        location_id = self.get_location_id(city_name)
        logger.info(f"📅 EventbriteCrawler: Mapped '{city_name}' to location ID {location_id}")

        real_events = self.fetch_events(location_id=location_id, max_pages=max_pages)

        if real_events and len(real_events) > 0:
            logger.info(f"📅 EventbriteCrawler: Retrieved {len(real_events)} real events for {city_name}")
        else:
            logger.warning(f"📅 EventbriteCrawler: No events found for {city_name}")

        return real_events

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
            "new_york": "https://mp.sohu.com/profile?xpt=aGFvY2hpYnVueUBzb2h1LmNvbQ==", # 纽约好吃不
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
            for i, article in enumerate(articles):
                # Preserve image_url from raw article data
                image_url = article.get('image_url', '')
                if article.get('article_url'):
                    try:
                        logger.debug(f"📰 SohuCrawler: Fetching content for article {i+1}")
                        article_html = self._fetch_sohu_article(article['article_url'])
                        content_data = self._parse_sohu_article_content(article_html)
                        article.update(content_data)
                        enhanced_articles.append(article)
                    except Exception as e:
                        logger.error(f"📰 SohuCrawler: Failed to fetch article content: {e}")
                        enhanced_articles.append(article)
                else:
                        enhanced_articles.append(article)

                # Ensure image_url is preserved in enhanced article
                if image_url and 'image_url' not in enhanced_articles[-1]:
                    enhanced_articles[-1]['image_url'] = image_url

            logger.info(f"📰 SohuCrawler: Enhanced {len(enhanced_articles)} articles with full content")

            # Normalize articles to event format and filter out advertisements
            normalized_events = []
            for article in enhanced_articles:
                normalized = self._normalize_sohu_event(article, city_name)
                if normalized is not None:  # Filter out advertisements (None return value)
                    normalized_events.append(normalized)

            logger.info(f"📰 SohuCrawler: Successfully normalized {len(normalized_events)} Sohu articles to events (filtered {len(enhanced_articles) - len(normalized_events)} advertisements)")
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

                # Extract image URL from the article item
                image_elem = item.find('img')
                if image_elem and image_elem.get('src'):
                    image_url = image_elem['src']
                    # Convert relative URLs to absolute
                    if image_url.startswith('//'):
                        image_url = 'https:' + image_url
                    elif image_url.startswith('/'):
                        image_url = 'https://www.sohu.com' + image_url
                    article_data['image_url'] = image_url
                else:
                    article_data['image_url'] = ""

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

    def _is_sohu_advertisement(self, article: Dict[str, Any]) -> bool:
        """Use AI to determine if a Sohu article is an advertisement/promotional content"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                # If no API key, use basic keyword filtering as fallback
                return self._basic_advertisement_check(article)

            try:
                # Handle httpx compatibility issue by using older client setup
                try:
                    client = OpenAI(api_key=api_key)
                except TypeError as e:
                    if "proxies" in str(e):
                        # Create httpx client without proxy arguments that cause issues
                        import httpx
                        http_client = httpx.Client(
                            timeout=60.0,
                            follow_redirects=True
                        )
                        client = OpenAI(
                            api_key=api_key,
                            http_client=http_client
                        )
                    else:
                        raise e
            except (TypeError, ValueError) as e:
                logger.warning(f"OpenAI client initialization failed for ad filtering: {e}. Using basic check.")
                return self._basic_advertisement_check(article)

            title = article.get("title", "")
            description = article.get("description", "")
            content_paragraphs = article.get("content_paragraphs", [])
            full_content = " ".join(content_paragraphs) if content_paragraphs else ""

            # Combine all text for analysis
            combined_text = f"Title: {title}\nDescription: {description}\nContent: {full_content[:1000]}"  # Limit content length

            prompt = f"""
            Analyze this Chinese article from Sohu and determine if it is pure commercial advertisement content.

            Article content:
            {combined_text}

            Return only "true" if it is a pure advertisement, otherwise return "false".

            Filter OUT (return "true") for:
            - Pure product advertisements (drugs, supplements, gadgets, etc.)
            - Real estate listings and promotions
            - Financial services ads (loans, investments, insurance)
            - Generic business promotions without specific events
            - Spam or promotional content with no real value

            KEEP (return "false") for:
            - Restaurant reviews and recommendations
            - Event announcements and listings
            - Business openings with actual events
            - Cultural or entertainment events
            - News articles about businesses or events
            - Legitimate business information and reviews

            Only filter pure advertisements, not actual events or business listings.
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )

            result = response.choices[0].message.content.strip().lower()

            if result == "true":
                logger.info(f"📰 Filtered advertisement: {title[:50]}...")
                return True

            return False

        except Exception as e:
            logger.warning(f"AI advertisement filtering failed: {e}. Using basic check.")
            return self._basic_advertisement_check(article)

    def _basic_advertisement_check(self, article: Dict[str, Any]) -> bool:
        """Basic keyword-based advertisement detection as fallback"""
        title = article.get("title", "").lower()
        description = article.get("description", "").lower()
        content_paragraphs = article.get("content_paragraphs", [])
        full_content = " ".join(content_paragraphs).lower() if content_paragraphs else ""

        # Keywords that indicate pure commercial advertisements (not events or restaurants)
        ad_keywords = [
            # Medical/cosmetic spam (but keep legitimate clinics)
            "医美", "减肥", "瘦身", "超声刀", "微整形",
            # Financial spam
            "贷款", "投资", "理财", "保险", "信用卡",
            # Real estate spam
            "购房", "卖房", "房地产", "房产", "楼盘",
            # Product spam
            "保健品", "药品", "补品", "保健", "养生",
            # Generic commercial spam
            "代理", "加盟", "招商", "致富", "赚钱",
            # Spam indicators
            "点击链接", "立即咨询", "免费领取", "限时优惠"
        ]

        combined_text = title + " " + description + " " + full_content[:500]  # Check first 500 chars

        # Count ad keywords
        keyword_count = sum(1 for keyword in ad_keywords if keyword in combined_text)

        # More conservative filtering - only filter if multiple spam indicators
        # This preserves restaurants, events, and legitimate business content
        if keyword_count >= 2:
            logger.info(f"📰 Basic filter detected spam advertisement (keywords: {keyword_count}): {title[:50]}...")
            return True

        return False

    def _extract_dates_with_ai(self, title: str, description: str, content_paragraphs: List[str]) -> Dict[str, str]:
        """Use AI to extract start and end dates/times from article content"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                # Fallback to basic regex extraction
                return self._extract_dates_basic(title, description, content_paragraphs)

            try:
                # Handle httpx compatibility issue by using older client setup
                try:
                    client = OpenAI(api_key=api_key)
                except TypeError as e:
                    if "proxies" in str(e):
                        # Create httpx client without proxy arguments that cause issues
                        import httpx
                        http_client = httpx.Client(
                            timeout=60.0,
                            follow_redirects=True
                        )
                        client = OpenAI(
                            api_key=api_key,
                            http_client=http_client
                        )
                    else:
                        raise e
            except (TypeError, ValueError) as e:
                logger.warning(f"OpenAI client initialization failed for date extraction: {e}. Using basic extraction.")
                return self._extract_dates_basic(title, description, content_paragraphs)

            # Combine all content for analysis
            full_content = " ".join(content_paragraphs) if content_paragraphs else ""
            combined_text = f"Title: {title}\nDescription: {description}\nContent: {full_content[:1500]}"  # Limit content length

            prompt = f"""
            Extract event date/time information from this Chinese news article.

            Article content:
            {combined_text}

            Return only a JSON object with this exact format:
            {{
                "start_datetime": "ISO datetime string or empty string",
                "end_datetime": "ISO datetime string or empty string"
            }}

            Rules:
            - Look for explicit dates, times, and duration information
            - Handle Chinese date formats (年/月/日) and Western formats
            - If only date is mentioned, assume time is not specified (empty time)
            - If duration is mentioned (e.g., "持续三天", "for 3 days"), calculate end date
            - For relative dates like "明天" (tomorrow), "下周" (next week), calculate actual dates
            - If no date information found, return empty strings
            - Return dates in ISO format (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD if no time)

            Examples:
            - "2025年11月7日" → "2025-11-07"
            - "明天晚上8点" → calculate tomorrow at 20:00:00
            - "从11月1日至11月3日" → "2025-11-01" and "2025-11-03"
            - "活动持续一周" → calculate end date one week from start
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1
            )

            result = json.loads(response.choices[0].message.content.strip())

            start_datetime = result.get("start_datetime", "").strip()
            end_datetime = result.get("end_datetime", "").strip()

            # Validate and normalize the dates
            if start_datetime:
                start_datetime = self._normalize_datetime_string(start_datetime)
            if end_datetime:
                end_datetime = self._normalize_datetime_string(end_datetime)

            return {
                "start_datetime": start_datetime,
                "end_datetime": end_datetime
            }

        except Exception as e:
            logger.warning(f"AI date extraction failed: {e}. Using basic extraction.")
            return self._extract_dates_basic(title, description, content_paragraphs)

    def _extract_dates_basic(self, title: str, description: str, content_paragraphs: List[str]) -> Dict[str, str]:
        """Basic regex-based date extraction as fallback"""
        import re
        from datetime import datetime, timedelta

        full_content = " ".join(content_paragraphs) if content_paragraphs else ""
        text_to_search = f"{title} {description} {full_content}"

        # Enhanced regex patterns for various date formats
        date_patterns = [
            # Chinese formats
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',  # 2025年11月7日
            r'(\d{1,2})月(\d{1,2})日',  # 11月7日 (assuming current year)
            r'(\d{1,2})月(\d{1,2})号',  # 11月7号
            r'(\d{4})年(\d{1,2})月',  # 2025年11月 (whole month)
            # Western formats
            r'(\d{4})/(\d{1,2})/(\d{1,2})',  # 2025/11/7
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 11/7/2025
            r'(\d{1,2})/(\d{1,2})',  # 11/7 (assuming current year)
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2025-11-7
            # Duration patterns
            r'持续(\d+)(天|周|月|年)',  # 持续三天
            r'为期(\d+)(天|周|月|年)',  # 为期三天
            r'(\d+)(天|周|月|年)活动',  # 三天活动
        ]

        dates_found = []
        duration_days = 0

        for pattern in date_patterns:
            matches = re.findall(pattern, text_to_search, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match) >= 2:
                        if '持续' in pattern or '为期' in pattern or '活动' in pattern:
                            # Handle duration patterns
                            duration_num = int(match[0])
                            duration_unit = match[1]
                            if duration_unit in ['天', '日', 'day']:
                                duration_days = max(duration_days, duration_num)
                            elif duration_unit in ['周', 'week']:
                                duration_days = max(duration_days, duration_num * 7)
                            elif duration_unit in ['月', 'month']:
                                duration_days = max(duration_days, duration_num * 30)  # Approximate
                            continue
                        elif len(match) == 3 and match[2]:  # Full date with year
                            year, month, day = map(int, match[:3])
                        elif len(match) == 2:  # Month/day only
                            year = datetime.now().year
                            month, day = map(int, match)
                        else:
                            continue

                        date_obj = datetime(year, month, day)
                        dates_found.append(date_obj)
                except (ValueError, IndexError):
                    continue

        # Sort dates and determine start/end
        dates_found.sort()

        start_date = ""
        end_date = ""

        if dates_found:
            start_date = dates_found[0].date().isoformat()

            # If multiple dates, assume the last one is end date
            if len(dates_found) > 1:
                end_date = dates_found[-1].date().isoformat()
            # If duration found, calculate end date
            elif duration_days > 0:
                end_date_obj = dates_found[0] + timedelta(days=duration_days)
                end_date = end_date_obj.date().isoformat()

        return {
            "start_datetime": start_date,
            "end_datetime": end_date
        }

    def _normalize_datetime_string(self, datetime_str: str) -> str:
        """Normalize various datetime string formats to ISO format"""
        import re
        from datetime import datetime

        if not datetime_str or datetime_str == "":
            return ""

        # If already in ISO format, return as-is
        if re.match(r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?$', datetime_str):
            return datetime_str

        # Try to parse common formats
        try:
            # Handle YYYY-MM-DD format
            if re.match(r'^\d{4}-\d{2}-\d{2}$', datetime_str):
                return datetime_str + "T00:00:00"
            # Handle YYYY/MM/DD format
            elif re.match(r'^\d{4}/\d{2}/\d{2}$', datetime_str):
                date_obj = datetime.strptime(datetime_str, '%Y/%m/%d')
                return date_obj.isoformat()
            # Handle MM/DD/YYYY format
            elif re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', datetime_str):
                date_obj = datetime.strptime(datetime_str, '%m/%d/%Y')
                return date_obj.isoformat()
        except ValueError:
            pass

        # If parsing fails, return original string (GPT should provide valid formats)
        return datetime_str

    def _format_venue_name_with_ai(self, venue_info: str, city_name: str) -> str:
        """Use AI to extract and format a clean, short venue name from address/location info"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                # Fallback to basic string processing
                return self._format_venue_name_basic(venue_info)

            try:
                # Handle httpx compatibility issue by using older client setup
                try:
                    client = OpenAI(api_key=api_key)
                except TypeError as e:
                    if "proxies" in str(e):
                        # Create httpx client without proxy arguments that cause issues
                        import httpx
                        http_client = httpx.Client(
                            timeout=60.0,
                            follow_redirects=True
                        )
                        client = OpenAI(
                            api_key=api_key,
                            http_client=http_client
                        )
                    else:
                        raise e
            except (TypeError, ValueError) as e:
                logger.warning(f"OpenAI client initialization failed for venue formatting: {e}. Using basic formatting.")
                return self._format_venue_name_basic(venue_info)

            prompt = f"""
            Extract a clean, short venue/business name from this address/location information.

            Raw venue info: "{venue_info}"
            City context: "{city_name}"

            Instructions:
            - Extract only the actual venue/business/place name
            - Remove addresses, phone numbers, hours, delivery info, promotional text
            - Keep it short and readable (1-4 words ideally)
            - For restaurants, cafes, bars, shops: use the business name
            - For events, parks, venues: use the proper name
            - If no clear name found, use a short descriptive term
            - Return only the venue name, nothing else

            Examples:
            Input: "331 NEW DORP LANE,STATEN ISLAND，NY 10306 营业时间：每天 12noon-10pm 外卖：doordash，ubereats，grubhub 一宿 SIU Kitchen，史丹顿岛一间专吃花胶鸡和椰子鸡的宝藏餐厅！用料上乘，出品品质超级高！已经火了三年啦！ 餐厅装修风格文艺又清新，温暖的灯光令人感到舒适，又不乏一丝情调"
            Output: "SIU Kitchen"

            Input: "Central Park, New York City, free entry, open 24 hours"
            Output: "Central Park"

            Input: "Times Square, Manhattan, NYC - holiday celebrations"
            Output: "Times Square"

            Input: "Brooklyn Bridge Park - waterfront park with amazing views"
            Output: "Brooklyn Bridge Park"
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.1
            )

            formatted_name = response.choices[0].message.content.strip()

            # Clean up the result
            formatted_name = formatted_name.strip('"').strip("'").strip()

            # Validate the result - should be reasonable length and not contain URLs/addresses
            if (len(formatted_name) > 0 and len(formatted_name) <= 100 and
                not any(char in formatted_name.lower() for char in ['http', 'www.', '@', '营业时间', '外卖'])):
                return formatted_name

        except Exception as e:
            logger.warning(f"AI venue name formatting failed: {e}. Using basic formatting.")

        # Fallback to basic formatting
        return self._format_venue_name_basic(venue_info)

    def _format_venue_name_basic(self, venue_info: str) -> str:
        """Basic string processing fallback for venue name formatting"""
        import re

        # Try to extract common patterns
        # Look for quoted names first
        quoted_match = re.search(r'[""''"]([^""''"]+)[""''""]', venue_info)
        if quoted_match:
            return quoted_match.group(1).strip()

        # Look for business names after common prefixes (restaurants, venues, etc.)
        prefixes = ['餐厅', '咖啡', '酒店', '酒吧', '商场', '公园', '博物馆', '剧院', '餐厅', 'cafe', 'hotel', 'bar', 'park', 'museum', 'theater', 'club', 'gallery']
        for prefix in prefixes:
            pattern = rf'{prefix}\s*[:：]?\s*([^\s,，。\.]+(?:\s+[^\s,，。\.]+)*)'
            match = re.search(pattern, venue_info, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 1 and len(name) < 50:
                    return name

        # Try to extract first reasonable segment before numbers or common separators
        segments = re.split(r'[，,。.：:()\[\]【】]', venue_info)
        for segment in segments:
            segment = segment.strip()
            # Skip if it contains numbers (likely address), is too short, or too long
            if (len(segment) >= 2 and len(segment) <= 30 and
                not re.search(r'\d', segment) and
                not any(word in segment.lower() for word in ['营业时间', '外卖', '电话', '地址', '联系方式', '预约', 'delivery', 'hours', 'phone', 'address'])):
                return segment

        # Last resort: return first 20 chars if nothing else works
        if venue_info and len(venue_info) > 2:
            return venue_info[:20].strip()

        return "Online"  # Default fallback

    def _normalize_sohu_event(self, article: Dict[str, Any], city_name: str) -> Dict[str, Any]:
        """Robust normalization of Sohu article to standard event format using regex + GPT fallback"""
        try:
            # Step 0: Filter out advertisements first
            if self._is_sohu_advertisement(article):
                logger.info(f"📰 Filtered out advertisement: {article.get('title', 'Unknown')}")
                return None  # Return None to indicate this should be filtered out

            # Step 1: Basic extraction using direct mapping and regex
            basic_event = self._extract_basic_sohu_event(article, city_name)

            # Step 2: Try enhanced extraction with GPT if content is complex
            enhanced_event = self._enhance_sohu_event_with_gpt(article, basic_event)

            # Step 3: Ensure all required fields are present
            final_event = self._finalize_sohu_event(article, enhanced_event)

            return final_event

        except Exception as e:
            logger.error(f"Error normalizing Sohu event: {e}")
            # Return basic normalized event on error
            return self._create_basic_sohu_event(article, city_name)

    def _extract_basic_sohu_event(self, article: Dict[str, Any], city_name: str) -> Dict[str, Any]:
        """Extract basic event information using regex patterns"""
        import re
        from datetime import datetime

        title = article.get("title", "")
        description = article.get("description", "")
        content_paragraphs = article.get("content_paragraphs", [])
        full_content = " ".join(content_paragraphs) if content_paragraphs else ""

        # Basic fields that don't need AI
        event = {
            "event_id": f"sohu_{hash(str(article))}",
            "title": title,
            "description": description[:200] + "..." if len(description) > 200 else description,
            "image_url": article.get("image_url", ""),
            "event_url": article.get("article_url", ""),
            "source": "sohu",
            "attendee_count": 0,
            "is_free": True,
            "ticket_min_price": "Free",
            "ticket_max_price": "Free"
        }

        # Extract dates using AI for better accuracy
        dates_info = self._extract_dates_with_ai(title, description, content_paragraphs)
        event["start_datetime"] = dates_info.get("start_datetime", "")
        event["end_datetime"] = dates_info.get("end_datetime", "")

        # Extract venue/location information
        venue_patterns = [
            r'地点[：:]?\s*([^。\n]+)',  # 地点：xxx
            r'地址[：:]?\s*([^。\n]+)',  # 地址：xxx
            r'Location[：:]?\s*([^。\n]+)',  # Location: xxx
            r'Address[：:]?\s*([^。\n]+)',  # Address: xxx
        ]

        venue_name = "Online"  # Default
        venue_city = city_name.lower().replace('_', ' ')  # Use input city name

        # Try to extract venue info and use AI to format it
        for pattern in venue_patterns:
            match = re.search(pattern, full_content, re.IGNORECASE)
            if match:
                venue_info = match.group(1).strip()
                # Use AI to extract a clean, short venue name
                formatted_name = self._format_venue_name_with_ai(venue_info, city_name)
                if formatted_name:
                    venue_name = formatted_name
                break

        event["venue_name"] = venue_name
        event["venue_city"] = venue_city

        # Basic categories based on content analysis
        categories = ["Article", "News"]
        if any(keyword in full_content.lower() for keyword in ["音乐", "演唱会", "concert", "music"]):
            categories.append("Music")
        if any(keyword in full_content.lower() for keyword in ["艺术", "展览", "art", "exhibition"]):
            categories.append("Arts")
        if any(keyword in full_content.lower() for keyword in ["美食", "餐厅", "food", "restaurant"]):
            categories.append("Food")
        if any(keyword in full_content.lower() for keyword in ["节日", "圣诞", "万圣节", "christmas", "halloween"]):
            categories.append("Festival")

        event["categories"] = categories
        event["organizer_name"] = article.get("author", "Sohu")

        return event

    def _enhance_sohu_event_with_gpt(self, article: Dict[str, Any], basic_event: Dict[str, Any]) -> Dict[str, Any]:
        """Use GPT to enhance basic extraction for complex cases"""
        try:
            # Only use GPT if we have limited information or complex content
            needs_enhancement = (
                not basic_event.get("start_datetime") or
                basic_event.get("venue_name") == "Online" or
                len(basic_event.get("categories", [])) <= 2
            )

            if not needs_enhancement:
                return basic_event

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return basic_event

            try:
                # Handle httpx compatibility issue by using older client setup
                try:
                    client = OpenAI(api_key=api_key)
                except TypeError as e:
                    if "proxies" in str(e):
                        # Create httpx client without proxy arguments that cause issues
                        import httpx
                        http_client = httpx.Client(
                            timeout=60.0,
                            follow_redirects=True
                        )
                        client = OpenAI(
                            api_key=api_key,
                            http_client=http_client
                        )
                    else:
                        raise e
            except (TypeError, ValueError) as e:
                # If OpenAI client initialization fails (often due to proxy configuration issues),
                # fall back to basic event processing without GPT enhancement
                logger.warning(f"OpenAI client initialization failed: {e}. Using basic event processing.")
                return basic_event

            prompt = f"""
            Enhance this basic event extraction from a Chinese news article.
            Focus on filling missing information and improving accuracy.

            Basic extracted data: {json.dumps(basic_event, indent=2, ensure_ascii=False)}

            Raw article data: {json.dumps(article, indent=2, ensure_ascii=False)}

            Return enhanced JSON with these fields (keep existing values if they're good):
            {{
                "title": "improved title if needed",
                "description": "better description under 200 chars",
                "start_datetime": "ISO datetime if found",
                "end_datetime": "ISO datetime if found",
                "venue_name": "specific venue/location",
                "venue_city": "normalized city name",
                "categories": ["improved", "categories"],
                "organizer_name": "event organizer if detectable",
                "image_url": "extract image URL if found in article content, otherwise keep existing"
            }}

            Only improve or add information, don't remove existing good data.
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.1
            )

            enhancement = json.loads(response.choices[0].message.content.strip())

            # Merge enhancement with basic event
            for key, value in enhancement.items():
                if value and (not basic_event.get(key) or key in ["title", "description", "categories"]):
                    basic_event[key] = value

            # Ensure image_url is preserved from original article if not provided by GPT
            if not basic_event.get("image_url") and article.get("image_url"):
                basic_event["image_url"] = article.get("image_url")

            return basic_event

        except Exception as e:
            logger.warning(f"GPT enhancement failed for Sohu event: {e}")
            return basic_event

    def _finalize_sohu_event(self, article: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all required fields are present in the final event"""
        required_fields = [
            "event_id", "title", "description", "start_datetime", "end_datetime",
            "venue_name", "venue_city", "organizer_name", "ticket_min_price",
            "ticket_max_price", "is_free", "categories", "image_url", "event_url", "source"
        ]

        for field in required_fields:
            if field not in event:
                if field == "event_id":
                    event[field] = f"sohu_{hash(str(article))}"
                elif field in ["start_datetime", "end_datetime", "venue_city"]:
                    event[field] = ""
                elif field == "event_url":
                    event[field] = article.get("article_url", "")
                elif field == "image_url":
                    event[field] = article.get("image_url", "")
                elif field == "source":
                    event[field] = "sohu"
                elif field == "is_free":
                    event[field] = True
                elif field == "categories":
                    event[field] = ["Article", "News"]
                elif field == "ticket_min_price":
                    event[field] = "Free"
                elif field == "ticket_max_price":
                    event[field] = "Free"
                elif field == "attendee_count":
                    event[field] = 0
                else:
                    event[field] = f"Unknown {field}"

        return event

    def _create_basic_sohu_event(self, article: Dict[str, Any], city_name: str = "") -> Dict[str, Any]:
        """Create a basic fallback event when all else fails"""
        return {
            "event_id": f"sohu_{hash(str(article))}",
            "title": article.get("title", "Unknown Article"),
            "description": article.get("description", "No description available")[:200],
            "start_datetime": "",
            "end_datetime": "",
            "venue_name": "Online",
            "venue_city": city_name.lower().replace('_', ' ') if city_name else "",
            "organizer_name": article.get("author", "Sohu"),
            "ticket_min_price": "Free",
            "ticket_max_price": "Free",
            "is_free": True,
            "categories": ["Article", "News"],
            "image_url": article.get("image_url", ""),
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

def test_sohu_parsing():
    """Test Sohu article parsing includes image_url"""
    sohu_crawler = SohuCrawler()

    # Test HTML parsing
    test_html = """
    <div class="TPLImageTextFeedItem">
        <div class="item-text-content-title">Test News Article</div>
        <div class="item-text-content-description">This is a news article about an event</div>
        <a class="tpl-image-text-feed-item-content" href="https://example.com/article">Link</a>
        <img src="https://example.com/image.jpg">
    </div>
    <div class="TPLImageTextFeedItem">
        <div class="item-text-content-title">PICO Medical Beauty Clinic</div>
        <div class="item-text-content-description">Professional medical beauty services with discounts</div>
        <a class="tpl-image-text-feed-item-content" href="https://example.com/ad">Link</a>
        <img src="https://example.com/ad.jpg">
    </div>
    """

    articles = sohu_crawler._parse_sohu_articles(test_html)
    print(f"Parsed articles: {len(articles)}")

    normalized_events = []
    for i, article in enumerate(articles):
        print(f"\nArticle {i+1}:")
        print(f"Title: {article.get('title')}")
        print(f"Image URL: {article.get('image_url', 'NOT SET')}")

        # Test normalization
        normalized = sohu_crawler._normalize_sohu_event(article, "new york")
        if normalized:
            print(f"✓ Kept as event - Image URL: {normalized.get('image_url', 'NOT SET')}")
            normalized_events.append(normalized)
        else:
            print("✗ Filtered out as advertisement")

    print(f"\nFinal result: {len(normalized_events)} events kept from {len(articles)} articles")
    return normalized_events

if __name__ == "__main__":
    event_crawler = EventCrawler()

def fetch_events_by_city(city_name: str, max_pages: int = 3) -> List[Dict[str, Any]]:
    """Convenience function - fetch from all sources"""
    return event_crawler.fetch_events_by_city(city_name, max_pages=max_pages)


    # Test the unified crawler
    logging.basicConfig(level=logging.INFO)

    print("Testing Unified Event Crawler")
    print("=" * 50)
    # Test unified
    print("\nFetching from both sources...")
    all_events = event_crawler.fetch_events_by_city("new york", sources=["eventbrite", "sohu"], max_pages=1)
    print(f"Total: {len(all_events)} events/articles")

    if all_events:
        sample = all_events[-1]
        print(json.dumps(sample, indent=2, ensure_ascii=False))