import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
console.log('🔧 Frontend API Base URL:', API_BASE_URL);
console.log('🌐 Current origin:', window.location.origin);
console.log('📡 VITE_API_BASE_URL env:', import.meta.env.VITE_API_BASE_URL);

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
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
  user_preferences?: UserPreferences;
  is_initial_response?: boolean;
  user_id: string;  // NEW - Required anonymous user ID
  conversation_id?: string | null;  // Optional conversation ID for continuing conversations
}

export interface EventData {
  event_id?: string;
  title: string;
  description: string;
  venue_name: string;
  venue_city: string;
  start_datetime: string;
  end_datetime?: string;
  timezone?: string;
  categories?: string[];
  is_free: boolean;
  ticket_min_price?: string;
  ticket_max_price?: string;
  image_url?: string;
  event_url?: string;
  organizer_name?: string;
  rating?: number;
  [key: string]: any;
}

export interface RestaurantData {
  restaurant_id?: string;
  name: string;
  description: string;
  venue_city: string;
  categories?: string[];
  is_open_now?: boolean;
  rating?: number;
  [key: string]: any;
}

export interface RecommendationItem {
  type: 'event' | 'restaurant';
  data: EventData | RestaurantData;
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

  async chatStream(
    request: ChatRequest,
    onStatus: (status: string) => void,
    onMessage: (message: string, metadata?: any) => void,
    onRecommendation: (recommendation: any) => void,
    onError: (error: string) => void,
    onDone: () => void
  ): Promise<void> {
    const url = `${this.baseURL}/api/chat/stream`;
    console.log('🔗 Streaming Chat API Call:', url);
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              switch (data.type) {
                case 'status':
                  onStatus(data.content);
                  break;
                case 'message':
                  onMessage(data.content, {
                    extraction_summary: data.extraction_summary,
                    usage_stats: data.usage_stats,
                    trial_exceeded: data.trial_exceeded,
                    conversation_id: data.conversation_id,
                    location_processed: data.location_processed
                  });
                  break;
                case 'recommendation':
                  onRecommendation(data.data);
                  break;
                case 'error':
                  onError(data.content);
                  break;
                case 'done':
                  onDone();
                  return;
              }
            } catch (parseError) {
              console.error('Error parsing SSE data:', parseError, 'Line:', line);
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming chat error:', error);
      onError(error instanceof Error ? error.message : 'Unknown error occurred');
      onDone();
    }
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

  async getSupportedEventTypes(): Promise<string[]> {
    const response = await axios.get(`${this.baseURL}/api/supported-event-types`);
    if (response.data.success) {
      return response.data.event_types || [];
    }
    return [];
  }

  async getSupportedCities(): Promise<string[]> {
    const response = await axios.get(`${this.baseURL}/api/supported-cities`);
    if (response.data.success) {
      return response.data.cities || [];
    }
    return [];
  }


  async getUserUsage(userId: string): Promise<any> {
    const response = await axios.get(`${this.baseURL}/api/usage/${userId}`);
    return response.data;
  }

  async registerWithToken(anonymousUserId: string, token: string): Promise<any> {
    const url = `${this.baseURL}/api/auth/register`;
    console.log('🔗 Register API Call:', url);
    const response = await axios.post(url, {
      anonymous_user_id: anonymousUserId,
      token
    });
    return response.data;
  }

  async verifyToken(token: string): Promise<any> {
    const url = `${this.baseURL}/api/auth/verify`;
    console.log('🔗 Verify API Call:', url);
    const response = await axios.post(url, {
      token
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
