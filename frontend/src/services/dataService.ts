import { ChatRequest, ChatResponse, RecommendationRequest } from '../api/client';
import { apiClient } from '../api/client';

// Export IDataService interface for use in mockData
export interface IDataService {
  chatStream(
    request: ChatRequest,
    onStatus: (status: string) => void,
    onMessage: (message: string, metadata?: any) => void,
    onRecommendation: (recommendation: any) => void,
    onError: (error: string) => void,
    onDone: () => void
  ): Promise<void>;
  getRecommendations(request: RecommendationRequest): Promise<any>;
  getEvents(query: string, location?: string, category?: string, maxResults?: number): Promise<any>;
  getRestaurants(query: string, location?: string, cuisine?: string, maxResults?: number): Promise<any>;
  getStats(): Promise<any>;
  healthCheck(): Promise<any>;
  getUserUsage(userId: string): Promise<any>;
  registerWithToken(anonymousUserId: string, token: string): Promise<any>;
  verifyToken(token: string): Promise<any>;
  createConversation(userId: string, metadata?: any): Promise<string>;
  getConversation(userId: string, conversationId: string): Promise<any>;
  listUserConversations(userId: string, limit?: number): Promise<any[]>;
  deleteConversation(userId: string, conversationId: string): Promise<void>;
}

const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true';

// Real implementation - delegates to apiClient
class RealDataService implements IDataService {
  async chatStream(
    request: ChatRequest,
    onStatus: (status: string) => void,
    onMessage: (message: string, metadata?: any) => void,
    onRecommendation: (recommendation: any) => void,
    onError: (error: string) => void,
    onDone: () => void
  ): Promise<void> {
    return apiClient.chatStream(request, onStatus, onMessage, onRecommendation, onError, onDone);
  }

  async getRecommendations(request: RecommendationRequest): Promise<any> {
    return apiClient.getRecommendations(request);
  }

  async getEvents(query: string, location?: string, category?: string, maxResults: number = 5): Promise<any> {
    return apiClient.getEvents(query, location, category, maxResults);
  }

  async getRestaurants(query: string, location?: string, cuisine?: string, maxResults: number = 5): Promise<any> {
    return apiClient.getRestaurants(query, location, cuisine, maxResults);
  }

  async getStats(): Promise<any> {
    return apiClient.getStats();
  }

  async healthCheck(): Promise<any> {
    return apiClient.healthCheck();
  }

  async getUserUsage(userId: string): Promise<any> {
    return apiClient.getUserUsage(userId);
  }

  async registerWithToken(anonymousUserId: string, token: string): Promise<any> {
    return apiClient.registerWithToken(anonymousUserId, token);
  }

  async verifyToken(token: string): Promise<any> {
    return apiClient.verifyToken(token);
  }

  async createConversation(userId: string, metadata: any = {}): Promise<string> {
    return apiClient.createConversation(userId, metadata);
  }

  async getConversation(userId: string, conversationId: string): Promise<any> {
    return apiClient.getConversation(userId, conversationId);
  }

  async listUserConversations(userId: string, limit: number = 50): Promise<any[]> {
    return apiClient.listUserConversations(userId, limit);
  }

  async deleteConversation(userId: string, conversationId: string): Promise<void> {
    return apiClient.deleteConversation(userId, conversationId);
  }
}

// Factory function to get the appropriate data service
export function getDataService(): IDataService {
  if (USE_MOCK_DATA) {
    // Import mock service when needed
    const { MockDataService } = require('./mockData');
    return new MockDataService();
  }
  return new RealDataService();
}

// Export singleton instance
export const dataService = getDataService();
