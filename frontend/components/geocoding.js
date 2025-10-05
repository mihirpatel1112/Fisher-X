// lib/geocoding.js
// Utility functions for Google Geocoding API

/**
 * Convert an address to coordinates (latitude/longitude)
 * @param {string} address - The address to geocode
 * @returns {Promise<Object>} - Object containing lat, lng, and formatted address
 */
export async function geocodeAddress(address) {
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
  
  if (!apiKey) {
    throw new Error('Google Maps API key is not configured');
  }

  const encodedAddress = encodeURIComponent(address);
  const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodedAddress}&key=${apiKey}`;

  try {
    const response = await fetch(url);
    const data = await response.json();

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
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
  
  if (!apiKey) {
    throw new Error('Google Maps API key is not configured');
  }

  const url = `https://maps.googleapis.com/maps/api/geocode/json?latlng=${lat},${lng}&key=${apiKey}`;

  try {
    const response = await fetch(url);
    const data = await response.json();

    if (data.status === 'OK' && data.results.length > 0) {
      const result = data.results[0];
      return {
        formattedAddress: result.formatted_address,
        placeId: result.place_id,
        addressComponents: result.address_components,
        types: result.types,
        allResults: data.results // All matching addresses
      };
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
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
  
  if (!apiKey) {
    throw new Error('Google Maps API key is not configured');
  }

  const encodedAddress = encodeURIComponent(address);
  const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodedAddress}&key=${apiKey}`;

  try {
    const response = await fetch(url);
    const data = await response.json();

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
