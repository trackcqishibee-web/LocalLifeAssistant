import chromadb
from chromadb.config import Settings
import json
import os
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from .models import Event, Restaurant

class ChromaDBManager:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get or create collections
        self.events_collection = self.client.get_or_create_collection(
            name="events",
            metadata={"hnsw:space": "cosine"}
        )
        self.restaurants_collection = self.client.get_or_create_collection(
            name="restaurants", 
            metadata={"hnsw:space": "cosine"}
        )

    def _create_embedding(self, text: str) -> List[float]:
        """Create embedding for text using sentence transformers"""
        return self.embedding_model.encode(text).tolist()

    def _prepare_event_document(self, event: Event) -> Dict[str, Any]:
        """Prepare event data for ChromaDB storage"""
        # Create searchable text combining multiple fields
        searchable_text = f"{event.title} {event.description} {event.venue_name} {event.venue_city} {' '.join(event.categories)}"
        
        return {
            "id": event.event_id,
            "document": searchable_text,
            "metadata": {
                "title": event.title,
                "description": event.description,
                "venue_name": event.venue_name,
                "venue_city": event.venue_city,
                "venue_country": event.venue_country,
                "latitude": event.latitude,
                "longitude": event.longitude,
                "start_datetime": event.start_datetime,
                "end_datetime": event.end_datetime,
                "categories": event.categories,
                "is_free": event.is_free,
                "ticket_min_price": event.ticket_min_price,
                "ticket_max_price": event.ticket_max_price,
                "organizer_name": event.organizer_name,
                "image_url": event.image_url,
                "event_url": event.event_url,
                "attendee_count": event.attendee_count,
                "source": event.source,
                "type": "event"
            }
        }

    def _prepare_restaurant_document(self, restaurant: Restaurant) -> Dict[str, Any]:
        """Prepare restaurant data for ChromaDB storage"""
        searchable_text = f"{restaurant.name} {restaurant.description} {restaurant.cuisine_type} {restaurant.venue_name} {restaurant.venue_city} {' '.join(restaurant.categories)}"
        
        return {
            "id": restaurant.restaurant_id,
            "document": searchable_text,
            "metadata": {
                "name": restaurant.name,
                "description": restaurant.description,
                "cuisine_type": restaurant.cuisine_type,
                "price_range": restaurant.price_range,
                "rating": restaurant.rating,
                "venue_name": restaurant.venue_name,
                "venue_city": restaurant.venue_city,
                "venue_country": restaurant.venue_country,
                "latitude": restaurant.latitude,
                "longitude": restaurant.longitude,
                "phone": restaurant.phone,
                "website": restaurant.website,
                "categories": restaurant.categories,
                "image_url": restaurant.image_url,
                "is_open_now": restaurant.is_open_now,
                "source": restaurant.source,
                "type": "restaurant"
            }
        }

    def add_events(self, events: List[Event]):
        """Add events to ChromaDB"""
        if not events:
            return
            
        documents = []
        metadatas = []
        ids = []
        
        for event in events:
            doc_data = self._prepare_event_document(event)
            documents.append(doc_data["document"])
            metadatas.append(doc_data["metadata"])
            ids.append(doc_data["id"])
        
        self.events_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def add_restaurants(self, restaurants: List[Restaurant]):
        """Add restaurants to ChromaDB"""
        if not restaurants:
            return
            
        documents = []
        metadatas = []
        ids = []
        
        for restaurant in restaurants:
            doc_data = self._prepare_restaurant_document(restaurant)
            documents.append(doc_data["document"])
            metadatas.append(doc_data["metadata"])
            ids.append(doc_data["id"])
        
        self.restaurants_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def search_events(self, query: str, n_results: int = 5, where: Optional[Dict] = None) -> List[Dict]:
        """Search for events using vector similarity"""
        query_embedding = self._create_embedding(query)
        
        results = self.events_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        return self._format_search_results(results)

    def search_restaurants(self, query: str, n_results: int = 5, where: Optional[Dict] = None) -> List[Dict]:
        """Search for restaurants using vector similarity"""
        query_embedding = self._create_embedding(query)
        
        results = self.restaurants_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        return self._format_search_results(results)

    def search_all(self, query: str, n_results: int = 5, where: Optional[Dict] = None) -> Dict[str, List[Dict]]:
        """Search both events and restaurants"""
        return {
            "events": self.search_events(query, n_results, where),
            "restaurants": self.search_restaurants(query, n_results, where)
        }

    def _format_search_results(self, results) -> List[Dict]:
        """Format ChromaDB search results"""
        formatted_results = []
        
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "id": doc_id,
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "document": results["documents"][0][i] if results["documents"] else ""
                })
        
        return formatted_results

    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about stored data"""
        return {
            "events_count": self.events_collection.count(),
            "restaurants_count": self.restaurants_collection.count()
        }

# Global database manager instance
db_manager = None

def get_db_manager() -> ChromaDBManager:
    global db_manager
    if db_manager is None:
        persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
        db_manager = ChromaDBManager(persist_directory=persist_dir)
    return db_manager
