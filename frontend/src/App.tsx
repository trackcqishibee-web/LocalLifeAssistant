import React, { useState, useEffect, useCallback } from 'react';
import { Settings, MessageCircle, MapPin } from 'lucide-react';
import ChatInterface from './components/ChatInterface';
import LocationInput from './components/LocationInput';
import RegistrationModal from './components/RegistrationModal';
import { ChatMessage, apiClient, LocationCoordinates } from './api/client';
import { getOrCreateUserId, setUserId } from './utils/userIdManager';
import { getUsageStats, updateUsageStats, shouldShowRegistrationPrompt, markRegistrationPrompted, getTrialWarningMessage } from './utils/usageTracker';

const App: React.FC = () => {
  const [conversationHistory, setConversationHistory] = useState<ChatMessage[]>([]);
  const [llmProvider, setLlmProvider] = useState('openai');
  const [showSettings, setShowSettings] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [userLocation, setUserLocation] = useState<LocationCoordinates | null>(null);
  const [userId, setUserIdState] = useState<string>('');
  const [usageStats, setUsageStats] = useState<any>(null);
  const [showRegistrationModal, setShowRegistrationModal] = useState(false);
  const [trialWarning, setTrialWarning] = useState('');
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);

  const availableProviders = [
    { value: 'openai', label: 'OpenAI (GPT-3.5)' },
    { value: 'anthropic', label: 'Anthropic Claude' },
    { value: 'ollama', label: 'Ollama (Local)' }
  ];

  useEffect(() => {
    checkConnection();
  }, []);

  // Initialize user ID
  useEffect(() => {
    const uid = getOrCreateUserId();
    setUserIdState(uid);
    console.log('User ID initialized:', uid);
  }, []);

  // Check usage stats for anonymous users
  useEffect(() => {
    if (userId && userId.startsWith('user_')) {
      // Fetch usage stats from backend
      apiClient.getUserUsage(userId).then(stats => {
        setUsageStats(stats);
        updateUsageStats({
          anonymous_user_id: userId,
          interaction_count: stats.interaction_count,
          trial_remaining: stats.trial_remaining,
          is_registered: stats.is_registered
        });
        
        // Show warning if trial is running low
        const warning = getTrialWarningMessage(stats.trial_remaining);
        setTrialWarning(warning);
        
        // Show registration modal if needed
        if (shouldShowRegistrationPrompt()) {
          setShowRegistrationModal(true);
          markRegistrationPrompted();
        }
      }).catch(error => {
        console.error('Failed to fetch usage stats:', error);
      });
    }
  }, [userId]);

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

  // Initialize conversation
  useEffect(() => {
    if (!userId) return;
    
    const initializeConversation = async () => {
      // Check localStorage for current conversation
      const savedConversationId = localStorage.getItem('current_conversation_id');
      
      if (savedConversationId) {
        try {
          // Try to load existing conversation
          const conversation = await apiClient.getConversation(userId, savedConversationId);
          setCurrentConversationId(savedConversationId);
          setConversationHistory(conversation.messages);
          console.log('Loaded existing conversation:', savedConversationId);
        } catch (error) {
          // Conversation not found, create new one
          console.log('Conversation not found, creating new one');
          const newId = await apiClient.createConversation(userId, { 
            llm_provider: llmProvider 
          });
          setCurrentConversationId(newId);
          localStorage.setItem('current_conversation_id', newId);
        }
      } else {
        // Create new conversation
        const newId = await apiClient.createConversation(userId, { 
          llm_provider: llmProvider 
        });
        setCurrentConversationId(newId);
        localStorage.setItem('current_conversation_id', newId);
        console.log('Created new conversation:', newId);
      }
    };
    
    initializeConversation();
  }, [userId, llmProvider]);

  const handleRegister = async (email: string, password: string, name: string) => {
    try {
      const response = await apiClient.register(userId, email, password, name);
      
      if (response.success) {
        // Update user ID to registered user
        setUserIdState(response.user_id);
        setUserId(response.user_id);
        
        // Update usage stats
        updateUsageStats({ is_registered: true });
        
        // Show success message
        alert('Registration successful! Your conversation history has been preserved.');
      }
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

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
        is_initial_response: conversationHistory.length === 0,
        user_id: userId
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
              {/* Usage Counter */}
              {usageStats && !usageStats.is_registered && (
                <div className="text-sm text-gray-600">
                  Trial: {usageStats.trial_remaining} interactions left
                </div>
              )}
              
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
          userId={userId}
          onTrialExceeded={() => setShowRegistrationModal(true)}
          conversationId={currentConversationId}
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

      {/* Trial Warning Banner */}
      {trialWarning && (
        <div className="fixed top-0 left-0 right-0 bg-amber-50 border-l-4 border-amber-500 p-4 z-40">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <p className="text-amber-700">{trialWarning}</p>
            <button
              onClick={() => setShowRegistrationModal(true)}
              className="text-amber-900 font-semibold hover:underline ml-4"
            >
              Register Now →
            </button>
          </div>
        </div>
      )}

      {/* Registration Modal */}
      <RegistrationModal
        isOpen={showRegistrationModal}
        onClose={() => setShowRegistrationModal(false)}
        onRegister={handleRegister}
        trialRemaining={usageStats?.trial_remaining || 0}
      />
    </div>
  );
};

export default App;
