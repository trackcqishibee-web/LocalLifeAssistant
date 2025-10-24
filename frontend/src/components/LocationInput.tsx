import React, { useState, useEffect } from 'react';
import { MapPin, Loader2, Check, X, Map, Keyboard } from 'lucide-react';
import { apiClient, LocationCoordinates } from '../api/client';
import MapInput from './MapInput';

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
  const [inputMode, setInputMode] = useState<'text' | 'map'>('text');
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

      // The API client returns coordinates directly when successful
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

  const handleMapLocationSelect = async (coordinates: LocationCoordinates) => {
    setIsLoading(true);
    setError(null);

    try {
      // Try to reverse geocode to get a formatted address
      const response = await apiClient.geocodeLocation(`${coordinates.latitude},${coordinates.longitude}`);
      const locationWithAddress = {
        ...coordinates,
        formatted_address: response.formatted_address
      };

      setCurrentLocation(locationWithAddress);
      onLocationChange(locationWithAddress);
      localStorage.setItem('userLocation', JSON.stringify(locationWithAddress));
      setSuccess(true);
      setTimeout(() => setSuccess(false), 2000);
    } catch (err: any) {
      // If reverse geocoding fails, use coordinates as address
      const locationWithCoords = {
        ...coordinates,
        formatted_address: `${coordinates.latitude.toFixed(4)}, ${coordinates.longitude.toFixed(4)}`
      };

      setCurrentLocation(locationWithCoords);
      onLocationChange(locationWithCoords);
      localStorage.setItem('userLocation', JSON.stringify(locationWithCoords));
      setSuccess(true);
      setTimeout(() => setSuccess(false), 2000);
    } finally {
      setIsLoading(false);
    }
  };

  // Format address for better display
  const formatAddress = (address: string) => {
    // Split by comma and clean up
    const parts = address.split(',').map(part => part.trim());

    // Remove "United States" if present
    const filteredParts = parts.filter(part =>
      !part.toLowerCase().includes('united states') &&
      !part.toLowerCase().includes('new york county') &&
      !part.toLowerCase().includes('city of new york')
    );

    if (filteredParts.length >= 3) {
      // Format as: "ZIP, Neighborhood", "City, State"
      const zipNeighborhood = filteredParts[0] + ', ' + filteredParts[1];
      const cityState = filteredParts[2] + (filteredParts[3] ? ', ' + filteredParts[3].substring(0, 2) : '');
      return [zipNeighborhood, cityState];
    } else if (filteredParts.length >= 2) {
      return [filteredParts[0] + ', ' + filteredParts[1]];
    }

    return [address];
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <MapPin className="w-4 h-4 text-amber-600" />
          <h3 className="text-base font-semibold text-gray-900">Location</h3>
        </div>

        {/* Input Mode Toggle - Compact */}
        <div className="flex bg-gray-100 rounded-md p-0.5">
          <button
            onClick={() => setInputMode('text')}
            className={`p-1.5 rounded text-sm transition-colors ${
              inputMode === 'text'
                ? 'bg-amber-600 text-white'
                : 'text-gray-600 hover:bg-gray-200'
            }`}
            title="Text input"
          >
            <Keyboard className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setInputMode('map')}
            className={`p-1.5 rounded text-sm transition-colors ${
              inputMode === 'map'
                ? 'bg-amber-600 text-white'
                : 'text-gray-600 hover:bg-gray-200'
            }`}
            title="Map input"
          >
            <Map className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {currentLocation ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-amber-50/50 border border-amber-200 rounded-lg backdrop-blur-sm">
            <div className="flex items-center space-x-2">
              <Check className="w-4 h-4 text-amber-600" />
              <div className="flex-1">
                {formatAddress(currentLocation.formatted_address).map((line, index) => (
                  <div key={index} className="text-sm font-medium text-amber-800">
                    {line}
                  </div>
                ))}
              </div>
            </div>
            <button
              onClick={handleClearLocation}
              className="p-1 text-amber-600 hover:text-amber-800 hover:bg-amber-100/50 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {inputMode === 'text' ? (
            <div className="flex space-x-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Enter US zipcode (e.g., 10001)"
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                style={{ width: '156px' }}
                disabled={isLoading}
              />
              <button
                onClick={handleGeocode}
                disabled={!inputValue.trim() || isLoading}
                className="px-3 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1 whitespace-nowrap"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <MapPin className="w-4 h-4" />
                )}
                <span className="text-sm">{isLoading ? 'Finding...' : 'Set'}</span>
              </button>
            </div>
          ) : (
            <MapInput
              onLocationSelect={handleMapLocationSelect}
              selectedLocation={currentLocation}
              className="h-64 w-full rounded-lg border border-amber-200"
            />
          )}

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
