import React from 'react';
import musicIcon from '../assets/images/figma/music-icon.png';
import tapIcon from '../assets/images/figma/tap-icon.png';

interface EventTypeButtonsProps {
  onSelect: (eventType: string) => void;
  disabled?: boolean;
}

// Map event types to display names, icons and retro-inspired accent colors
const eventTypeConfig: Record<string, { label: string; icon: string; color: string }> = {
  music: {
    label: 'Music',
    icon: musicIcon,
    color: '#E9B8A6' // Soft peach
  },
  sports: {
    label: 'Sports',
    icon: tapIcon,
    color: '#C9A0A0' // Warm taupe
  },
  nightlife: {
    label: 'Nightlife',
    icon: tapIcon,
    color: '#D3A48F' // Muted terracotta
  },
  business: {
    label: 'Business',
    icon: tapIcon,
    color: '#B9C6B0' // Sage
  },
  tech: {
    label: 'Tech',
    icon: tapIcon,
    color: '#AEC4C9' // Dusty teal
  },
  dating: {
    label: 'Dating',
    icon: tapIcon,
    color: '#C7C1D7' // Lavender gray
  }
};

const EventTypeButtons: React.FC<EventTypeButtonsProps> = ({ onSelect, disabled = false }) => {
  const eventTypes = ['music', 'sports', 'nightlife', 'business', 'tech', 'dating'];

  return (
    <div className="overflow-x-auto -mx-4 px-4 mt-3 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
      <div className="flex gap-3 pb-2" style={{ minWidth: 'max-content' }}>
        {eventTypes.map((eventType) => {
          const config = eventTypeConfig[eventType];
          if (!config) return null;

          return (
            <button
              key={eventType}
              onClick={() => !disabled && onSelect(eventType)}
              disabled={disabled}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl border-2 transition-all hover:shadow-md active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
              style={{
                backgroundColor: 'white',
                borderColor: config.color,
                borderWidth: '2px'
              }}
            >
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                style={{ backgroundColor: `${config.color}20` }}
              >
                <img
                  src={config.icon}
                  alt={config.label}
                  className="w-5 h-5 object-contain"
                  style={{ filter: 'none' }}
                />
              </div>
              <span
                className="text-sm font-medium whitespace-nowrap"
                style={{ color: '#221A13' }}
              >
                {config.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default EventTypeButtons;

