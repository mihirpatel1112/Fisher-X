from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openaq import OpenAQ
from dotenv import load_dotenv
import os
from typing import Optional
import xarray as xr
import numpy as np
from datetime import datetime, timedelta
import requests
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from weatherDataAgg import NLDASWeatherManager
from .MeteoStat_Analysis import MeteostatAPI
from pydantic import BaseModel, Field
from typing import Optional

load_dotenv()

app = FastAPI(title="SpaceApps AQ Backend")

# Initialize the client
openaq_client = None
weather_manager = None


@app.on_event("startup")
async def startup_event():
    global openaq_client, weather_manager
    openaq_client = OpenAQ(api_key=os.getenv("OPENAQ_API_KEY"))
    weather_manager = NLDASWeatherManager(cache_dir="./weather_cache")

@app.on_event("shutdown")
async def shutdown_event():
    global openaq_client
    if openaq_client:
        openaq_client.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://*.ngrok-free.app",
        "https://*.ngrok.io",
        "https://fisher-x-fronty.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Please enter valid URL endpoint"}

@app.get("/health")
def health():
    return {"status": "healthy", "ok": True}


# =================================================
# Combined Location + Weather Endpoint
# =================================================

class CombinedDataResponse(BaseModel):
    success: bool
    air_quality: dict
    weather: dict
    location: dict
    message: Optional[str] = None


@app.get("/api/query/combined", response_model=CombinedDataResponse)
async def get_combined_data(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: Optional[int] = Query(5000, description="Initial search radius in meters"),
    altitude: Optional[float] = Query(None, description="Altitude in meters"),
    weather_days: Optional[int] = Query(7, description="Number of days of weather data"),
    date: Optional[str] = Query(None, description="Target date for weather (YYYY-MM-DD)")
):
    """
    Combined endpoint that fetches both air quality and weather data for a location.
    
    Returns:
    - Air quality data from nearest monitoring station
    - Weather data (latest available or date range)
    - Location information
    """
    result = {
        "success": True,
        "air_quality": {},
        "weather": {},
        "location": {},
        "message": None
    }
    
    errors = []
    
    # =================================================
    # 1. Fetch Air Quality Data
    # =================================================
    try:
        max_radius = 100000  # Maximum 100km
        radius_increment = 10000  # Increase by 10km each time
        current_radius = radius
        nearby_locations = None
        
        while current_radius <= max_radius:
            nearby_locations = openaq_client.locations.list(
                coordinates=f"{lat},{lng}",
                radius=current_radius,
                limit=1
            )
            
            if nearby_locations and len(nearby_locations.results) > 0:
                break
            
            current_radius += radius_increment
        
        if not nearby_locations or len(nearby_locations.results) == 0:
            errors.append(f"No air quality stations found within {max_radius/1000}km radius")
            result["air_quality"] = {
                "error": f"No locations found within {max_radius/1000}km radius",
                "searched_radius_km": max_radius / 1000
            }
        else:
            nearest_location = nearby_locations.results[0]
            location_id = nearest_location.id

            # Get sensor information
            sensors = {}
            if hasattr(nearest_location, 'sensors') and nearest_location.sensors:
                for sensor in nearest_location.sensors:
                    param_id = sensor.id
                    param_name = sensor.parameter.name if hasattr(sensor, 'parameter') else 'unknown'
                    param_display = sensor.parameter.display_name if hasattr(sensor, 'parameter') else param_name
                    param_unit = sensor.parameter.units if hasattr(sensor, 'parameter') else ''
                    sensors[param_id] = {
                        'name': param_name,
                        'display_name': param_display,
                        'unit': param_unit
                    }

            # Fetch latest measurements
            latest = openaq_client.locations.latest(locations_id=location_id)

            latest_measurements = {}
            if latest and hasattr(latest, 'results'):
                for idx, item in enumerate(latest.results):
                    value = getattr(item, 'value', None)
                    if idx < len(sensors):
                        sensor_id = list(sensors.keys())[idx]
                        sensor_info = sensors[sensor_id]
                        latest_measurements[sensor_info['name']] = {
                            "value": value,
                            "unit": sensor_info['unit'],
                            "display_name": sensor_info['display_name']
                        }
                    else:
                        latest_measurements[f"parameter_{idx}"] = {
                            "value": value,
                            "unit": "unknown"
                        }

            result["air_quality"] = {
                "nearest_station": {
                    "id": location_id,
                    "name": nearest_location.name,
                    "coordinates": nearest_location.coordinates,
                    "distance": getattr(nearest_location, 'distance', None)
                },
                "latest_measurements": latest_measurements,
                "available_sensors": sensors,
                "search_radius_used_km": current_radius / 1000
            }
            
            # Update location info
            result["location"] = {
                "latitude": lat,
                "longitude": lng,
                "nearest_station": nearest_location.name,
                "distance_to_station_km": round(getattr(nearest_location, 'distance', 0) / 1000, 2) if hasattr(nearest_location, 'distance') else None
            }
    
    except Exception as e:
        errors.append(f"Air quality error: {str(e)}")
        result["air_quality"] = {"error": str(e)}
    
    # =================================================
    # 2. Fetch Weather Data
    # =================================================
    try:
        weather_api = MeteostatAPI()
        
        if date:
            # Get single day weather data
            try:
                target_date = datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
            
            weather_result = weather_api.get_latest_single_day(
                latitude=lat,
                longitude=lng,
                altitude=altitude,
                target_date=target_date
            )
        else:
            # Get weather range data
            weather_result = weather_api.get_latest_data(
                latitude=lat,
                longitude=lng,
                days=weather_days,
                altitude=altitude,
                format="dict"
            )
        
        if weather_result.get("success"):
            result["weather"] = weather_result
        else:
            errors.append(weather_result.get("error", "No weather data found"))
            result["weather"] = {"error": weather_result.get("error", "No weather data found")}
    
    except Exception as e:
        errors.append(f"Weather error: {str(e)}")
        result["weather"] = {"error": str(e)}
    
    # =================================================
    # 3. Final Result
    # =================================================
    if not result["location"]:
        result["location"] = {
            "latitude": lat,
            "longitude": lng
        }
    
    # Determine overall success
    result["success"] = len(errors) == 0
    
    if errors:
        result["message"] = "; ".join(errors)
    
    return result


# =================================================
# Original Individual Endpoints (kept for backwards compatibility)
# =================================================

@app.get("/api/query/location")
def query_location_endpoint(
    lat: float,
    lng: float,
    radius: Optional[int] = 5000,
    limit: Optional[int] = 100
):
    # Step 1: Find nearest location with increasing radius if needed
    max_radius = 100000  # Maximum 100km
    radius_increment = 10000  # Increase by 10km each time
    current_radius = radius
    nearby_locations = None
    
    while current_radius <= max_radius:
        nearby_locations = openaq_client.locations.list(
            coordinates=f"{lat},{lng}",
            radius=current_radius,
            limit=1
        )
        
        # Check if we found any locations
        if nearby_locations and len(nearby_locations.results) > 0:
            break
        
        # No results found, increase radius
        current_radius += radius_increment
    
    # If still no locations found after reaching max radius
    if not nearby_locations or len(nearby_locations.results) == 0:
        return {
            "error": f"No locations found within {max_radius/1000}km radius",
            "searched_radius_km": max_radius / 1000
        }

    # Step 2: Get the first location's ID and sensors info
    nearest_location = nearby_locations.results[0]
    location_id = nearest_location.id

    # Get sensor information from the location
    sensors = {}
    if hasattr(nearest_location, 'sensors') and nearest_location.sensors:
        for sensor in nearest_location.sensors:
            param_id = sensor.id
            param_name = sensor.parameter.name if hasattr(sensor, 'parameter') else 'unknown'
            param_display = sensor.parameter.display_name if hasattr(sensor, 'parameter') else param_name
            param_unit = sensor.parameter.units if hasattr(sensor, 'parameter') else ''
            sensors[param_id] = {
                'name': param_name,
                'display_name': param_display,
                'unit': param_unit
            }

    # Step 3: Fetch latest measurements (use the shared client)
    latest = openaq_client.locations.latest(locations_id=location_id)

    # Match measurements with sensor metadata
    latest_measurements = {}
    if latest and hasattr(latest, 'results'):
        for idx, item in enumerate(latest.results):
            value = getattr(item, 'value', None)
            if idx < len(sensors):
                sensor_id = list(sensors.keys())[idx]
                sensor_info = sensors[sensor_id]
                latest_measurements[sensor_info['name']] = {
                    "value": value,
                    "unit": sensor_info['unit'],
                    "display_name": sensor_info['display_name']
                }
            else:
                latest_measurements[f"parameter_{idx}"] = {
                    "value": value,
                    "unit": "unknown"
                }

    return {
        "nearest_location": {
            "id": location_id,
            "name": nearest_location.name,
            "coordinates": nearest_location.coordinates,
            "distance": getattr(nearest_location, 'distance', None)
        },
        "latest_measurements": latest_measurements,
        "available_sensors": sensors,
        "search_radius_used_km": current_radius / 1000  # Include the radius that found results
    }


# =================================================
# Meteo Getter
# =================================================

# Initialize the API
weather_api = MeteostatAPI()


# Response models
class LatestDayResponse(BaseModel):
    success: bool
    location: dict
    requested_date: str
    actual_date: str
    days_back: int
    data: dict
    message: Optional[str] = None


class LatestRangeResponse(BaseModel):
    success: bool
    data: list
    total_records: int
    statistics: Optional[dict] = None
    data_completeness: Optional[dict] = None
    date_range: Optional[dict] = None
    location: Optional[dict] = None


@app.get("/api/query/weatherGetter", response_model=LatestDayResponse)
async def get_latest_weather(
    latitude: float,
    longitude: float,
    altitude: Optional[float] = Query(None, description="Altitude in meters"),
    date: Optional[str] = Query(None, description="Target date (YYYY-MM-DD)")
):
    """
    Get the most recent single day of weather data.
    Automatically searches backwards until data is found.
    """
    try:
        target_date = None
        if date:
            try:
                target_date = datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        result = weather_api.get_latest_single_day(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            target_date=target_date
        )
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result.get("error", "No data found"))
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/weather/latest/range", response_model=LatestRangeResponse)
async def get_latest_weather_range(
    latitude: float,
    longitude: float,
    days: Optional[int],
    altitude: Optional[float]
):
    """
    Get the most recent range of weather data.
    Returns the specified number of days leading up to the most recent available date.
    """
    try:
        result = weather_api.get_latest_data(
            latitude=latitude,
            longitude=longitude,
            days=days,
            altitude=altitude,
            format="dict"
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "No data found"))
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")