# 🛰️ Urban Intelligence Dashboard
**Data Science Major Project**

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Train the ML models (run once)
```bash
cd urban_dashboard
python models/train_models.py
```

### 3. Add API keys
Edit `.streamlit/secrets.toml`:
- `GOOGLE_MAPS_KEY` → https://console.cloud.google.com (for satellite images)
- Gemini key is entered directly in the Page 4 chat UI

### 4. Run the app
```bash
streamlit run app.py
```

## Project Structure
```
urban_dashboard/
├── app.py                    ← Main entry point (sidebar + routing)
├── data/
│   └── cities.csv            ← 273-city dataset
├── models/
│   ├── train_models.py       ← Train & save ML models (run once)
│   ├── xgb_livability.pkl    ← XGBoost livability regressor
│   ├── rf_aqi.pkl            ← Random Forest AQI classifier
│   ├── rf_urban.pkl          ← Random Forest urbanization classifier
│   └── scaler.pkl            ← StandardScaler
├── pages/
│   ├── page1_search.py       ← Place input + geocoding + map preview
│   ├── page2_analysis.py     ← Environmental metrics + interactive map
│   ├── page3_predictions.py  ← UNet sim + forecasts + what-if + report
│   └── page4_chat.py         ← Gemini AI context-aware chat
└── utils/
    └── helpers.py            ← Shared utilities, metric computation, grades
```

## Pages
| Page | Description |
|------|-------------|
| 🔍 Place Search | Type any city → get coordinates + satellite map |
| 📊 Analysis | All 14 metrics + interactive map + city comparison |
| 🤖 Predictions | UNet land cover change + 11-year forecast + what-if |
| 💬 AI Assistant | Gemini chat with full city context injected |

## Models Used
- **XGBoost** — Livability score regression
- **Random Forest** — AQI classification + Urbanization classification
- **UNet Simulation** — Land cover change from NDVI/NDBI trends
