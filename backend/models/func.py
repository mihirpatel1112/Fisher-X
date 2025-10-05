import os, json, pickle, numpy as np, pandas as pd
from sklearn.preprocessing import MinMaxScaler

#log transformation features
LOG_CFG = {
    "pm10": {"apply": True,  "shift": 0.0},
    "no":   {"apply": True,  "shift": 1.0},
    "nox":  {"apply": True,  "shift": 1.0},
    "pm25": {"apply": True,  "shift": 0.9},
    "no2":  {"apply": True,  "shift": 1.0},
    "o3":   {"apply": False, "shift": 0.0},
    "so2":  {"apply": False, "shift": 0.0},
    "co":   {"apply": False, "shift": 0.0},
}
#AQI thresholds
breakpoints = {
    "pm25": [(0.0, 12.0, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
             (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 500.4, 301, 500)],
    "pm10": [(0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150),
             (255, 354, 151, 200), (355, 424, 201, 300), (425, 604, 301, 500)],
    "no2": [(0, 53, 0, 50), (54, 100, 51, 100), (101, 360, 101, 150),
            (361, 649, 151, 200), (650, 1249, 201, 300), (1250, 2049, 301, 500)],
    "so2": [(0, 35, 0, 50), (36, 75, 51, 100), (76, 185, 101, 150),
            (186, 304, 151, 200), (305, 604, 201, 300), (605, 1004, 301, 500)],
    "co": [(0.0, 4.4, 0, 50), (4.5, 9.4, 51, 100), (9.5, 12.4, 101, 150),
           (12.5, 15.4, 151, 200), (15.5, 30.4, 201, 300), (30.5, 50.4, 301, 500)],
    "o3": [(0.0, 0.054, 0, 50), (0.055, 0.070, 51, 100), (0.071, 0.085, 101, 150),
           (0.086, 0.105, 151, 200), (0.106, 0.200, 201, 300)]
}

#helper functions==========================================================
def _log_if_needed(param, x):
    cfg = LOG_CFG.get(param.lower(), {"apply": False, "shift": 0.0})
    return float(np.log(float(x) + cfg["shift"])) if cfg["apply"] else float(x)

def load_artifacts(model_dir="models/trained_models"):
    meta = json.loads(open(os.path.join(model_dir, "metadata.json")).read())
    models = {p: pickle.load(open(os.path.join(model_dir, f"{p}_model.pkl"), "rb"))
              for p in meta.keys()}
    scalers = pickle.load(open(os.path.join(model_dir, "scalers.pkl"), "rb"))
    return models, meta, scalers

def build_feature_row_for(param, raw_tminus1: dict, meta, scalers) -> pd.DataFrame:
    """
    Build the EXACT 1×N DataFrame row matching meta[param]['feature_cols'].
    raw_tminus1 must contain t-1 raw values: temp, dwpt, rhum, prcp, wdir, wspd, coco, and all pollutants.
    """
    feats_needed = meta[param]["feature_cols"]
    sc_info = scalers[param]                     # which unscaled features were used to fit MinMax for THIS param
    sc = sc_info["scaler"]
    base_names = sc_info["feature_names"]        # e.g., ['temp','dwpt','rhum','no2_log', 'pm25_log', ...]

    # 1) create a one-row DF of those base names (compute *_log from raw pollutant if needed)
    base_vals = {}
    for name in base_names:
        if name.endswith("_log"):
            pol = name[:-4]
            if pol not in raw_tminus1:
                raise KeyError(f"Missing raw input for '{pol}' to compute '{name}'")
            base_vals[name] = _log_if_needed(pol, raw_tminus1[pol])
        else:
            if name not in raw_tminus1:
                raise KeyError(f"Missing raw input for '{name}'")
            base_vals[name] = float(raw_tminus1[name])
    base_df = pd.DataFrame([base_vals])

    # 2) scale them and rename to *_scaled_lag1
    if base_df.shape[1] > 0:
        scaled = sc.transform(base_df[base_names])
        scaled_cols = [f"{c}_scaled_lag1" for c in base_names]
        scaled_df = pd.DataFrame(scaled, columns=scaled_cols, index=base_df.index)
    else:
        scaled_df = pd.DataFrame(index=base_df.index)

    # 3) add the needed non-scaled lag features (pollutants/weather that appear as *_lag1 without "scaled")
    extra = {}
    for col in feats_needed:
        if col.endswith("_lag1") and ("_scaled_" not in col):    
            if col.endswith("_log_lag1"):
                pol = col.replace("_log_lag1", "")
                if pol not in raw_tminus1:
                    raise KeyError(f"Missing raw input for '{pol}' to compute '{col}'")
                extra[col] = _log_if_needed(pol, raw_tminus1[pol])
            else:
                pol = col.replace("_lag1", "")
                if pol not in raw_tminus1:
                    raise KeyError(f"Missing raw input for '{pol}' to fill '{col}'")
                extra[col] = float(raw_tminus1[pol])
    extra_df = pd.DataFrame([extra], index=base_df.index)

    # 4) assemble and order exactly like feature_cols
    X = pd.concat([scaled_df, extra_df], axis=1)
    # fill any missing expected columns with NaN (better to provide all inputs ideally)
    for c in feats_needed:
        if c not in X.columns:
            X[c] = np.nan
    return X[feats_needed]

def predict_param(param, raw_tminus1, models, meta, scalers):
    X = build_feature_row_for(param, raw_tminus1, meta, scalers)
    yhat = float(models[param].predict(X)[0])
    if meta[param].get("is_log_transformed", False):
        # invert log using the target param’s shift
        yhat = float(np.exp(yhat) - LOG_CFG[param]["shift"])
    return yhat

def calculate_individual_aqi(concentration, pollutant):
    for conc_low, conc_high, aqi_low, aqi_high in breakpoints[pollutant]:
        if conc_low <= concentration <= conc_high:
            aqi = ((aqi_high - aqi_low) / (conc_high - conc_low)) * (concentration - conc_low) + aqi_low
            return round(aqi)
    return None

def calculate_overall_aqi(pollutant_values):
    aqi_values = []
    for pollutant, value in pollutant_values.items():
        if pollutant in breakpoints:
            aqi = calculate_individual_aqi(value, pollutant)
            if aqi is not None:
                aqi_values.append(aqi)
    if aqi_values:
        return max(aqi_values)
    else:
        return None
#===============================================================

def start_prediction(raw):
    params = ['co', 'no', 'no2', 'nox', 'o3', 'pm10', 'pm25', 'so2']
    models, meta, scalers = load_artifacts("trained_models")
    predictions={}
    for param in params:
        pred = predict_param(param, raw, models, meta, scalers)
        predictions[param] = pred
    dominant_aqi = calculate_overall_aqi(predictions)
    predictions["aqi"] = dominant_aqi
    return predictions



# raw = {
#     # t-1 weather (unscaled)
#     "temp": 30.2, "dwpt": 24.0, "rhum": 70, "prcp": 0.0,
#     "wdir": 210,  "wspd": 3.1,  "coco": 3,
#     # t-1 pollutants (unlogged, original units)
#     "co": 0.25, "no": 4.0, "no2": 6.0, "nox": 8.0,
#     "o3": 0.031, "pm10": 42.0, "pm25": 18.5, "so2": 0.0002
# }

# start_prediction(raw)





