"""
NLDAS Weather Data File Explorer
Reads and formats NLDAS .nc file to JSON
"""

import xarray as xr
import json
import numpy as np

# Open the NLDAS file
filepath = "dataManagement/WeatherDataManagement/NLDAS_FORA0125_H.A20250930.1200.020.nc"
print(f"Opening: {filepath}\n")

ds = xr.open_dataset(filepath)

print("=" * 70)
print("NLDAS WEATHER DATA FILE")
print("=" * 70)

# Dimensions
print("\nDIMENSIONS:")
for dim, size in ds.dims.items():
    print(f"  {dim}: {size} points")

# Variables (weather parameters)
print("\nWEATHER PARAMETERS (Variables):")
for var in ds.data_vars:
    print(f"\n  {var}:")
    print(f"    Units: {ds[var].attrs.get('units', 'N/A')}")
    print(f"    Description: {ds[var].attrs.get('long_name', 'N/A')}")
    print(f"    Shape: {ds[var].shape}")
    print(f"    Min: {float(ds[var].min().values):.2f}")
    print(f"    Max: {float(ds[var].max().values):.2f}")
    print(f"    Mean: {float(ds[var].mean().values):.2f}")

# Coordinates
print("\nCOORDINATES:")
for coord in ds.coords:
    values = ds.coords[coord].values
    print(f"\n  {coord}:")
    print(f"    Size: {len(values)}")
    if len(values) < 10:
        print(f"    Values: {values}")
    else:
        print(f"    Range: {values.min()} to {values.max()}")

# Global attributes
print("\nFILE METADATA:")
for attr, value in ds.attrs.items():
    print(f"  {attr}: {value}")

# Extract sample data to JSON
print("\n" + "=" * 70)
print("EXTRACTING SAMPLE DATA TO JSON...")
print("=" * 70)

# Get actual dimension names
dim_names = list(ds.dims.keys())
print(f"Actual dimensions: {dim_names}")

# Find spatial dimensions (usually lat/lon or x/y or similar)
spatial_dims = [d for d in dim_names if d not in ['time']]
print(f"Spatial dimensions: {spatial_dims}")

if len(spatial_dims) >= 2:
    dim1 = spatial_dims[0]
    dim2 = spatial_dims[1]
    
    # Sample 100 random points
    total_points = ds.dims[dim1] * ds.dims[dim2]
    sample_size = min(100, total_points)
    
    # Get random indices
    np.random.seed(42)
    idx1 = np.random.randint(0, ds.dims[dim1], sample_size)
    idx2 = np.random.randint(0, ds.dims[dim2], sample_size)
else:
    print("Warning: Could not identify spatial dimensions")
    sample_size = min(100, ds.dims[dim_names[0]])
    idx1 = np.arange(sample_size)
    idx2 = None

# Extract data for sample points
sample_data = []

for i in range(sample_size):
    point = {}
    
    # Try to get lat/lon coordinates
    if 'lat' in ds.coords and 'lon' in ds.coords:
        # Get coordinates based on dimension structure
        if idx2 is not None:
            point["lat"] = float(ds['lat'].values[idx1[i], idx2[i]])
            point["lon"] = float(ds['lon'].values[idx1[i], idx2[i]])
        else:
            point["lat"] = float(ds['lat'].values[idx1[i]])
            point["lon"] = float(ds['lon'].values[idx1[i]])
    
    # Add all weather variables
    for var in ds.data_vars:
        if var not in ['lat', 'lon']:
            try:
                # Handle different data structures
                if 'time' in ds[var].dims:
                    if idx2 is not None:
                        value = ds[var].values[0, idx1[i], idx2[i]]
                    else:
                        value = ds[var].values[0, idx1[i]]
                else:
                    if idx2 is not None:
                        value = ds[var].values[idx1[i], idx2[i]]
                    else:
                        value = ds[var].values[idx1[i]]
                
                point[var] = float(value)
            except:
                pass  # Skip if can't extract
    
    if point:  # Only add if we got some data
        sample_data.append(point)

# Build JSON output
output = {
    "metadata": {
        "filename": filepath.split('/')[-1],
        "timestamp": ds.attrs.get('begin_date', 'N/A') + ' ' + ds.attrs.get('begin_time', 'N/A'),
        "description": "NLDAS-2 Hourly Forcing Data"
    },
    "geographic_extent": {
        "lat_min": float(ds['lat'].min()),
        "lat_max": float(ds['lat'].max()),
        "lon_min": float(ds['lon'].min()),
        "lon_max": float(ds['lon'].max())
    },
    "parameters": {},
    "sample_data": sample_data
}

# Add parameter descriptions
for var in ds.data_vars:
    if var not in ['lat', 'lon']:
        output["parameters"][var] = {
            "units": ds[var].attrs.get('units', 'N/A'),
            "description": ds[var].attrs.get('long_name', 'N/A'),
            "min": float(ds[var].min().values),
            "max": float(ds[var].max().values),
            "mean": float(ds[var].mean().values)
        }

# Save to JSON
json_path = "nldas_weather_data.json"
with open(json_path, 'w') as f:
    json.dump(output, f, indent=2)

print(f"\n✓ Saved to: {json_path}")
print(f"  Sample points: {len(sample_data)}")

# Print sample JSON preview
print("\nJSON PREVIEW (first point):")
print(json.dumps(sample_data[0], indent=2))

ds.close()

print("\n" + "=" * 70)
print("COMPLETE!")
print("=" * 70)
