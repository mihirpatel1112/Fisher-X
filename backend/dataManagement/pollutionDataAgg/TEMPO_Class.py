"""
TEMPO Hourly Snapshot - Full Data Export
Gets all TEMPO data from the last hour and exports to JSON
Each Full Snapshot ~ 500mb nc file, ~1000mb JSON file
"""

import earthaccess
import xarray as xr
import json
import numpy as np
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

load_dotenv()  # Use ENV

# ============================================================================
# CONFIGURATION PARAMETERS
# ============================================================================

# Data source
PRODUCT_TYPE = "NO2_L3"  # Options: NO2_L3, HCHO_L3, O3TOT_L3
LOOKBACK_HOURS = 5  # How far back to fetch data (default: 1 hour)

# Geographic filtering (None = global, or specify bounds)
REGION_FILTER = None  # Set to None for all data
# Example: REGION_FILTER = {'lat': (25, 50), 'lon': (-125, -65)}  # Continental US

# Output settings
OUTPUT_DIR = "./snapshots"  # Where to save JSON files

"""
Note: If want specify a specific area of points, change region filter to a range, will get multiple points and ranges
Prev try, 5mil points complete geographic coverage of the map and their pollution points, cutting it down to 10,000 - 100,000
would cover less geographic area but serve its purpose
Possible ToDo: add a threshold for lowest or highest in range.
"""
MAX_POINTS_PER_FILE = None  # None = unlimited, or set a limit (e.g., 10000)

# Data fields to include
INCLUDE_UNCERTAINTY = True  # Include uncertainty values
INCLUDE_QUALITY_FLAGS = True  # Include quality flag data
INCLUDE_ANGLES = True  # Include viewing/solar angles

# ============================================================================


class TEMPODataManager:
    """
    Manages TEMPO satellite data fetching and processing
    
    Usage:
        test = TEMPODataManager()
        data = manager.get_latest_snapshot()
        California = manager.get_region_data(lat_bounds=(32, 42), lon_bounds=(-125, -114))
    """
    
    def __init__(self, cache_directory="./TEMPO_snap") -> None:
        """
        Initialises tempo data manager
        """
        self.cache_directory = cache_directory
        self.nc_directory = os.path.join(cache_directory, "netcdf")
        self.json_directory = os.path.join(cache_directory, "json")
        self.authenticated = False  # Assume user not authenticated
        
        os.makedirs(self.nc_directory, exist_ok=True)
        os.makedirs(self.json_directory, exist_ok=True)
    
    def authenticate(self) -> bool:
        """
        Authenticate with NASA Earthdata
        """
        try:
            auth = earthaccess.login()
            if not auth.authenticated:
                auth = earthaccess.login(strategy="environment", persist=True)
            
            self.authenticated = auth.authenticated
            return self.authenticated
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def search_data(
        self,
        product_type: str = PRODUCT_TYPE,
        lookback_hours: int = LOOKBACK_HOURS,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List:
        """
        Search for TEMPO data
        Args:
            product_type: NO2_L3, HCHO_L3, or O3TOT_L3
            lookback_hours: Hours to look back (if start_time/end_time not provided)
            start_time: Specific start time (optional)
            end_time: Specific end time (optional)
        """
        if not self.authenticated:
            self.authenticate()
        
        product_map = {
            "NO2_L3": "TEMPO_NO2_L3",
            "HCHO_L3": "TEMPO_HCHO_L3",
            "O3TOT_L3": "TEMPO_O3TOT_L3"
        }
        
        short_name = product_map.get(product_type, "TEMPO_NO2_L3")
        
        if not end_time:
            end_time = datetime.now(timezone.utc)
        if not start_time:
            start_time = end_time - timedelta(hours=lookback_hours)
        
        print(f"\nFetching {short_name} data...")
        print(f"Time window: {start_time:%Y-%m-%d %H:%M} to {end_time:%Y-%m-%d %H:%M} UTC")
        
        results = earthaccess.search_data(
            short_name=short_name,
            temporal=(start_time.strftime("%Y-%m-%d %H:%M"),
                     end_time.strftime("%Y-%m-%d %H:%M")),
            count=100
        )
        
        print(f"Found {len(results)} granule(s)")
        return results
    
    def download_granules(self, granules: List) -> List[str]:
        """
        Download TEMPO granules
        Args:
            granules: List of granules from search_data()
        """
        if not granules:
            return []
        
        print(f"Downloading {len(granules)} file(s)...")
        files = earthaccess.download(granules, self.nc_directory)
        print(f"Downloaded to {self.nc_directory}")
        return files
    
    def extract_full_data(
        self,
        nc_filepath: str,
        region_filter: Optional[Dict] = REGION_FILTER,
        max_points: Optional[int] = MAX_POINTS_PER_FILE
    ) -> Dict[str, Any]:
        """
        Extract ALL data from TEMPO file to JSON
        
        Args:
            nc_filepath: Path to .nc file
            region_filter: Optional geographic bounds
            max_points: Optional limit on number of points
        """
        filename = os.path.basename(nc_filepath)
        print(f"\nProcessing: {filename}")
        
        try:
            # Read all groups
            ds_root = xr.open_dataset(nc_filepath)
            ds_product = xr.open_dataset(nc_filepath, group='product')
            ds_geolocation = xr.open_dataset(nc_filepath, group='geolocation')
            ds = xr.merge([ds_root, ds_product, ds_geolocation])
            
            # Get coordinates
            lats = ds.coords['latitude'].values
            lons = ds.coords['longitude'].values
            
            # Main variable
            main_var = 'vertical_column_troposphere'
            data = ds[main_var].values
            
            print(f"  Original shape: {data.shape}")
            print(f"  Total points: {data.size:,}")
            
            # Apply region filter if specified
            if region_filter:
                lat_mask = (lats >= region_filter['lat'][0]) & (lats <= region_filter['lat'][1])
                lon_mask = (lons >= region_filter['lon'][0]) & (lons <= region_filter['lon'][1])
                
                if len(data.shape) == 3:  # (time, lat, lon)
                    data = data[:, lat_mask, :][:, :, lon_mask]
                    lats = lats[lat_mask]
                    lons = lons[lon_mask]
                
                print(f"  After region filter: {data.shape}")
            
            # Get all valid data points
            valid_mask = ~np.isnan(data)
            valid_indices = np.argwhere(valid_mask)
            
            print(f"  Valid points: {len(valid_indices):,}")
            
            # Limit points if specified
            if max_points and len(valid_indices) > max_points:
                print(f"  Limiting to {max_points:,} points (random sample)")
                sample_idx = valid_indices[np.random.choice(len(valid_indices), max_points, replace=False)]
            else:
                sample_idx = valid_indices
            
            # Extract all data points
            print(f"  Extracting {len(sample_idx):,} points...")
            all_data = []
            
            for idx in sample_idx:
                point = {}
                
                # Main value
                point["value"] = float(data[tuple(idx)])
                
                # Coordinates (handle 3D data)
                if len(idx) == 3 and len(lats.shape) == 1:
                    point["lat"] = float(lats[idx[1]])
                    point["lon"] = float(lons[idx[2]])
                
                # Uncertainty
                if INCLUDE_UNCERTAINTY and 'vertical_column_troposphere_uncertainty' in ds:
                    uncertainty = ds['vertical_column_troposphere_uncertainty'].values
                    if region_filter:
                        uncertainty = uncertainty[:, lat_mask, :][:, :, lon_mask]
                    point["uncertainty"] = float(uncertainty[tuple(idx)])
                
                # Quality flag
                if INCLUDE_QUALITY_FLAGS and 'main_data_quality_flag' in ds:
                    quality = ds['main_data_quality_flag'].values
                    if region_filter:
                        quality = quality[:, lat_mask, :][:, :, lon_mask]
                    point["quality_flag"] = int(quality[tuple(idx)])
                
                # Viewing angles
                if INCLUDE_ANGLES:
                    if 'solar_zenith_angle' in ds:
                        solar_angle = ds['solar_zenith_angle'].values
                        if region_filter:
                            solar_angle = solar_angle[:, lat_mask, :][:, :, lon_mask]
                        point["solar_zenith"] = float(solar_angle[tuple(idx)])
                    if 'viewing_zenith_angle' in ds:
                        viewing_angle = ds['viewing_zenith_angle'].values
                        if region_filter:
                            viewing_angle = viewing_angle[:, lat_mask, :][:, :, lon_mask]
                        point["viewing_zenith"] = float(viewing_angle[tuple(idx)])
                
                all_data.append(point)
            
            # Build output
            output = {
                "metadata": {
                    "filename": filename,
                    "product_type": PRODUCT_TYPE,
                    "scan_time": ds.attrs.get('time_coverage_start', 'N/A'),
                    "scan_end": ds.attrs.get('time_coverage_end', 'N/A'),
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "variable": main_var,
                    "units": ds[main_var].attrs.get('units', 'N/A'),
                    "description": ds[main_var].attrs.get('long_name', 'N/A')
                },
                "geographic_extent": {
                    "lat_min": float(np.min(lats)),
                    "lat_max": float(np.max(lats)),
                    "lon_min": float(np.min(lons)),
                    "lon_max": float(np.max(lons)),
                    "region_filter_applied": region_filter is not None
                },
                "data_summary": {
                    "total_grid_points": int(data.size),
                    "valid_points": int(np.sum(valid_mask)),
                    "points_in_output": len(all_data),
                    "coverage_percent": float(np.sum(valid_mask) / data.size * 100)
                },
                "statistics": {
                    "min": float(np.nanmin(data)),
                    "max": float(np.nanmax(data)),
                    "mean": float(np.nanmean(data)),
                    "median": float(np.nanmedian(data)),
                    "std": float(np.nanstd(data)),
                    "percentile_25": float(np.nanpercentile(data, 25)),
                    "percentile_75": float(np.nanpercentile(data, 75))
                },
                "data": all_data
            }
            
            ds.close()
            print(f"  Extraction complete: {len(all_data):,} points")
            return output
            
        except Exception as e:
            print(f"  Error: {e}")
            return None
    
    def get_latest_snapshot(
        self,
        product_type: str = PRODUCT_TYPE,
        max_points: Optional[int] = MAX_POINTS_PER_FILE,
        region: Optional[Dict] = REGION_FILTER
    ) -> Dict[str, Any]:
        """
        Get latest TEMPO data snapshot (convenience method)
        
        Args:
            product_type: NO2_L3, HCHO_L3, or O3TOT_L3
            max_points: Maximum points to return
            region: Geographic filter
        
        Returns:
            Processed data dictionary
        """
        # Search for latest data
        granules = self.search_data(product_type=product_type, lookback_hours=LOOKBACK_HOURS)
        
        if not granules:
            return {"error": "No data found"}
        
        # Download first (most recent) granule
        files = self.download_granules([granules[0]])
        
        if not files:
            return {"error": "Download failed"}
        
        # Process and return
        return self.extract_full_data(
            files[0],
            region_filter=region,
            max_points=max_points
        )
    
    def get_region_data(
        self,
        lat_bounds: tuple,
        lon_bounds: tuple,
        product_type: str = PRODUCT_TYPE,
        max_points: Optional[int] = MAX_POINTS_PER_FILE
    ) -> Dict[str, Any]:
        """
        Get data for specific geographic region
        
        Args:
            lat_bounds: (min_lat, max_lat)
            lon_bounds: (min_lon, max_lon)
            product_type: NO2_L3, HCHO_L3, or O3TOT_L3
            max_points: Maximum points (None = all in region)
        
        Returns:
            Processed data for region
        """
        region = {'lat': lat_bounds, 'lon': lon_bounds}
        return self.get_latest_snapshot(
            product_type=product_type,
            max_points=max_points,
            region=region
        )
    
    def save_to_json(self, data: Dict, output_path: str) -> bool:
        """
        Save processed data to JSON file
        
        Args:
            data: Processed data dictionary
            output_path: Path to save JSON
        
        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving JSON: {e}")
            return False


