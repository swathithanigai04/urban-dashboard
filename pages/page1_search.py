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
# from utils.city_background import set_city_background  <-- REMOVED

from geopy.geocoders import Nominatim, Photon, ArcGIS, GoogleV3
from geopy.exc import GeopyError

# ── Geocoding (using geopy with multi-provider fallback) ──────────────────────
def geocode(place_name: str):
    """
    Tries multiple geocoding providers to ensure reliability.
    """
    user_agent = f"JatayuX_Spatial_App_{hash(place_name) % 10000}"
    last_error = "All providers returned no results."
    
    # 1. Try Google Maps (Most reliable - if key is available)
    google_key = st.secrets.get("GOOGLE_MAPS_KEY", "")
    if google_key:
        try:
            google = GoogleV3(api_key=google_key, timeout=8)
            location = google.geocode(place_name)
            if location:
                return location.latitude, location.longitude, location.address
        except Exception as e:
            last_error = f"GoogleMaps error: {e}"

    # 2. Try ArcGIS (Reliable backup)
    try:
        arcgis = ArcGIS(timeout=10)
        location = arcgis.geocode(place_name)
        if location:
            return location.latitude, location.longitude, location.address
    except Exception as e:
        last_error = f"ArcGIS error: {e}"

    # 3. Try Nominatim (OSM)
    try:
        geolocator = Nominatim(user_agent=user_agent, timeout=6)
        location = geolocator.geocode(place_name)
        if location:
            return location.latitude, location.longitude, location.address
    except Exception as e:
        last_error = f"Nominatim error: {e}"

    # 4. Try Photon (OSM-based)
    try:
        photon = Photon(user_agent=user_agent, timeout=6)
        location = photon.geocode(place_name)
        if location:
            return location.latitude, location.longitude, location.address
    except Exception as e:
        last_error = f"Photon error: {e}"

    # If all fail, show the last specific error for diagnostics
    st.session_state["search_error"] = f"Geocoding failed for '{place_name}'. {last_error}"
    return None, None, None

# ── Match city in our dataset ─────────────────────────────────────────────────
def find_in_dataset(place_name: str, df: pd.DataFrame):
    name_lower = place_name.lower().strip()
    for _, row in df.iterrows():
        if name_lower in row["city"].lower() or row["city"].lower() in name_lower:
            return row
    return None

def render():
    st.title("Place Search")
    st.markdown("Enter any city or location in the world to begin analysis.")

    df = load_data()
    
    # Robust local imports to prevent UnboundLocalError in Streamlit
    import folium
    from streamlit_folium import st_folium

    # Show background handled by app.py

    col1, col2 = st.columns([3, 1])
    with col1:
        place = st.text_input(
            "City or place name",
            placeholder="e.g. Chennai, India",
            label_visibility="collapsed"
        )
    with col2:
        search_clicked = st.button("🔍 Search")


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
            
            if match is None:
                from utils.live_data import generate_city_data
                with st.spinner("🌍 Fetching live meteorological data for " + place + "..."):
                    synthetic_row = generate_city_data(place, lat, lon)
                    match = pd.Series(synthetic_row)

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
            st.session_state["place_name"]    = match["city"] if match is not None else place
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

        c1, c2 = st.columns(2)
        c1.metric("Latitude",  f"{lat:.5f}°")
        c2.metric("Longitude", f"{lon:.5f}°")


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
                f"?center={lat},{lon}&zoom=17&size=800x500"
                f"&maptype=satellite&key={GOOGLE_KEY}"
            )
            st.image(tile_url, caption=f"Google Satellite: {place}", use_container_width=True)
        else:
            # High-quality fallback using Folium + Esri World Imagery
            m_sat = folium.Map(location=[lat, lon], zoom_start=17, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri World Imagery")
            
            folium.Marker(
                location=[lat, lon],
                popup="Search Location",
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m_sat)
            
            st_folium(m_sat, height=500, use_container_width=True, key=f"sat_map_{lat}_{lon}")
            st.caption("_🛰️ High-detail Esri Satellite tiles (No API key required)_")


