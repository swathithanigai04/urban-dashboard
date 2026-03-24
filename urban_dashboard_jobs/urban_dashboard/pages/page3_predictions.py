"""
Page 3 — Model Predictions
• UNet-style land cover change simulation
• XGBoost livability forecast
• RF AQI & urbanization prediction
• What-if sliders
• Auto report card
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import pickle, os
from utils.helpers import load_data, compute_extended_metrics, grade

FEATURES = ["NDVI", "NDBI", "Rainfall", "Temperature", "AQI"]
URBAN_LABELS = {0: "Low", 1: "Medium", 2: "High"}
URBAN_COLORS = {0: "#4CAF50", 1: "#FFC107", 2: "#F44336"}

# ── Load (or lazy-train) models ───────────────────────────────────────────────
@st.cache_resource
def load_models():
    paths = [
        "models/xgb_livability.pkl",
        "models/rf_aqi.pkl",
        "models/rf_urban.pkl",
        "models/scaler.pkl"
    ]
    if not all(os.path.exists(p) for p in paths):
        # Auto-train if pkl files not present
        import subprocess, sys
        subprocess.run([sys.executable, "models/train_models.py"], check=True)

    with open("models/xgb_livability.pkl", "rb") as f: xgb_m   = pickle.load(f)
    with open("models/rf_aqi.pkl",         "rb") as f: rf_aqi  = pickle.load(f)
    with open("models/rf_urban.pkl",       "rb") as f: rf_urb  = pickle.load(f)
    with open("models/scaler.pkl",         "rb") as f: scaler  = pickle.load(f)
    return xgb_m, rf_aqi, rf_urb, scaler

def predict_all(values_dict, xgb_m, rf_aqi, rf_urb, scaler):
    x = np.array([[values_dict[f] for f in FEATURES]])
    xs = scaler.transform(x)
    livability = float(xgb_m.predict(xs)[0])
    aqi_pred   = int(rf_aqi.predict(xs)[0])
    urb_pred   = int(rf_urb.predict(xs)[0])
    return livability, aqi_pred, urb_pred

# ── UNet simulation ───────────────────────────────────────────────────────────
def simulate_unet_change(ndvi_old, ndvi_new, ndbi_old, ndbi_new, size=64):
    """
    Simulate a UNet output: returns two segmentation masks (past, current)
    and a difference map. Each pixel is classified as:
      0 = Built-up (NDBI dominated)
      1 = Vegetation (NDVI dominated)
      2 = Bare soil / other
      3 = Water (low NDVI, low NDBI)
    """
    np.random.seed(42)

    def make_mask(ndvi, ndbi, size):
        mask = np.zeros((size, size), dtype=int)
        for i in range(size):
            for j in range(size):
                r = np.random.random()
                veg_prob   = np.clip(ndvi * 1.5 + np.random.normal(0, 0.15), 0, 1)
                built_prob = np.clip((ndbi + 0.3) * 2.2 + np.random.normal(0, 0.1), 0, 1)
                water_prob = 0.05 + np.random.random() * 0.05

                if r < veg_prob * 0.6:     mask[i, j] = 1  # vegetation
                elif r < built_prob * 0.5: mask[i, j] = 0  # built-up
                elif r < water_prob:       mask[i, j] = 3  # water
                else:                      mask[i, j] = 2  # bare soil
        return mask

    past    = make_mask(ndvi_old, ndbi_old, size)
    current = make_mask(ndvi_new, ndbi_new, size)
    diff    = (current != past).astype(int) * (current + 1)
    return past, current, diff

def mask_to_rgb(mask):
    COLORS = {
        0: [80, 80, 80],     # Built-up: gray
        1: [56, 142, 60],    # Vegetation: green
        2: [166, 124, 82],   # Bare soil: brown
        3: [33, 150, 243],   # Water: blue
    }
    rgb = np.zeros((*mask.shape, 3), dtype=np.uint8)
    for k, c in COLORS.items():
        rgb[mask == k] = c
    return rgb

# ── Forecast chart ────────────────────────────────────────────────────────────
def forecast_chart(current_livability, city_name, xgb_m, rf_aqi, rf_urb, scaler, base_vals):
    years = list(range(2024, 2036))
    livability_vals = []
    ndvi_now = base_vals["NDVI"]
    temp_now = base_vals["Temperature"]

    for yr in years:
        t = yr - 2024
        sim = {
            "NDVI":        max(0.01, ndvi_now - 0.008 * t),
            "NDBI":        min(0.13, base_vals["NDBI"] + 0.005 * t),
            "Rainfall":    base_vals["Rainfall"] * (1 - 0.01 * t),
            "Temperature": temp_now + 0.06 * t,
            "AQI":         min(5, base_vals["AQI"] + 0.05 * t),
        }
        lv, _, _ = predict_all(sim, xgb_m, rf_aqi, rf_urb, scaler)
        livability_vals.append(round(lv, 2))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=livability_vals, mode="lines+markers",
        line=dict(color="#4CAF50", width=2.5),
        marker=dict(size=7, color="#4CAF50"),
        fill="tozeroy", fillcolor="rgba(76,175,80,0.12)",
        name="Projected livability"
    ))
    fig.add_hline(y=current_livability, line_dash="dash",
                  line_color="#FFC107", annotation_text="Current",
                  annotation_font_color="#FFC107")
    fig.update_layout(
        title=f"Livability Forecast (2024–2035) — {city_name}",
        paper_bgcolor="#0f1117", plot_bgcolor="#111827",
        font=dict(color="white"),
        xaxis=dict(title="Year", gridcolor="#333"),
        yaxis=dict(title="Livability Score", gridcolor="#333"),
        height=320, margin=dict(l=20, r=20, t=45, b=20)
    )
    return fig, livability_vals

# ── Feature importance chart ──────────────────────────────────────────────────
def importance_chart(xgb_m):
    fi = xgb_m.feature_importances_
    fig = px.bar(
        x=FEATURES, y=fi, color=fi,
        color_continuous_scale="Greens",
        title="Feature Importance — Livability Model"
    )
    fig.update_layout(
        paper_bgcolor="#0f1117", plot_bgcolor="#111827",
        font=dict(color="white"), showlegend=False,
        height=280, margin=dict(l=20, r=20, t=45, b=20),
        coloraxis_showscale=False
    )
    return fig

# ── Main render ───────────────────────────────────────────────────────────────
def render():
    st.title("🤖 Model Predictions")

    df = load_data()

    with st.spinner("Loading AI models..."):
        xgb_m, rf_aqi, rf_urb, scaler = load_models()

    cities_list = sorted(df["city"].tolist())
    session_city = st.session_state.get("place_name", "Chennai")
    default_idx  = next(
        (i for i, c in enumerate(cities_list) if session_city.lower() in c.lower()), 0
    )
    city = st.selectbox("Select city", cities_list, index=default_idx)
    row  = df[df["city"] == city].iloc[0]
    m    = compute_extended_metrics(row)

    # ── TABS ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Land Cover Change", "📉 Livability Forecast",
        "🎛️ What-If Simulator", "📋 Report Card"
    ])

    # ─── Tab 1: UNet simulation ───────────────────────────────────────────────
    with tab1:
        st.subheader("🛰️ UNet Land Cover Change Simulation")
        st.markdown(
            "Simulates how land cover categories (vegetation, built-up, water, bare soil) "
            "have changed over a 10-year period using NDVI/NDBI trends."
        )

        col_a, col_b = st.columns(2)
        with col_a:
            ndvi_old = st.slider("NDVI — 10 years ago", 0.01, 0.85,
                                 min(0.85, float(row["NDVI"]) + 0.12), 0.01)
            ndbi_old = st.slider("NDBI — 10 years ago", -0.29, 0.13,
                                 max(-0.29, float(row["NDBI"]) - 0.06), 0.01)
        with col_b:
            ndvi_new = st.slider("NDVI — Current", 0.01, 0.85, float(row["NDVI"]), 0.01)
            ndbi_new = st.slider("NDBI — Current", -0.29, 0.13, float(row["NDBI"]), 0.01)

        past, current, diff = simulate_unet_change(ndvi_old, ndvi_new, ndbi_old, ndbi_new)
        past_rgb    = mask_to_rgb(past)
        current_rgb = mask_to_rgb(current)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Past (10 years ago)**")
            st.image(past_rgb, caption="Segmented land cover", use_column_width=True)
        with c2:
            st.markdown("**Current**")
            st.image(current_rgb, caption="Segmented land cover", use_column_width=True)
        with c3:
            st.markdown("**Change Map**")
            diff_display = (diff * 80).astype(np.uint8)
            st.image(diff_display, caption="Changed pixels", use_column_width=True)

        # Stats
        total = past.size
        def pct(mask, cls): return round((mask == cls).sum() / total * 100, 1)
        stat_df = pd.DataFrame({
            "Category":    ["Built-up", "Vegetation", "Bare soil", "Water"],
            "Past (%)":    [pct(past,c)    for c in [0,1,2,3]],
            "Current (%)": [pct(current,c) for c in [0,1,2,3]],
        })
        stat_df["Change"] = stat_df["Current (%)"] - stat_df["Past (%)"]
        st.dataframe(stat_df, use_container_width=True, hide_index=True)

        changed_pct = round((diff > 0).sum() / total * 100, 1)
        st.info(f"🔄 **{changed_pct}%** of the city's land cover has changed over 10 years.")

    # ─── Tab 2: Livability Forecast ───────────────────────────────────────────
    with tab2:
        st.subheader("📉 Livability & Environment Forecast (2024–2035)")
        st.markdown(
            "Projecting how livability score changes over the next 11 years "
            "assuming current urbanization trends continue."
        )
        base_vals = {f: float(row[f]) for f in FEATURES}
        fig_fc, lv_vals = forecast_chart(
            m["Livability"], city, xgb_m, rf_aqi, rf_urb, scaler, base_vals
        )
        st.plotly_chart(fig_fc, use_container_width=True)

        trend = lv_vals[-1] - lv_vals[0]
        if trend < -5:
            st.warning(f"⚠️ Livability is projected to **decrease by {abs(trend):.1f} points** "
                       f"by 2035 if current trends continue.")
        elif trend > 5:
            st.success(f"✅ Livability is projected to **improve by {trend:.1f} points** by 2035.")
        else:
            st.info("ℹ️ Livability is projected to remain relatively stable through 2035.")

        st.markdown("---")
        st.plotly_chart(importance_chart(xgb_m), use_container_width=True)
        st.caption("Higher importance = this feature has more influence on the livability prediction.")

    # ─── Tab 3: What-If Simulator ─────────────────────────────────────────────
    with tab3:
        st.subheader("🎛️ What-If Simulator")
        st.markdown("Adjust environmental parameters and see how the predicted livability changes.")

        s1, s2 = st.columns(2)
        with s1:
            wi_ndvi  = st.slider("NDVI",        0.01, 0.85,  float(row["NDVI"]),        0.01)
            wi_ndbi  = st.slider("NDBI",       -0.29, 0.13,  float(row["NDBI"]),         0.01)
            wi_rain  = st.slider("Rainfall (mm)", 15, 3120,  int(float(row["Rainfall"])), 10)
        with s2:
            wi_temp  = st.slider("Temperature (°C)", 12.0, 45.0, float(row["Temperature"]), 0.5)
            wi_aqi   = st.slider("AQI (1=Good, 5=Bad)", 1, 5,   int(float(row["AQI"])))

        wi_vals = {"NDVI": wi_ndvi, "NDBI": wi_ndbi,
                   "Rainfall": wi_rain, "Temperature": wi_temp, "AQI": wi_aqi}
        lv_pred, aqi_pred, urb_pred = predict_all(wi_vals, xgb_m, rf_aqi, rf_urb, scaler)

        lv_current = m["Livability"]
        delta = lv_pred - lv_current
        delta_str = f"+{delta:.2f}" if delta >= 0 else f"{delta:.2f}"
        delta_col = "#4CAF50" if delta >= 0 else "#F44336"

        r1, r2, r3 = st.columns(3)
        r1.metric("Predicted Livability", f"{lv_pred:.2f}", delta_str)
        r2.metric("Predicted AQI", f"{aqi_pred}", f"was {int(float(row['AQI']))}")
        r3.metric("Urbanization", URBAN_LABELS[urb_pred])

        # comparison bar
        fig_wi = go.Figure()
        fig_wi.add_trace(go.Bar(name="Current",   x=["Livability"], y=[lv_current],
                                marker_color="#555"))
        fig_wi.add_trace(go.Bar(name="Predicted", x=["Livability"], y=[lv_pred],
                                marker_color=delta_col))
        fig_wi.update_layout(
            barmode="group", height=260,
            paper_bgcolor="#0f1117", plot_bgcolor="#111827",
            font=dict(color="white"), margin=dict(l=20,r=20,t=20,b=20)
        )
        st.plotly_chart(fig_wi, use_container_width=True)

    # ─── Tab 4: Report Card ────────────────────────────────────────────────────
    with tab4:
        st.subheader(f"📋 Report Card — {city}")
        st.markdown("Automated environmental assessment based on all available metrics.")

        report_items = [
            ("Livability",           m["Livability"],         "Livability",   "/100"),
            ("NDVI (Greenness)",      m["NDVI"] * 100,        "NDVI",         "/100 (scaled)"),
            ("Air Quality (AQI)",     m["AQI"],               "AQI",          "1=best, 5=worst"),
            ("Climate Resilience",    m["Climate Resilience"],"Climate Resilience", "/100"),
        ]

        cols = st.columns(4)
        for i, (label, val, metric_key, unit) in enumerate(report_items):
            g, gc = grade(val if metric_key != "NDVI" else val / 100, metric_key)
            with cols[i]:
                st.markdown(
                    f"""<div style="background:#1e2130;border-radius:12px;
                        padding:16px;text-align:center;margin-bottom:8px">
                        <div style="font-size:12px;color:#aaa">{label}</div>
                        <div style="font-size:36px;font-weight:800;color:{gc}">{g}</div>
                        <div style="font-size:14px;color:#ddd">{val:.1f}</div>
                        <div style="font-size:11px;color:#666">{unit}</div>
                    </div>""",
                    unsafe_allow_html=True
                )

        # Strengths & Risks
        st.markdown("---")
        col_s, col_r = st.columns(2)
        with col_s:
            st.markdown("### ✅ Strengths")
            if m["NDVI"] > 0.3:
                st.markdown(f"- Good vegetation cover (NDVI = {m['NDVI']:.3f})")
            if m["AQI"] <= 2:
                st.markdown(f"- Clean air (AQI = {int(m['AQI'])})")
            if m["Rainfall"] > 800:
                st.markdown(f"- Adequate rainfall ({m['Rainfall']:.0f} mm)")
            if m["Climate Resilience"] > 40:
                st.markdown(f"- Good climate resilience ({m['Climate Resilience']:.0f}/100)")
            if m["Livability"] > 45:
                st.markdown(f"- Above-average livability ({m['Livability']:.2f})")
        with col_r:
            st.markdown("### ⚠️ Risk Areas")
            if m["Heat Stress (0-10)"] > 6:
                st.markdown(f"- High heat stress ({m['Heat Stress (0-10)']:.1f}/10)")
            if m["Flood Risk (0-10)"] > 5:
                st.markdown(f"- Elevated flood risk ({m['Flood Risk (0-10)']:.1f}/10)")
            if m["Urbanization Score"] > 60:
                st.markdown(f"- Heavy urbanization ({m['Urbanization Score']:.0f}/100)")
            if m["NDVI"] < 0.2:
                st.markdown(f"- Low vegetation (NDVI = {m['NDVI']:.3f})")
            if m["AQI"] >= 4:
                st.markdown(f"- Poor air quality (AQI = {int(m['AQI'])})")

        # Download report as text
        report_text = f"""
URBAN INTELLIGENCE DASHBOARD — CITY REPORT
City: {city}
Generated by: Urban Intelligence Dashboard (Major Project)

=== METRICS ===
Livability Score:    {m['Livability']:.2f} / 100
NDVI:                {m['NDVI']:.4f}
NDBI:                {m['NDBI']:.4f}
Air Quality (AQI):   {int(m['AQI'])} / 5
Rainfall:            {m['Rainfall']:.0f} mm
Temperature:         {m['Temperature']:.1f} °C
Heat Stress:         {m['Heat Stress (0-10)']:.2f} / 10
Flood Risk:          {m['Flood Risk (0-10)']:.2f} / 10
Climate Resilience:  {m['Climate Resilience']:.1f} / 100
Urbanization:        {m['Urbanization Score']:.1f} / 100
"""
        st.download_button(
            "⬇️ Download Report (TXT)", report_text,
            file_name=f"{city}_urban_report.txt", mime="text/plain"
        )
