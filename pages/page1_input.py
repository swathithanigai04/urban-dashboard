import streamlit as st
import folium
from streamlit_folium import st_folium
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.metrics import geocode_city, load_data

def show():
    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class='hero-box'>
      <div class='hero-title'>🌍 Place Input</div>
      <div class='hero-sub'>Enter any city or place in the world to begin analysis</div>
    </div>
    """, unsafe_allow_html=True)

    df = load_data()
    all_cities = sorted(df["city"].tolist())

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🔍 Search a City")
        city_input = st.text_input(
            "City name",
            placeholder="e.g. Chennai, Tokyo, New York, Lagos...",
            label_visibility="collapsed",
            key="city_text_input"
        )

        st.markdown("##### Or pick from our dataset")
        city_select = st.selectbox(
            "Dataset cities",
            ["— select —"] + all_cities,
            label_visibility="collapsed",
            key="city_dropdown"
        )

        # Resolve which input to use
        chosen = ""
        if city_input.strip():
            chosen = city_input.strip()
        elif city_select != "— select —":
            chosen = city_select

        search_btn = st.button("🚀 Analyse this city", use_container_width=True)

    with col2:
        st.markdown("### 📋 Dataset Coverage")
        st.metric("Cities in dataset", len(df))
        st.metric("Countries covered", df["city"].nunique())
        st.markdown(f"""
        <div class='metric-card'>
          <div class='metric-label'>Features available</div>
          <div style='font-size:13px; color:#ccc; margin-top:8px; line-height:1.8'>
            NDVI · NDBI · Rainfall<br>
            Temperature · AQI<br>
            Livability Score<br>
            + 6 derived metrics
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Geocode & display ─────────────────────────────────────────────────────
    if search_btn and chosen:
        with st.spinner(f"📡 Locating {chosen}..."):
            result = geocode_city(chosen)

        if result is None:
            st.error(f"❌ Could not find '{chosen}'. Try a different spelling.")
            return

        # Save to session state
        st.session_state.city_name    = result["display_name"]
        st.session_state.coordinates  = {"lat": result["lat"], "lon": result["lon"]}
        st.session_state.in_dataset   = result["in_dataset"]

        # Find dataset row if available
        match = df[df["city"].str.lower() == result["display_name"].lower()]
        if match.empty:
            match = df[df["city"].str.lower() == chosen.lower()]
        st.session_state.city_row = match.iloc[0].to_dict() if not match.empty else None

    # ── Show result if we have a city ─────────────────────────────────────────
    if "city_name" in st.session_state and st.session_state.city_name:
        city  = st.session_state.city_name
        lat   = st.session_state.coordinates["lat"]
        lon   = st.session_state.coordinates["lon"]
        in_ds = st.session_state.get("in_dataset", False)

        st.markdown("---")
        st.markdown(f"## ✅ Found: **{city}**")

        # Coordinates + dataset badge
        c1, c2, c3 = st.columns(3)
        c1.metric("Latitude",  f"{lat:.5f}°")
        c2.metric("Longitude", f"{lon:.5f}°")
        with c3:
            if in_ds:
                st.success("✅ In dataset — full analysis available")
            else:
                st.warning("⚠️ Not in dataset — derived metrics only")

        st.markdown("---")

        # ── Map preview ───────────────────────────────────────────────────────
        st.markdown("### 🗺️ Location Preview")

        map_col, info_col = st.columns([3, 1])

        with map_col:
            m = folium.Map(
                location=[lat, lon],
                zoom_start=10,
                tiles="CartoDB dark_matter"
            )
            # Marker
            folium.CircleMarker(
                location=[lat, lon],
                radius=10,
                color="#4a90d9",
                fill=True,
                fill_color="#4a90d9",
                fill_opacity=0.8,
                popup=folium.Popup(f"<b>{city}</b><br>{lat:.4f}°N, {lon:.4f}°E", max_width=200),
            ).add_to(m)
            # Pulsing ring
            folium.CircleMarker(
                location=[lat, lon],
                radius=22,
                color="#4a90d9",
                fill=False,
                weight=1.5,
                opacity=0.4,
            ).add_to(m)
            # Satellite tile layer toggle
            folium.TileLayer(
                tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
                attr="Google Satellite",
                name="🛰️ Satellite view",
                overlay=False,
            ).add_to(m)
            folium.LayerControl().add_to(m)

            st_folium(m, width=None, height=420, returned_objects=[])

        with info_col:
            st.markdown("""
            <div class='metric-card'>
              <div class='metric-label'>Map layers</div>
              <div style='font-size:13px; color:#aaa; line-height:2; margin-top:8px;'>
                🌑 Dark base map<br>
                🛰️ Google Satellite<br>
                📍 City pin<br>
              </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class='metric-card'>
              <div class='metric-label'>How to use</div>
              <div style='font-size:12px; color:#aaa; line-height:1.8; margin-top:8px;'>
                Toggle satellite view<br>
                using the layers icon<br>
                (top right of map).<br><br>
                Zoom in to see<br>
                real satellite imagery.
              </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Next step prompt ──────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("""
        <div style='background:#1a2744; border:1px solid #2a3d6e; border-radius:12px;
                    padding:20px 24px; text-align:center;'>
          <div style='font-size:18px; font-weight:700; color:#fff;'>
            📊 Ready for analysis!
          </div>
          <div style='font-size:14px; color:#8b8fa8; margin-top:8px;'>
            Head to <b>📊 Analysis</b> in the sidebar to see environmental metrics,
            or jump to <b>🤖 Predictions</b> for ML forecasts.
          </div>
        </div>
        """, unsafe_allow_html=True)

    elif not (search_btn and chosen == ""):
        # Landing state — show tips
        st.markdown("---")
        st.markdown("### 💡 What this dashboard does")
        cols = st.columns(4)
        tips = [
            ("🌍", "Input", "Search any city worldwide and pin it on the map"),
            ("📊", "Analyse", "View NDVI, AQI, heat stress, flood risk & more"),
            ("🤖", "Predict", "ML models forecast livability & urbanization trends"),
            ("💬", "Ask AI", "Chat with Gemini — it knows your city's full data"),
        ]
        for col, (icon, title, desc) in zip(cols, tips):
            col.markdown(f"""
            <div class='metric-card' style='text-align:center;'>
              <div style='font-size:32px'>{icon}</div>
              <div style='font-size:16px; font-weight:700; color:#fff; margin:8px 0 4px'>{title}</div>
              <div style='font-size:12px; color:#8b8fa8;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)
