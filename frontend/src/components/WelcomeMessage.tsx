import React from 'react';
import { MessageCircle, Sparkles } from 'lucide-react';

interface WelcomeMessageProps {
  onDismiss?: () => void;
}

const WelcomeMessage: React.FC<WelcomeMessageProps> = ({ onDismiss }) => {
  return (
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
          <div className="whitespace-pre-wrap mb-3">
            <div className="flex items-center space-x-2 mb-3">
              <Sparkles className="w-5 h-5 text-primary-500" />
              <span className="font-semibold text-gray-900">Welcome to Local Life Assistant!</span>
            </div>
            
            <div className="text-gray-700 leading-relaxed">
              👋 I'm your AI-powered local event and recommendation assistant! 
              To help you find the perfect experiences, please tell me:
            </div>
            
            <div className="mt-4 space-y-2 text-sm">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-primary-500 rounded-full"></span>
                <span><strong>Where are you located?</strong> (e.g., "New York", "San Francisco", "Chicago")</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-primary-500 rounded-full"></span>
                <span><strong>What date/time works for you?</strong> (e.g., "this weekend", "tomorrow evening", "next Friday")</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-primary-500 rounded-full"></span>
                <span><strong>What type of events interest you?</strong> (e.g., "music", "food", "art", "sports", "networking")</span>
              </div>
            </div>
            
            <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="text-sm text-blue-800">
                <strong>💡 Example:</strong> "I'm in Brooklyn, looking for jazz concerts this weekend"
              </div>
            </div>
            
            <div className="mt-3 text-xs text-gray-500">
              Just type your response below and I'll help you discover amazing local experiences! 🎉
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeMessage;
