import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, User } from 'lucide-react';
import { ChatMessage, apiClient, ChatRequest, LocationCoordinates } from '../api/client';
import RecommendationCard from './RecommendationCard';
import WelcomeMessage from './WelcomeMessage';

interface ChatMessageWithRecommendations extends ChatMessage {
  recommendations?: any[];
}

interface ChatInterfaceProps {
  onNewMessage: (message: ChatMessage) => void;
  onRecommendations: (recommendations: any[]) => void;
  llmProvider: string;
  conversationHistory: ChatMessage[];
  userLocation: LocationCoordinates | null;
  userId: string;
  onTrialExceeded: () => void;
  conversationId: string | null;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  onNewMessage,
  onRecommendations,
  llmProvider,
  conversationHistory,
  userLocation,
  userId,
  onTrialExceeded,
  conversationId
}) => {
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [extractionSummary, setExtractionSummary] = useState<string | null>(null);
  const [messagesWithRecommendations, setMessagesWithRecommendations] = useState<ChatMessageWithRecommendations[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };


  useEffect(() => {
    scrollToBottom();
  }, [conversationHistory, messagesWithRecommendations]);

  // Sync with conversation history
  useEffect(() => {
    const syncedMessages = conversationHistory.map(msg => {
      const existing = messagesWithRecommendations.find(m => m.timestamp === msg.timestamp);
      return {
        ...msg,
        recommendations: existing?.recommendations || (msg as any).recommendations || []
      };
    });
    setMessagesWithRecommendations(syncedMessages);
  }, [conversationHistory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    const userMessage: ChatMessageWithRecommendations = {
      role: 'user',
      content: message.trim(),
      timestamp: new Date().toISOString(),
      recommendations: []
    };

    onNewMessage(userMessage);
    setMessagesWithRecommendations(prev => [...prev, userMessage]);
    setMessage('');
    setIsLoading(true);
    setExtractionSummary(null);

    try {
      // Detect if this is the first user message (initial response to welcome message)
      const isInitialResponse = conversationHistory.length === 0;
      
      const request: ChatRequest = {
        message: message.trim(),
        conversation_history: conversationHistory,
        llm_provider: llmProvider,
        location: userLocation,
        is_initial_response: isInitialResponse,
        user_id: userId,
        conversation_id: conversationId
      };

      const response = await apiClient.chat(request);
      
      // Check if trial exceeded
      if (response.trial_exceeded) {
        onTrialExceeded();
      }

      // Update conversation ID if it changed (new conversation)
      if (response.conversation_id && response.conversation_id !== conversationId) {
        // This will trigger App.tsx to update
        console.log('Conversation ID updated:', response.conversation_id);
        localStorage.setItem('current_conversation_id', response.conversation_id);
      }
      
      // Set extraction summary if available and keep loading state to show it
      if (response.extraction_summary) {
        setExtractionSummary(response.extraction_summary);
        // Keep loading state for a moment to show the extraction summary
        setTimeout(() => {
          const assistantMessage: ChatMessageWithRecommendations = {
            role: 'assistant',
            content: response.message,
            timestamp: new Date().toISOString(),
            recommendations: response.recommendations || []
          };

          onNewMessage(assistantMessage);
          console.log('Received recommendations:', response.recommendations);
          onRecommendations(response.recommendations || []);
          
          // Update local state with recommendations
          setMessagesWithRecommendations(prev => [...prev, assistantMessage]);
          
          // Clear loading state
          setIsLoading(false);
          setExtractionSummary(null);
        }, 1500); // Show extraction summary for 1.5 seconds
      } else {
        // No extraction summary, proceed normally
        const assistantMessage: ChatMessageWithRecommendations = {
          role: 'assistant',
          content: response.message,
          timestamp: new Date().toISOString(),
          recommendations: response.recommendations || []
        };

        onNewMessage(assistantMessage);
        console.log('Received recommendations:', response.recommendations);
        onRecommendations(response.recommendations || []);
        
        // Update local state with recommendations
        setMessagesWithRecommendations(prev => [...prev, assistantMessage]);
        
        // Clear loading state
        setIsLoading(false);
        setExtractionSummary(null);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      };
      onNewMessage(errorMessage);
      setIsLoading(false);
      setExtractionSummary(null);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Show welcome message when conversation is empty */}
        {messagesWithRecommendations.length === 0 && (
          <WelcomeMessage />
        )}
        
        {messagesWithRecommendations.map((msg, index) => (
          <div
            key={index}
            className={`chat-message ${msg.role}`}
          >
            <div className="flex items-start space-x-2">
              <div className="flex-shrink-0">
                {msg.role === 'user' ? (
                  <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center text-white">
                    <User className="w-4 h-4" />
                  </div>
                ) : (
                  <div className="w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                    AI
                  </div>
                )}
              </div>
              <div className="flex-1">
                <div className="text-sm text-gray-500 mb-1">
                  {msg.role === 'user' ? 'You' : 'Assistant'}
                </div>
                <div className="whitespace-pre-wrap mb-3">{msg.content}</div>
                
                {/* Display recommendations inline */}
                {msg.recommendations && msg.recommendations.length > 0 && (
                  <div className="mt-4 space-y-3">
                    <div className="text-sm font-medium text-gray-700 mb-2">
                      📋 Recommendations ({msg.recommendations.length})
                    </div>
                    {msg.recommendations.map((rec, recIndex) => (
                      <div key={recIndex} className="border border-gray-200 rounded-lg p-3 bg-gray-50">
                        <RecommendationCard recommendation={rec} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="chat-message assistant">
            <div className="flex items-start space-x-2">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  AI
                </div>
              </div>
              <div className="flex-1">
                <div className="text-sm text-gray-500 mb-1">
                  Assistant
                </div>
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>
                    {extractionSummary || 'Processing your request...'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask me about events, restaurants, or anything local..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!message.trim() || isLoading}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            <span>Send</span>
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
