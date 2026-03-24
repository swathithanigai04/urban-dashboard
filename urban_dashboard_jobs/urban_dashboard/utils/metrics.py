import pandas as pd
import numpy as np

# ── Load dataset ─────────────────────────────────────────────────────────────
def load_data():
    df = pd.read_csv("data/cities.csv")
    df.columns = df.columns.str.strip()
    return df

# ── Derive extra metrics from base columns ───────────────────────────────────
def compute_derived_metrics(row):
    """
    From the 8 base columns, derive the richer set of indicators
    shown on Page 2. All formulas are physically motivated.
    """
    ndvi  = float(row["NDVI"])
    ndbi  = float(row["NDBI"])
    rain  = float(row["Rainfall"])
    temp  = float(row["Temperature"])
    aqi   = float(row["AQI"])
    lat   = float(row["latitude"])
    lon   = float(row["longitude"])
    liv   = float(row["Livability"])

    # Green cover loss proxy  (lower NDVI → higher loss)
    green_cover_loss = round(max(0, (0.5 - ndvi) / 0.5 * 100), 1)

    # Urbanization score  (NDBI drives this; normalised 0-100)
    # NDBI range in dataset: roughly -0.15 to +0.15
    urbanization_score = round(min(100, max(0, (ndbi + 0.15) / 0.30 * 100)), 1)

    # Heat stress index  (temp + AQI penalty)
    heat_stress = round(min(10, (temp - 20) / 2 + aqi * 0.5), 2)

    # Rainfall anomaly  (deviation from "comfortable" 1200 mm baseline)
    rainfall_anomaly = round((rain - 1200) / 1200 * 100, 1)   # % above/below

    # Flood risk index  (high rain + low NDVI + high urban = higher risk)
    flood_risk_index = round(
        min(10, (rain / 500) * 0.4 + (1 - ndvi) * 3 + urbanization_score / 100 * 3), 2
    )

    # Climate resilience score  (higher NDVI + moderate rain + low urban)
    climate_resilience = round(
        max(0, min(100,
            ndvi * 40 + (1 - urbanization_score / 100) * 30
            + min(1, rain / 1500) * 20 + (1 - aqi / 5) * 10
        )), 1
    )

    # Land surface temp  (proxy; actual LST ≈ air temp + NDBI contribution)
    land_surface_temp = round(temp + ndbi * 15, 2)

    return {
        "coordinates":         {"lat": lat, "lon": lon},
        "aqi":                  aqi,
        "ndvi":                 round(ndvi, 4),
        "ndbi":                 round(ndbi, 4),
        "land_surface_temp":    land_surface_temp,
        "rainfall":             round(rain, 1),
        "green_cover_loss":     green_cover_loss,
        "urbanization_score":   urbanization_score,
        "heat_stress":          heat_stress,
        "rainfall_anomaly":     rainfall_anomaly,
        "flood_risk_index":     flood_risk_index,
        "climate_resilience_score": climate_resilience,
        "livability":           round(liv, 2),
        "temperature":          round(temp, 2),
    }

# ── Grade a metric value ─────────────────────────────────────────────────────
def grade_metric(name, value):
    """Return (letter, color_class) for a metric."""
    thresholds = {
        # (best→worst breakpoints for A/B/C/D/F)
        "ndvi":                    ([0.5, 0.35, 0.2, 0.1],  "higher_better"),
        "ndbi":                    ([-0.05, 0.0, 0.05, 0.1], "lower_better"),
        "aqi":                     ([1.5, 2.5, 3.5, 4.5],   "lower_better"),
        "land_surface_temp":       ([28, 32, 36, 40],        "lower_better"),
        "rainfall":                ([800, 500, 300, 150],    "higher_better"),
        "green_cover_loss":        ([10, 25, 40, 60],        "lower_better"),
        "urbanization_score":      ([20, 40, 60, 80],        "lower_better"),
        "heat_stress":             ([2, 4, 6, 8],            "lower_better"),
        "flood_risk_index":        ([2, 4, 6, 8],            "lower_better"),
        "climate_resilience_score":([70, 50, 35, 20],        "higher_better"),
        "livability":              ([60, 45, 30, 15],        "higher_better"),
    }
    if name not in thresholds:
        return "N/A", "grade-C"

    breaks, direction = thresholds[name]
    if direction == "higher_better":
        if value >= breaks[0]: letter = "A"
        elif value >= breaks[1]: letter = "B"
        elif value >= breaks[2]: letter = "C"
        elif value >= breaks[3]: letter = "D"
        else: letter = "F"
    else:
        if value <= breaks[0]: letter = "A"
        elif value <= breaks[1]: letter = "B"
        elif value <= breaks[2]: letter = "C"
        elif value <= breaks[3]: letter = "D"
        else: letter = "F"

    css = {"A": "grade-A", "B": "grade-B", "C": "grade-C",
           "D": "grade-D", "F": "grade-F"}[letter]
    return letter, css

# ── Overall city health score (0-100) ───────────────────────────────────────
def city_health_score(metrics):
    weights = {
        "ndvi": 0.15,
        "aqi": 0.20,          # inverted
        "climate_resilience_score": 0.20,
        "livability": 0.25,
        "heat_stress": 0.10,  # inverted
        "flood_risk_index": 0.10,  # inverted
    }
    score = 0
    score += metrics["ndvi"] * 100 * weights["ndvi"]
    score += (1 - (metrics["aqi"] - 1) / 4) * 100 * weights["aqi"]
    score += metrics["climate_resilience_score"] * weights["climate_resilience_score"]
    score += metrics["livability"] * weights["livability"]
    score += (1 - metrics["heat_stress"] / 10) * 100 * weights["heat_stress"]
    score += (1 - metrics["flood_risk_index"] / 10) * 100 * weights["flood_risk_index"]
    return round(min(100, max(0, score)), 1)

# ── Geocode a city name (no API key needed via nominatim) ────────────────────
def geocode_city(city_name):
    """
    First check if city is in our dataset.
    Then fall back to Nominatim (OpenStreetMap, free, no key).
    Returns dict {lat, lon, display_name} or None.
    """
    df = load_data()
    match = df[df["city"].str.lower() == city_name.strip().lower()]
    if not match.empty:
        row = match.iloc[0]
        return {
            "lat": float(row["latitude"]),
            "lon": float(row["longitude"]),
            "display_name": row["city"],
            "in_dataset": True,
        }

    # Nominatim fallback
    try:
        from geopy.geocoders import Nominatim
        from geopy.exc import GeocoderTimedOut
        geolocator = Nominatim(user_agent="urban_intelligence_dashboard")
        location = geolocator.geocode(city_name, timeout=10)
        if location:
            return {
                "lat": location.latitude,
                "lon": location.longitude,
                "display_name": location.address.split(",")[0],
                "in_dataset": False,
            }
    except Exception:
        pass
    return None

# ── AQI label ────────────────────────────────────────────────────────────────
AQI_LABELS = {
    1: ("Good", "#4ade80"),
    2: ("Moderate", "#86efac"),
    3: ("Unhealthy (sensitive)", "#fbbf24"),
    4: ("Unhealthy", "#fb923c"),
    5: ("Very Unhealthy", "#f87171"),
}

def aqi_label(val):
    k = min(5, max(1, int(round(val))))
    return AQI_LABELS.get(k, ("Unknown", "#ffffff"))
