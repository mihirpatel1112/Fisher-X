from fastapi import FastAPI
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

@app.get("/api/query/location")
def query_location_endpoint(
    lat: float,
    lng: float,
    radius: Optional[int] = 5000,
    limit: Optional[int] = 100
):
    # Step 1: Find nearest location
    nearby_locations = openaq_client.locations.list(
        coordinates=f"{lat},{lng}",
        radius=radius,
        limit=1
    )

    if not nearby_locations or len(nearby_locations.results) == 0:
        return {"error": "No locations found within the specified radius"}

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
        "available_sensors": sensors
    }
