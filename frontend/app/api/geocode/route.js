// Server-side API route - API key is hidden from client
import { NextResponse } from 'next/server';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const address = searchParams.get('address');
  const latlng = searchParams.get('latlng');
  
  // API key is only accessible on the server
  const apiKey = process.env.GOOGLE_MAPS_API_KEY;
  
  if (!apiKey) {
    return NextResponse.json(
      { error: 'API key not configured on server' },
      { status: 500 }
    );
  }

  try {
    let url;
    
    if (address) {
      // Geocoding: address to coordinates
      // Restrict to North American countries
      url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&components=country:US|country:CA|country:MX&key=${apiKey}`;
    } else if (latlng) {
      // Reverse geocoding: coordinates to address
      url = `https://maps.googleapis.com/maps/api/geocode/json?latlng=${latlng}&key=${apiKey}`;
    } else {
      return NextResponse.json(
        { error: 'Missing required parameter: address or latlng' },
        { status: 400 }
      );
    }

    const response = await fetch(url);
    const data = await response.json();

    // Don't expose the API key in error messages
    if (data.status === 'REQUEST_DENIED') {
      return NextResponse.json(
        { error: 'API request denied. Please contact administrator.' },
        { status: 403 }
      );
    }

    if (data.status === 'OVER_QUERY_LIMIT') {
      return NextResponse.json(
        { error: 'API quota exceeded. Please try again later.' },
        { status: 429 }
      );
    }

    return NextResponse.json(data);
    
  } catch (error) {
    console.error('Geocoding API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch location data' },
      { status: 500 }
    );
  }
}