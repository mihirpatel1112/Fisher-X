// lib/geocoding.js
// Utility functions for Google Geocoding API - uses server-side proxy

/**
 * Convert an address to coordinates (latitude/longitude)
 * @param {string} address - The address to geocode
 * @returns {Promise<Object>} - Object containing lat, lng, and formatted address
 */
export async function geocodeAddress(address) {
  // Call our server-side API route instead of Google directly
  const url = `/api/geocode?address=${encodeURIComponent(address)}`;

  try {
    const response = await fetch(url);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Geocoding request failed');
    }

    if (data.status === 'OK' && data.results.length > 0) {
      const result = data.results[0];
      return {
        lat: result.geometry.location.lat,
        lng: result.geometry.location.lng,
        formattedAddress: result.formatted_address,
        placeId: result.place_id,
        addressComponents: result.address_components,
        viewport: result.geometry.viewport,
        locationType: result.geometry.location_type
      };
    } else if (data.status === 'ZERO_RESULTS') {
      throw new Error('No results found for this address');
    } else {
      throw new Error(`Geocoding failed: ${data.status}`);
    }
  } catch (error) {
    console.error('Geocoding error:', error);
    throw error;
  }
}

/**
 * Convert coordinates to an address (reverse geocoding)
 * @param {number} lat - Latitude
 * @param {number} lng - Longitude
 * @returns {Promise<Object>} - Object containing formatted address and details
 */
export async function reverseGeocode(lat, lng) {
  // Call our server-side API route instead of Google directly
  const url = `/api/geocode?latlng=${lat},${lng}`;

  try {
    const response = await fetch(url);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Reverse geocoding request failed');
    }

    if (data.status === 'OK' && data.results.length > 0) {
      const result = data.results[0];
      return {
        formattedAddress: result.formatted_address,
        placeId: result.place_id,
        addressComponents: result.address_components,
        types: result.types,
        allResults: data.results // All matching addresses
      };
    } else if (data.status === 'ZERO_RESULTS') {
      throw new Error('No address found for these coordinates');
    } else {
      throw new Error(`Reverse geocoding failed: ${data.status}`);
    }
  } catch (error) {
    console.error('Reverse geocoding error:', error);
    throw error;
  }
}

/**
 * Get multiple geocoding results for an address
 * @param {string} address - The address to geocode
 * @returns {Promise<Array>} - Array of all matching results
 */
export async function geocodeAddressMultiple(address) {
  const url = `/api/geocode?address=${encodeURIComponent(address)}`;

  try {
    const response = await fetch(url);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Geocoding request failed');
    }

    if (data.status === 'OK') {
      return data.results.map(result => ({
        lat: result.geometry.location.lat,
        lng: result.geometry.location.lng,
        formattedAddress: result.formatted_address,
        placeId: result.place_id,
        types: result.types,
        addressComponents: result.address_components
      }));
    } else {
      throw new Error(`Geocoding failed: ${data.status}`);
    }
  } catch (error) {
    console.error('Geocoding error:', error);
    throw error;
  }
}

/**
 * Extract specific address component
 * @param {Array} addressComponents - Address components from geocoding result
 * @param {string} type - Component type (e.g., 'locality', 'country', 'postal_code')
 * @returns {string|null} - The component value or null
 */
export function getAddressComponent(addressComponents, type) {
  const component = addressComponents.find(comp => comp.types.includes(type));
  return component ? component.long_name : null;
}