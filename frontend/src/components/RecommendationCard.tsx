import React from 'react';
import { MapPin, Calendar, Star, ExternalLink, Clock } from 'lucide-react';

interface RecommendationCardProps {
  recommendation: {
    type: 'event' | 'restaurant';
    data: any;
    relevance_score: number;
    explanation: string;
  };
}

const RecommendationCard: React.FC<RecommendationCardProps> = ({ recommendation }) => {
  const { type, data, explanation } = recommendation;

  const formatDate = (dateString: string) => {
    try {
      if (!dateString || dateString === 'TBD') return 'Date TBD';
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return dateString;
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString || 'Date TBD';
    }
  };

  const getRatingDisplay = () => {
    if (type === 'restaurant' && data.rating) {
      return (
        <div className="flex items-center space-x-1">
          <Star className="w-4 h-4 text-yellow-400 fill-current" />
          <span className="text-sm font-medium">{data.rating}/5</span>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="recommendation-card">
      <div className="flex items-start justify-between mb-0.5">
        <h3 className="text-lg font-bold flex-1 pr-4">
          {type === 'event' ? data.title : data.name}
        </h3>
        {data.event_url && (
          <a
            href={data.event_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-1 px-3 py-1 bg-orange-500 text-white text-sm rounded-md hover:bg-orange-600 transition-colors font-medium flex-shrink-0"
          >
            <span>View Details →</span>
          </a>
        )}
      </div>
      <div className="flex items-center space-x-4 text-sm mb-0.5">
        <div className="flex items-center space-x-1">
          <MapPin className="w-4 h-4" />
          <span>{data.venue_name || data.name}, {data.venue_city}</span>
        </div>
        {type === 'event' && (
          <div className="flex items-center space-x-1">
            <Calendar className="w-4 h-4" />
            <span>{formatDate(data.start_datetime)}</span>
          </div>
        )}
      </div>

      <p className="mb-1 line-clamp-3">
        {data.description}
      </p>

      <div className="flex flex-wrap gap-1 mb-1">
        {data.categories?.map((category: string, index: number) => (
          <span
            key={index}
            className={`px-1 py-0.5 text-xs rounded font-medium ${
              category.toLowerCase().includes('free') 
                ? 'bg-orange-500 text-white' 
                : 'bg-amber-200 text-amber-800'
            }`}
          >
            {category}
          </span>
        ))}
      </div>

      {type === 'restaurant' && data.is_open_now !== undefined && (
        <div className="flex items-center space-x-1 text-sm">
          <Clock className="w-4 h-4" />
          <span className={data.is_open_now ? 'text-green-600' : 'text-red-600'}>
            {data.is_open_now ? 'Open now' : 'Closed'}
          </span>
        </div>
      )}
      
      {getRatingDisplay()}
      
      {data.website && (
        <div className="mt-2">
          <a
            href={data.website}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-1 text-sm hover:opacity-80 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            <span>Website</span>
          </a>
        </div>
      )}

      {explanation && (
        <div className="mt-2 text-xs italic opacity-75">
          {explanation}
        </div>
      )}
    </div>
  );
};

export default RecommendationCard;
