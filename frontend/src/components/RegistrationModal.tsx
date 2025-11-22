import React, { useState } from 'react';
import { X } from 'lucide-react';
import { signInWithPopup } from 'firebase/auth';
import { auth, googleProvider } from '../firebase/config';

interface RegistrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRegister: (userId: string, email: string, password: string, name: string, customToken: string) => Promise<void>;
  trialRemaining: number;
}

const RegistrationModal: React.FC<RegistrationModalProps> = ({
  isOpen,
  onClose,
  onRegister,
  trialRemaining
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleGoogleSignUp = async () => {
    setError('');
    setIsLoading(true);

    try {
      // Sign in/up with Google (Firebase handles both registration and login)
      const result = await signInWithPopup(auth, googleProvider);
      const user = result.user;

      // Get ID token
      const idToken = await user.getIdToken();

      // Generate a user ID for our backend
      const userId = `registered_${Date.now()}`;

      // Call the backend registration with the Firebase user info
      // The backend will handle creating the account if it doesn't exist
      await onRegister(userId, user.email || '', '', user.displayName || '', idToken);
      onClose();
    } catch (err: any) {
      let errorMessage = 'Registration failed. Please try again.';
      if (err.code === 'auth/popup-closed-by-user') {
        errorMessage = 'Registration was cancelled.';
      } else if (err.code === 'auth/popup-blocked') {
        errorMessage = 'Pop-up was blocked by your browser. Please allow pop-ups for this site.';
      }
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Sign in / Register</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>

        {trialRemaining === 0 ? (
          <p className="text-red-600 mb-6">
            🔒 You've used all your free interactions. Register to continue!
          </p>
        ) : trialRemaining < 10 ? (
          <p className="text-amber-600 mb-6">
            ⚠️ Only {trialRemaining} free interactions remaining. Register to keep your conversation history!
          </p>
        ) : (
          <p className="text-blue-600 mb-6">
            🎉 Register now to save your conversations and get unlimited access!
          </p>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <button
          onClick={handleGoogleSignUp}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-3 bg-white border border-gray-300 text-gray-700 py-3 px-4 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          {isLoading ? 'Registering...' : 'Continue with Google'}
        </button>

        <div className="mt-4 text-center text-sm text-gray-600">
          By registering, you'll get access to conversation history and unlimited usage.
        </div>
      </div>
    </div>
  );
};

export default RegistrationModal;
