
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from meteostat import Point, Daily
import pandas as pd


class MeteostatAPI:
    """
    A class for interacting with Meteostat weather data.
    
    This class provides methods to check data availability and download weather data
    for specified locations and date ranges.
    """
    
    def __init__(self):
        """Initialize the MeteostatAPI instance."""
        pass
    
    def _create_point(self, latitude: float, longitude: float, 
                     altitude: Optional[float] = None) -> Point:
        """
        Create a Meteostat Point object.
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            altitude: Altitude in meters (optional)
            
        Returns:
            Point: Meteostat Point object
        """
        if altitude is not None:
            return Point(latitude, longitude, altitude)
        else:
            return Point(latitude, longitude)
    
    def find_most_recent_available_date(self, latitude: float, longitude: float,
                                       max_days_back: int = 365,
                                       altitude: Optional[float] = None) -> Optional[datetime]:
        """
        Find the most recent date with available weather data.
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            max_days_back: Maximum number of days to check backwards
            altitude: Altitude in meters (optional)
            
        Returns:
            datetime object of most recent available date, or None if no data found
        """
        location = self._create_point(latitude, longitude, altitude)
        current_date = datetime.now()
        
        for days_back in range(max_days_back):
            check_date = current_date - timedelta(days=days_back)
            check_end = check_date + timedelta(days=1)
            
            data = Daily(location, check_date, check_end)
            data = data.fetch()
            
            if not data.empty:
                return check_date
        
        return None
    
    def check_availability(self, latitude: float, longitude: float,
                          start_date: str, end_date: str,
                          altitude: Optional[float] = None,
                          reverse: bool = False) -> Dict[str, Any]:
        """
        Check which dates have available weather data within the specified range.
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            altitude: Altitude in meters (optional)
            reverse: If True, checks from most recent to oldest
            
        Returns:
            Dictionary containing:
                - success: bool
                - location: dict with latitude, longitude, altitude
                - date_range: dict with start and end dates
                - available_dates: list of available dates as strings
                - total_days_available: int
                - most_recent_date: str (if reverse=True)
        """
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start > end:
                raise ValueError("start_date must be before end_date")
            
            location = self._create_point(latitude, longitude, altitude)
            available_dates = []
            
            if reverse:
                current_date = end
                while current_date >= start:
                    check_end = current_date + timedelta(days=1)
                    data = Daily(location, current_date, check_end)
                    data = data.fetch()
                    
                    if not data.empty:
                        available_dates.append(current_date)
                    
                    current_date -= timedelta(days=1)
                available_dates.reverse()
            else:
                current_date = start
                while current_date <= end:
                    check_end = current_date + timedelta(days=1)
                    data = Daily(location, current_date, check_end)
                    data = data.fetch()
                    
                    if not data.empty:
                        available_dates.append(current_date)
                    
                    current_date += timedelta(days=1)
            
            available_date_strings = [d.strftime('%Y-%m-%d') for d in available_dates]
            
            result = {
                "success": True,
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "altitude": altitude
                },
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "available_dates": available_date_strings,
                "total_days_available": len(available_date_strings)
            }
            
            if reverse and available_date_strings:
                result["most_recent_date"] = available_date_strings[0]
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def download_weather_data(self, latitude: float, longitude: float,
                             dates: List[str],
                             altitude: Optional[float] = None,
                             format: str = "dataframe") -> Any:
        """
        Download weather data for specified dates and location.
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            dates: List of dates in YYYY-MM-DD format
            altitude: Altitude in meters (optional)
            format: Output format - "dataframe", "dict", or "csv"
            
        Returns:
            pandas.DataFrame, dict, or str (CSV) depending on format parameter
        """
        if not dates:
            return pd.DataFrame() if format == "dataframe" else {}
        
        try:
            date_objects = [datetime.strptime(d, '%Y-%m-%d') for d in dates]
            location = self._create_point(latitude, longitude, altitude)
            
            start_date = min(date_objects)
            end_date = max(date_objects) + timedelta(days=1)
            
            data = Daily(location, start_date, end_date)
            data = data.fetch()
            
            if format == "dataframe":
                return data
            elif format == "csv":
                return data.to_csv()
            elif format == "dict":
                return self._dataframe_to_dict(data)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            raise Exception(f"Error downloading data: {str(e)}")
    
    def get_latest_data(self, latitude: float, longitude: float,
                       days: int = 30,
                       altitude: Optional[float] = None,
                       format: str = "dataframe") -> Any:
        """
        Get the most recent available weather data.
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            days: Number of days to retrieve
            altitude: Altitude in meters (optional)
            format: Output format - "dataframe", "dict", or "csv"
            
        Returns:
            pandas.DataFrame, dict, or str (CSV) depending on format parameter
        """
        try:
            # Find most recent available date
            most_recent = self.find_most_recent_available_date(latitude, longitude, altitude=altitude)
            
            if most_recent is None:
                return pd.DataFrame() if format == "dataframe" else {}
            
            # Calculate start date
            start_date = most_recent - timedelta(days=days - 1)
            location = self._create_point(latitude, longitude, altitude)
            
            # Download data
            data = Daily(location, start_date, most_recent + timedelta(days=1))
            data = data.fetch()
            
            if format == "dataframe":
                return data
            elif format == "csv":
                return data.to_csv()
            elif format == "dict":
                return self._dataframe_to_dict(data, include_metadata=True,
                                              start_date=start_date, end_date=most_recent,
                                              latitude=latitude, longitude=longitude, altitude=altitude)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            raise Exception(f"Error getting latest data: {str(e)}")
    
    def _dataframe_to_dict(self, data: pd.DataFrame, include_metadata: bool = False,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          latitude: Optional[float] = None,
                          longitude: Optional[float] = None,
                          altitude: Optional[float] = None) -> Dict[str, Any]:
        """
        Convert DataFrame to dictionary format.
        
        Args:
            data: pandas DataFrame with weather data
            include_metadata: Whether to include metadata in response
            start_date, end_date, latitude, longitude, altitude: Metadata fields
            
        Returns:
            Dictionary with weather data and optional metadata
        """
        if data.empty:
            return {"success": False, "error": "No data available"}
        
        # Convert to list of records
        data_records = []
        for idx, row in data.iterrows():
            record = {
                "date": idx.strftime('%Y-%m-%d'),
                "tavg": float(row['tavg']) if pd.notna(row['tavg']) else None,
                "tmin": float(row['tmin']) if pd.notna(row['tmin']) else None,
                "tmax": float(row['tmax']) if pd.notna(row['tmax']) else None,
                "prcp": float(row['prcp']) if pd.notna(row['prcp']) else None,
                "snow": float(row['snow']) if pd.notna(row['snow']) else None,
                "wdir": float(row['wdir']) if pd.notna(row['wdir']) else None,
                "wspd": float(row['wspd']) if pd.notna(row['wspd']) else None,
                "wpgt": float(row['wpgt']) if pd.notna(row['wpgt']) else None,
                "pres": float(row['pres']) if pd.notna(row['pres']) else None,
                "tsun": float(row['tsun']) if pd.notna(row['tsun']) else None,
            }
            data_records.append(record)
        
        result = {
            "success": True,
            "data": data_records,
            "total_records": len(data_records)
        }
        
        if include_metadata:
            # Calculate statistics
            statistics = {}
            for col in data.columns:
                non_null = data[col].notna().sum()
                if non_null > 0:
                    statistics[col] = {
                        "mean": float(data[col].mean()) if pd.notna(data[col].mean()) else None,
                        "min": float(data[col].min()) if pd.notna(data[col].min()) else None,
                        "max": float(data[col].max()) if pd.notna(data[col].max()) else None,
                        "std": float(data[col].std()) if pd.notna(data[col].std()) else None,
                    }
            
            # Calculate data completeness
            data_completeness = {}
            for col in data.columns:
                non_null = data[col].notna().sum()
                data_completeness[col] = {
                    "available_count": int(non_null),
                    "total_count": len(data),
                    "coverage_percentage": round((non_null / len(data)) * 100, 2)
                }
            
            result["statistics"] = statistics
            result["data_completeness"] = data_completeness
            
            if start_date and end_date:
                result["date_range"] = {
                    "start": start_date.strftime('%Y-%m-%d'),
                    "end": end_date.strftime('%Y-%m-%d')
                }
            
            if latitude is not None and longitude is not None:
                result["location"] = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "altitude": altitude
                }
        
        return result

    def get_latest_single_day(self, latitude: float, longitude: float,
                             altitude: Optional[float] = None,
                             target_date: Optional[datetime] = None,
                             max_days_back: int = 365) -> Dict[str, Any]:
        """
        Get the most recent single day of weather data.
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            altitude: Altitude in meters (optional)
            target_date: Date to start searching from (defaults to today)
            max_days_back: Maximum days to search backwards
            
        Returns:
            Dictionary with single day weather data
        """
        start_date = target_date if target_date else datetime.now()
        
        # Update find_most_recent_available_date to accept target_date
        location = self._create_point(latitude, longitude, altitude)
        most_recent = None
        
        for days_back in range(max_days_back):
            check_date = start_date - timedelta(days=days_back)
            check_end = check_date + timedelta(days=1)
            
            data = Daily(location, check_date, check_end)
            data = data.fetch()
            
            if not data.empty:
                most_recent = check_date
                break
        
        if most_recent is None:
            return {
                "success": False,
                "error": f"No data found in the last {max_days_back} days"
            }
        
        location = self._create_point(latitude, longitude, altitude)
        data = Daily(location, most_recent, most_recent + timedelta(days=1))
        data = data.fetch()
        
        if data.empty:
            return {
                "success": False,
                "error": "Failed to fetch data for the found date"
            }
        
        # Get the single row
        row = data.iloc[0]
        
        days_back = (start_date - most_recent).days
        
        return {
            "success": True,
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude
            },
            "requested_date": start_date.strftime('%Y-%m-%d'),
            "actual_date": most_recent.strftime('%Y-%m-%d'),
            "days_back": days_back,
            "data": {
                "date": most_recent.strftime('%Y-%m-%d'),
                "tavg": float(row['tavg']) if pd.notna(row['tavg']) else None,
                "tmin": float(row['tmin']) if pd.notna(row['tmin']) else None,
                "tmax": float(row['tmax']) if pd.notna(row['tmax']) else None,
                "prcp": float(row['prcp']) if pd.notna(row['prcp']) else None,
                "snow": float(row['snow']) if pd.notna(row['snow']) else None,
                "wdir": float(row['wdir']) if pd.notna(row['wdir']) else None,
                "wspd": float(row['wspd']) if pd.notna(row['wspd']) else None,
                "wpgt": float(row['wpgt']) if pd.notna(row['wpgt']) else None,
                "pres": float(row['pres']) if pd.notna(row['pres']) else None,
                "tsun": float(row['tsun']) if pd.notna(row['tsun']) else None,
            },
            "message": f"Data from {days_back} day(s) ago" if days_back > 0 else "Data from today"
        }


# Example usage
if __name__ == "__main__":
    # Initialize API
    api = MeteostatAPI()
    
    # Example 1: Check availability
    print("Checking availability...")
    availability = api.check_availability(
        latitude=15.5819,
        longitude=120.9042,
        start_date="2025-07-01",
        end_date="2025-09-30",
        reverse=True
    )
    print(f"Found {availability['total_days_available']} days of data")
    
    # Example 2: Get latest data
    print("\nGetting latest data...")
    latest_data = api.get_latest_data(
        latitude=15.5819,
        longitude=120.9042,
        days=30,
        format="dict"
    )
    print(f"Retrieved {latest_data['total_records']} records")
    
    # Example 3: Download specific dates
    if availability['available_dates']:
        print("\nDownloading specific dates...")
        data = api.download_weather_data(
            latitude=15.5819,
            longitude=120.9042,
            dates=availability['available_dates'][:10],  # First 10 days
            format="dataframe"
        )
        print(data.head())

