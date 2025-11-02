import { IDataService, ChatRequest, ChatResponse, RecommendationRequest, RecommendationItem } from '../api/client';

// Mock event data matching the backend structure
const mockEvents: any[] = [
  {
    event_id: "mock-1",
    title: "SoulSearch Enlightenment Expo",
    description: "Experience psychic & tarot readings, energy healings, chakra balancing, and more. Perfect match for your spiritual wellness interests!",
    venue_name: "Crowne Plaza Palo Alto",
    venue_city: "Palo Alto",
    start_datetime: "2025-11-15T12:00:00",
    end_datetime: "2025-11-15T18:00:00",
    timezone: "America/Los_Angeles",
    categories: ["Psychic", "Meditation", "Energy Healing"],
    is_free: false,
    ticket_min_price: "$25",
    ticket_max_price: "$25",
    image_url: "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=800&q=80",
    event_url: "https://example.com/event/1",
    organizer_name: "SoulSearch Events",
    rating: 4.8
  },
  {
    event_id: "mock-2",
    title: "Mindfulness Meditation Workshop",
    description: "Learn mindfulness techniques for stress reduction and personal growth in a peaceful setting.",
    venue_name: "Palo Alto Art Center",
    venue_city: "Palo Alto",
    start_datetime: "2025-11-16T10:00:00",
    end_datetime: "2025-11-16T12:00:00",
    timezone: "America/Los_Angeles",
    categories: ["Meditation", "Wellness"],
    is_free: true,
    ticket_min_price: "Free",
    ticket_max_price: "Free",
    image_url: "https://images.unsplash.com/photo-1545389336-cf090694435e?w=800&q=80",
    event_url: "https://example.com/event/2",
    organizer_name: "Mindful Palo Alto",
    rating: 4.9
  },
  {
    event_id: "mock-3",
    title: "Yoga & Sound Healing",
    description: "Combine gentle yoga with the healing vibrations of singing bowls for ultimate relaxation.",
    venue_name: "Stanford Wellness Center",
    venue_city: "Palo Alto",
    start_datetime: "2025-11-15T18:00:00",
    end_datetime: "2025-11-15T20:00:00",
    timezone: "America/Los_Angeles",
    categories: ["Yoga", "Wellness", "Sound Healing"],
    is_free: false,
    ticket_min_price: "$35",
    ticket_max_price: "$35",
    image_url: "https://images.unsplash.com/photo-1599901860904-17e6ed7083a0?w=800&q=80",
    event_url: "https://example.com/event/3",
    organizer_name: "Stanford Wellness",
    rating: 4.7
  },
  {
    event_id: "mock-4",
    title: "Breathwork & Cold Plunge",
    description: "Transform your nervous system through breathwork and ice therapy techniques.",
    venue_name: "Willow Creek Spa",
    venue_city: "Palo Alto",
    start_datetime: "2025-11-16T08:00:00",
    end_datetime: "2025-11-16T10:00:00",
    timezone: "America/Los_Angeles",
    categories: ["Wellness", "Breathwork"],
    is_free: false,
    ticket_min_price: "$45",
    ticket_max_price: "$45",
    image_url: "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?w=800&q=80",
    event_url: "https://example.com/event/4",
    organizer_name: "Willow Creek Wellness",
    rating: 4.6
  }
];

// Mock implementation of data service
class MockDataService implements IDataService {
  async chat(request: ChatRequest): Promise<ChatResponse> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    // Generate mock recommendations
    const recommendations: RecommendationItem[] = mockEvents.slice(0, 4).map((event, index) => ({
      type: 'event' as const,
      data: event,
      relevance_score: 0.9 - (index * 0.1),
      explanation: `Event in ${event.venue_city}: ${event.title}`
    }));

    return {
      message: `🎉 Found ${recommendations.length} events that match your search! Check out the recommendations below ↓`,
      recommendations,
      llm_provider_used: 'mock',
      cache_used: false,
      conversation_id: `mock-conv-${Date.now()}`
    };
  }

  async chatStream(
    request: ChatRequest,
    onStatus: (status: string) => void,
    onMessage: (message: string, metadata?: any) => void,
    onRecommendation: (recommendation: any) => void,
    onError: (error: string) => void,
    onDone: () => void
  ): Promise<void> {
    try {
      // Simulate status update
      onStatus('Searching for events...');
      await new Promise(resolve => setTimeout(resolve, 300));

      onStatus('Found great matches!');
      await new Promise(resolve => setTimeout(resolve, 300));

      // Send message
      const message = `🎉 Found ${mockEvents.length} events that match your search! Check out the recommendations below ↓`;
      onMessage(message, {
        extraction_summary: 'Extracted preferences: spiritual wellness, personal growth',
        conversation_id: `mock-conv-${Date.now()}`
      });

      await new Promise(resolve => setTimeout(resolve, 200));

      // Stream recommendations one by one
      onStatus(`Preparing ${mockEvents.length} recommendations...`);
      await new Promise(resolve => setTimeout(resolve, 300));

      for (const event of mockEvents) {
        const recommendation: RecommendationItem = {
          type: 'event',
          data: event,
          relevance_score: 0.9,
          explanation: `Event in ${event.venue_city}: ${event.title}`
        };
        onRecommendation(recommendation);
        await new Promise(resolve => setTimeout(resolve, 200));
      }

      onDone();
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unknown error occurred');
      onDone();
    }
  }

  async getRecommendations(request: RecommendationRequest): Promise<any> {
    await new Promise(resolve => setTimeout(resolve, 300));
    return {
      recommendations: mockEvents.slice(0, request.max_results || 5).map((event, index) => ({
        type: 'event',
        data: event,
        relevance_score: 0.9 - (index * 0.1),
        explanation: `Event in ${event.venue_city}: ${event.title}`
      }))
    };
  }

  async getEvents(query: string, location?: string, category?: string, maxResults: number = 5): Promise<any> {
    await new Promise(resolve => setTimeout(resolve, 300));
    return {
      events: mockEvents.slice(0, maxResults)
    };
  }

  async getRestaurants(query: string, location?: string, cuisine?: string, maxResults: number = 5): Promise<any> {
    await new Promise(resolve => setTimeout(resolve, 300));
    return {
      restaurants: []
    };
  }

  async getStats(): Promise<any> {
    await new Promise(resolve => setTimeout(resolve, 100));
    return {
      status: 'ok',
      cache_stats: {
        total_events: mockEvents.length,
        cache_hits: 0
      },
      features: ['mock_data']
    };
  }

  async healthCheck(): Promise<any> {
    await new Promise(resolve => setTimeout(resolve, 100));
    return {
      status: 'healthy',
      version: '1.0.0-mock',
      features: ['mock_data']
    };
  }

  async getUserUsage(userId: string): Promise<any> {
    await new Promise(resolve => setTimeout(resolve, 100));
    return {
      anonymous_user_id: userId,
      interaction_count: 5,
      trial_remaining: 95,
      is_registered: false
    };
  }

  async registerWithToken(anonymousUserId: string, token: string): Promise<any> {
    await new Promise(resolve => setTimeout(resolve, 300));
    return {
      success: true,
      user_id: `user_${Date.now()}`
    };
  }

  async verifyToken(token: string): Promise<any> {
    await new Promise(resolve => setTimeout(resolve, 100));
    return {
      success: true,
      user_id: `user_${Date.now()}`
    };
  }

  async createConversation(userId: string, metadata: any = {}): Promise<string> {
    await new Promise(resolve => setTimeout(resolve, 100));
    return `conv_${Date.now()}`;
  }

  async getConversation(userId: string, conversationId: string): Promise<any> {
    await new Promise(resolve => setTimeout(resolve, 100));
    return {
      conversation_id: conversationId,
      messages: []
    };
  }

  async listUserConversations(userId: string, limit: number = 50): Promise<any[]> {
    await new Promise(resolve => setTimeout(resolve, 100));
    return [];
  }

  async deleteConversation(userId: string, conversationId: string): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 100));
  }
}

export { MockDataService };

