'use client';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Area, ComposedChart } from 'recharts';

const AQI_THRESHOLDS = {
  pm25: [
    { level: 'Good', max: 12, color: '#009E73' },
    { level: 'Moderate', max: 35.4, color: '#D5BF00' },
    { level: 'Unhealthy for Sensitive', max: 55.4, color: '#E67E22' },
    { level: 'Unhealthy', max: 150.4, color: '#D13C4F' },
    { level: 'Very Unhealthy', max: 250.4, color: '#7E3F8F' },
    { level: 'Hazardous', max: Infinity, color: '#5E1A1A' }
  ],
  no2: [
    { level: 'Good', max: 53, color: '#009E73' },
    { level: 'Moderate', max: 100, color: '#D5BF00' },
    { level: 'Unhealthy for Sensitive', max: 360, color: '#E67E22' },
    { level: 'Unhealthy', max: 649, color: '#D13C4F' },
    { level: 'Very Unhealthy', max: 1249, color: '#7E3F8F' },
    { level: 'Hazardous', max: Infinity, color: '#5E1A1A' }
  ]
};

export default function AirQualityChart({ data, pollutant = 'pm25', title = 'Air Quality' }) {
  // Get alert level based on current value
  const getAlertLevel = (value) => {
    const thresholds = AQI_THRESHOLDS[pollutant] || AQI_THRESHOLDS.pm25;
    for (let threshold of thresholds) {
      if (value <= threshold.max) {
        return threshold;
      }
    }
    return thresholds[thresholds.length - 1];
  };

  // Get current alert if latest value exceeds safe levels
  const latestValue = data && data.length > 0 ? data[data.length - 1].value : 0;
  const currentAlert = getAlertLevel(latestValue);
  const showWarning = currentAlert.level !== 'Good';

  const thresholds = AQI_THRESHOLDS[pollutant] || AQI_THRESHOLDS.pm25;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header with Alert */}
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-800">{title}</h3>
        {showWarning && (
          <div 
            className="mt-2 p-3 rounded-md flex items-center gap-2"
            style={{ backgroundColor: currentAlert.color + '20', borderLeft: `4px solid ${currentAlert.color}` }}
          >
            <svg className="w-5 h-5" style={{ color: currentAlert.color }} fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span className="font-semibold" style={{ color: currentAlert.color }}>
              {currentAlert.level}: {latestValue.toFixed(1)} µg/m³
            </span>
          </div>
        )}
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="timestamp" 
            stroke="#6b7280"
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            stroke="#6b7280"
            tick={{ fontSize: 12 }}
            label={{ value: 'µg/m³', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
            labelStyle={{ fontWeight: 'bold' }}
          />
          <Legend />
          
          {/* Threshold reference lines */}
          <ReferenceLine 
            y={thresholds[1].max} 
            stroke="#D5BF00" 
            strokeDasharray="3 3" 
            label={{ value: 'Moderate', position: 'right', fontSize: 10 }} 
          />
          <ReferenceLine 
            y={thresholds[2].max} 
            stroke="#D13C4F" 
            strokeDasharray="3 3" 
            label={{ value: 'Unhealthy', position: 'right', fontSize: 10 }} 
          />
          
          {/* Data line */}
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke="#0B3D91" 
            strokeWidth={2}
            dot={{ fill: '#0B3D91', r: 3 }}
            activeDot={{ r: 5 }}
            name={pollutant.toUpperCase()}
          />
          
          {/* Filled area for emphasis */}
          <Area 
            type="monotone" 
            dataKey="value" 
            fill="#0B3D91" 
            fillOpacity={0.1}
            stroke="none"
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Legend for threshold colors */}
      <div className="mt-4 flex flex-wrap gap-3 text-xs">
        {thresholds.slice(0, 4).map((threshold, idx) => (
          <div key={idx} className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: threshold.color }}></div>
            <span className="text-gray-600">{threshold.level}</span>
          </div>
        ))}
      </div>
    </div>
  );
}