"use client";
import { useState, useEffect } from "react";
import DashboardGrid from "@/components/dashgrid";
import AQSummary from "@/components/aqSummary";
import CitySearch from "@/components/citySearch";
import LocationInfo from "@/components/locationInfo";

export default function Dashboard() {
  const [airQualityData, setAirQualityData] = useState(null);
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [locationInfo, setLocationInfo] = useState(null);
  const [currentLocation, setCurrentLocation] = useState({
    lat: 34.0522,
    lng: -118.2445,
  });

  // Fetch data from your backend API
  async function fetchData(lat, lng) {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "";
      
      // Use the new combined endpoint with parameters
      const response = await fetch(
        `${backendUrl}/api/query/combined?lat=${lat}&lng=${lng}&radius=10000&weather_days=14`
      );
  
      if (!response.ok) {
        throw new Error("Failed to fetch data");
      }
  
      const combinedData = await response.json();
  
      // Transform the data to match component expectations
      const transformedAQ = {
        latest: combinedData.air_quality?.latest_measurements || {},
        meta: {
          nearest_station: combinedData.air_quality?.nearest_station,
          available_sensors: combinedData.air_quality?.available_sensors,
          search_radius: combinedData.air_quality?.search_radius_used_km,
        },
      };
  
      // Transform weather data for charts
      const transformedWeather = transformWeatherData(combinedData.weather?.data || []);
  
      setAirQualityData(transformedAQ);
      setWeatherData(transformedWeather);
      setLocationInfo(combinedData.location);
    } catch (error) {
      console.error("Error fetching data:", error);
      setAirQualityData(null);
      setWeatherData(null);
      setLocationInfo(null);
    } finally {
      setLoading(false);
    }
  }

  function transformWeatherData(weatherArray) {
    if (!weatherArray || weatherArray.length === 0) return [];
    
    return weatherArray.map(day => ({
      timestamp: day.date,
      date: day.date,
      temperature: day.tavg,
      tempMin: day.tmin,
      tempMax: day.tmax,
      humidity: null, // Not available in this dataset
      precipitation: day.prcp,
      windSpeed: day.wspd,
      pressure: day.pres,
      snow: day.snow
    }));
  }

  const handleLocationSelect = (location) => {
    setLoading(true);
    setCurrentLocation({
      lat: location.lat,
      lng: location.lng
    });
  };

  useEffect(() => {
    fetchData(currentLocation.lat, currentLocation.lng);

    // Refresh data every 5 minutes
    const interval = setInterval(() => fetchData(currentLocation.lat, currentLocation.lng), 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [currentLocation]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl text-gray-600">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-6 py-8 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold" style={{ color: "#0B3D91" }}>
            Air Quality & Weather Dashboard
          </h1>
          <p className="mt-2 text-gray-600">
            Real-time monitoring of air pollutants and weather conditions
          </p>
        </div>

        <CitySearch 
          onLocationSelect={handleLocationSelect}
          currentLocation={currentLocation}
        />
        <LocationInfo 
          location={locationInfo} 
          airQuality={airQualityData?.meta}
        />
        <AQSummary
          latest={airQualityData?.latest}
          sensors={airQualityData?.meta?.available_sensors}
        />
        <DashboardGrid
          airQualityData={airQualityData}
          weatherData={weatherData}
        />
      </div>
    </div>
  );
}
