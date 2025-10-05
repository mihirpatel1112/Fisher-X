'use client';

import { useState } from 'react';
import { geocodeAddress, reverseGeocode, getAddressComponent } from '@/lib/geocoding';

export default function GeocodingSearch() {
  const [address, setAddress] = useState('');
  const [coordinates, setCoordinates] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Handle address to coordinates
  const handleGeocodeAddress = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await geocodeAddress(address);
      setResult({
        type: 'geocode',
        data: data
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle coordinates to address
  const handleReverseGeocode = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Parse coordinates (format: "lat, lng")
      const [lat, lng] = coordinates.split(',').map(coord => parseFloat(coord.trim()));
      
      if (isNaN(lat) || isNaN(lng)) {
        throw new Error('Invalid coordinates format. Use: latitude, longitude');
      }

      const data = await reverseGeocode(lat, lng);
      setResult({
        type: 'reverse',
        data: data
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <h1 className="text-black-3xl font-bold">Geocoding API Demo</h1>

      {/* Address to Coordinates */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-black-xl font-semibold mb-4">Address to Coordinates</h2>
        <form onSubmit={handleGeocodeAddress} className="space-y-4">
          <div>
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter an address (e.g., 1600 Amphitheatre Parkway, Mountain View, CA)"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Searching...' : 'Geocode Address'}
          </button>
        </form>
      </div>

      {/* Coordinates to Address */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Coordinates to Address</h2>
        <form onSubmit={handleReverseGeocode} className="space-y-4">
          <div>
            <input
              type="text"
              value={coordinates}
              onChange={(e) => setCoordinates(e.target.value)}
              placeholder="Enter coordinates (e.g., -33.8688, 151.2093)"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Searching...' : 'Reverse Geocode'}
          </button>
        </form>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
          <p className="font-semibold">Error:</p>
          <p>{error}</p>
        </div>
      )}

      {/* Results Display */}
      {result && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Results</h2>
          
          {result.type === 'geocode' && (
            <div className="space-y-2">
              <p><strong>Address:</strong> {result.data.formattedAddress}</p>
              <p><strong>Latitude:</strong> {result.data.lat}</p>
              <p><strong>Longitude:</strong> {result.data.lng}</p>
              <p><strong>Place ID:</strong> {result.data.placeId}</p>
              <p><strong>Location Type:</strong> {result.data.locationType}</p>
              
              {result.data.addressComponents && (
                <div className="mt-4">
                  <p className="font-semibold mb-2">Address Components:</p>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div><strong>City:</strong> {getAddressComponent(result.data.addressComponents, 'locality') || 'N/A'}</div>
                    <div><strong>State:</strong> {getAddressComponent(result.data.addressComponents, 'administrative_area_level_1') || 'N/A'}</div>
                    <div><strong>Country:</strong> {getAddressComponent(result.data.addressComponents, 'country') || 'N/A'}</div>
                    <div><strong>Postal Code:</strong> {getAddressComponent(result.data.addressComponents, 'postal_code') || 'N/A'}</div>
                  </div>
                </div>
              )}
            </div>
          )}

          {result.type === 'reverse' && (
            <div className="space-y-2">
              <p><strong>Address:</strong> {result.data.formattedAddress}</p>
              <p><strong>Place ID:</strong> {result.data.placeId}</p>
              <p><strong>Types:</strong> {result.data.types.join(', ')}</p>
              
              {result.data.allResults && result.data.allResults.length > 1 && (
                <div className="mt-4">
                  <p className="font-semibold mb-2">All Matching Addresses ({result.data.allResults.length}):</p>
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    {result.data.allResults.slice(0, 5).map((addr, idx) => (
                      <li key={idx}>{addr.formatted_address}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          <div className="mt-4 p-3 bg-gray-50 rounded">
            <p className="text-sm font-mono text-black-600">
              <strong>Raw JSON:</strong>
            </p>
            <pre className="text-black-xs overflow-auto mt-2">
              {JSON.stringify(result.data, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
