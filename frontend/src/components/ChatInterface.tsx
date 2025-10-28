import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, User } from 'lucide-react';
import { ChatMessage, apiClient, ChatRequest } from '../api/client';
import RecommendationCard from './RecommendationCard';
import WelcomeMessage from './WelcomeMessage';

interface ChatMessageWithRecommendations {
  role: 'user' | 'assistant';
  content?: string; // Optional to allow undefined for recommendation-only messages
  timestamp?: string;
  recommendations?: any[];
}

interface ChatInterfaceProps {
  onNewMessage: (message: ChatMessage) => void;
  onRecommendations: (recommendations: any[]) => void;
  llmProvider: string;
  conversationHistory: ChatMessage[];
  userId: string;
  onTrialExceeded: () => void;
  conversationId: string | null;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  onNewMessage,
  onRecommendations,
  llmProvider,
  conversationHistory,
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



  // Scroll to bottom when new content is added (but not for recommendation-only messages)
  useEffect(() => {
    const lastMessage = messagesWithRecommendations[messagesWithRecommendations.length - 1];
    if (lastMessage) {
      // Check if this is a recommendation-only message
      const hasContent = lastMessage.content && lastMessage.content.trim() !== '';
      const isRecommendationOnly = !hasContent && lastMessage.recommendations && lastMessage.recommendations.length > 0;

      // Don't scroll for recommendation-only messages
      if (!isRecommendationOnly) {
        scrollToBottom();
      }
    }
  }, [messagesWithRecommendations]);

  // Sync with conversation history
  useEffect(() => {
    const syncedMessages: ChatMessageWithRecommendations[] = [];
    
    conversationHistory.forEach(msg => {
      // Add the original message
      syncedMessages.push({
        ...msg,
        recommendations: []
      });
      
      // If this message has recommendations, create separate messages for each recommendation
      if ((msg as any).recommendations && (msg as any).recommendations.length > 0) {
        (msg as any).recommendations.forEach((rec: any) => {
          syncedMessages.push({
            role: 'assistant',
            content: '', // Empty content - just show the recommendation card
            timestamp: new Date().toISOString(),
            recommendations: [rec]
          });
        });
      }
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

    onNewMessage(userMessage as ChatMessage);
    setMessagesWithRecommendations(prev => [...prev, userMessage]);
    setMessage('');
    setIsLoading(true);
    setExtractionSummary(null);
    setCurrentStatus('');

    try {
      // Detect if this is the first user message (initial response to welcome message)
      const isInitialResponse = conversationHistory.length === 0;
      
      const request: ChatRequest = {
        message: message.trim(),
        conversation_history: conversationHistory,
        llm_provider: llmProvider,
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
          onNewMessage(assistantMessage as ChatMessage);
          setMessagesWithRecommendations(prev => [...prev, assistantMessage]);
          
          // Clear the streaming state to prevent re-rendering
          
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
            content: undefined, // Use undefined for cleaner detection of recommendation-only messages
            timestamp: new Date().toISOString(),
            recommendations: [recommendation]
          };
          
          // Add to local UI state for rendering (don't add to conversation history)
          setMessagesWithRecommendations(prev => [...prev, recommendationMessage]);
          
          // Update recommendations tracking
          onRecommendations([recommendation]);
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
      setExtractionSummary(null);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {/* Show welcome message when conversation is empty */}
          {messagesWithRecommendations.length === 0 && (
            <WelcomeMessage />
          )}

          {messagesWithRecommendations.map((msg, index) => {
          // Check if this message has meaningful content (not just whitespace)
          const hasContent = msg.content && msg.content.trim() !== '';
          // Check if this is a recommendation-only message (no meaningful content, only recommendations)
          const isRecommendationOnly = !hasContent && msg.recommendations && msg.recommendations.length > 0;

          // Skip completely empty assistant messages that aren't recommendation-only
          if (msg.role === 'assistant' && !hasContent && (!msg.recommendations || msg.recommendations.length === 0)) {
            return null;
          }
          
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
