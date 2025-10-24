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
      <div className="mb-4">
        <h3 className="text-xl font-semibold text-amber-900/90 mb-2">
          {type === 'event' ? data.title : data.name}
        </h3>
        <div className="flex items-center space-x-4 text-sm text-amber-700/80 mb-2">
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
      </div>

      <p className="text-amber-800/90 mb-4 line-clamp-3">
        {data.description}
      </p>

      <div className="flex flex-wrap gap-2 mb-4">
        {data.categories?.map((category: string, index: number) => (
          <span
            key={index}
            className="px-2 py-1 bg-amber-100 text-amber-800 text-xs rounded-full"
          >
            {category}
          </span>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* Price display removed */}
          
          
          {type === 'restaurant' && data.is_open_now !== undefined && (
            <div className="flex items-center space-x-1 text-sm text-amber-700/80">
              <Clock className="w-4 h-4" />
              <span className={data.is_open_now ? 'text-green-600' : 'text-red-600'}>
                {data.is_open_now ? 'Open now' : 'Closed'}
              </span>
            </div>
          )}
          
          {getRatingDisplay()}
        </div>

        <div className="flex space-x-2">
          {data.event_url && (
            <a
              href={data.event_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center space-x-1 px-3 py-1 bg-amber-600 text-white text-sm rounded hover:bg-amber-700 transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              <span>View on Eventbrite</span>
            </a>
          )}
          
          {data.website && (
            <a
              href={data.website}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center space-x-1 px-3 py-1 bg-gray-500 text-white text-sm rounded hover:bg-gray-600 transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              <span>Website</span>
            </a>
          )}
        </div>
      </div>

      {explanation && (
        <div className="mt-4 p-3 bg-amber-50/50 rounded-lg border border-amber-200/30">
          <div className="text-sm text-amber-800">
            <strong>Why this recommendation:</strong> {explanation}
          </div>
        </div>
      )}
    </div>
  );
};

export default RecommendationCard;
