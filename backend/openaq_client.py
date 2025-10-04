# backend/openaq_client.py
import os
import time
import logging
from typing import Dict, Iterable, List, Optional, Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# ---- Config ----
OPENAQ_BASE_URL = os.getenv("OPENAQ_BASE_URL", "https://api.openaq.org/v3").rstrip("/")
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY", "")

# ---- Logger ----
logger = logging.getLogger("openaq")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# ---- Error ----
class OpenAQError(Exception):
    pass

# ---- Helpers ----
def _headers() -> Dict[str, str]:
    h = {"Accept": "application/json"}
    if OPENAQ_API_KEY:
        h["X-API-Key"] = OPENAQ_API_KEY
    return h

@retry(
    retry=retry_if_exception_type(OpenAQError),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(5),
)
def _get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{OPENAQ_BASE_URL}/{path.lstrip('/')}"
    r = requests.get(url, params=params, headers=_headers(), timeout=60)
    logger.info("OpenAQ GET %s params=%s -> %s", url, params, r.status_code)

    # 限流处理
    if r.status_code == 429:
        retry_after = int(r.headers.get("Retry-After", "1"))
        time.sleep(max(1, retry_after))
        raise OpenAQError("Rate limited (429)")

    # 其他错误
    if not r.ok:
        raise OpenAQError(
            f"OpenAQ {r.status_code} for {url} params={params} body={r.text[:300]}"
        )
    return r.json()

# ---- Public API wrappers ----
def list_locations(
    *,
    coordinates: Optional[str] = None,   # "lat,lon"
    radius: Optional[int] = None,        # meters (<= 25000)
    bbox: Optional[str] = None,          # "minLon,minLat,maxLon,maxLat"
    country: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = 1000,
    page: int = 1,
) -> Dict[str, Any]:
    """列出位置（不在此处按 parameters 过滤，避免上游兼容性问题）"""
    if coordinates and bbox:
        raise ValueError("Use either coordinates+radius OR bbox, not both.")
    params: Dict[str, Any] = {"limit": limit, "page": page}
    if coordinates:
        params["coordinates"] = coordinates
        if radius:
            params["radius"] = radius
    if bbox:
        params["bbox"] = bbox
    if country:
        params["country"] = country
    if city:
        params["city"] = city
    return _get("locations", params)

def list_location_sensors(
    location_id: int,
    parameters: Optional[Iterable[str]] = None,
    limit: int = 1000,
    page: int = 1,
) -> Dict[str, Any]:
    """取站点的传感器清单；不在请求里过滤，**本地过滤**"""
    params: Dict[str, Any] = {"limit": limit, "page": page}
    data = _get(f"locations/{location_id}/sensors", params)
    if parameters:
        keep = set(parameters)
        data["results"] = [
            s for s in data.get("results", [])
            if (isinstance(s.get("parameter"), dict) and s["parameter"].get("name") in keep)
            or (isinstance(s.get("parameter"), str) and s["parameter"] in keep)
        ]
    return data

def get_sensor_hours(
    sensor_id: int,
    *,
    datetime_from: str,
    datetime_to: str,
    limit: int = 1000,
    page: int = 1,
) -> Dict[str, Any]:
    """取单传感器小时值：兼容两套参数名与两条路径"""
    params = {
        # 两套都带，上游接受哪套就用哪套
        "datetime_from": datetime_from,
        "datetime_to": datetime_to,
        "date_from": datetime_from,
        "date_to": datetime_to,
        # 粒度字段兼容
        "temporal": "hour",
        "interval": "hour",
        "limit": limit,
        "page": page,
    }
    try:
        return _get(f"sensors/{sensor_id}/measurements", params)
    except OpenAQError:
        return _get(f"sensors/{sensor_id}/hours", params)

def get_location_latest(location_id: int, parameters: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    if parameters:
        for p in parameters:
            params.setdefault("parameters", []).append(p)
    return _get(f"locations/{location_id}/latest", params)

# ---- High-level aggregator ----
def get_timeseries_by_coords(
    *,
    coordinates: str,
    radius: int,
    parameters: Iterable[str],
    datetime_from: str,
    datetime_to: str,
    max_sensors: int = 30,
) -> Dict[str, Any]:
    """
    步骤：找位置 -> 列传感器(本地按参数过滤) -> 逐传感器分页取小时值
    返回结构:
    {
      "metadata": {"locations_found": N},
      "series": [
        {"sensor_id":..., "parameter":"pm25", "unit":"µg/m³", "value":..., "utc": "...", "local":"...", "location_id": ...},
        ...
      ]
    }
    """
    out: Dict[str, Any] = {"metadata": {}, "series": []}
    wanted = list(parameters)

    # 1) 位置（不按参数过滤，避免错过站点）
    locs = list_locations(coordinates=coordinates, radius=radius, limit=1000, page=1)
    out["metadata"]["locations_found"] = locs.get("meta", {}).get("found", len(locs.get("results", [])))
    location_ids = [loc.get("id") for loc in locs.get("results", []) if "id" in loc]

    # 2) 传感器（本地过滤）
    sensor_ids: List[int] = []
    for lid in location_ids:
        res = list_location_sensors(lid, parameters=wanted, limit=1000, page=1)
        for s in res.get("results", []):
            sid = s.get("id")
            if sid is not None:
                sensor_ids.append(sid)
                if len(sensor_ids) >= max_sensors:
                    break
        if len(sensor_ids) >= max_sensors:
            break

    logger.info("Collected %d sensors to query.", len(sensor_ids))

    # 3) 逐传感器分页取小时值
    for sid in sensor_ids:
        page = 1
        while True:
            hours = get_sensor_hours(
                sid,
                datetime_from=datetime_from,
                datetime_to=datetime_to,
                limit=1000,
                page=page,
            )
            rows = hours.get("results", [])
            if rows:
                for r in rows:
                    # 兼容不同字段形态
                    param_obj = r.get("parameter")
                    if isinstance(param_obj, dict):
                        param_name = param_obj.get("name")
                        unit = param_obj.get("units") or r.get("unit")
                    else:
                        param_name = param_obj  # 可能直接是字符串
                        unit = r.get("unit")

                    # 时间戳：有的结构用 period.datetimeTo，有的用 date.utc/local
                    utc = (
                        ((r.get("period") or {}).get("datetimeTo") or {}).get("utc")
                        or (r.get("date") or {}).get("utc")
                    )
                    local = (
                        ((r.get("period") or {}).get("datetimeTo") or {}).get("local")
                        or (r.get("date") or {}).get("local")
                    )

                    out["series"].append(
                        {
                            "sensor_id": sid,
                            "parameter": param_name,
                            "unit": unit,
                            "value": r.get("value") if r.get("value") is not None else r.get("average"),
                            "utc": utc,
                            "local": local,
                            "location_id": r.get("locationId") or r.get("location_id"),
                        }
                    )

            # 分页推进：优先用 meta.found，其次按条数推断
            meta = hours.get("meta", {}) or {}
            page_limit = meta.get("limit", 1000)
            found = meta.get("found")
            if found is not None:
                if page * page_limit >= found:
                    break
            else:
                if len(rows) < page_limit:
                    break
            page += 1

    return out

# ---- Debug helper（可选：在路由里调用，查看收集到的传感器）----
def discover_sensors_by_coords(
    *,
    coordinates: str,
    radius: int = 25000,
    parameters: Iterable[str] = ("pm25",),
) -> Dict[str, Any]:
    locs = list_locations(coordinates=coordinates, radius=radius, limit=1000, page=1)
    location_ids = [loc.get("id") for loc in locs.get("results", []) if "id" in loc]
    keep = set(parameters)
    sensors = []
    for lid in location_ids:
        res = list_location_sensors(lid, parameters=keep, limit=1000, page=1)
        for s in res.get("results", []):
            pname = s.get("parameter", {}).get("name") if isinstance(s.get("parameter"), dict) else s.get("parameter")
            sensors.append({"location_id": lid, "sensor_id": s.get("id"), "parameter": pname})
    return {"locations": location_ids, "sensors": sensors}


