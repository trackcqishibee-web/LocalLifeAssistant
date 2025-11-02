import React from 'react';

interface WelcomeMessageProps {
  onExampleClick?: (text: string) => void;
}

const WelcomeMessage: React.FC<WelcomeMessageProps> = ({ onExampleClick }) => {
  const handleExampleClick = (text: string) => {
    if (onExampleClick) {
      onExampleClick(text);
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 pb-32 bg-[#FCFBF9]">
      <h2 className="text-slate-900 mb-2 text-center" style={{ color: '#221A13' }}>
        Discover Local Events
      </h2>
      <p className="text-center text-sm mb-8" style={{ color: '#5E574E' }}>
        Ask me anything about events, activities, and experiences near you
      </p>
      <div className="w-full space-y-3">
        <button
          onClick={() => handleExampleClick('Art galleries open this weekend')}
          className="w-full p-4 bg-white/80 backdrop-blur-sm rounded-xl text-left text-sm hover:bg-white transition-colors shadow-sm"
          style={{ color: '#221A13' }}
        >
          🎨 Art galleries open this weekend
        </button>
        <button
          onClick={() => handleExampleClick('Wellness activities in Palo Alto')}
          className="w-full p-4 bg-white/80 backdrop-blur-sm rounded-xl text-left text-sm hover:bg-white transition-colors shadow-sm"
          style={{ color: '#221A13' }}
        >
          🧘 Wellness activities in Palo Alto
        </button>
      </div>
    </div>
  );
};

export default WelcomeMessage;
