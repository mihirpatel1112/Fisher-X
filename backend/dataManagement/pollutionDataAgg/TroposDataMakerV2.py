# ============================================================================
# TEMPO Hourly Snapshot - Full Data Export
# Gets all TEMPO data from the last hour and exports to JSON
# Each Full Snapshot ~ 500mb nc file, ~1000mb JSON file 
# ============================================================================


import earthaccess
import xarray as xr
import json
import numpy as np
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv() # Use ENV

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
def authenticate():
    auth = earthaccess.login()
    if not auth.authenticated:
        # NOTE DOES NOT USE .ENV, USES .netrc
        username = os.getenv('EARTHDATA_USERNAME')
        password = os.getenv('EARTHDATA_PASSWORD')
        if username and password:
            auth = earthaccess.login(strategy="environment", persist=True)
    
    if not auth.authenticated:
        raise Exception("Authentication failed. Check credentials in .env")
    return auth


def fetch_latest_scans(product_type, lookback_hours):
    """
    Fetch latest TEMPO scans
    
    Args:
        product_type: NO2_L3, HCHO_L3, or O3TOT_L3
        lookback_hours: How many hours back to search
    
    Returns:
        List of granules
    """
    product_map = {
        "NO2_L3": "TEMPO_NO2_L3",
        "HCHO_L3": "TEMPO_HCHO_L3",
        "O3TOT_L3": "TEMPO_O3TOT_L3"
    }
    
    short_name = product_map.get(product_type, "TEMPO_NO2_L3")
    
    from datetime import timezone
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=lookback_hours)
    
    print(f"\nFetching {short_name} data...")
    print(f"Time window: {start_time:%Y-%m-%d %H:%M} to {end_time:%Y-%m-%d %H:%M} UTC")
    
    results = earthaccess.search_data(
        short_name=short_name,
        temporal=(start_time.strftime("%Y-%m-%d %H:%M"), 
                 end_time.strftime("%Y-%m-%d %H:%M")),
        count=100  # Get all available in time window
    )
    
    print(f"Found {len(results)} granule(s)")
    return results


def download_files(results, output_dir):
    """Download files to output directory"""
    nc_dir = os.path.join(output_dir, "netcdf")
    os.makedirs(nc_dir, exist_ok=True)
    
    if not results:
        return []
    
    print(f"Downloading {len(results)} file(s)...")
    files = earthaccess.download(results, nc_dir)
    print(f"Downloaded to {nc_dir}")
    return files


# ============================================================================
# Data Extraction
# ============================================================================

def extract_full_data(nc_filepath, region_filter=None, max_points=None):
    """
    Extract ALL data from TEMPO file to JSON
    
    Args:
        nc_filepath: Path to .nc file
        region_filter: Optional geographic bounds
        max_points: Optional limit on number of points
    
    Returns:
        Dictionary with all extracted data
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
                point["uncertainty"] = float(uncertainty[tuple(idx)])
            
            # Quality flag
            if INCLUDE_QUALITY_FLAGS and 'main_data_quality_flag' in ds:
                quality = ds['main_data_quality_flag'].values
                point["quality_flag"] = int(quality[tuple(idx)])
            
            # Viewing angles
            if INCLUDE_ANGLES:
                if 'solar_zenith_angle' in ds:
                    point["solar_zenith"] = float(ds['solar_zenith_angle'].values[tuple(idx)])
                if 'viewing_zenith_angle' in ds:
                    point["viewing_zenith"] = float(ds['viewing_zenith_angle'].values[tuple(idx)])
            
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


def main():
    """Main execution"""
    print("=" * 70)
    print("TEMPO Hourly Snapshot - Full Data Export")
    print("=" * 70)
    
    print(f"\nConfiguration:")
    print(f"  Product: {PRODUCT_TYPE}")
    print(f"  Lookback: {LOOKBACK_HOURS} hour(s)")
    print(f"  Region filter: {REGION_FILTER or 'None (global)'}")
    print(f"  Max points: {MAX_POINTS_PER_FILE or 'Unlimited'}")
    print(f"  Output: {OUTPUT_DIR}")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        # Authenticate
        print("\nAuthenticating...")
        authenticate()
        
        # Fetch latest scans
        results = fetch_latest_scans(PRODUCT_TYPE, LOOKBACK_HOURS)
        
        if not results:
            print("\nNo data found in time window")
            return
        
        # Download files
        nc_files = download_files(results, OUTPUT_DIR)
        
        # Process each file
        json_dir = os.path.join(OUTPUT_DIR, "json")
        os.makedirs(json_dir, exist_ok=True)
        
        for nc_file in nc_files:
            json_data = extract_full_data(
                nc_file, 
                region_filter=REGION_FILTER,
                max_points=MAX_POINTS_PER_FILE
            )
            
            if json_data:
                # Save with timestamp
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                json_filename = f"tempo_{PRODUCT_TYPE}_{timestamp}.json"
                json_path = os.path.join(json_dir, json_filename)
                
                with open(json_path, 'w') as f:
                    json.dump(json_data, f, indent=2)
                
                file_size_mb = os.path.getsize(json_path) / (1024 * 1024)
                print(f"\nSaved: {json_filename}")
                print(f"  Size: {file_size_mb:.2f} MB")
                print(f"  Points: {len(json_data['data']):,}")
        
        print("\n" + "=" * 70)
        print("Snapshot complete!")
        print(f"JSON files saved to: {json_dir}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
