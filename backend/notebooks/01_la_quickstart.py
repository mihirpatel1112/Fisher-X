# notebooks/01_la_quickstart.py  —— OpenAQ v3 + earthaccess 修正版
import os, json, warnings
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
import requests
import xarray as xr
import folium

# ---- 可选依赖：有更好；没有也不中断 ----
try:
    import earthaccess
except Exception as e:
    print("earthaccess import warning:", e)

# ---- 基本配置：LA 范围 + 时间窗（放宽更易命中） ----
LA_BBOX = (-120.5, 31.5, -115.5, 36.5)   # west, south, east, north
CENTER  = (34.05, -118.25)

def iso_z(dt):
    dt = dt.replace(second=0, microsecond=0)
    s = dt.isoformat().replace("+00:00","Z")
    return s if s.endswith("Z") else (s + "Z")

HOURS = 96  # 72/96/120 都可以；命中率更高
t_end   = datetime.now(timezone.utc)
t_start = t_end - timedelta(hours=HOURS)
T0, T1  = iso_z(t_start), iso_z(t_end)
print("Time window (UTC):", (T0, T1))

os.makedirs("data/tempo", exist_ok=True)
os.makedirs("data/outputs", exist_ok=True)

# ======================================================================
#                        OpenAQ v3 （带 API Key）
# ======================================================================
OPENAQ_KEY = os.getenv("OPENAQ_KEY", "").strip()
OA_HEADERS = {"Accept": "application/json"}
if OPENAQ_KEY:
    OA_HEADERS["X-API-Key"] = OPENAQ_KEY
OA_BASE = "https://api.openaq.org/v3"

def oa_get(path, params, timeout=30):
    import requests
    url = f"{OA_BASE}{path}"
    r = requests.get(url, params=params, headers=OA_HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()

def oa_param_ids(names=("pm25","no2")):
    """把参数名转换为 v3 的数值 ID；必要时回退到已知 ID（pm25=2, no2=5）"""
    wanted = {n.lower() for n in names}
    mapping = {}
    page, limit = 1, 200
    while True:
        js = oa_get("/parameters", {"page": page, "limit": limit})
        for it in js.get("results", []):
            nm = str(it.get("name", "")).lower()
            if nm in wanted and "id" in it:
                mapping[nm] = int(it["id"])
        meta = js.get("meta", {}) or {}
        if page * limit >= int(meta.get("found", 0)):
            break
        page += 1

    # 回退：如果拿到的 id 异常（例如 19860 这种），用已知标准 id
    fallback = {"pm25": 2, "no2": 5}
    for k in list(wanted):
        vid = mapping.get(k)
        if not isinstance(vid, int) or vid <= 0 or vid > 1000:
            mapping[k] = fallback[k] if k in fallback else vid
    return mapping
# ========== 替换结束 ==========


# ========== 替换开始：请求 v3 /measurements ==========
def fetch_openaq_v3_measurements(bbox, t0, t1, names=("pm25","no2"),
                                 page_limit=1000, max_pages=30):
    """使用重复的 parameter_id=… 方式查询 /v3/measurements"""
    import requests
    ids = oa_param_ids(names)
    print("OpenAQ param ids (sanitized):", ids)
    # 组装重复 key：parameter_id=2&parameter_id=5
    param_id_pairs = [("parameter_id", str(ids[n.lower()])) for n in names if n.lower() in ids]

    west, south, east, north = bbox
    base_params = [
        ("bbox", f"{west},{south},{east},{north}"),
        ("date_from", t0),
        ("date_to",   t1),
        ("limit",     str(page_limit)),
        ("page",      "1"),
    ]
    # 注意：用列表传参让 requests 按重复 key 编码
    params = base_params + param_id_pairs

    all_rows = []
    for _ in range(max_pages):
        try:
            js = oa_get("/measurements", params)
        except requests.HTTPError as e:
            print(f"[OpenAQ v3] /measurements failed with these params: {params}\n  reason: {e!r}")
            break

        rows = js.get("results", [])
        for m in rows:
            coords = m.get("coordinates") or {}
            all_rows.append({
                "parameter": (m.get("parameter") or "").lower(),
                "value": m.get("value"),
                "unit": m.get("unit"),
                "latitude": coords.get("latitude"),
                "longitude": coords.get("longitude"),
                "location": m.get("location"),
                "country": m.get("country"),
                "city": m.get("city"),
                "date": (m.get("date") or {}).get("utc") or m.get("date"),
            })

        meta = js.get("meta", {}) or {}
        found = int(meta.get("found", 0))
        page  = int(meta.get("page", int([v for k,v in params if k=="page"][0])))
        limit = int(meta.get("limit", int([v for k,v in params if k=="limit"][0])))
        if page * limit >= found or not rows:
            break
        # 翻页：把 params 里 page 替换为下一页
        params = [(k, (str(page+1) if k=="page" else v)) for k,v in params]

    if not all_rows:
        return pd.DataFrame(columns=["parameter","value","unit",
                                     "latitude","longitude","location",
                                     "country","city","date"])
    df = pd.DataFrame(all_rows).dropna(subset=["latitude","longitude"])
    df = df[df["parameter"].isin([n.lower() for n in names])]
    return df

print("Fetching OpenAQ v3…")
try:
    openaq_df = fetch_openaq_v3_measurements(LA_BBOX, T0, T1, names=("pm25","no2"))
    print("OpenAQ v3 rows:", len(openaq_df))
except Exception as e:
    print("[OpenAQ v3] unexpected error:", repr(e))
    openaq_df = pd.DataFrame(columns=["parameter","value","unit",
                                      "latitude","longitude","location",
                                      "country","city","date"])

# ======================================================================
#                        TEMPO（earthaccess）
# ======================================================================
def ea_search_tempo(bbox, t0, t1):
    """按短名逐一搜索（NO₂ & NRT），注意 bounding_box/temporal 传法"""
    try:
        # ~/.netrc 如果不存在，搜索仍可运行，下载可能失败
        earthaccess.login(strategy="netrc")
    except Exception:
        pass

    west, south, east, north = bbox
    short_names = ["TEMPO_L2_NO2_NRT", "TEMPO_L2_NO2", "TEMPO_L2_HCHO", "TEMPO_L2_AI"]

    for sn in short_names:
        try:
            q = (earthaccess.DataGranules()
                 .short_name(sn)
                 .bounding_box(west, south, east, north)   # 4 个独立参数
                 .temporal(t0, t1))                        # 两个独立参数
            rs = q.get()
            if rs:
                print(f"Found {len(rs)} granules for {sn}")
                return rs
        except Exception as e:
            print(f"search error for {sn}:", repr(e))
    return []

def ea_download_first(granules, outdir="data/tempo"):
    if not granules:
        return None
    try:
        files = earthaccess.download(granules[:1], local_path=outdir)
        if files:
            print("Downloaded:", files[0])
            return files[0]
    except Exception as e:
        print("Download error:", repr(e))
    return None

def xr_open_any(path):
    for eng in ("h5netcdf", "netcdf4", None):
        try:
            return xr.open_dataset(path, engine=eng)
        except Exception:
            pass
    raise RuntimeError("xarray cannot open file with known engines")

def extract_no2_points(ds, bbox, max_points=50000):
    # 简单规则：挑首个名字里含 no2 且维度≥2 的变量
    cand = [v for v in ds.data_vars if "no2" in v.lower() and getattr(ds[v], "ndim", 0) >= 2]
    if not cand:
        print("No obvious NO2 variable; available:", list(ds.data_vars))
        return pd.DataFrame(columns=["lat","lon","no2"])
    var = cand[0]

    # 猜测经纬度变量
    lat_name = next((k for k in ds.variables if k.lower() in ("latitude","lat")), None)
    lon_name = next((k for k in ds.variables if k.lower() in ("longitude","lon")), None)
    if lat_name is None or lon_name is None:
        for k, v in ds.variables.items():
            an = str(getattr(v, "standard_name", "")).lower()
            if an == "latitude":  lat_name = lat_name or k
            if an == "longitude": lon_name = lon_name or k
    if lat_name is None or lon_name is None:
        print("Cannot auto-detect lat/lon; variables:", list(ds.variables))
        return pd.DataFrame(columns=["lat","lon","no2"])

    latv = np.array(ds[lat_name]).astype(float)
    lonv = np.array(ds[lon_name]).astype(float)
    arr  = np.array(ds[var]).astype(float)

    flat = pd.DataFrame({"lat": latv.ravel(), "lon": lonv.ravel(), "no2": arr.ravel()}).dropna()
    # 裁剪到 BBOX
    w, s, e, n = bbox
    flat = flat[(flat["lat"].between(s, n)) & (flat["lon"].between(w, e))]
    if len(flat) > max_points:
        flat = flat.sample(max_points, random_state=42)
    return flat

tempo_points = pd.DataFrame(columns=["lat","lon","no2"])
try:
    granules = ea_search_tempo(LA_BBOX, T0, T1)
    path = ea_download_first(granules)
    if path:
        ds = xr_open_any(path)
        tempo_points = extract_no2_points(ds, LA_BBOX)
        print("TEMPO points:", len(tempo_points))
    else:
        print("No TEMPO granule found for this window.")
except Exception as e:
    print("TEMPO pipeline warning:", repr(e))

# ======================================================================
#                        地图渲染（Folium）
# ======================================================================
m = folium.Map(location=CENTER, zoom_start=8, control_scale=True, tiles="CartoDB positron")

# OpenAQ（PM2.5/NO2）
if not openaq_df.empty:
    for p, color in (("pm25","#C0392B"), ("no2","#1F618D")):
        sub = openaq_df[openaq_df["parameter"]==p].copy()
        for _, r in sub.iterrows():
            folium.CircleMarker(
                location=(float(r["latitude"]), float(r["longitude"])),
                radius=4, color=color, weight=1, fill=True, fill_opacity=0.7,
                popup=f"{p.upper()} {r['value']} {r.get('unit','')} · {r.get('location','')}"
            ).add_to(m)
else:
    folium.Marker(CENTER, tooltip="OpenAQ v3: no rows for this window").add_to(m)

# TEMPO 散点（分位数上色）
def color_scale(v, q=(0.2,0.8), palette=("#2E86C1","#28B463","#F1C40F","#E67E22","#C0392B")):
    lo, hi = np.nanquantile(v, q[0]), np.nanquantile(v, q[1])
    if not np.isfinite(lo) or not np.isfinite(hi) or lo == hi:
        lo, hi = np.nanmin(v), np.nanmax(v)
    bins = np.linspace(lo, hi, num=len(palette))
    def f(x):
        idx = np.digitize([x], bins)[0]-1
        idx = max(0, min(idx, len(palette)-1))
        return palette[idx]
    return f

if not tempo_points.empty:
    cfun = color_scale(tempo_points["no2"].values)
    for _, r in tempo_points.iterrows():
        folium.CircleMarker(
            location=(float(r["lat"]), float(r["lon"])),
            radius=2, color=cfun(r["no2"]), weight=0, fill=True, fill_opacity=0.6
        ).add_to(m)
else:
    folium.Marker(CENTER, tooltip="No recent TEMPO NO2 granule for this window").add_to(m)

out_html = "data/outputs/la_quickstart.html"
m.save(out_html)
print("Map saved ->", out_html)





