# TEMPO NetCDF File Reader and Visualizer
# Reads .nc files and extracts/visualizes air quality data
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import json
import os


def read_tempo_file(filepath):
    """
    Read a TEMPO NetCDF file   
        filepath: Path to .nc file
        Returns: xarray Dataset
    """
    print(f"\n Opening file: {os.path.basename(filepath)}")
    
    try:
        # TEMPO files have multiple groups - we want the 'product' group
        ds = xr.open_dataset(filepath, group='product')
        print(" File opened successfully!")
        return ds
    except Exception as e:
        print(f"Error opening file: {e}")
        print("\nTrying to open without group...")
        try:
            ds = xr.open_dataset(filepath)
            print(" File opened successfully!")
            return ds
        except Exception as e2:
            print(f"Still failed: {e2}")
            return None


def explore_tempo_file(ds):
    """
    Display information about the TEMPO dataset 
    Args: ds: xarray Dataset
    """
    if ds is None:
        return
    
    print("\n" + "="*70)
    print("TEMPO FILE CONTENTS")
    print("="*70)
    
    # Dimensions
    print("\n Dimensions:")
    for dim, size in ds.dims.items():
        print(f"   {dim}: {size}")
    
    # Variables (data fields)
    print("\nVariables (Data Fields):")
    for var in ds.data_vars:
        print(f"   • var")
    
    # Coordinates
    print("Coordinates:")
    for coord in ds.coords:
        print(f"   • {coord}: {ds.coords[coord].shape}")

# Too many points to make json better as just an NC file this for general debugging
def extract_to_json(ds, output_file="tempo_data.json", sample_size=100):
    """
    Extract TEMPO data to JSON format 
    Args:
        ds: xarray Dataset
        output_file: Output JSON filename
        sample_size: Number of sample points to extract
    Returns:Dictionary with extracted data
    """
    if ds is None:
        return None
    
    print(f"\nExtracting data to JSON...")
    
    # Find the main data variable usually vertical_column_troposphere or ssmthg
    main_vars = [v for v in ds.data_vars if 'column' in v.lower() or 'troposphere' in v.lower()]
    
    if not main_vars:
        print("Couldn't find main data variable, using first variable")
        main_vars = [list(ds.data_vars)[0]]
    
    main_var = main_vars[0]
    print(f"📊 Extracting variable: {main_var}")
    
    # Get the data
    data = ds[main_var].values
    
    # Get coordinates
    if 'latitude' in ds.coords and 'longitude' in ds.coords:
        lats = ds.coords['latitude'].values
        lons = ds.coords['longitude'].values
    else:
        print("No lat/lon coordinates found")
        lats = lons = None
    
    # Sample the data (to avoid huge JSON files)
    if data.size > sample_size:
        # Flatten and sample
        flat_data = data.flatten()
        valid_indices = ~np.isnan(flat_data)
        valid_data = flat_data[valid_indices]
        
        if len(valid_data) > sample_size:
            sample_indices = np.random.choice(len(valid_data), sample_size, replace=False)
            sampled_data = valid_data[sample_indices].tolist()
        else:
            sampled_data = valid_data.tolist()
    else:
        sampled_data = data[~np.isnan(data)].tolist()
    
    # Create output dictionary
    output = {
        "variable": main_var,
        "units": ds[main_var].attrs.get('units', 'unknown'),
        "description": ds[main_var].attrs.get('long_name', 'N/A'),
        "time": str(ds.attrs.get('time_coverage_start', 'N/A')),
        "data_points": len(sampled_data),
        "statistics": {
            "min": float(np.nanmin(data)),
            "max": float(np.nanmax(data)),
            "mean": float(np.nanmean(data)),
            "median": float(np.nanmedian(data))
        },
        "sample_values": sampled_data[:100]  # First 100 values
    }
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Data saved to: {output_file}")
    return output

def main():
    """
    Main function to demonstrate reading TEMPO files
    """
    print("\n" + "="*70)
    print("TEMPO NetCDF FILE READER")
    print("="*70)
    
    # Check for TEMPO data files
    data_dir = "./tempo_data"
       
    # Find .nc files
    nc_files = [f for f in os.listdir(data_dir) if f.endswith('.nc')]
    
    if not nc_files:
        print(f"\nNo .nc files found in {data_dir}")
        return
    
    print(f"\nFound {len(nc_files)} NetCDF file(s)")
    for i, f in enumerate(nc_files, 1):
        print(f"   {i}. {f}")
    
    # Read the first file
    filepath = os.path.join(data_dir, nc_files[0])
    ds = read_tempo_file(filepath)
    
    if ds:
        # Explore the file
        explore_tempo_file(ds)
        
        # Extract to JSON
        extract_to_json(ds, output_file="tempo_data.json")
       
        # Close dataset
        ds.close()
        
        print("\n" + "="*70)
        print("Processing complete!")
        print("\nGenerated files:")
        print("tempo_data.json - Data in JSON format")
        print("="*70)


if __name__ == "__main__":
    main()
