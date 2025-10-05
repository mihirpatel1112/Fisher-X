import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from openaq_client import get_timeseries_by_coords

def fetch_boston_pm25_json(days: int = 7) -> dict:
    # Boston 市中心附近；可替换为前端传入
    coordinates = "42.3601,-71.0589"
    radius = 20000  # 20km
    parameters = ["pm25"]
    dt_to = datetime.now(tz=timezone.utc).replace(minute=0, second=0, microsecond=0)
    dt_from = dt_to - timedelta(days=days)
    payload = get_timeseries_by_coords(
        coordinates=coordinates,
        radius=radius,
        parameters=parameters,
        datetime_from=dt_from.isoformat().replace("+00:00", "Z"),
        datetime_to=dt_to.isoformat().replace("+00:00", "Z"),
        max_sensors=8
    )
    return payload

if __name__ == "__main__":
    data = fetch_boston_pm25_json(7)
    out = Path(__file__).resolve().parent / "data" / "openaq_pm25_boston.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"Saved: {out}")

