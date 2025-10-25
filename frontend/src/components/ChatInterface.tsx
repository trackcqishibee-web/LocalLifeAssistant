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
  const [currentStatus, setCurrentStatus] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const scrollToMostRecentUserMessage = (messages: ChatMessageWithRecommendations[]) => {
    console.log('🔄 scrollToMostRecentUserMessage called with messages:', messages.length);
    // Find all user messages and scroll to the most recent one
    const userMessages = messages.filter(msg => msg.role === 'user');
    console.log('👤 Found user messages:', userMessages.length);
    
    if (userMessages.length > 0) {
      const mostRecentUserMessage = userMessages[userMessages.length - 1];
      const messageIndex = messages.findIndex(msg => msg.timestamp === mostRecentUserMessage.timestamp);
      console.log('📍 Most recent user message index:', messageIndex);
      
      // Find the DOM element and scroll to it
      const messageElements = document.querySelectorAll('.chat-message');
      console.log('🎯 Found DOM elements:', messageElements.length);
      
      if (messageElements[messageIndex]) {
        console.log('📍 Scrolling to most recent user message at index:', messageIndex);
        messageElements[messageIndex].scrollIntoView({ behavior: 'smooth', block: 'start' });
      } else {
        console.log('❌ Element not found at index:', messageIndex);
      }
    } else {
      console.log('❌ No user messages found');
    }
  };


  useEffect(() => {
    // Only scroll to bottom for user messages, not for assistant messages
    const lastMessage = messagesWithRecommendations[messagesWithRecommendations.length - 1];
    if (lastMessage && lastMessage.role === 'user') {
      scrollToBottom();
    }
  }, [conversationHistory, messagesWithRecommendations]);

  // Scroll to most recent user message when assistant message is added
  useEffect(() => {
    const lastMessage = messagesWithRecommendations[messagesWithRecommendations.length - 1];
    if (lastMessage && lastMessage.role === 'assistant' && lastMessage.content.includes('Found')) {
      // This is the main "Found X events" message, scroll to the most recent user message
      setTimeout(() => {
        scrollToMostRecentUserMessage(messagesWithRecommendations);
      }, 100);
    }
  }, [messagesWithRecommendations]);

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
    setCurrentStatus('');
    // Clear previous streaming state when starting new message
    setCurrentAssistantMessage(null);
    setCurrentRecommendations([]);

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

      await apiClient.chatStream(
        request,
        // onStatus
        (status: string) => {
          setCurrentStatus(status);
        },
        // onMessage
        (messageContent: string, metadata?: any) => {
          // Create the main message without recommendations (they're separate now)
          const assistantMessage: ChatMessageWithRecommendations = {
            role: 'assistant',
            content: messageContent,
            timestamp: new Date().toISOString(),
            recommendations: []
          };
          
          // Add to conversation history immediately
          onNewMessage(assistantMessage);
          setMessagesWithRecommendations(prev => [...prev, assistantMessage]);
          
          // Clear the streaming state to prevent re-rendering
          setCurrentAssistantMessage(null);
          setCurrentRecommendations([]);
          
          // Check if trial exceeded
          if (metadata?.trial_exceeded) {
            onTrialExceeded();
          }

          // Update conversation ID if it changed (new conversation)
          if (metadata?.conversation_id && metadata.conversation_id !== conversationId) {
            console.log('Conversation ID updated:', metadata.conversation_id);
            localStorage.setItem('current_conversation_id', metadata.conversation_id);
          }
          
          // Set extraction summary if available
          if (metadata?.extraction_summary) {
            setExtractionSummary(metadata.extraction_summary);
          }
        },
        // onRecommendation
        (recommendation: any) => {
          // Create a separate message for each recommendation
          const recommendationMessage: ChatMessageWithRecommendations = {
            role: 'assistant',
            content: '', // Empty content - just show the recommendation card
            timestamp: new Date().toISOString(),
            recommendations: [recommendation]
          };
          
          // Add to conversation history immediately
          onNewMessage(recommendationMessage);
          setMessagesWithRecommendations(prev => [...prev, recommendationMessage]);
          
          // Update current recommendations for tracking
          setCurrentRecommendations(prev => {
            const newRecommendations = [...prev, recommendation];
            onRecommendations(newRecommendations);
            return newRecommendations;
          });
        },
        // onError
        (error: string) => {
          console.error('Streaming error:', error);
          const errorMessage: ChatMessage = {
            role: 'assistant',
            content: `Sorry, I encountered an error: ${error}`,
            timestamp: new Date().toISOString()
          };
          onNewMessage(errorMessage);
        },
        // onDone
        () => {
          // Clear loading state and reset streaming state
          setIsLoading(false);
          setCurrentStatus('');
          setCurrentAssistantMessage(null);
          setCurrentRecommendations([]);
          setExtractionSummary(null);
        }
      );
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      };
      onNewMessage(errorMessage);
      setIsLoading(false);
      setCurrentStatus('');
      setCurrentAssistantMessage(null);
      setCurrentRecommendations([]);
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
        
        {messagesWithRecommendations.map((msg, index) => {
          // Check if this is a recommendation-only message (no content, only recommendations)
          const isRecommendationOnly = !msg.content && msg.recommendations && msg.recommendations.length > 0;
          
          return (
            <div
              key={index}
              className={`chat-message ${msg.role}`}
            >
              {isRecommendationOnly ? (
                // For recommendation-only messages, just show the recommendation card
                <div className="space-y-3">
                  {msg.recommendations?.map((rec, recIndex) => (
                    <div key={recIndex} className="mb-6 animate-fadeIn">
                      <RecommendationCard recommendation={rec} />
                    </div>
                  ))}
                </div>
              ) : (
                // For regular messages, show avatar, label, content, and recommendations
                <div className="flex items-start space-x-2">
                  <div className="flex-shrink-0">
                    {msg.role === 'user' ? (
                      <div className="w-8 h-8 bg-amber-600 rounded-full flex items-center justify-center text-white">
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
                        <div className="text-sm font-medium text-gray-600 mb-4">
                          📋 Recommendations ({msg.recommendations.length})
                        </div>
                        {msg.recommendations.map((rec, recIndex) => (
                          <div key={recIndex} className="mb-6">
                            <RecommendationCard recommendation={rec} />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
        
        
        {isLoading && (
          <div className="chat-message assistant">
            <div className="flex items-start space-x-2">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-amber-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
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
                    {currentStatus || extractionSummary || 'Processing your request...'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-gray-50/50 p-4 shadow-sm">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask me about events, restaurants, or anything local..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!message.trim() || isLoading}
            className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
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
