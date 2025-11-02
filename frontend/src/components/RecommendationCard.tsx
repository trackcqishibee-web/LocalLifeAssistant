import React from 'react';
import { MapPin, Clock, Star, Heart } from 'lucide-react';
import { EventData } from '../api/client';
import { ImageWithFallback } from './ImageWithFallback';

interface RecommendationCardProps {
  recommendation: {
    type: 'event' | 'restaurant';
    data: EventData | any;
    relevance_score: number;
    explanation: string;
  };
}

const RecommendationCard: React.FC<RecommendationCardProps> = ({ recommendation }) => {
  const { type, data } = recommendation;

  if (type !== 'event') {
    return null;
  }

  const eventData = data as EventData;
  
  const formatDate = (dateString: string) => {
    try {
      if (!dateString || dateString === 'TBD') return 'Date TBD';
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return dateString;
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString || 'Date TBD';
    }
  };

  const price = eventData.is_free ? 'Free' : (eventData.ticket_min_price || 'TBD');
  const [liked, setLiked] = React.useState(false);

  return (
    <div
      className="flex-shrink-0 w-[240px] bg-white rounded-xl shadow-md border transition-all cursor-pointer hover:shadow-lg active:shadow-lg active:scale-[0.98] p-3 flex flex-col"
      style={{ borderColor: '#F5F5F5' }}
    >
      {/* Event Image */}
      <div className="relative w-full h-[120px] overflow-hidden rounded mb-3">
        <ImageWithFallback
          src={eventData.image_url || ''}
          alt={eventData.title}
          className="w-full h-full object-cover"
        />
        {/* Star Rating Badge - Top Left */}
        {eventData.rating && (
          <div className="absolute top-2 left-2 bg-white/70 backdrop-blur-sm rounded-md px-1.5 py-0.5 flex items-center gap-0.5">
            <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
            <span className="text-xs" style={{ color: '#221A13' }}>{eventData.rating}</span>
          </div>
        )}
        {/* Heart Icon - Top Right */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            setLiked(!liked);
          }}
          className="absolute top-2 right-2 transition-opacity hover:opacity-80 z-10"
        >
          <Heart
            className={`w-6 h-6 transition-colors drop-shadow-md ${
              liked
                ? 'fill-red-500 text-red-500'
                : 'fill-white/60 text-white/60'
            }`}
          />
        </button>
      </div>

      {/* Card Content */}
      <div className="flex flex-col flex-1 space-y-2.5">
        <h3 className="line-clamp-2 text-[15px]" style={{ color: '#221A13', fontFamily: 'Abitare Sans, sans-serif' }}>
          {eventData.title}
        </h3>

        {/* Date/Time and Location */}
        <div className="flex flex-col gap-1.5 text-xs" style={{ color: '#5E574E' }}>
          <div className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" style={{ color: '#B46A55' }} />
            <span>{formatDate(eventData.start_datetime)}</span>
          </div>
          <div className="flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5 flex-shrink-0" style={{ color: '#B46A55' }} />
            <span className="truncate">{eventData.venue_name}</span>
          </div>
        </div>

        <p className="text-sm line-clamp-2" style={{ color: '#5E574E', lineHeight: '1.4' }}>
          {eventData.description}
        </p>

        {/* Divider */}
        <div className="border-t pt-2 mt-auto" style={{ borderColor: '#F5F5F5' }} />

        {/* Price and Visit Button */}
        <div className="flex items-center gap-2">
          <span className="text-sm" style={{ color: '#221A13' }}>{price}</span>
          {eventData.event_url && (
            <a
              href={eventData.event_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="ml-auto px-5 py-2 text-white rounded-lg text-xs transition-all active:scale-95 hover:opacity-90 shadow-sm"
              style={{ backgroundColor: '#B46A55' }}
            >
              Visit
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default RecommendationCard;
