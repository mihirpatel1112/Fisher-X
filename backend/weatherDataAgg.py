"""
NLDAS Weather Data Manager
Downloads and processes hourly weather data with geographic filtering
"""

import requests
import xarray as xr
import json
import numpy as np
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

EARTHDATA_USERNAME = os.getenv('EARTHDATA_USERNAME')
EARTHDATA_PASSWORD = os.getenv('EARTHDATA_PASSWORD')


class SessionWithHeaderRedirection(requests.Session):
    """Handle NASA Earthdata redirects properly"""
    AUTH_HOST = 'urs.earthdata.nasa.gov'
    
    def __init__(self, username, password):
        super().__init__()
        self.auth = (username, password)
    
    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        url = prepared_request.url
        
        if 'Authorization' in headers:
            original_parsed = requests.utils.urlparse(response.request.url)
            redirect_parsed = requests.utils.urlparse(url)
            
            if (original_parsed.hostname != redirect_parsed.hostname) and \
                    redirect_parsed.hostname != self.AUTH_HOST and \
                    original_parsed.hostname != self.AUTH_HOST:
                del headers['Authorization']


class NLDASWeatherManager:
    """
    Manages NLDAS weather data downloading and processing
    
    Usage:
        manager = NLDASWeatherManager()
        data = manager.get_latest_weather(lat_bounds=(35, 45), lon_bounds=(-80, -70))
    """
    
    def __init__(self, cache_dir="./weather_cache"):
        """
        Initialize NLDAS weather manager
        
        Args:
            cache_dir: Directory for caching downloaded files
        """
        self.cache_dir = cache_dir
        self.nc_dir = os.path.join(cache_dir, "netcdf")
        self.json_dir = os.path.join(cache_dir, "json")
        
        os.makedirs(self.nc_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)
    
    def download_file(self, date: str, hour: str) -> Optional[str]:
        """
        Download NLDAS weather data file
        
        Args:
            date: Date string YYYYMMDD (e.g., "20250930")
            hour: Hour string 0000-2300 (e.g., "1200")
        
        Returns:
            Path to downloaded file or None if failed
        """
        dt = datetime.strptime(date, "%Y%m%d")
        year = dt.year
        doy = dt.strftime("%j")
        
        base_url = "https://data.gesdisc.earthdata.nasa.gov/data/NLDAS"
        filename = f"NLDAS_FORA0125_H.A{date}.{hour}.020.nc"
        filepath = os.path.join(self.nc_dir, filename)
        
        # Check if already downloaded
        if os.path.exists(filepath):
            print(f"File already exists: {filename}")
            return filepath
        
        url = f"{base_url}/NLDAS_FORA0125_H.2.0/{year}/{doy}/{filename}"
        
        # Create authenticated session
        session = SessionWithHeaderRedirection(EARTHDATA_USERNAME, EARTHDATA_PASSWORD)
        
        print(f"Downloading {filename}...")
        
        try:
            response = session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"Downloaded: {filename}")
            return filepath
            
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None
    
    def download_time_range(
        self,
        start_date: str,
        end_date: str,
        hours: List[str] = None
    ) -> List[str]:
        """
        Download multiple files across a date range
        
        Args:
            start_date: Start date YYYYMMDD
            end_date: End date YYYYMMDD
            hours: List of hours to download (e.g., ["0000", "0600", "1200", "1800"])
                   If None, downloads all 24 hours
        
        Returns:
            List of downloaded file paths
        """
        if hours is None:
            hours = [f"{h:02d}00" for h in range(24)]
        
        start = datetime.strptime(start_date, "%Y%m%d")
        end = datetime.strptime(end_date, "%Y%m%d")
        
        files = []
        current = start
        while current <= end:
            date_str = current.strftime("%Y%m%d")
            for hour in hours:
                filepath = self.download_file(date_str, hour)
                if filepath:
                    files.append(filepath)
            current += timedelta(days=1)
        
        return files
    
    def process_file(
        self,
        filepath: str,
        lat_bounds: Optional[tuple] = None,
        lon_bounds: Optional[tuple] = None,
        max_points: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process NLDAS file to JSON format with optional geographic filtering
        
        Args:
            filepath: Path to .nc file
            lat_bounds: (min_lat, max_lat) to filter region
            lon_bounds: (min_lon, max_lon) to filter region
            max_points: Maximum points to include (None = all)
        
        Returns:
            Dictionary with processed weather data
        """
        print(f"\nProcessing: {os.path.basename(filepath)}")
        
        try:
            ds = xr.open_dataset(filepath)
            
            # Get coordinates
            lats = ds['lat'].values
            lons = ds['lon'].values
            
            # Apply geographic filter
            if lat_bounds:
                lat_mask = (lats >= lat_bounds[0]) & (lats <= lat_bounds[1])
                lats = lats[lat_mask]
            else:
                lat_mask = np.ones(len(lats), dtype=bool)
            
            if lon_bounds:
                lon_mask = (lons >= lon_bounds[0]) & (lons <= lon_bounds[1])
                lons = lons[lon_mask]
            else:
                lon_mask = np.ones(len(lons), dtype=bool)
            
            print(f"  Grid size after filtering: {len(lats)} x {len(lons)} = {len(lats) * len(lons):,} points")
            
            # Sample points
            total_points = len(lats) * len(lons)
            if max_points and total_points > max_points:
                sample_size = max_points
                lat_indices = np.random.randint(0, len(lats), sample_size)
                lon_indices = np.random.randint(0, len(lons), sample_size)
            else:
                # Create grid of all points
                lat_grid, lon_grid = np.meshgrid(range(len(lats)), range(len(lons)), indexing='ij')
                lat_indices = lat_grid.flatten()
                lon_indices = lon_grid.flatten()
                sample_size = len(lat_indices)
            
            print(f"  Extracting {sample_size:,} points...")
            
            # Extract data
            data_points = []
            for i in range(sample_size):
                lat_idx = lat_indices[i]
                lon_idx = lon_indices[i]
                
                # Map back to original indices if filtered
                orig_lat_idx = np.where(lat_mask)[0][lat_idx]
                orig_lon_idx = np.where(lon_mask)[0][lon_idx]
                
                point = {
                    "lat": float(lats[lat_idx]),
                    "lon": float(lons[lon_idx])
                }
                
                # Extract all weather variables
                for var in ds.data_vars:
                    if var not in ['lat', 'lon', 'time_bnds']:
                        try:
                            value = ds[var].values[0, orig_lat_idx, orig_lon_idx]
                            point[var] = float(value)
                        except:
                            pass
                
                data_points.append(point)
            
            # Build output
            output = {
                "metadata": {
                    "filename": os.path.basename(filepath),
                    "timestamp": str(ds['time'].values[0]),
                    "source": "NLDAS-2 Hourly Forcing Data",
                    "resolution": "0.125° (~12km)"
                },
                "geographic_extent": {
                    "lat_min": float(lats.min()),
                    "lat_max": float(lats.max()),
                    "lon_min": float(lons.min()),
                    "lon_max": float(lons.max()),
                    "filtered": lat_bounds is not None or lon_bounds is not None
                },
                "parameters": {},
                "data": data_points
            }
            
            # Add parameter info
            for var in ds.data_vars:
                if var not in ['lat', 'lon', 'time_bnds']:
                    output["parameters"][var] = {
                        "units": ds[var].attrs.get('units', 'N/A'),
                        "description": ds[var].attrs.get('long_name', 'N/A')
                    }
            
            ds.close()
            print(f"  Extraction complete")
            return output
            
        except Exception as e:
            print(f"  Error: {e}")
            return None
    
    def get_latest_weather(
        self,
        lat_bounds: Optional[tuple] = None,
        lon_bounds: Optional[tuple] = None,
        max_points: int = 10000,
        hours_back: int = 6
    ) -> Dict[str, Any]:
        """
        Get latest weather data (convenience method)
        
        Args:
            lat_bounds: (min_lat, max_lat) to filter region
            lon_bounds: (min_lon, max_lon) to filter region
            max_points: Maximum points to return
            hours_back: How many hours back to look for data
        
        Returns:
            Processed weather data
        """
        # Get most recent available time
        now = datetime.utcnow()
        
        # Try recent hours (NLDAS has a delay)
        for hour_offset in range(hours_back, hours_back + 24):
            target_time = now - timedelta(hours=hour_offset)
            date_str = target_time.strftime("%Y%m%d")
            hour_str = target_time.strftime("%H00")
            
            filepath = self.download_file(date_str, hour_str)
            
            if filepath:
                return self.process_file(
                    filepath,
                    lat_bounds=lat_bounds,
                    lon_bounds=lon_bounds,
                    max_points=max_points
                )
        
        return {"error": "No data available"}
    
    def save_to_json(self, data: Dict, output_path: str) -> bool:
        """Save processed data to JSON"""
        try:
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving JSON: {e}")
            return False


# Example usage
if __name__ == "__main__":
    manager = NLDASWeatherManager()
    
    # Example 1: Get latest weather for East Coast
    print("Fetching latest weather for East Coast...")
    east_coast = manager.get_latest_weather(
        lat_bounds=(35, 45),
        lon_bounds=(-80, -70),
        max_points=5000
    )
    
    if "error" not in east_coast:
        print(f"\nGot {len(east_coast['data'])} weather points")
        manager.save_to_json(east_coast, "east_coast_weather.json")
    
    # Example 2: Download specific date/time
    print("\n\nDownloading specific date/time...")
    filepath = manager.download_file("20250930", "1200")
    
    if filepath:
        # Process for California
        california = manager.process_file(
            filepath,
            lat_bounds=(32, 42),
            lon_bounds=(-125, -114),
            max_points=3000
        )
        
        if california:
            manager.save_to_json(california, "california_weather.json")
