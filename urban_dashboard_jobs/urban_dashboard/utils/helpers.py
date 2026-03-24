"""
Shared utility functions used across all pages.
"""
import math
import pandas as pd
import numpy as np

# ── Load dataset once ────────────────────────────────────────────────────────
def load_data():
    df = pd.read_csv("data/cities.csv")
    df.columns = [c.strip() for c in df.columns]
    return df

# ── Derived / computed metrics ───────────────────────────────────────────────
def compute_extended_metrics(row):
    """
    Given a dataset row (or a dict with NDVI, NDBI, Rainfall, Temperature, AQI, Livability),
    compute extra metrics that are not in the CSV but shown on the dashboard.
    All formulas are heuristic / interpretable for a student project.
    """
    ndvi        = float(row["NDVI"])
    ndbi        = float(row["NDBI"])
    rainfall    = float(row["Rainfall"])
    temp        = float(row["Temperature"])
    aqi         = float(row["AQI"])
    livability  = float(row["Livability"])

    # Green cover (0–100 %)  — derived from NDVI (0 = no vegetation, 1 = dense)
    green_cover = round(ndvi * 100, 1)

    # Urbanization score (0–100) — higher NDBI → more built-up
    urbanization_score = round(np.clip((ndbi + 0.3) / 0.45 * 100, 0, 100), 1)

    # Heat stress index (0–10) — combines temp and AQI
    heat_stress = round(np.clip((temp - 20) / 25 * 6 + aqi / 5 * 4, 0, 10), 2)

    # Rainfall anomaly (deviation from 1028mm global mean in dataset)
    rainfall_anomaly = round(rainfall - 1028.0, 1)

    # Flood risk index (0–10) — high rainfall + low NDBI (less absorption)
    flood_risk = round(np.clip(
        (rainfall / 3119) * 7 + (1 - (ndbi + 0.3) / 0.43) * 3, 0, 10
    ), 2)

    # Climate resilience (0–100) — high NDVI + low temp + good rainfall
    climate_resilience = round(np.clip(
        ndvi * 40 + (1 - temp / 45) * 30 + np.clip(rainfall / 3119, 0, 1) * 30, 0, 100
    ), 1)

    # Land Surface Temp estimate (offset from air temp based on NDBI)
    land_surface_temp = round(temp + ndbi * 15 + 2.5, 2)

    # Green cover loss (positive = loss vs global average NDVI of 0.28)
    green_cover_loss = round((0.28 - ndvi) * 100, 1)

    return {
        "NDVI":                 ndvi,
        "NDBI":                 ndbi,
        "Rainfall":             rainfall,
        "Temperature":          temp,
        "AQI":                  int(aqi),
        "Livability":           livability,
        "Green Cover (%)":      green_cover,
        "Urbanization Score":   urbanization_score,
        "Heat Stress (0-10)":   heat_stress,
        "Rainfall Anomaly (mm)":rainfall_anomaly,
        "Flood Risk (0-10)":    flood_risk,
        "Climate Resilience":   climate_resilience,
        "Land Surface Temp":    land_surface_temp,
        "Green Cover Loss (%)": green_cover_loss,
    }

# ── Grade system (A–F) ────────────────────────────────────────────────────────
def grade(value, metric):
    """Return letter grade + colour for a metric value."""
    thresholds = {
        # (value, grade, hex_colour)  — evaluated top-down, first match wins
        "Livability": [
            (65, "A", "#4CAF50"), (50, "B", "#8BC34A"),
            (35, "C", "#FFC107"), (20, "D", "#FF5722"), (0, "F", "#F44336")
        ],
        "NDVI": [
            (0.6, "A", "#4CAF50"), (0.4, "B", "#8BC34A"),
            (0.25, "C", "#FFC107"), (0.1, "D", "#FF5722"), (0, "F", "#F44336")
        ],
        "AQI": [  # lower AQI = better
            (1.5, "A", "#4CAF50"), (2.5, "B", "#8BC34A"),
            (3.5, "C", "#FFC107"), (4.5, "D", "#FF5722"), (6, "F", "#F44336")
        ],
        "Climate Resilience": [
            (60, "A", "#4CAF50"), (45, "B", "#8BC34A"),
            (30, "C", "#FFC107"), (15, "D", "#FF5722"), (0, "F", "#F44336")
        ],
    }
    rules = thresholds.get(metric, [])
    if metric == "AQI":  # lower is better
        for threshold, g, colour in rules:
            if value <= threshold:
                return g, colour
    else:
        for threshold, g, colour in rules:
            if value >= threshold:
                return g, colour
    return "F", "#F44336"

# ── AQI label ────────────────────────────────────────────────────────────────
AQI_LABELS = {1: "Good", 2: "Moderate", 3: "Unhealthy (Sensitive)",
              4: "Unhealthy", 5: "Very Unhealthy"}
AQI_COLORS = {1: "#4CAF50", 2: "#CDDC39", 3: "#FFC107", 4: "#FF5722", 5: "#F44336"}

def aqi_label(val):
    v = int(round(val))
    return AQI_LABELS.get(v, "Unknown"), AQI_COLORS.get(v, "#999")
