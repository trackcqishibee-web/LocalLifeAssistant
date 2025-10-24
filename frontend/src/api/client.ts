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
}

export interface GeocodeResponse {
  success: boolean;
  coordinates: {
    latitude: number;
    longitude: number;
    formatted_address: string;
  } | null;
  error_message: string | null;
}

export interface UserPreferences {
  location?: string;
  date?: string;
  time?: string;
  event_type?: string;
}

export interface ChatRequest {
  message: string;
  conversation_history: ChatMessage[];
  llm_provider?: string;
  location?: LocationCoordinates | null;
  user_preferences?: UserPreferences;
  is_initial_response?: boolean;
  user_id: string;  // NEW - Required anonymous user ID
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
  cache_used?: boolean;
  cache_age_hours?: number;
  extracted_preferences?: UserPreferences;
  extraction_summary?: string;
  usage_stats?: any;  // NEW - Trial info
  trial_exceeded?: boolean;  // NEW - Flag to show registration prompt
  conversation_id: string;  // NEW
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
    
    // Handle the backend's response format
    if (response.data.success && response.data.coordinates) {
      return response.data.coordinates;
    } else {
      throw new Error(response.data.error_message || 'Failed to geocode location');
    }
  }

  async getUserUsage(userId: string): Promise<any> {
    const response = await axios.get(`${this.baseURL}/api/usage/${userId}`);
    return response.data;
  }

  async register(anonymousUserId: string, email: string, password: string, name?: string): Promise<any> {
    const response = await axios.post(`${this.baseURL}/api/users/register`, {
      anonymous_user_id: anonymousUserId,
      email,
      password,
      name
    });
    return response.data;
  }

  async login(email: string, password: string): Promise<any> {
    const response = await axios.post(`${this.baseURL}/api/users/login`, {
      email,
      password
    });
    return response.data;
  }

  async createConversation(userId: string, metadata: any = {}): Promise<string> {
    const response = await axios.post(`${this.baseURL}/api/conversations/create`, {
      user_id: userId,
      ...metadata
    });
    return response.data.conversation_id;
  }

  async getConversation(userId: string, conversationId: string): Promise<any> {
    const response = await axios.get(
      `${this.baseURL}/api/conversations/${userId}/${conversationId}`
    );
    return response.data;
  }

  async listUserConversations(userId: string, limit: number = 50): Promise<any[]> {
    const response = await axios.get(
      `${this.baseURL}/api/conversations/${userId}/list?limit=${limit}`
    );
    return response.data.conversations;
  }

  async deleteConversation(userId: string, conversationId: string): Promise<void> {
    await axios.delete(
      `${this.baseURL}/api/conversations/${userId}/${conversationId}`
    );
  }
}

export const apiClient = new APIClient();
export default apiClient;
