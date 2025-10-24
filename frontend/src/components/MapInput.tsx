import React, { useState, useCallback, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents, Popup } from 'react-leaflet';
import { Icon } from 'leaflet';
import { LocationCoordinates } from '../api/client';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icon in react-leaflet
delete (Icon.Default.prototype as any)._getIconUrl;
Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface MapClickHandlerProps {
  onLocationSelect: (coordinates: LocationCoordinates) => void;
}

const MapClickHandler: React.FC<MapClickHandlerProps> = ({ onLocationSelect }) => {
  useMapEvents({
    click: (e) => {
      const { lat, lng } = e.latlng;
      onLocationSelect({
        latitude: lat,
        longitude: lng,
        formatted_address: `${lat.toFixed(4)}, ${lng.toFixed(4)}`
      });
    },
  });
  return null;
};

interface MapInputProps {
  onLocationSelect: (coordinates: LocationCoordinates) => void;
  selectedLocation?: LocationCoordinates | null;
  className?: string;
}

const MapInput: React.FC<MapInputProps> = ({
  onLocationSelect,
  selectedLocation,
  className = "h-64 w-full rounded-lg border border-amber-200"
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);

  // Get user's current location on mount
  useEffect(() => {
    if (navigator.geolocation && !selectedLocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation([latitude, longitude]);
        },
        (error) => {
          console.warn('Could not get user location:', error);
          // Fall back to default location
        },
        { enableHighAccuracy: true, timeout: 5000, maximumAge: 300000 }
      );
    }
  }, [selectedLocation]);

  // Use user location, selected location, or default US center
  const defaultCenter: [number, number] = selectedLocation
    ? [selectedLocation.latitude, selectedLocation.longitude]
    : userLocation || [39.8283, -98.5795]; // Geographic center of US

  const handleMapLoad = useCallback(() => {
    setIsLoaded(true);
  }, []);

  return (
    <div className={className}>
      <MapContainer
        center={defaultCenter}
        zoom={selectedLocation ? 13 : userLocation ? 12 : 4}
        style={{ height: '100%', width: '100%' }}
        whenReady={handleMapLoad}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapClickHandler onLocationSelect={onLocationSelect} />

        {selectedLocation && (
          <Marker
            position={[selectedLocation.latitude, selectedLocation.longitude]}
          >
            <Popup>
              <div className="text-sm">
                <div className="font-medium">Selected Location</div>
                <div>{selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)}</div>
                {selectedLocation.formatted_address && selectedLocation.formatted_address !== `${selectedLocation.latitude.toFixed(4)}, ${selectedLocation.longitude.toFixed(4)}` && (
                  <div className="mt-1 text-gray-600">{selectedLocation.formatted_address}</div>
                )}
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>

      {isLoaded && (
        <div className="absolute bottom-2 left-2 bg-white/90 backdrop-blur-sm rounded px-2 py-1 text-xs text-gray-600 shadow-sm">
          Click on the map to select your location
        </div>
      )}
    </div>
  );
};

export default MapInput;
