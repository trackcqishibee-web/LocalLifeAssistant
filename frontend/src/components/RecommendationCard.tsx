import React from 'react';
import { MapPin, Clock, Star } from 'lucide-react';
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
  const isExample = eventData.is_example === true;
  
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

  const formatPrice = (priceValue: string | number | undefined): string => {
    if (!priceValue || priceValue === 'TBD' || priceValue === '') return 'TBD';
    const priceStr = String(priceValue).trim();
    if (priceStr.startsWith('$')) return priceStr;
    if (priceStr === 'Free') return 'Free';
    const numericValue = parseFloat(priceStr);
    if (isNaN(numericValue)) return priceStr;
    return `$${numericValue}`;
  };

  const price = eventData.is_free ? 'Free' : formatPrice(eventData.ticket_min_price);
  
  const handleCardClick = () => {
    if (isExample) return;
    if (eventData.event_url) {
      window.open(eventData.event_url, '_blank', 'noopener,noreferrer');
    }
  };
  
  return (
    <div
      data-card
      onClick={handleCardClick}
      className={`flex-shrink-0 w-[240px] h-[360px] bg-white rounded-xl shadow-md border-[0.5px] transition-all cursor-pointer hover:shadow-lg active:shadow-lg active:scale-[0.98] p-3 flex flex-col ${
        isExample ? 'cursor-default' : ''
      }`}
      style={{ borderColor: '#F5F5F5' }}
    >
      {/* Event Image */}
      <div className="relative w-full h-[120px] overflow-hidden rounded mb-3">
        <ImageWithFallback
          src={eventData.image_url || ''}
          alt={eventData.title}
          className="w-full h-full object-cover"
        />
        {/* Price Badge - Bottom Left */}
        <div className="absolute bottom-2 left-2 bg-white/70 backdrop-blur-sm rounded-full px-2 py-1 flex items-center justify-center">
          <span className="text-xs font-medium" style={{ color: '#221A13' }}>{price}</span>
        </div>
        {/* Star Rating Badge - Top Left */}
        {eventData.rating && !isExample && (
          <div className="absolute top-2 left-2 bg-white/70 backdrop-blur-sm rounded-md px-1.5 py-0.5 flex items-center gap-0.5">
            <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
            <span className="text-xs" style={{ color: '#221A13' }}>{eventData.rating}</span>
          </div>
        )}
      </div>
      
      {/* Card Content */}
      <div className="flex flex-col flex-1 min-h-0 space-y-1.5">
        <h3 className="line-clamp-2 min-h-[2.5rem] flex items-start" style={{ color: '#221A13', fontFamily: 'Abitare Sans, sans-serif' }}>{eventData.title}</h3>
        
        {/* Date/Time and Location */}
        <div className="flex flex-col gap-1.5 text-xs flex-shrink-0" style={{ color: '#5E574E' }}>
          <div className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 flex-shrink-0" style={{ color: '#B46A55' }} />
            <span className="truncate">{formatDate(eventData.start_datetime)}</span>
          </div>
          <div className="flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5 flex-shrink-0" style={{ color: '#B46A55' }} />
            <span className="truncate">{eventData.venue_name}</span>
          </div>
        </div>
        
        <p className="text-sm line-clamp-2 min-h-[2.5rem] flex-1" style={{ color: '#5E574E', lineHeight: '1.4' }}>
          {eventData.description}
        </p>
      </div>
    </div>
  );
};

export default RecommendationCard;
