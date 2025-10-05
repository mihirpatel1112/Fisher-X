"use client";

export default function AQSummary({
  latest = {},
  sensors = {},
  isPrediction = false,
  predictionHours = null,
}) {
  const entries = Object.entries(latest);
  if (!entries.length) return null;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 lg:col-span-2">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-gray-800">
          {isPrediction ? "Predicted Pollutants" : "Current Pollutants"}
        </h3>
        {isPrediction && predictionHours && (
          <span className="text-sm font-medium text-blue-600 bg-blue-50 px-3 py-1 rounded-full">
            {predictionHours} hour forecast
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {entries.map(([key, { value, unit, display_name }]) => (
          <div key={key} className="p-4 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-500">
              {display_name || key.toUpperCase()}
            </div>
            <div className="text-2xl font-semibold text-gray-900">
              {value != null ? value.toFixed(3) : "—"}
            </div>
            <div className="text-xs text-gray-500">
              {unit || sensors?.[key]?.unit || ""}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
