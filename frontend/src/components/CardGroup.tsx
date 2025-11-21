import React from 'react';
import { useEqualCardHeights } from '../hooks/useEqualCardHeights';
import RecommendationCard from './RecommendationCard';

interface CardGroupProps {
  recommendations: any[];
}

const CardGroup: React.FC<CardGroupProps> = ({ recommendations }) => {
  const containerRef = useEqualCardHeights(recommendations.length);

  return (
    <div ref={containerRef} className="flex gap-3 overflow-x-auto overflow-y-hidden scrollbar-hide horizontal-scroll-mobile pb-2">
      {recommendations.map((rec, recIndex) => (
        <div key={recIndex} className="flex-none flex-shrink-0">
          <RecommendationCard recommendation={rec} />
        </div>
      ))}
    </div>
  );
};

export default CardGroup;

