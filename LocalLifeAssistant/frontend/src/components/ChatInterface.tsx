import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { ChatMessage, apiClient, ChatRequest } from '../api/client';
import RecommendationCard from './RecommendationCard';

interface ChatMessageWithRecommendations extends ChatMessage {
  recommendations?: any[];
}

interface ChatInterfaceProps {
  onNewMessage: (message: ChatMessage) => void;
  onRecommendations: (recommendations: any[]) => void;
  llmProvider: string;
  conversationHistory: ChatMessage[];
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  onNewMessage,
  onRecommendations,
  llmProvider,
  conversationHistory
}) => {
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
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
        recommendations: existing?.recommendations || []
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

    try {
      const request: ChatRequest = {
        message: message.trim(),
        conversation_history: conversationHistory,
        llm_provider: llmProvider
      };

      const response = await apiClient.chat(request);
      
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
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      };
      onNewMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messagesWithRecommendations.map((msg, index) => (
          <div
            key={index}
            className={`chat-message ${msg.role}`}
          >
            <div className="flex items-start space-x-2">
              <div className="flex-shrink-0">
                {msg.role === 'user' ? (
                  <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                    U
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
            <div className="flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Thinking...</span>
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
