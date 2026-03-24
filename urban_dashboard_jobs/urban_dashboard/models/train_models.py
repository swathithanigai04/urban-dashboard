"""
Train and save all ML models from the 273-city dataset.
Run this ONCE: python models/train_models.py
Models are saved to models/ as .pkl files.
"""
import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, accuracy_score
import xgboost as xgb

# ── Load data ─────────────────────────────────────────────────────────────────
df = pd.read_csv("data/cities.csv")
FEATURES = ["NDVI", "NDBI", "Rainfall", "Temperature", "AQI"]

X = df[FEATURES].values
y_livability   = df["Livability"].values
y_aqi          = df["AQI"].values.astype(int)

# ── Urbanization label (Low / Medium / High) from NDBI ───────────────────────
def urb_label(ndbi):
    if ndbi > 0.0:  return 2   # High
    if ndbi > -0.1: return 1   # Medium
    return 0                   # Low

y_urban = np.array([urb_label(v) for v in df["NDBI"]])

# ── Train / test split ────────────────────────────────────────────────────────
X_tr, X_te, yl_tr, yl_te = train_test_split(X, y_livability, test_size=0.2, random_state=42)
_, __,  ya_tr, ya_te      = train_test_split(X, y_aqi,        test_size=0.2, random_state=42)
_, __,  yu_tr, yu_te      = train_test_split(X, y_urban,      test_size=0.2, random_state=42)

# ── Scaler ────────────────────────────────────────────────────────────────────
scaler = StandardScaler()
X_tr_s = scaler.fit_transform(X_tr)
X_te_s  = scaler.transform(X_te)

# ── 1. Livability regressor (XGBoost) ─────────────────────────────────────────
xgb_model = xgb.XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.05,
                              random_state=42, verbosity=0)
xgb_model.fit(X_tr_s, yl_tr)
print(f"Livability MAE: {mean_absolute_error(yl_te, xgb_model.predict(X_te_s)):.2f}")

# ── 2. AQI classifier (Random Forest) ─────────────────────────────────────────
rf_aqi = RandomForestClassifier(n_estimators=150, max_depth=6, random_state=42)
rf_aqi.fit(X_tr_s, ya_tr)
print(f"AQI Accuracy:   {accuracy_score(ya_te, rf_aqi.predict(X_te_s)):.2%}")

# ── 3. Urbanization classifier (Random Forest) ────────────────────────────────
rf_urb = RandomForestClassifier(n_estimators=150, max_depth=5, random_state=42)
rf_urb.fit(X_tr_s, yu_tr)
print(f"Urban Accuracy: {accuracy_score(yu_te, rf_urb.predict(X_te_s)):.2%}")

# ── Save all ──────────────────────────────────────────────────────────────────
with open("models/xgb_livability.pkl", "wb") as f: pickle.dump(xgb_model, f)
with open("models/rf_aqi.pkl",        "wb") as f: pickle.dump(rf_aqi,     f)
with open("models/rf_urban.pkl",      "wb") as f: pickle.dump(rf_urb,     f)
with open("models/scaler.pkl",        "wb") as f: pickle.dump(scaler,     f)

print("✅ All models saved to models/")
