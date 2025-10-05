"use client";
import { useState, useEffect } from "react";
import DashboardGrid from "@/components/dashgrid";
import AQSummary from "@/components/aqSummary";
import CitySearch from "@/components/citySearch";

export default function Dashboard() {
  const [airQualityData, setAirQualityData] = useState(null);
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentLocation, setCurrentLocation] = useState({
    lat: 34.0522,
    lng: -118.2445,
  });

  // Fetch data from your backend API
  async function fetchData(lat, lng) {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "";
      const aqResponse = await fetch(
        `${backendUrl}/api/query/location?lat=${lat}&lng=${lng}`
      );

      // Optional: weather may not exist yet; fetch it but don't fail the whole page if it 404s
      let wData = null;
      try {
        const weatherResponse = await fetch(`${backendUrl}/api/weather`);
        if (weatherResponse.ok) {
          wData = await weatherResponse.json();
        }
      } catch (_) {}

      if (!aqResponse.ok) {
        throw new Error("Failed to fetch air quality data");
      }

      const aqData = await aqResponse.json();

      const now = new Date().toISOString();
      const transformedAQ = {
        pm25: aqData?.latest_measurements?.pm25
          ? [{ timestamp: now, value: aqData.latest_measurements.pm25.value }]
          : [],
        no2: aqData?.latest_measurements?.no2
          ? [{ timestamp: now, value: aqData.latest_measurements.no2.value }]
          : [],
        latest: aqData?.latest_measurements || {},
        meta: {
          nearest_location: aqData?.nearest_location,
          available_sensors: aqData?.available_sensors,
        },
      };

      setAirQualityData(transformedAQ);
      setWeatherData(wData);
    } catch (error) {
      console.error("Error fetching data:", error);
      // Set error state to show error message to user
      setAirQualityData(null);
      setWeatherData(null);
    } finally {
      setLoading(false);
    }
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
