'use client';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function WeatherChart({ data, title = 'Weather Data', metrics = [] }) {
  // Color palette for different weather metrics
  const colors = {
    temperature: '#ef4444',
    humidity: '#3b82f6',
    precipitation: '#06b6d4',
    windSpeed: '#8b5cf6',
    pressure: '#ec4899'
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
          />
          <YAxis 
            stroke="#6b7280"
            tick={{ fontSize: 12 }}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
            labelStyle={{ fontWeight: 'bold' }}
          />
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
              name={metric.charAt(0).toUpperCase() + metric.slice(1)}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}