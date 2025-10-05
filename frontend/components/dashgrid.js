'use client';
import AirQualityChart from './airQualityChart';
import WeatherChart from './weatherChart';

export default function DashboardGrid({ airQualityData, weatherData }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* PM2.5 Chart */}
      <AirQualityChart 
        data={airQualityData?.pm25 || []}
        pollutant="pm25"
        title="PM2.5 Levels"
      />
      
      {/* NO2 Chart */}
      <AirQualityChart 
        data={airQualityData?.no2 || []}
        pollutant="no2"
        title="NO₂ Levels"
      />
      
      {/* Weather Chart - Temperature & Humidity */}
      <WeatherChart 
        data={weatherData || []}
        title="Temperature & Humidity"
        metrics={['temperature', 'humidity']}
      />
      
      {/* Weather Chart - Wind & Precipitation */}
      <WeatherChart 
        data={weatherData || []}
        title="Wind & Precipitation"
        metrics={['windSpeed', 'precipitation']}
      />
    </div>
  );
}