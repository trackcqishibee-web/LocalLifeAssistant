import React, { useState, useEffect, useRef } from 'react';
import { MobileSearchView } from './components/MobileSearchView';
import RegistrationModal from './components/RegistrationModal';
import LoginModal from './components/LoginModal';
import { ChatMessage, apiClient } from './api/client';
import { getOrCreateUserId, setUserId } from './utils/userIdManager';
import { updateUsageStats, shouldShowRegistrationPrompt, markRegistrationPrompted, getTrialWarningMessage } from './utils/usageTracker';
import { auth } from './firebase/config';
import { onAuthStateChanged, User } from 'firebase/auth';

// Helper function to create initial conversation messages (empty - no welcome message)
const createInitialMessages = (): ChatMessage[] => {
  return [];
};

const App: React.FC = () => {
  const [conversationHistory, setConversationHistory] = useState<ChatMessage[]>([]);
  const [llmProvider] = useState('openai');
  const [userId, setUserIdState] = useState<string>('');
  const [usageStats, setUsageStats] = useState<any>(null);
  const [showRegistrationModal, setShowRegistrationModal] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [trialWarning, setTrialWarning] = useState('');
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);

  // Firebase authentication state
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    // Prevent browser scroll restoration on page load
    if ('scrollRestoration' in history) {
      history.scrollRestoration = 'manual';
    }

    // Scroll to top on initial load
    window.scrollTo(0, 0);

    // On page refresh, always clear conversation history and start fresh
    setConversationHistory([]);
    localStorage.removeItem('current_conversation_id');
    localStorage.removeItem('conversation_history');
  }, []);

  // Firebase authentication state listener
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setCurrentUser(user);
      setAuthLoading(false);

      if (user) {
        // User is signed in, verify token with backend
        try {
          const token = await user.getIdToken();
          const response = await apiClient.verifyToken(token);

          // Update user ID to the authenticated user's ID
          const authenticatedUserId = response.user_id || user.uid;
          setUserIdState(authenticatedUserId);
          setUserId(authenticatedUserId);

          // Update usage stats for registered user
          updateUsageStats({ is_registered: true });

          console.log('User authenticated:', authenticatedUserId);
        } catch (error) {
          console.error('Token verification failed:', error);
          // If token verification fails, sign out
          await auth.signOut();
        }
      } else {
        // User is signed out, use anonymous user ID
        const uid = getOrCreateUserId();
        setUserIdState(uid);
        console.log('User not authenticated, using anonymous ID:', uid);
      }
    });

    return () => unsubscribe();
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

  const handleNewMessage = (message: ChatMessage) => {
    setConversationHistory(prev => {
      const updated = [...prev, message];
      // Persist to localStorage for session preservation
      localStorage.setItem('conversation_history', JSON.stringify(updated));
      return updated;
    });
  };

  const handleRecommendations = (recommendations: any[]) => {
    // Handle recommendations if needed
    console.log('Received recommendations:', recommendations);
  };

  // Initialize conversation when userId changes (but preserve during login/logout)
  // Use a ref to track if we're in the middle of a login/logout operation
  const preserveConversationRef = useRef(false);
  
  useEffect(() => {
    if (!userId) return;
    
    const initializeConversation = async () => {
      // If we're preserving conversation (during login/logout), don't create new one
      if (preserveConversationRef.current) {
        preserveConversationRef.current = false; // Reset flag
        return;
      }
      
      // Check if we have an existing conversation from localStorage (only if preserving)
      const existingConvId = localStorage.getItem('current_conversation_id');
      const existingHistoryJson = localStorage.getItem('conversation_history');
      
      // Only restore if we have both and conversationHistory is empty (preserved state)
      if (existingConvId && existingHistoryJson && conversationHistory.length === 0) {
        try {
          const existingHistory = JSON.parse(existingHistoryJson);
          if (Array.isArray(existingHistory) && existingHistory.length > 0) {
            // Try to load the existing conversation from the backend
            try {
              const conversation = await apiClient.getConversation(userId, existingConvId);
              if (conversation && conversation.messages && conversation.messages.length > 0) {
                // Preserve existing conversation from backend
                setCurrentConversationId(existingConvId);
                setConversationHistory(conversation.messages);
                localStorage.setItem('conversation_history', JSON.stringify(conversation.messages));
                console.log('Restored conversation from backend:', existingConvId);
                return;
              }
            } catch (error) {
              console.log('Could not load conversation from backend, using localStorage:', error);
              // Use localStorage version as fallback
              setCurrentConversationId(existingConvId);
              setConversationHistory(existingHistory);
              console.log('Restored conversation from localStorage:', existingConvId);
              return;
            }
          }
        } catch (error) {
          console.log('Could not parse conversation history from localStorage:', error);
          // Continue to create new conversation
        }
      }
      
      // No existing conversation or on fresh page load - create new one
      if (conversationHistory.length === 0) {
        const newId = await apiClient.createConversation(userId, { 
          llm_provider: llmProvider 
        });
        setCurrentConversationId(newId);
        localStorage.setItem('current_conversation_id', newId);
        
        // Start conversation with welcome message and sample events, followed by city prompt
        const initialMessages = createInitialMessages();
        setConversationHistory(initialMessages);
        localStorage.setItem('conversation_history', JSON.stringify(initialMessages));
        
        console.log('Created new conversation:', newId);
      }
    };
    
    initializeConversation();
  }, [userId, llmProvider]);

  const handleRegister = async (anonymousUserId: string, _email: string, _password: string, _name: string, idToken: string) => {
    try {
      // Preserve current conversation before registration
      const currentConvId = currentConversationId;
      const currentHistory = conversationHistory;
      
      // Set flag to preserve conversation during userId change
      preserveConversationRef.current = true;
      
      // The Firebase user is already created, now register with our backend using token
      const response = await apiClient.registerWithToken(anonymousUserId, idToken);

      if (response.success) {
        // Update user ID to registered user
        const registeredUserId = response.user_id;
        setUserIdState(registeredUserId);
        setUserId(registeredUserId);

        // Update usage stats
        updateUsageStats({ is_registered: true });

        // Preserve conversation if it exists
        if (currentConvId && currentHistory.length > 0) {
          // Try to use the migrated conversation
          try {
            const conversation = await apiClient.getConversation(registeredUserId, currentConvId);
            if (conversation && conversation.messages && conversation.messages.length > 0) {
              setCurrentConversationId(currentConvId);
              setConversationHistory(conversation.messages);
              localStorage.setItem('current_conversation_id', currentConvId);
              localStorage.setItem('conversation_history', JSON.stringify(conversation.messages));
              console.log('Preserved conversation after registration:', currentConvId);
            } else {
              // Fallback: use current history
              setCurrentConversationId(currentConvId);
              setConversationHistory(currentHistory);
              localStorage.setItem('current_conversation_id', currentConvId);
              localStorage.setItem('conversation_history', JSON.stringify(currentHistory));
            }
          } catch (error) {
            // Fallback: preserve current history
            setCurrentConversationId(currentConvId);
            setConversationHistory(currentHistory);
            localStorage.setItem('current_conversation_id', currentConvId);
            localStorage.setItem('conversation_history', JSON.stringify(currentHistory));
          }
        }

        // Show success message
        alert('Registration successful! Your conversation history has been preserved.');
      }
    } catch (error) {
      console.error('Backend registration failed:', error);
      // If backend registration fails, we should sign out from Firebase
      await auth.signOut();
      throw error;
    }
  };

  const handleLogin = async (_user: User, token: string) => {
    try {
      // Preserve current conversation before login
      const currentConvId = currentConversationId;
      const currentHistory = conversationHistory;
      
      // Set flag to preserve conversation during userId change
      preserveConversationRef.current = true;
      
      // Firebase authentication is already handled, just verify with backend
      const response = await apiClient.verifyToken(token);

      if (response.success) {
        // Update user ID to authenticated user
        const authenticatedUserId = response.user_id || _user.uid;
        setUserIdState(authenticatedUserId);
        setUserId(authenticatedUserId);

        // Update usage stats for registered user
        updateUsageStats({ is_registered: true });

        // Preserve conversation if it exists, otherwise load user's conversations
        if (currentConvId && currentHistory.length > 0) {
          // Try to preserve current conversation
          try {
            const conversation = await apiClient.getConversation(authenticatedUserId, currentConvId);
            if (conversation && conversation.messages && conversation.messages.length > 0) {
              setCurrentConversationId(currentConvId);
              setConversationHistory(conversation.messages);
              localStorage.setItem('current_conversation_id', currentConvId);
              localStorage.setItem('conversation_history', JSON.stringify(conversation.messages));
              console.log('Preserved conversation after login:', currentConvId);
            } else {
              // Fallback: use current history
              setCurrentConversationId(currentConvId);
              setConversationHistory(currentHistory);
              localStorage.setItem('current_conversation_id', currentConvId);
              localStorage.setItem('conversation_history', JSON.stringify(currentHistory));
            }
          } catch (error) {
            // Fallback: preserve current history
            setCurrentConversationId(currentConvId);
            setConversationHistory(currentHistory);
            localStorage.setItem('current_conversation_id', currentConvId);
            localStorage.setItem('conversation_history', JSON.stringify(currentHistory));
          }
        } else {
          // No current conversation - try to load user's conversations
          try {
            const conversations = await apiClient.listUserConversations(authenticatedUserId);

            // Load most recent conversation if exists
            if (conversations && conversations.length > 0) {
              const mostRecent = conversations[0];
              const conversation = await apiClient.getConversation(authenticatedUserId, mostRecent.conversation_id);
              setCurrentConversationId(mostRecent.conversation_id);
              setConversationHistory(conversation.messages || []);
              localStorage.setItem('current_conversation_id', mostRecent.conversation_id);
              localStorage.setItem('conversation_history', JSON.stringify(conversation.messages || []));
            } else {
              // New user - start with welcome message and sample events
              const initialMessages = createInitialMessages();
              setConversationHistory(initialMessages);
              localStorage.setItem('conversation_history', JSON.stringify(initialMessages));
            }
          } catch (conversationError: any) {
            // If listing conversations fails, start with welcome message and sample events
            console.warn('Could not load conversations, starting fresh:', conversationError);
            const initialMessages = createInitialMessages();
            setConversationHistory(initialMessages);
            localStorage.setItem('conversation_history', JSON.stringify(initialMessages));
          }
        }

        setShowLoginModal(false);
        alert('Login successful! Welcome back!');
      }
    } catch (error: any) {
      console.error('Login verification failed:', error);
      // If verification fails, sign out from Firebase
      await auth.signOut();
      throw error;
    }
  };


  const handleLogout = async () => {
    try {
      // Preserve current conversation before logout
      const currentConvId = currentConversationId;
      const currentHistory = conversationHistory;
      
      // Set flag to preserve conversation during userId change
      preserveConversationRef.current = true;
      
      await auth.signOut();
      
      // Reset to anonymous user ID
      const anonymousId = getOrCreateUserId();
      setUserIdState(anonymousId);
      setUserId(anonymousId);

      // Preserve conversation if it exists
      if (currentConvId && currentHistory.length > 0) {
        // Try to preserve the conversation with anonymous user
        // The conversation will be migrated if user logs back in
        setCurrentConversationId(currentConvId);
        setConversationHistory(currentHistory);
        localStorage.setItem('current_conversation_id', currentConvId);
        localStorage.setItem('conversation_history', JSON.stringify(currentHistory));
        console.log('Preserved conversation after logout:', currentConvId);
      } else {
        // No conversation to preserve - clear state
        setCurrentConversationId(null);
        setConversationHistory([]);
        localStorage.removeItem('current_conversation_id');
        localStorage.removeItem('conversation_history');
      }

      // Update usage stats for anonymous user
      updateUsageStats({ is_registered: false });

      console.log('Signed out, switched to anonymous user:', anonymousId);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };


  return (
    <div className="min-h-screen bg-[#E8EEE8]">
      <MobileSearchView
        onNewMessage={handleNewMessage}
        onRecommendations={handleRecommendations}
        llmProvider={llmProvider}
        conversationHistory={conversationHistory}
        userId={userId}
        onTrialExceeded={() => setShowRegistrationModal(true)}
        conversationId={currentConversationId}
        currentUser={currentUser}
        authLoading={authLoading}
        usageStats={usageStats}
        trialWarning={trialWarning}
        onLogin={() => setShowLoginModal(true)}
        onRegister={() => setShowRegistrationModal(true)}
        onLogout={handleLogout}
      />

      {/* Registration Modal */}
      <RegistrationModal
        isOpen={showRegistrationModal}
        onClose={() => setShowRegistrationModal(false)}
        onRegister={handleRegister}
        trialRemaining={usageStats?.trial_remaining || 0}
      />

      {/* Login Modal */}
      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onLogin={handleLogin}
      />
    </div>
  );
};

export default App;
