"""
Page 1 — Place Search
User types a city/place name → geocode → show coordinates + satellite tile preview
"""
import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from utils.helpers import load_data

# ── Geocoding (free Nominatim, no API key needed) ────────────────────────────
def geocode(place_name: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place_name, "format": "json", "limit": 1}
    headers = {"User-Agent": "UrbanDashboard/1.0"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=8)
        results = r.json()
        if results:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            display_name = results[0]["display_name"]
            return lat, lon, display_name
    except Exception as e:
        st.error(f"Geocoding error: {e}")
    return None, None, None

# ── Match city in our dataset ─────────────────────────────────────────────────
def find_in_dataset(place_name: str, df: pd.DataFrame):
    name_lower = place_name.lower().strip()
    for _, row in df.iterrows():
        if name_lower in row["city"].lower() or row["city"].lower() in name_lower:
            return row
    return None

def render():
    st.title("🔍 Place Search")
    st.markdown("Enter any city or location in the world to begin analysis.")

    df = load_data()

    col1, col2 = st.columns([3, 1])
    with col1:
        place = st.text_input(
            "City or place name",
            placeholder="e.g. Chennai, India",
            label_visibility="collapsed"
        )
    with col2:
        search_clicked = st.button("🔍 Search")

    # Autocomplete suggestions from dataset
    with st.expander("💡 Cities in our dataset (click to expand)"):
        cities = sorted(df["city"].tolist())
        st.write(", ".join(cities))

    # ── On button click: geocode and STORE everything in session_state ────────
    # Results are stored in session_state so they survive Streamlit reruns.
    if search_clicked and place:
        with st.spinner("📡 Locating place..."):
            lat, lon, display_name = geocode(place)

        if lat is None:
            st.session_state["search_error"] = "Could not find this location. Try a more specific name."
            st.session_state["search_result"] = None
        else:
            match = find_in_dataset(place, df)
            # Store EVERYTHING needed for display into session_state
            st.session_state["search_result"] = {
                "place":        place,
                "lat":          lat,
                "lon":          lon,
                "display_name": display_name,
                "match":        match.to_dict() if match is not None else None,
            }
            st.session_state["search_error"]  = None
            # Also store for other pages
            st.session_state["place_name"]    = place
            st.session_state["lat"]           = lat
            st.session_state["lon"]           = lon
            st.session_state["display_name"]  = display_name
            st.session_state["dataset_row"]   = match

    # ── Always render from session_state (persists across reruns) ────────────
    if st.session_state.get("search_error"):
        st.error(st.session_state["search_error"])

    result = st.session_state.get("search_result")
    if result:
        lat          = result["lat"]
        lon          = result["lon"]
        place        = result["place"]
        display_name = result["display_name"]
        match_dict   = result["match"]

        # ── Info cards ────────────────────────────────────────────────────────
        st.markdown("---")
        st.success(f"✅ Found: **{display_name}**")

        c1, c2, c3 = st.columns(3)
        c1.metric("Latitude",  f"{lat:.5f}°")
        c2.metric("Longitude", f"{lon:.5f}°")
        c3.metric(
            "In Dataset",
            "✅ Yes" if match_dict is not None else "⚠️ Not found",
            help="Whether this city is in your 273-city dataset"
        )

        if match_dict is not None:
            st.info(
                f"📂 **Dataset match found:** {match_dict['city']} — "
                f"Livability: {match_dict['Livability']}, "
                f"AQI: {int(match_dict['AQI'])}, "
                f"NDVI: {float(match_dict['NDVI']):.3f}"
            )

        # ── Folium map preview ─────────────────────────────────────────────────
        st.markdown("### 🗺️ Location Preview")
        m = folium.Map(location=[lat, lon], zoom_start=11, tiles="CartoDB dark_matter")

        folium.CircleMarker(
            location=[lat, lon],
            radius=12,
            color="#4CAF50",
            fill=True,
            fill_color="#4CAF50",
            fill_opacity=0.7,
            popup=folium.Popup(f"<b>{place}</b><br>{lat:.4f}, {lon:.4f}", max_width=200)
        ).add_to(m)

        folium.Marker(
            location=[lat, lon],
            popup=place,
            icon=folium.Icon(color="green", icon="map-pin", prefix="fa")
        ).add_to(m)

        st_folium(m, height=420, use_container_width=True)

        # ── Satellite / map tile ───────────────────────────────────────────────
        st.markdown("### 🛰️ Satellite View")

        GOOGLE_KEY = st.secrets.get("GOOGLE_MAPS_KEY", "")
        if GOOGLE_KEY:
            tile_url = (
                f"https://maps.googleapis.com/maps/api/staticmap"
                f"?center={lat},{lon}&zoom=12&size=640x400"
                f"&maptype=satellite&key={GOOGLE_KEY}"
            )
            st.image(tile_url, caption=f"Satellite image: {place}", use_column_width=True)
        else:
            st.caption("_Add your Google Maps API key in `.streamlit/secrets.toml` for real satellite tiles._")
            st.markdown(
                f'<iframe width="100%" height="380" '
                f'src="https://www.openstreetmap.org/export/embed.html'
                f'?bbox={lon-0.05},{lat-0.05},{lon+0.05},{lat+0.05}&layer=mapnik" '
                f'style="border:1px solid #333; border-radius:8px;"></iframe>',
                unsafe_allow_html=True
            )

        st.markdown("---")
        st.success("✅ Location set! Navigate to **📊 Analysis** from the sidebar.")

        # Clear button so user can search again cleanly
        if st.button("🔄 Search a different city"):
            st.session_state["search_result"] = None
            st.session_state["search_error"]  = None
            st.rerun()
