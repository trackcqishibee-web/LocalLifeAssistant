import React, { useState, useEffect } from 'react';
import { MapPin, Loader2, Check, X } from 'lucide-react';
import { apiClient, LocationCoordinates, GeocodeResponse } from '../api/client';

interface LocationInputProps {
  onLocationChange: (coordinates: LocationCoordinates | null) => void;
  initialLocation?: LocationCoordinates | null;
}

const LocationInput: React.FC<LocationInputProps> = ({
  onLocationChange,
  initialLocation
}) => {
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentLocation, setCurrentLocation] = useState<LocationCoordinates | null>(initialLocation || null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Load saved location from localStorage on mount
  useEffect(() => {
    const savedLocation = localStorage.getItem('userLocation');
    if (savedLocation) {
      try {
        const location = JSON.parse(savedLocation);
        setCurrentLocation(location);
        onLocationChange(location);
      } catch (e) {
        console.error('Failed to parse saved location:', e);
      }
    }
  }, [onLocationChange]);

  const handleGeocode = async () => {
    if (!inputValue.trim()) {
      setError('Please enter a location');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const response: LocationCoordinates = await apiClient.geocodeLocation(inputValue.trim());

      // The API client now returns coordinates directly
      setCurrentLocation(response);
      onLocationChange(response);
      
      // Save to localStorage
      localStorage.setItem('userLocation', JSON.stringify(response));
      
      setSuccess(true);
      setInputValue('');
      
      // Clear success message after 2 seconds
      setTimeout(() => setSuccess(false), 2000);
    } catch (err) {
      console.error('Geocoding error:', err);
      setError('Failed to geocode location. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearLocation = () => {
    setCurrentLocation(null);
    onLocationChange(null);
    localStorage.removeItem('userLocation');
    setError(null);
    setSuccess(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading) {
      handleGeocode();
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center space-x-2 mb-3">
        <MapPin className="w-5 h-5 text-primary-500" />
        <h3 className="text-lg font-semibold text-gray-900">Location</h3>
      </div>

      {currentLocation ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <Check className="w-4 h-4 text-green-600" />
              <div>
                <div className="text-sm font-medium text-green-800">
                  {currentLocation.formatted_address}
                </div>
                <div className="text-xs text-green-600">
                  {currentLocation.latitude.toFixed(4)}, {currentLocation.longitude.toFixed(4)}
                </div>
              </div>
            </div>
            <button
              onClick={handleClearLocation}
              className="p-1 text-green-600 hover:text-green-800 hover:bg-green-100 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex space-x-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter US zipcode (e.g., 10001)"
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              style={{ width: '156px' }}
              disabled={isLoading}
            />
            <button
              onClick={handleGeocode}
              disabled={!inputValue.trim() || isLoading}
              className="px-3 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1 whitespace-nowrap"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <MapPin className="w-4 h-4" />
              )}
              <span className="text-sm">{isLoading ? 'Finding...' : 'Set'}</span>
            </button>
          </div>

          {error && (
            <div className="flex items-center space-x-2 p-2 bg-red-50 border border-red-200 rounded-lg">
              <X className="w-4 h-4 text-red-600" />
              <span className="text-sm text-red-600">{error}</span>
            </div>
          )}

          {success && (
            <div className="flex items-center space-x-2 p-2 bg-green-50 border border-green-200 rounded-lg">
              <Check className="w-4 h-4 text-green-600" />
              <span className="text-sm text-green-600">Location set successfully!</span>
            </div>
          )}

          <div className="text-xs text-gray-500">
            Enter your US zipcode (e.g., 10001) to get location-based recommendations.
          </div>
        </div>
      )}
    </div>
  );
};

export default LocationInput;
