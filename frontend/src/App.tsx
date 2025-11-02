import React, { useState, useEffect } from 'react';
import { Menu, Home, LogIn, UserPlus } from 'lucide-react';
import ChatInterface from './components/ChatInterface';
import RegistrationModal from './components/RegistrationModal';
import LoginModal from './components/LoginModal';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from './components/ui/sheet';
import { ChatMessage, apiClient } from './api/client';
import { getOrCreateUserId, setUserId } from './utils/userIdManager';
import { updateUsageStats, shouldShowRegistrationPrompt, markRegistrationPrompted, getTrialWarningMessage } from './utils/usageTracker';
import { auth } from './firebase/config';
import { onAuthStateChanged, User } from 'firebase/auth';

const App: React.FC = () => {
  const [conversationHistory, setConversationHistory] = useState<ChatMessage[]>([]);
  const [llmProvider] = useState('openai');
  const [menuOpen, setMenuOpen] = useState(false);
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
    setConversationHistory(prev => [...prev, message]);
  };

  const handleRecommendations = (recommendations: any[]) => {
    // Handle recommendations if needed
    console.log('Received recommendations:', recommendations);
  };

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

  const handleRegister = async (anonymousUserId: string, _email: string, _password: string, _name: string, idToken: string) => {
    try {
      // The Firebase user is already created, now register with our backend using token
      const response = await apiClient.registerWithToken(anonymousUserId, idToken);

      if (response.success) {
        // Update user ID to registered user
        const registeredUserId = response.user_id;
        setUserIdState(registeredUserId);
        setUserId(registeredUserId);

        // Update usage stats
        updateUsageStats({ is_registered: true });

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
      // Firebase authentication is already handled, just verify with backend
      const response = await apiClient.verifyToken(token);

      if (response.success) {
        // Update user ID to authenticated user
        const authenticatedUserId = response.user_id || _user.uid;
        setUserIdState(authenticatedUserId);
        setUserId(authenticatedUserId);

        // Update usage stats for registered user
        updateUsageStats({ is_registered: true });

        // Try to load user's conversations (may be empty for new users)
        try {
          const conversations = await apiClient.listUserConversations(authenticatedUserId);

          // Load most recent conversation if exists
          if (conversations && conversations.length > 0) {
            const mostRecent = conversations[0];
            const conversation = await apiClient.getConversation(authenticatedUserId, mostRecent.conversation_id);
            setCurrentConversationId(mostRecent.conversation_id);
            setConversationHistory(conversation.messages || []);
            localStorage.setItem('current_conversation_id', mostRecent.conversation_id);
          } else {
            // New user - start with empty conversation
            setConversationHistory([]);
            setCurrentConversationId(null);
            localStorage.removeItem('current_conversation_id');
          }
        } catch (conversationError: any) {
          // If listing conversations fails (404 for new users or missing endpoint), just start fresh
          console.warn('Could not load conversations, starting fresh:', conversationError);
          setConversationHistory([]);
          setCurrentConversationId(null);
          localStorage.removeItem('current_conversation_id');
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
      await auth.signOut();
      // Clear conversation and reset to anonymous user
      setConversationHistory([]);
      setCurrentConversationId(null);
      localStorage.removeItem('current_conversation_id');

      // Reset to anonymous user ID
      const anonymousId = getOrCreateUserId();
      setUserIdState(anonymousId);
      setUserId(anonymousId);

      // Update usage stats for anonymous user
      updateUsageStats({ is_registered: false });

      console.log('Signed out, switched to anonymous user:', anonymousId);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };


  return (
    <div className="h-dvh bg-[#FCFBF9] flex flex-col max-w-md mx-auto">
      {/* Sticky Header Container */}
      <div className="sticky top-0 z-50 bg-[#FCFBF9] flex-shrink-0">
        {/* Status Bar */}
        <div className="h-11 bg-[#FCFBF9] flex items-center justify-between px-4 text-xs text-slate-700">
          <span>9:41</span>
          <div className="flex items-center gap-1">
            <div className="w-4 h-3 border border-slate-700 rounded-sm" />
            <div className="w-3 h-3 border border-slate-700 rounded-sm" />
          </div>
        </div>

        {/* Header */}
        <div className="bg-[#FCFBF9] px-4 py-2.5 border-b border-slate-200/50 flex items-center gap-2">
          <button
            onClick={() => setMenuOpen(true)}
            type="button"
            className="p-1.5 hover:bg-slate-200/50 rounded-lg transition-colors"
          >
            <Menu className="w-5 h-5" style={{ color: 'rgb(118, 193, 178)' }} />
          </button>
          <h1
            className="text-lg"
            style={{
              background: 'linear-gradient(135deg, #76C1B2 0%, #B46A55 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              fontFamily: 'Aladin, cursive'
            }}
          >
            LocoMoco. Catch the Vibe. Locally
          </h1>
        </div>
      </div>

      {/* Side Menu */}
      <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
        <SheetContent side="left" className="w-[85%] bg-[#FCFBF9] p-0" aria-describedby={undefined}>
          <SheetHeader className="sr-only">
            <SheetTitle>Menu</SheetTitle>
          </SheetHeader>
          <div className="flex flex-col h-full">
            {/* Menu Header */}
            <div className="px-4 py-6 border-b border-slate-200/50">
              <h2 className="text-lg font-semibold" style={{ color: '#221A13' }}>
                Menu
              </h2>
            </div>

            {/* Menu Items */}
            <div className="flex-1 px-4 py-6 space-y-4">
              <button
                onClick={() => {
                  setMenuOpen(false);
                  window.location.href = '/';
                }}
                className="w-full flex items-center gap-3 p-4 bg-white/80 backdrop-blur-sm rounded-xl hover:bg-white transition-colors"
              >
                <Home className="w-5 h-5" style={{ color: '#76C1B2' }} />
                <span style={{ color: '#221A13' }}>Home</span>
              </button>

              {authLoading ? (
                <div className="text-sm" style={{ color: '#5E574E' }}>Loading...</div>
              ) : currentUser ? (
                <div className="space-y-2">
                  <div className="px-4 py-2 text-sm" style={{ color: '#5E574E' }}>
                    Welcome, {currentUser.displayName || currentUser.email?.split('@')[0] || 'User'}
                  </div>
                  <button
                    onClick={async () => {
                      setMenuOpen(false);
                      await handleLogout();
                    }}
                    className="w-full flex items-center gap-3 p-4 bg-white/80 backdrop-blur-sm rounded-xl hover:bg-white transition-colors"
                  >
                    <LogIn className="w-5 h-5" style={{ color: '#B46A55' }} />
                    <span style={{ color: '#221A13' }}>Sign Out</span>
                  </button>
                </div>
              ) : (
                <>
                  <button
                    onClick={() => {
                      setMenuOpen(false);
                      setShowLoginModal(true);
                    }}
                    className="w-full flex items-center gap-3 p-4 bg-white/80 backdrop-blur-sm rounded-xl hover:bg-white transition-colors"
                  >
                    <LogIn className="w-5 h-5" style={{ color: '#76C1B2' }} />
                    <span style={{ color: '#221A13' }}>Sign In</span>
                  </button>
                  <button
                    onClick={() => {
                      setMenuOpen(false);
                      setShowRegistrationModal(true);
                    }}
                    className="w-full flex items-center gap-3 p-4 bg-white/80 backdrop-blur-sm rounded-xl hover:bg-white transition-colors"
                  >
                    <UserPlus className="w-5 h-5" style={{ color: '#B46A55' }} />
                    <span style={{ color: '#221A13' }}>Register</span>
                  </button>
                  {usageStats && !usageStats.is_registered && (
                    <div className="px-4 py-2 text-xs" style={{ color: '#5E574E' }}>
                      Trial: {usageStats.trial_remaining} interactions left
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </SheetContent>
      </Sheet>

      {/* Chat Interface - Full Height */}
      <div className="flex-1 min-h-0">
        <ChatInterface
          onNewMessage={handleNewMessage}
          onRecommendations={handleRecommendations}
          llmProvider={llmProvider}
          conversationHistory={conversationHistory}
          userId={userId}
          onTrialExceeded={() => setShowRegistrationModal(true)}
          conversationId={currentConversationId}
        />
      </div>

      {/* Trial Warning Banner */}
      {trialWarning && (
        <div className="fixed top-0 left-0 right-0 bg-amber-50 border-l-4 border-amber-500 p-4 z-40 max-w-md mx-auto">
          <p className="text-amber-700">{trialWarning}</p>
        </div>
      )}

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
