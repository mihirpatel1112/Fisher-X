'use client';
import AirQualityChart from './airQualityChart';
import WeatherChart from './weatherChart';

export default function DashboardGrid({ airQualityData, weatherData }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Air Quality Charts - one for each available sensor */}
      {airQualityData?.meta?.available_sensors && Object.entries(airQualityData.meta.available_sensors).map(([sensorId, sensor]) => (
        <AirQualityChart 
          key={sensor.name}
          data={airQualityData.latest?.[sensor.name] ? [{ 
            timestamp: new Date().toISOString(), 
            value: airQualityData.latest[sensor.name].value 
          }] : []}
          pollutant={sensor.name}
          title={`${sensor.display_name} Levels`}
        />
      ))}
      
      {/* Weather Chart - Temperature Trends (min, avg, max) */}
      <WeatherChart 
        data={weatherData || []}
        title="Temperature Trends (°C)"
        metrics={['tempMin', 'temperature', 'tempMax']}
        yAxisLabel="Temperature (°C)"
      />
      
      {/* Weather Chart - Wind & Precipitation */}
      <WeatherChart 
        data={weatherData || []}
        title="Wind Speed & Precipitation"
        metrics={['windSpeed', 'precipitation']}
        yAxisLabel="Wind (km/h) / Precip (mm)"
      />

      {/* Weather Chart - Atmospheric Pressure */}
      <WeatherChart 
        data={weatherData || []}
        title="Atmospheric Pressure"
        metrics={['pressure']}
        yAxisLabel="Pressure (hPa)"
      />
    </div>
  );
}