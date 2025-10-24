import React, { useState, useEffect, useCallback } from 'react';
import { Settings, MessageCircle, MapPin } from 'lucide-react';
import ChatInterface from './components/ChatInterface';
import LocationInput from './components/LocationInput';
import { ChatMessage, apiClient, LocationCoordinates } from './api/client';

const App: React.FC = () => {
  const [conversationHistory, setConversationHistory] = useState<ChatMessage[]>([]);
  const [llmProvider, setLlmProvider] = useState('openai');
  const [showSettings, setShowSettings] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [userLocation, setUserLocation] = useState<LocationCoordinates | null>(null);

  const availableProviders = [
    { value: 'openai', label: 'OpenAI (GPT-3.5)' },
    { value: 'anthropic', label: 'Anthropic Claude' },
    { value: 'ollama', label: 'Ollama (Local)' }
  ];

  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      await apiClient.healthCheck();
      setIsConnected(true);
    } catch (error) {
      console.error('Connection failed:', error);
      setIsConnected(false);
    }
  };

  const handleNewMessage = (message: ChatMessage) => {
    setConversationHistory(prev => [...prev, message]);
  };

  const handleRecommendations = (recommendations: any[]) => {
    // Handle recommendations if needed
    console.log('Received recommendations:', recommendations);
  };


  const handleLocationChange = useCallback((location: LocationCoordinates | null) => {
    setUserLocation(location);
  }, []);

  const handleExampleQuery = async (query: string) => {
    const userMessage: ChatMessage = {
      role: 'user',
      content: query,
      timestamp: new Date().toISOString()
    };
    
    // Add user message to chat
    handleNewMessage(userMessage);
    
    // Create a temporary chat interface to send the request
    try {
      const request = {
        message: query,
        conversation_history: conversationHistory,
        llm_provider: llmProvider,
        location: userLocation,
        is_initial_response: conversationHistory.length === 0
      };
      
      const response = await apiClient.chat(request);
      
      const assistantMessage = {
        role: 'assistant' as const,
        content: response.message,
        timestamp: new Date().toISOString(),
        recommendations: response.recommendations || []
      } as any;
      
      handleNewMessage(assistantMessage);
      handleRecommendations(response.recommendations || []);
    } catch (error) {
      console.error('Error sending example query:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      };
      handleNewMessage(errorMessage);
    }
  };

  const clearConversation = () => {
    setConversationHistory([]);
  };

  const exampleQueries = [
    "Find me a jazz concert this weekend",
    "What restaurants are good for a date night?",
    "Show me free events in Brooklyn",
    "I want to try some new cuisine",
    "What networking events are happening?",
    "Find events in Los Angeles",
    "Show me restaurants in Chicago",
    "What's happening in Miami this weekend?"
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
                <MapPin className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Local Life Assistant</h1>
                <p className="text-sm text-gray-500">AI-powered recommendations for your city</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Settings Panel */}
      {showSettings && (
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  LLM Provider
                </label>
                <select
                  value={llmProvider}
                  onChange={(e) => setLlmProvider(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  {availableProviders.map(provider => (
                    <option key={provider.value} value={provider.value}>
                      {provider.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="flex items-end">
                <button
                  onClick={clearConversation}
                  className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  Clear Conversation
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Chat Interface */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 h-[700px] flex flex-col">
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center space-x-2">
                  <MessageCircle className="w-5 h-5 text-primary-500" />
                  <h2 className="text-lg font-semibold text-gray-900">Chat with Assistant</h2>
                </div>
              </div>
              
              <ChatInterface
                onNewMessage={handleNewMessage}
                onRecommendations={handleRecommendations}
                llmProvider={llmProvider}
                conversationHistory={conversationHistory}
                userLocation={userLocation}
              />
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Location Input */}
            <LocationInput
              onLocationChange={handleLocationChange}
              initialLocation={userLocation}
            />

            {/* Quick Examples */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Try asking:</h3>
              <div className="space-y-2">
                {exampleQueries.map((query, index) => (
                  <button
                    key={index}
                    onClick={() => handleExampleQuery(query)}
                    className="w-full text-left p-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                  >
                    "{query}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-500">
            <p>Local Life Assistant - Powered by AI and RAG technology</p>
            <p className="text-sm mt-2">
              Built with FastAPI, React, ChromaDB, and multiple LLM providers
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
