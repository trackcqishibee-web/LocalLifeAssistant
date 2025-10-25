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
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          {type === 'event' ? data.title : data.name}
        </h3>
        <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
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

      <p className="text-gray-700 mb-4 line-clamp-3">
        {data.description}
      </p>

      <div className="flex flex-wrap gap-2 mb-4">
        {data.categories?.map((category: string, index: number) => (
          <span
            key={index}
            className={`px-2 py-1 text-xs rounded-md font-medium ${
              category.toLowerCase().includes('free') 
                ? 'bg-orange-500 text-white' 
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            {category}
          </span>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* Price display removed */}
          
          
          {type === 'restaurant' && data.is_open_now !== undefined && (
            <div className="flex items-center space-x-1 text-sm text-gray-600">
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
              className="inline-flex items-center space-x-1 px-4 py-2 bg-orange-500 text-white text-sm rounded-md hover:bg-orange-600 transition-colors font-medium"
            >
              <span>View Details →</span>
            </a>
          )}
          
          {data.website && (
            <a
              href={data.website}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center space-x-1 px-3 py-1 text-gray-600 text-sm hover:text-gray-800 transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              <span>Website</span>
            </a>
          )}
        </div>
      </div>

      {explanation && (
        <div className="mt-4 text-sm text-gray-500 italic">
          {explanation}
        </div>
      )}
    </div>
  );
};

export default RecommendationCard;
