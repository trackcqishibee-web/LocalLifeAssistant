import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface LocationCoordinates {
  latitude: number;
  longitude: number;
  formatted_address: string;
  success?: boolean;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  error_message?: string;
}

export interface ChatRequest {
  message: string;
  conversation_history: ChatMessage[];
  llm_provider?: string;
}

export interface RecommendationItem {
  type: 'event' | 'restaurant';
  data: any;
  relevance_score: number;
  explanation: string;
}

export interface ChatResponse {
  message: string;
  recommendations: RecommendationItem[];
  llm_provider_used: string;
}

export interface RecommendationRequest {
  query: string;
  type?: 'event' | 'restaurant';
  location?: string;
  category?: string;
  max_results?: number;
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await axios.post(`${this.baseURL}/api/chat`, request);
    return response.data;
  }

  async getRecommendations(request: RecommendationRequest): Promise<any> {
    const params = new URLSearchParams();
    params.append('query', request.query);
    if (request.type) params.append('type', request.type);
    if (request.location) params.append('location', request.location);
    if (request.category) params.append('category', request.category);
    if (request.max_results) params.append('max_results', request.max_results.toString());

    const response = await axios.get(`${this.baseURL}/api/recommendations?${params}`);
    return response.data;
  }

  async getEvents(query: string, location?: string, category?: string, maxResults: number = 5): Promise<any> {
    const params = new URLSearchParams();
    params.append('query', query);
    if (location) params.append('location', location);
    if (category) params.append('category', category);
    params.append('max_results', maxResults.toString());

    const response = await axios.get(`${this.baseURL}/api/events?${params}`);
    return response.data;
  }

  async getRestaurants(query: string, location?: string, cuisine?: string, maxResults: number = 5): Promise<any> {
    const params = new URLSearchParams();
    params.append('query', query);
    if (location) params.append('location', location);
    if (cuisine) params.append('cuisine', cuisine);
    params.append('max_results', maxResults.toString());

    const response = await axios.get(`${this.baseURL}/api/restaurants?${params}`);
    return response.data;
  }

  async getStats(): Promise<any> {
    const response = await axios.get(`${this.baseURL}/stats`);
    return response.data;
  }

  async healthCheck(): Promise<any> {
    const response = await axios.get(`${this.baseURL}/health`);
    return response.data;
  }

  async geocodeLocation(input: string): Promise<LocationCoordinates> {
    const response = await axios.post(`${this.baseURL}/api/geocode`, {
      input_text: input
    });
    return response.data;
  }
}

export const apiClient = new APIClient();
export default apiClient;
