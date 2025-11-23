import React, { useState, useRef, useEffect } from 'react';
import { Send, MapPin, Moon, Briefcase, Heart, Laptop } from 'lucide-react';
import { ChatMessage, ChatRequest, apiClient } from '../api/client';
import { dataService } from '../services/dataService';
import RecommendationCard from './RecommendationCard';
import { ImageWithFallback } from './ImageWithFallback';
import { CompactWheelPicker } from './CompactWheelPicker';
import userAvatarImg from '../assets/images/figma/user-avatar.png';
import agentAvatarImg from '../assets/images/figma/agent-avatar.png';
import refreshIcon from '../assets/images/figma/refresh-icon.png';
import musicIcon from '../assets/images/figma/music-icon.png';
import wellnessIcon from '../assets/images/figma/wellness-icon.png';
import luckyIcon from '../assets/images/figma/lucky-icon.png';
import tapIcon from '../assets/images/figma/tap-icon.png';

interface ChatMessageWithRecommendations {
  role: 'user' | 'assistant';
  content?: string;
  timestamp?: string;
  recommendations?: any[];
  showEvents?: boolean;
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

// Helper function to convert snake_case to Title Case
const snakeToTitleCase = (str: string): string => {
  return str
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
};



// Helper component to render icon based on type
const EventTypeIcon: React.FC<{ eventType: string; className?: string }> = ({ eventType, className = "w-6 h-6" }) => {
  const iconStyle = { color: '#76C1B2' };
  
  switch (eventType) {
    case 'music':
      return <img src={musicIcon} alt="Music" className={className} />;
    case 'sports':
      return <span className={className} style={{ fontSize: '24px' }}>🏆</span>;
    case 'nightlife':
      return <Moon className={className} style={iconStyle} />;
    case 'business':
      return <Briefcase className={className} style={iconStyle} />;
    case 'tech':
      return <Laptop className={className} style={iconStyle} />;
    case 'dating':
      return <Heart className={className} style={iconStyle} />;
    default:
      return <img src={tapIcon} alt="Event" className={className} />;
  }
};

// Event type specific examples with icon components
const eventTypeExamples: Record<string, Array<{ text: string; icon: string; eventType: string }>> = {
  'music': [
    { text: 'Show me live music this weekend', icon: musicIcon, eventType: 'music' },
    { text: 'Find jazz concerts near me', icon: musicIcon, eventType: 'music' },
    { text: 'What music events are happening tonight?', icon: musicIcon, eventType: 'music' },
    { text: 'Surprise me with a music event!', icon: luckyIcon, eventType: 'music' }
  ],
  'sports': [
    { text: 'Show me sports events this weekend', icon: 'sports', eventType: 'sports' },
    { text: 'Find basketball games near me', icon: 'sports', eventType: 'sports' },
    { text: 'What sports events are happening tonight?', icon: 'sports', eventType: 'sports' },
    { text: 'Surprise me with a sports event!', icon: luckyIcon, eventType: 'sports' }
  ],
  'nightlife': [
    { text: 'Show me nightlife events this weekend', icon: 'nightlife', eventType: 'nightlife' },
    { text: 'Find bars and clubs near me', icon: 'nightlife', eventType: 'nightlife' },
    { text: 'What\'s happening tonight?', icon: 'nightlife', eventType: 'nightlife' },
    { text: 'Surprise me with a nightlife event!', icon: luckyIcon, eventType: 'nightlife' }
  ],
  'business': [
    { text: 'Show me business events this weekend', icon: 'business', eventType: 'business' },
    { text: 'Find networking events near me', icon: 'business', eventType: 'business' },
    { text: 'What business events are happening tonight?', icon: 'business', eventType: 'business' },
    { text: 'Surprise me with a business event!', icon: luckyIcon, eventType: 'business' }
  ],
  'tech': [
    { text: 'Show me tech events this weekend', icon: 'tech', eventType: 'tech' },
    { text: 'Find tech meetups near me', icon: 'tech', eventType: 'tech' },
    { text: 'What tech events are happening tonight?', icon: 'tech', eventType: 'tech' },
    { text: 'Surprise me with a tech event!', icon: luckyIcon, eventType: 'tech' }
  ],
  'dating': [
    { text: 'Show me dating events this weekend', icon: 'dating', eventType: 'dating' },
    { text: 'Find social events near me', icon: 'dating', eventType: 'dating' },
    { text: 'What dating events are happening tonight?', icon: 'dating', eventType: 'dating' },
    { text: 'Surprise me with a dating event!', icon: luckyIcon, eventType: 'dating' }
  ]
};

// Default examples (fallback)
const defaultExamples: Array<{ text: string; icon: string; eventType: string }> = [
  { text: 'Show me live music this weekend', icon: musicIcon, eventType: 'music' },
  { text: 'Find wellness activities near me', icon: wellnessIcon, eventType: 'business' },
  { text: 'Surprise me with something fun!', icon: luckyIcon, eventType: 'business' },
  { text: 'What\'s happening tonight?', icon: tapIcon, eventType: 'business' }
];

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
  const [messagesWithRecommendations, setMessagesWithRecommendations] = useState<ChatMessageWithRecommendations[]>([]);
  const [currentStatus, setCurrentStatus] = useState<string>('');
  const [supportedCities, setSupportedCities] = useState<string[]>([]);
  const [citiesDisplay, setCitiesDisplay] = useState<string[]>([]);
  const [supportedEventTypes, setSupportedEventTypes] = useState<string[]>([]);
  const [selectedCityIndex, setSelectedCityIndex] = useState(0);
  const [selectedEventTypeIndex, setSelectedEventTypeIndex] = useState(0);
  const [showWheelPicker, setShowWheelPicker] = useState(true);
  const [hasCompletedInitialSelection, setHasCompletedInitialSelection] = useState(false);
  const [showRefreshHint, setShowRefreshHint] = useState(false);
  const [keyboardOpen, setKeyboardOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const hasShownRefreshHint = useRef(false);
  const initialViewportHeight = useRef<number>(0);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    initialViewportHeight.current = window.innerHeight;
    
    const handleResize = () => {
      const currentHeight = window.innerHeight;
      const heightDifference = initialViewportHeight.current - currentHeight;
      setKeyboardOpen(heightDifference > 150);
    };
    
    window.addEventListener('resize', handleResize);
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', handleResize);
    }
    
    return () => {
      window.removeEventListener('resize', handleResize);
      if (window.visualViewport) {
        window.visualViewport.removeEventListener('resize', handleResize);
      }
    };
  }, []);

  useEffect(() => {
    const loadCities = async () => {
      try {
        const citiesSnakeCase = await apiClient.getSupportedCities();
        setSupportedCities(citiesSnakeCase);
        // Convert to Title Case for display
        const citiesTitleCase = citiesSnakeCase.map(city => snakeToTitleCase(city));
        setCitiesDisplay(citiesTitleCase);
      } catch (error) {
        console.error('Error loading supported cities:', error);
        const fallbackCities = ['san_francisco', 'new_york', 'los_angeles', 'miami', 'chicago', 'seattle', 'boston'];
        setSupportedCities(fallbackCities);
        setCitiesDisplay(fallbackCities.map(city => snakeToTitleCase(city)));
      }
    };
    
    const loadEventTypes = async () => {
      try {
        const eventTypes = await apiClient.getSupportedEventTypes();
        setSupportedEventTypes(eventTypes);
      } catch (error) {
        console.error('Error loading supported event types:', error);
        setSupportedEventTypes(['music', 'sports', 'nightlife', 'business', 'tech', 'dating']);
      }
    };
    
    loadCities();
    loadEventTypes();
  }, []);

  useEffect(() => {
    setMessagesWithRecommendations(prevMessages => {
      if (conversationHistory.length === 0) {
        return [];
      }

      const recommendationOnlyMessages = prevMessages.filter(msg => {
        const hasContent = msg.content && msg.content.trim() !== '';
        const hasRecommendations = msg.recommendations && msg.recommendations.length > 0;
        return !hasContent && hasRecommendations;
      });

      const conversationMessages: ChatMessageWithRecommendations[] = conversationHistory.map(msg => {
        const recommendations = (msg as any).recommendations ?? [];
        return {
          ...msg,
          recommendations: recommendations,
          showEvents: recommendations.length > 0
        };
      });

      const combinedMessages = [...conversationMessages, ...recommendationOnlyMessages];
      combinedMessages.sort((a, b) => {
        const aTime = a.timestamp ? new Date(a.timestamp).getTime() : 0;
        const bTime = b.timestamp ? new Date(b.timestamp).getTime() : 0;
        return aTime - bTime;
      });

      return combinedMessages;
    });
  }, [conversationHistory]);

  const handleSuggestionClick = async (suggestionText: string) => {
    if (isLoading) return;
    
    // Include selected city and event type in message if available (send snake_case format)
    let messageToSend = suggestionText;
    if (hasCompletedInitialSelection && supportedCities[selectedCityIndex] && supportedEventTypes[selectedEventTypeIndex]) {
      const citySnakeCase = supportedCities[selectedCityIndex];
      const eventType = supportedEventTypes[selectedEventTypeIndex];
      messageToSend = `${citySnakeCase}:${eventType}: ${suggestionText}`;
    }
    
    const userMessage: ChatMessageWithRecommendations = {
      role: 'user',
      content: suggestionText,
      timestamp: new Date().toISOString(),
      recommendations: []
    };

    onNewMessage(userMessage as ChatMessage);
    setMessagesWithRecommendations(prev => [...prev, userMessage]);
    setIsLoading(true);
    setCurrentStatus('');

    try {
      const request: ChatRequest = {
        message: messageToSend,
        conversation_history: conversationHistory,
        llm_provider: llmProvider,
        is_initial_response: conversationHistory.length <= 1,
        user_id: userId,
        conversation_id: conversationId
      };

      await dataService.chatStream(
        request,
        (status: string) => setCurrentStatus(status),
        (messageContent: string, metadata?: any) => {
          const assistantMessage: ChatMessageWithRecommendations = {
            role: 'assistant',
            content: messageContent,
            timestamp: new Date().toISOString(),
            recommendations: []
          };
          
          onNewMessage(assistantMessage as ChatMessage);
          setMessagesWithRecommendations(prev => [...prev, assistantMessage]);
          
          if (metadata?.trial_exceeded) {
            onTrialExceeded();
          }
          if (metadata?.conversation_id && metadata.conversation_id !== conversationId) {
            localStorage.setItem('current_conversation_id', metadata.conversation_id);
          }
        },
        (recommendation: any) => {
          setMessagesWithRecommendations(prev => {
            if (prev.length === 0) {
              return [{
                role: 'assistant',
                content: 'I found some great events for you. Here are my top recommendations:',
                timestamp: new Date().toISOString(),
                recommendations: [recommendation],
                showEvents: true
              }];
            }

            const updatedMessages = [...prev];
            const lastIndex = updatedMessages.length - 1;
            const lastMessage = updatedMessages[lastIndex];

            if (lastMessage.role === 'assistant') {
              updatedMessages[lastIndex] = {
                ...lastMessage,
                recommendations: [...(lastMessage.recommendations ?? []), recommendation],
                showEvents: true
              };
            } else {
              updatedMessages.push({
                role: 'assistant',
                content: 'I found some great events for you. Here are my top recommendations:',
                timestamp: new Date().toISOString(),
                recommendations: [recommendation],
                showEvents: true
              });
            }

            if (!hasShownRefreshHint.current) {
              setTimeout(() => {
                setShowRefreshHint(true);
                hasShownRefreshHint.current = true;
                setTimeout(() => setShowRefreshHint(false), 5000);
              }, 500);
            }

            return updatedMessages;
          });
          onRecommendations([recommendation]);
        },
        (error: string) => {
          console.error('Streaming error:', error);
          const errorMessage: ChatMessage = {
            role: 'assistant',
            content: `Sorry, I encountered an error: ${error}`,
            timestamp: new Date().toISOString()
          };
          onNewMessage(errorMessage);
        },
        () => {
          setIsLoading(false);
          setCurrentStatus('');
        }
      );
    } catch (error) {
      console.error('Error sending suggestion:', error);
      setIsLoading(false);
      setCurrentStatus('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    inputRef.current?.blur();

    // Include selected city and event type in message if available (send snake_case format)
    let messageToSend = message.trim();
    if (hasCompletedInitialSelection && supportedCities[selectedCityIndex] && supportedEventTypes[selectedEventTypeIndex]) {
      const citySnakeCase = supportedCities[selectedCityIndex];
      const eventType = supportedEventTypes[selectedEventTypeIndex];
      messageToSend = `${citySnakeCase}:${eventType}: ${message.trim()}`;
    }

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
    setCurrentStatus('');

    try {
      const request: ChatRequest = {
        message: messageToSend,
        conversation_history: conversationHistory,
        llm_provider: llmProvider,
        is_initial_response: conversationHistory.length <= 1,
        user_id: userId,
        conversation_id: conversationId
      };

      await dataService.chatStream(
        request,
        (status: string) => setCurrentStatus(status),
        (messageContent: string, metadata?: any) => {
          const assistantMessage: ChatMessageWithRecommendations = {
            role: 'assistant',
            content: messageContent,
            timestamp: new Date().toISOString(),
            recommendations: [],
            showEvents: false
          };
          
          onNewMessage(assistantMessage as ChatMessage);
          setMessagesWithRecommendations(prev => [...prev, assistantMessage]);
          
          if (metadata?.trial_exceeded) {
            onTrialExceeded();
          }
          if (metadata?.conversation_id && metadata.conversation_id !== conversationId) {
            localStorage.setItem('current_conversation_id', metadata.conversation_id);
          }
        },
        (recommendation: any) => {
          setMessagesWithRecommendations(prev => {
            if (prev.length === 0) {
              return [{
                role: 'assistant',
                content: 'I found some great events for you. Here are my top recommendations:',
                timestamp: new Date().toISOString(),
                recommendations: [recommendation],
                showEvents: true
              }];
            }

            const updatedMessages = [...prev];
            const lastIndex = updatedMessages.length - 1;
            const lastMessage = updatedMessages[lastIndex];

            if (lastMessage.role === 'assistant') {
              updatedMessages[lastIndex] = {
                ...lastMessage,
                recommendations: [...(lastMessage.recommendations ?? []), recommendation],
                showEvents: true
              };
            } else {
              updatedMessages.push({
                role: 'assistant',
                content: 'I found some great events for you. Here are my top recommendations:',
                timestamp: new Date().toISOString(),
                recommendations: [recommendation],
                showEvents: true
              });
            }

            if (!hasShownRefreshHint.current) {
              setTimeout(() => {
                setShowRefreshHint(true);
                hasShownRefreshHint.current = true;
                setTimeout(() => setShowRefreshHint(false), 5000);
              }, 500);
            }

            return updatedMessages;
          });
          onRecommendations([recommendation]);
        },
        (error: string) => {
          console.error('Streaming error:', error);
          const errorMessage: ChatMessage = {
            role: 'assistant',
            content: `Sorry, I encountered an error: ${error}`,
            timestamp: new Date().toISOString()
          };
          onNewMessage(errorMessage);
        },
        () => {
          setIsLoading(false);
          setCurrentStatus('');
        }
      );
    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
      setCurrentStatus('');
    }
  };

  const handleRefresh = async () => {
    const hasRecommendations = messagesWithRecommendations.some(
      msg => msg.recommendations && msg.recommendations.length > 0
    );
    
    if (!hasRecommendations || isLoading) return;

    const lastUserMessage = messagesWithRecommendations
      .slice()
      .reverse()
      .find(msg => msg.role === 'user' && msg.content);

    if (!lastUserMessage || !lastUserMessage.content) return;

    setIsLoading(true);
    setCurrentStatus('Refreshing recommendations...');

    try {
      const request: ChatRequest = {
        message: lastUserMessage.content,
        conversation_history: conversationHistory,
        llm_provider: llmProvider,
        is_initial_response: false,
        user_id: userId,
        conversation_id: conversationId
      };

      await dataService.chatStream(
        request,
        (status: string) => setCurrentStatus(status),
        (messageContent: string, metadata?: any) => {
          const assistantMessage: ChatMessageWithRecommendations = {
            role: 'assistant',
            content: messageContent,
            timestamp: new Date().toISOString(),
            recommendations: []
          };
          
          onNewMessage(assistantMessage as ChatMessage);
          setMessagesWithRecommendations(prev => [...prev, assistantMessage]);
          
          if (metadata?.trial_exceeded) {
            onTrialExceeded();
          }
        },
        (recommendation: any) => {
          setMessagesWithRecommendations(prev => {
            const updatedMessages = [...prev];
            const lastIndex = updatedMessages.length - 1;
            const lastMessage = updatedMessages[lastIndex];

            const isRecommendationOnly =
              lastMessage.role === 'assistant' &&
              (!lastMessage.content || lastMessage.content.trim().length === 0);

            if (isRecommendationOnly) {
              updatedMessages[lastIndex] = {
                ...lastMessage,
                recommendations: [...(lastMessage.recommendations ?? []), recommendation]
              };
            } else {
              updatedMessages.push({
                role: 'assistant',
                content: undefined,
                timestamp: new Date().toISOString(),
                recommendations: [recommendation]
              });
            }

            return updatedMessages;
          });
          onRecommendations([recommendation]);
        },
        (error: string) => {
          console.error('Refresh error:', error);
        },
        () => {
          setIsLoading(false);
          setCurrentStatus('');
        }
      );
    } catch (error) {
      console.error('Error refreshing:', error);
      setIsLoading(false);
      setCurrentStatus('');
    }
  };

  const hasRecommendations = messagesWithRecommendations.some(
    msg => msg.recommendations && msg.recommendations.length > 0
  );

  // Get examples based on selected event type
  const getCurrentExamples = () => {
    if (supportedEventTypes.length > 0 && selectedEventTypeIndex >= 0 && selectedEventTypeIndex < supportedEventTypes.length) {
      const eventType = supportedEventTypes[selectedEventTypeIndex];
      return eventTypeExamples[eventType] || defaultExamples;
    }
    return defaultExamples;
  };

  const currentExamples = getCurrentExamples();

  return (
    <div className="flex flex-col h-full bg-[#FCFBF9]">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-h-0">
        {messagesWithRecommendations.length > 0 ? (
          <>
            {/* Flexible Spacer */}
            <div className={`bg-[#FCFBF9] transition-all duration-300 ${keyboardOpen ? 'flex-grow-0' : 'flex-1'}`} />
            
            {/* Chat Conversation */}
            <div className="overflow-y-auto bg-[#FCFBF9] px-4 py-4 space-y-4 scrollbar-hide flex-shrink min-h-0">
          {messagesWithRecommendations.map((msg, index) => {
          const hasContent = msg.content && msg.content.trim() !== '';
          const isRecommendationOnly = !hasContent && msg.recommendations && msg.recommendations.length > 0;

          if (msg.role === 'assistant' && !hasContent && (!msg.recommendations || msg.recommendations.length === 0)) {
            return null;
          }
          
          return (
            <div key={index}>
              {msg.role === 'user' ? (
                <div className="flex justify-end gap-2 items-start">
                        <div className="rounded-xl rounded-tr-sm px-4 py-3 max-w-[80%] border shadow-sm" style={{ backgroundColor: '#E9E6DF', borderColor: '#EDEBE6' }}>
                    <p className="text-[15px]" style={{ color: '#221A13' }}>{msg.content}</p>
                  </div>
                        <div className="w-11 h-11 rounded-full flex-shrink-0 flex items-center justify-center mt-1 overflow-hidden p-1 border-0" style={{ backgroundColor: '#E9E6DF' }}>
                    <ImageWithFallback src={userAvatarImg} alt="User" className="w-3/4 h-3/4 object-cover rounded-full" />
                  </div>
                </div>
              ) : isRecommendationOnly ? (
                <div className="flex gap-2 items-start">
                  <div className="w-11 h-11 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    {msg.recommendations && msg.recommendations.length > 0 && (
                            <div className="overflow-x-auto overflow-y-hidden -mx-1 scrollbar-hide">
                              <div className="flex gap-3 px-1 pb-2">
                                {msg.recommendations.map((rec, recIndex) => (
                                  <div key={recIndex} className="flex-shrink-0">
                                    <RecommendationCard recommendation={rec} />
                                  </div>
                                ))}
                              </div>
                            </div>
                    )}
                  </div>
                </div>
                    ) : (
                      <div className="flex gap-2 items-start">
                        <div className="w-11 h-11 rounded-full flex-shrink-0 flex items-center justify-center mt-1 overflow-hidden p-1.5 border-2" style={{ backgroundColor: 'white', borderColor: 'rgba(118, 193, 178, 0.6)' }}>
                          <ImageWithFallback src={agentAvatarImg} alt="Agent" className="w-4/5 h-4/5 object-cover" />
                        </div>
                        
                        <div className="flex-1 space-y-3 min-w-0">
                          {msg.content && (
                            <div className="bg-white rounded-xl rounded-tl-sm px-4 py-3 shadow-md border" style={{ borderColor: '#F5F5F5' }}>
                              <p className="text-[15px]" style={{ color: '#221A13' }}>{msg.content}</p>
                            </div>
                          )}

                          {msg.showEvents && msg.recommendations && msg.recommendations.length > 0 && (
                            <div className="overflow-x-auto overflow-y-hidden -mx-1 scrollbar-hide">
                              <div className="flex gap-3 px-1 pb-2">
                                {msg.recommendations.map((rec, recIndex) => (
                                  <div key={recIndex} className="flex-shrink-0">
                                    <RecommendationCard recommendation={rec} />
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}

              {isLoading && (
                <div className="flex gap-2 items-start">
                  <div className="w-11 h-11 rounded-full flex-shrink-0 flex items-center justify-center mt-1 overflow-hidden p-1.5 border-2" style={{ backgroundColor: 'white', borderColor: 'rgba(118, 193, 178, 0.6)' }}>
                    <ImageWithFallback src={agentAvatarImg} alt="Agent" className="w-4/5 h-4/5 object-cover" />
                  </div>
                  <div className="bg-white rounded-lg rounded-tl-sm px-4 py-3 shadow-md border" style={{ borderColor: '#F5F5F5' }}>
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms', animationDuration: '1s' }} />
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms', animationDuration: '1s' }} />
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms', animationDuration: '1s' }} />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center px-6 pb-32 bg-[#FCFBF9]">
            <h2 className="text-slate-900 mb-2 text-center" style={{ fontFamily: 'Aladin, cursive' }}>Discover Local Events</h2>
            <p className="text-slate-600 text-center text-sm mb-8">
              {hasCompletedInitialSelection ? 'Tap a suggestion below to get started' : 'Select your city and vibe to start'}
            </p>
            <div className="w-full space-y-3">
              {currentExamples.map((example, index) => (
                <button 
                  key={index}
                  disabled={!hasCompletedInitialSelection}
                  onClick={() => handleSuggestionClick(example.text)}
                  className="w-full px-4 py-4 bg-white rounded-xl text-left hover:shadow-md transition-all shadow-sm border border-slate-100 flex items-center gap-3 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:shadow-sm"
                  style={{ color: '#221A13' }}
                >
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 bg-[#FCFBF9]">
                    {typeof example.icon === 'string' && (example.icon === 'sports' || example.icon === 'nightlife' || example.icon === 'business' || example.icon === 'tech' || example.icon === 'dating') ? (
                      <EventTypeIcon eventType={example.eventType} className="w-6 h-6" />
                    ) : typeof example.icon === 'string' ? (
                      <img src={example.icon} alt="" className="w-6 h-6" />
                    ) : null}
                  </div>
                  <span className="text-sm">{example.text}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area - Always at Bottom */}
        <div className="bg-[#FCFBF9] px-4 py-3 flex-shrink-0 relative">
          {/* Selection Tags - Above Input */}
          {hasCompletedInitialSelection && (
            <div className="mb-3 flex items-center gap-2 animate-in fade-in slide-in-from-bottom-2 duration-200">
              <button
                onClick={() => setShowWheelPicker(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-white rounded-lg shadow-sm border border-slate-200 hover:shadow-md transition-all text-sm"
                style={{ color: '#221A13' }}
              >
                <MapPin className="w-3.5 h-3.5" style={{ color: '#76C1B2' }} />
                <span>{citiesDisplay[selectedCityIndex] || 'Select City'}</span>
              </button>
              <button
                onClick={() => setShowWheelPicker(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-white rounded-lg shadow-sm border border-slate-200 hover:shadow-md transition-all text-sm"
                style={{ color: '#221A13' }}
              >
                <span className="w-3.5 h-3.5 flex items-center justify-center" style={{ color: '#76C1B2' }}>🎯</span>
                <span>{supportedEventTypes[selectedEventTypeIndex] ? supportedEventTypes[selectedEventTypeIndex].charAt(0).toUpperCase() + supportedEventTypes[selectedEventTypeIndex].slice(1) : 'Select Vibe'}</span>
              </button>
        </div>
          )}

          {/* Wheel Pickers - Floating Overlay */}
          {showWheelPicker && (
            <div className="absolute bottom-full left-0 right-0 mb-2 px-4 animate-in slide-in-from-bottom-4 duration-200 z-50">
              <div className="bg-white rounded-xl shadow-2xl border border-slate-200 py-4 px-3">
                <h3 className="text-center mb-3" style={{ color: '#221A13', fontFamily: 'Aladin, cursive' }}>
                  Choose Your Loco & Vibe
                </h3>
                
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <CompactWheelPicker
                    items={citiesDisplay.length > 0 ? citiesDisplay : ['Loading...']}
                    selectedIndex={selectedCityIndex}
                    onChange={setSelectedCityIndex}
                    label="City"
                  />
                  <CompactWheelPicker
                    items={supportedEventTypes.length > 0 ? supportedEventTypes.map(et => et.charAt(0).toUpperCase() + et.slice(1)) : ['Loading...']}
                    selectedIndex={selectedEventTypeIndex}
                    onChange={setSelectedEventTypeIndex}
                    label="Vibe"
                  />
                </div>

                <button
                  onClick={() => {
                    setShowWheelPicker(false);
                    setHasCompletedInitialSelection(true);
                  }}
                  className="w-full py-3 text-white rounded-xl text-sm transition-all active:scale-95 hover:opacity-90 shadow-sm"
                  style={{ backgroundColor: '#76C1B2' }}
                >
                  Confirm Selection
                </button>
              </div>
            </div>
          )}

          {/* Input Form */}
        <form onSubmit={handleSubmit} className="flex gap-3 items-center relative">
            <div className="relative">
              {showRefreshHint && (
                <div className="absolute bottom-full left-[100%] -translate-x-[40%] mb-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <div className="text-white px-5 py-3 rounded-xl shadow-lg text-sm whitespace-nowrap min-w-[220px]" style={{ backgroundColor: '#76C1B2' }}>
                    <div className="flex items-center gap-2">
                      <img src={tapIcon} alt="Tap" className="w-5 h-5" style={{ filter: 'brightness(0) invert(1)' }} />
                      <span>Tap to refresh all events!</span>
                    </div>
                    <div className="absolute top-full left-[12%] -mt-px">
                      <div className="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[6px]" style={{ borderTopColor: '#76C1B2' }} />
                    </div>
                  </div>
                </div>
              )}
              
            <button
              type="button"
              onClick={handleRefresh}
              disabled={!hasRecommendations || isLoading}
              className="rounded-full bg-white h-14 w-14 flex items-center justify-center transition-all shadow-md border-[0.5px] border-slate-200 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 disabled:hover:bg-white active:scale-90 active:shadow-lg"
            >
              <img 
                src={refreshIcon} 
                alt="Refresh" 
                className="w-8 h-8 transition-transform active:rotate-180" 
                style={{ 
                  filter: 'invert(67%) sepia(18%) saturate(1245%) hue-rotate(121deg) brightness(92%) contrast(86%)'
                }} 
              />
            </button>
            </div>
            <input
              ref={inputRef}
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e as any);
                }
              }}
              placeholder={messagesWithRecommendations.length > 1 ? "What else are you looking for?" : "What vibe are you looking for?"}
              className="flex-1 rounded-xl border-[0.5px] border-slate-200 bg-white shadow-md h-14 text-base px-6 placeholder:text-[#5E574E]"
              style={{ color: '#221A13' }}
            />
          <button
            type="submit"
              className="rounded-full bg-white hover:bg-slate-50 h-14 w-14 flex items-center justify-center transition-all shadow-md border-[0.5px] border-slate-200 active:scale-90 active:shadow-lg"
          >
              <Send className="w-7 h-7" style={{ color: '#B46A55' }} />
          </button>
        </form>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
