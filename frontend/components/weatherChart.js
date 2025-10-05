'use client';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function WeatherChart({ data, title = 'Weather Data', metrics = [], yAxisLabel = '' }) {
  // Color palette for different weather metrics
  const colors = {
    temperature: '#ef4444',      // red
    tempMin: '#93c5fd',          // light blue
    tempMax: '#dc2626',          // dark red
    humidity: '#3b82f6',         // blue
    precipitation: '#06b6d4',    // cyan
    windSpeed: '#8b5cf6',        // purple
    pressure: '#ec4899',         // pink
    snow: '#e0f2fe'              // light blue
  };

  // Format date for display
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Custom tooltip to show formatted values
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-800">{formatDate(label)}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {entry.value != null ? entry.value.toFixed(1) : 'N/A'}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-xl font-bold text-gray-800 mb-4">{title}</h3>
      
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="timestamp" 
            stroke="#6b7280"
            tick={{ fontSize: 12 }}
            tickFormatter={formatDate}
          />
          <YAxis 
            stroke="#6b7280"
            tick={{ fontSize: 12 }}
            label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: 'insideLeft', style: { fontSize: 12 } } : undefined}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          
          {/* Render a line for each metric */}
          {metrics.map((metric, idx) => (
            <Line 
              key={metric}
              type="monotone" 
              dataKey={metric} 
              stroke={colors[metric] || `hsl(${idx * 60}, 70%, 50%)`}
              strokeWidth={2}
              dot={{ r: 2 }}
              activeDot={{ r: 4 }}
              name={formatMetricName(metric)}
              connectNulls={true}  // Connect lines even if some data points are null
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// Helper function to format metric names for display
function formatMetricName(metric) {
  const names = {
    temperature: 'Avg Temp',
    tempMin: 'Min Temp',
    tempMax: 'Max Temp',
    humidity: 'Humidity',
    precipitation: 'Precipitation',
    windSpeed: 'Wind Speed',
    pressure: 'Pressure',
    snow: 'Snow'
  };
  return names[metric] || metric.charAt(0).toUpperCase() + metric.slice(1);
}