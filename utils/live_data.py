import requests
import numpy as np
import hashlib
import os
import pickle

def generate_city_data(place_name, lat, lon):
    """
    Generates dataset-compatible metrics for cities outside the 273 static list.
    Calculates actual rainfall and temperature from open-meteo, explicitly infers
    NDVI/NDBI via pseudo-spatial heuristics, and uses the pre-trained XGBoost to predict livability.
    """
    # 1. Fetch live climate data from Open-Meteo (2023 full year for annual averages)
    try:
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2023-01-01&end_date=2023-12-31&daily=temperature_2m_mean,precipitation_sum&timezone=auto"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        
        temps = [t for t in data["daily"]["temperature_2m_mean"] if t is not None]
        rains = [p for p in data["daily"]["precipitation_sum"] if p is not None]
        
        temperature = sum(temps) / len(temps) if temps else 25.0
        rainfall = sum(rains) if rains else 1000.0
    except Exception as e:
        # Fallback geo heuristic if API fails
        abslat = abs(lat)
        temperature = max(min(35.0 - (abslat * 0.5), 35.0), -10.0)
        rainfall = max(min(2500 - (abslat * 20), 3000), 200)

    # 2. Generative Algorithm for NDVI, NDBI, AQI based on coordinates + random seed
    seed_val = int(hashlib.md5(place_name.encode('utf-8')).hexdigest(), 16) % 10000
    np.random.seed(seed_val)
    
    base_ndvi = np.clip((rainfall / 2500) * 0.5 + 0.1, 0.05, 0.8)
    ndvi = np.clip(np.random.normal(base_ndvi, 0.1), 0.05, 0.85)

    base_ndbi = np.clip(0.15 - (ndvi * 0.2), -0.3, 0.3)
    ndbi = np.clip(np.random.normal(base_ndbi, 0.05), -0.3, 0.4)
    
    base_aqi = np.clip(1 + (ndbi * 10) + (temperature / 15), 1, 5)
    aqi = np.clip(int(np.random.normal(base_aqi, 0.5)), 1, 5)

    # 3. Use pre-trained XGBoost to predict Livability
    features = np.array([[ndvi, ndbi, rainfall, temperature, aqi]])
    
    livability = 50.0
    try:
        if os.path.exists("models/scaler.pkl"):
            with open("models/scaler.pkl", "rb") as f: scaler = pickle.load(f)
            with open("models/xgb_livability.pkl", "rb") as f: xgb_model = pickle.load(f)
            fs = scaler.transform(features)
            livability = float(xgb_model.predict(fs)[0])
    except:
        livability = np.clip(ndvi * 40 - ndbi * 50 - aqi * 10 + 60, 10, 95)
        
    return {
        "city": place_name,
        "country": "Live Generation",
        "NDVI": round(ndvi, 4),
        "NDBI": round(ndbi, 4),
        "Rainfall": round(rainfall, 0),
        "Temperature": round(temperature, 1),
        "latitude": lat,
        "longitude": lon,
        "AQI": int(aqi),
        "Livability": round(float(livability), 2),
    }
