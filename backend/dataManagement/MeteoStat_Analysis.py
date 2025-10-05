# Import Meteostat library and dependencies
from datetime import datetime
from meteostat import Point, Daily

# Set time period
start = datetime(2024, 10, 1)
end = datetime(2024, 10, 2)

# Create Point for Vancouver, BC
del_norte = Point(15.5819, 120.9042)

# Get daily data for 2018
data = Daily(del_norte, start, end)
data = data.fetch()

# Display the raw data
print(data)

# Optional: Save to CSV file
data.to_csv('latest_del_norteWeather.csv')
print("\nData saved to 'vancouver_weather_2018.csv'")

# Optional: See all available columns
print("\nAvailable columns:", data.columns.tolist())

# Optional: See basic statistics
print("\nBasic statistics:")
print(data.describe())
