'use client';

export default function LocationInfo({ location, airQuality }) {
  if (!location) return null;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      <h3 className="text-lg font-bold text-gray-800 mb-3">Location Details</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div>
          <span className="text-gray-500">Coordinates:</span>
          <div className="font-semibold">
            {location.latitude?.toFixed(4)}, {location.longitude?.toFixed(4)}
          </div>
        </div>
        <div>
          <span className="text-gray-500">Nearest Station:</span>
          <div className="font-semibold">{location.nearest_station || 'N/A'}</div>
        </div>
        <div>
          <span className="text-gray-500">Distance to Station:</span>
          <div className="font-semibold">{location.distance_to_station_km?.toFixed(2)} km</div>
        </div>
      </div>
      {airQuality?.search_radius_used_km && (
        <div className="mt-3 text-xs text-gray-500">
          Search radius: {airQuality.search_radius_used_km} km
        </div>
      )}
    </div>
  );
}