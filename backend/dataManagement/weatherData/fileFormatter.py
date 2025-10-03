import xarray as xr

# Read the .nc file
ds = xr.open_dataset("dataManagement/NLDAS_FORA0125_H.A20250930.1200.020.nc")
print(ds)
