'use client';

import { useState, useCallback, useRef, useEffect } from 'react';

export default function CitySearch({ onLocationSelect, currentLocation }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const debounceTimer = useRef(null);

  // North American countries for filtering
  const NORTH_AMERICAN_COUNTRIES = ['US', 'CA', 'MX'];

  const handleSearch = useCallback(async (query) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Call our server-side API route (API key is hidden)
      const response = await fetch(
        `/api/geocode?address=${encodeURIComponent(query)}`
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch location data');
      }

      const data = await response.json();

      if (data.status === 'OK' && data.results.length > 0) {
        // Filter for North American results only
        const filteredResults = data.results.filter(result => {
          const country = result.address_components.find(
            comp => comp.types.includes('country')
          );
          return country && NORTH_AMERICAN_COUNTRIES.includes(country.short_name);
        });

        setSuggestions(filteredResults.slice(0, 5));
        setShowSuggestions(true);
      } else {
        setSuggestions([]);
      }
    } catch (err) {
      console.error('Search error:', err);
      setError(err.message);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleInputChange = (e) => {
    const value = e.target.value;
    setSearchQuery(value);
    
    // Clear previous timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Debounce search
    debounceTimer.current = setTimeout(() => {
      handleSearch(value);
    }, 500);
  };

  useEffect(() => {
    // Cleanup timer on unmount
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, []);

  const handleSelectLocation = (result) => {
    const location = {
      lat: result.geometry.location.lat,
      lng: result.geometry.location.lng,
      address: result.formatted_address,
      placeId: result.place_id
    };

    setSearchQuery(result.formatted_address);
    setShowSuggestions(false);
    setSuggestions([]);
    setError(null);
    onLocationSelect(location);
  };

  return (
    <div className="relative w-full max-w-2xl">
      <div className="relative">
        <input
          type="text"
          value={searchQuery}
          onChange={handleInputChange}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          placeholder="Search for a city in North America (e.g., Los Angeles, Toronto, Mexico City)"
          className="w-full px-4 py-3 pr-10 text-gray-900 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        
        {/* Search Icon */}
        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          {loading ? (
            <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          ) : (
            <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="absolute mt-2 w-full bg-red-50 border border-red-200 text-red-800 px-4 py-2 rounded-lg shadow-lg z-10">
          <p className="text-sm font-semibold">Error:</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Suggestions Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute mt-2 w-full bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto z-20">
          {suggestions.map((result, index) => (
            <button
              key={result.place_id || index}
              onClick={() => handleSelectLocation(result)}
              className="w-full text-left px-4 py-3 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none border-b border-gray-100 last:border-b-0"
            >
              <div className="flex items-start">
                <svg className="h-5 w-5 text-gray-400 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{result.formatted_address}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {result.geometry.location.lat.toFixed(4)}, {result.geometry.location.lng.toFixed(4)}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Click outside to close */}
      {showSuggestions && (
        <div
          className="fixed inset-0 z-10"
          onClick={() => setShowSuggestions(false)}
        />
      )}
    </div>
  );
}