
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from openaq_client import (
    list_locations,
    list_location_sensors,
    get_sensor_hours,
    get_timeseries_by_coords
)

app = FastAPI(title="SpaceApps AQ Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发期
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

# 1) 直接透传 OpenAQ 的几个端点（原味 JSON）
@app.get("/openaq/locations")
def api_locations(
    coordinates: Optional[str] = Query(None, description="格式: lat,lon"),
    radius: Optional[int] = Query(None, description="meters <= 25000"),
    bbox: Optional[str] = Query(None, description="minLon,minLat,maxLon,maxLat"),
    country: Optional[str] = None,
    city: Optional[str] = None,
    parameters: Optional[List[str]] = Query(None)
):
    return list_locations(
      coordinates=coordinates, radius=radius, bbox=bbox,
      country=country, city=city,
      limit=1000, page=1
    )

@app.get("/openaq/locations/{location_id}/sensors")
def api_location_sensors(location_id: int, parameters: Optional[List[str]] = Query(None)):
    return list_location_sensors(location_id, parameters=parameters, limit=1000, page=1)

@app.get("/openaq/sensors/{sensor_id}/hours")
def api_sensor_hours(
    sensor_id: int,
    datetime_from: str = Query(..., description="ISO8601 UTC, e.g. 2025-09-01T00:00:00Z"),
    datetime_to: str = Query(..., description="ISO8601 UTC")
):
    return get_sensor_hours(
    sensor_id,
    datetime_from=datetime_from,
    datetime_to=datetime_to,
    limit=1000,
    page=1
)

# 2) 聚合端点：一口气返回周边所有站点的时序（最适合前端直接吃）
@app.get("/openaq/timeseries")
def api_timeseries(
    coordinates: str = Query(..., description="lat,lon"),
    radius: int = Query(12000, description="meters"),
    parameters: List[str] = Query(["pm25"]),
    datetime_from: str = Query(...),
    datetime_to: str = Query(...),
    max_sensors: int = Query(10)
):
    return get_timeseries_by_coords(
        coordinates=coordinates,
        radius=radius,
        parameters=parameters,
        datetime_from=datetime_from,
        datetime_to=datetime_to,
        max_sensors=max_sensors
    )

