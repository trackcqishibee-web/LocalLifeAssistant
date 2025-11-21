import React from 'react';
import tapIcon from '../assets/images/figma/tap-icon.png';

interface CityButtonsProps {
  cities: string[];
  onSelect: (city: string) => void;
  disabled?: boolean;
}

// Format city name from snake_case to Title Case
const formatCityName = (city: string): string => {
  return city
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// City colors for visual variety
const cityColors = [
  '#3B82F6', // Blue
  '#10B981', // Green
  '#8B5CF6', // Purple
  '#F59E0B', // Amber
  '#6366F1', // Indigo
  '#EC4899', // Pink
  '#EF4444', // Red
];

const CityButtons: React.FC<CityButtonsProps> = ({ cities, onSelect, disabled = false }) => {
  return (
    <div className="overflow-x-auto -mx-4 px-4 mt-3 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
      <div className="flex gap-3 pb-2" style={{ minWidth: 'max-content' }}>
        {cities.map((city, index) => {
          const formattedName = formatCityName(city);
          const color = cityColors[index % cityColors.length];

          return (
            <button
              key={city}
              onClick={() => !disabled && onSelect(city)}
              disabled={disabled}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl border-2 transition-all hover:shadow-md active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
              style={{
                backgroundColor: 'white',
                borderColor: color,
                borderWidth: '2px'
              }}
            >
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                style={{ backgroundColor: `${color}20` }}
              >
                <img
                  src={tapIcon}
                  alt={formattedName}
                  className="w-5 h-5 object-contain"
                  style={{ filter: 'none' }}
                />
              </div>
              <span
                className="text-sm font-medium whitespace-nowrap"
                style={{ color: '#221A13' }}
              >
                {formattedName}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default CityButtons;

