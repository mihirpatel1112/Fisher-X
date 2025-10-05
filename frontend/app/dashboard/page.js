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
  const [predictionHours, setPredictionHours] = useState("");
  const [weatherDays, setWeatherDays] = useState(7);
  const [isPrediction, setIsPrediction] = useState(false);

  // Fetch data from your backend API
  async function fetchData(lat, lng, predictionHours = "", weatherDays = 7) {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "";

      // Build query parameters
      let queryParams = `lat=${lat}&lng=${lng}&radius=10000&weather_days=${weatherDays}`;

      // Add prediction_hours parameter if set
      if (predictionHours !== "") {
        queryParams += `&hours=${predictionHours}`;
      }

      // Use the new combined endpoint with parameters
      const response = await fetch(
        `${backendUrl}/api/query/combined?${queryParams}`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch data");
      }

      const combinedData = await response.json();

      // Transform the data to match component expectations
      // If predictions exist, merge them with the latest measurements
      let latestMeasurements =
        combinedData.air_quality?.latest_measurements || {};

      // If predictions are available, replace values with predicted values
      if (combinedData.predictions?.values) {
        const predictedValues = combinedData.predictions.values;

        // Create a new object with predicted values, maintaining the structure
        latestMeasurements = {
          ...latestMeasurements,
          co: latestMeasurements.co
            ? {
                ...latestMeasurements.co,
                value: predictedValues.co ?? latestMeasurements.co.value,
              }
            : null,
          no2: latestMeasurements.no2
            ? {
                ...latestMeasurements.no2,
                value: predictedValues.no2 ?? latestMeasurements.no2.value,
              }
            : null,
          o3: latestMeasurements.o3
            ? {
                ...latestMeasurements.o3,
                value: predictedValues.o3 ?? latestMeasurements.o3.value,
              }
            : null,
          pm10: latestMeasurements.pm10
            ? {
                ...latestMeasurements.pm10,
                value: predictedValues.pm10 ?? latestMeasurements.pm10.value,
              }
            : null,
          pm25: latestMeasurements.pm25
            ? {
                ...latestMeasurements.pm25,
                value: predictedValues.pm25 ?? latestMeasurements.pm25.value,
              }
            : null,
          so2: latestMeasurements.so2
            ? {
                ...latestMeasurements.so2,
                value: predictedValues.so2 ?? latestMeasurements.so2.value,
              }
            : null,
        };

        // Filter out null values
        latestMeasurements = Object.fromEntries(
          Object.entries(latestMeasurements).filter(([_, v]) => v !== null)
        );
      }

      const transformedAQ = {
        latest: latestMeasurements,
        meta: {
          nearest_station: combinedData.air_quality?.nearest_station,
          available_sensors: combinedData.air_quality?.available_sensors,
          search_radius: combinedData.air_quality?.search_radius_used_km,
          // Add prediction metadata if available
          prediction_horizon: combinedData.predictions?.horizon_hours,
          aqi: combinedData.predictions?.values?.aqi,
        },
      };

      // Transform weather data for charts
      const transformedWeather = transformWeatherData(
        combinedData.weather?.data || []
      );

      setAirQualityData(transformedAQ);
      setWeatherData(transformedWeather);
      setLocationInfo(combinedData.location);
      setIsPrediction(!!combinedData.predictions?.values);
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

    return weatherArray.map((day) => ({
      timestamp: day.date,
      date: day.date,
      temperature: day.tavg,
      tempMin: day.tmin,
      tempMax: day.tmax,
      humidity: null, // Not available in this dataset
      precipitation: day.prcp,
      windSpeed: day.wspd,
      pressure: day.pres,
      snow: day.snow,
    }));
  }

  const handleLocationSelect = (location) => {
    setLoading(true);
    setCurrentLocation({
      lat: location.lat,
      lng: location.lng,
    });
  };

  const handlePredictionChange = (e) => {
    const value = e.target.value;
    setPredictionHours(value);
    setLoading(true);

    if (value === "") {
      // Real-time data - no prediction
      console.log("Showing real-time data");
      fetchData(currentLocation.lat, currentLocation.lng, "", weatherDays);
    } else {
      const hours = parseInt(value);
      // Trigger the prediction API call with hours parameter
      console.log(`Fetching prediction for next ${hours} hour(s)`);
      fetchData(currentLocation.lat, currentLocation.lng, hours, weatherDays);
    }
  };

  const handleWeatherDaysChange = (e) => {
    const days = parseInt(e.target.value);
    setWeatherDays(days);
    setLoading(true);
    fetchData(currentLocation.lat, currentLocation.lng, predictionHours, days);
  };

  useEffect(() => {
    fetchData(
      currentLocation.lat,
      currentLocation.lng,
      predictionHours,
      weatherDays
    );

    // Refresh data every 5 minutes
    const interval = setInterval(
      () =>
        fetchData(
          currentLocation.lat,
          currentLocation.lng,
          predictionHours,
          weatherDays
        ),
      5 * 60 * 1000
    );
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

        <div className="mb-6 flex items-center gap-6">
          <div className="flex items-center gap-4">
            <label
              htmlFor="prediction-hours"
              className="text-sm font-medium text-gray-700"
            >
              Prediction Timeframe:
            </label>
            <select
              id="prediction-hours"
              value={predictionHours}
              onChange={handlePredictionChange}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Real-time Data</option>
              <option value={1}>Next 1 Hour</option>
              <option value={6} disabled>
                Next 6 Hours (Coming Soon)
              </option>
              <option value={12} disabled>
                Next 12 Hours (Coming Soon)
              </option>
              <option value={24} disabled>
                Next 24 Hours (Coming Soon)
              </option>
            </select>
          </div>

          <div className="flex items-center gap-4">
            <label
              htmlFor="weather-days"
              className="text-sm font-medium text-gray-700"
            >
              Weather History:
            </label>
            <select
              id="weather-days"
              value={weatherDays}
              onChange={handleWeatherDaysChange}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value={3}>Last 3 Days</option>
              <option value={7}>Last 7 Days</option>
              <option value={14}>Last 14 Days</option>
              <option value={30}>Last 30 Days</option>
            </select>
          </div>
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
          isPrediction={isPrediction}
          predictionHours={airQualityData?.meta?.prediction_horizon}
        />
        <DashboardGrid
          airQualityData={airQualityData}
          weatherData={weatherData}
        />
      </div>
    </div>
  );
}
