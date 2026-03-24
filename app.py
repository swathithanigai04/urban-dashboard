import streamlit as st
import pandas as pd
import base64, os
from utils.helpers import load_data
from utils.city_background import set_city_background
from pages.page1_search import geocode, find_in_dataset


# ── Static Background Helper ────────────────────────────────────────────────
def get_base64_image(image_path):
    if not os.path.exists(image_path):
        return ""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


st.set_page_config(
    page_title="JatayuX",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "view" not in st.session_state or st.session_state.view not in ["home", "dashboard"]:
    st.session_state.view = "home"

df = load_data()

def search_location(place):
    lat, lon, display_name = geocode(place)
    if lat is not None:
        match = find_in_dataset(place, df)
        
        # If city is missing from static dataset, generate live data!
        if match is None:
            from utils.live_data import generate_city_data
            with st.spinner("🌍 Fetching live meteorological data for " + place + "..."):
                synthetic_row = generate_city_data(place, lat, lon)
                match = pd.Series(synthetic_row)

        st.session_state["place_name"] = match["city"] if match is not None else place
        st.session_state["lat"] = lat
        st.session_state["lon"] = lon
        st.session_state["display_name"] = display_name
        st.session_state["dataset_row"] = match
        
        st.session_state["search_result"] = {
            "place": place,
            "lat": lat,
            "lon": lon,
            "display_name": display_name,
            "match": match.to_dict() if match is not None else None,
        }
        st.session_state["search_error"] = None
        
        # Immediately jump to Place Search (Page 1) after a global search
        st.session_state.view = "dashboard"
        st.session_state.dashboard_page = "Place Search"

if st.session_state.view == "home":
    # Custom CSS for dark mode JatayuX theme ONLY on home page
    img_b64 = get_base64_image("assets/home_bg.png")
    st.markdown(f"""
    <style>
        /* Hide Sidebar */
        [data-testid="stSidebar"] {{ display: none !important; }}
        [data-testid="collapsedControl"] {{ display: none !important; }}
        
        header {{ background: transparent !important; }}
        .hero-title {{ 
            font-size: 5rem; 
            font-weight: 800; 
            text-align: center; 
            margin-top: 18vh; 
            margin-bottom: 5px; 
            color: #ffffff; 
            letter-spacing: -1.5px; 
        }}
        .hero-subtitle {{ font-size: 1.2rem; text-align: center; color: #8b949e; margin-bottom: 40px; }}
        
        /* Premium Sketch Background */
        .stApp {{
            background-color: #06090f;
            background-image: 
                linear-gradient(rgba(6,11,18,0.78) 0%, rgba(6,11,18,0.92) 100%),
                url("data:image/png;base64,{img_b64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #c9d1d9;
        }}
        .stTextInput>div>div>input {{ background-color: #161b22; color: white; border: 1px solid #30363d; border-radius: 8px; padding: 12px 16px; }}
        .stButton>button {{ background-color: #21262d !important; color: #c9d1d9 !important; border: 1px solid #30363d !important; border-radius: 20px !important; padding: 4px 16px !important; }}
        .stButton>button:hover {{ background-color: #30363d !important; border-color: #8b949e !important; }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="hero-title">JatayuX</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Spatial Intelligence for Earth\'s Data</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1.5, 3, 1.5])
    with col2:
        query = st.chat_input("Ask anything or mention a location...", key="home_search")
        if query:
            search_location(query)
            st.rerun()

        st.write("")
        st.markdown("<div style='text-align:center; color:#8b949e; margin-top:20px; margin-bottom:10px;'>Try these examples:</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1,1,1])
        if c1.button("Mumbai", use_container_width=True):
            search_location("Mumbai")
            st.rerun()
        if c2.button("Bangalore", use_container_width=True):
            search_location("Bangalore")
            st.rerun()
        if c3.button("Chennai", use_container_width=True):
            search_location("Chennai")
            st.rerun()

elif st.session_state.view == "dashboard":
    # ── Inject city landmark background (applies to all pages) ──────────────
    _active_city = st.session_state.get("place_name", "Chennai")
    set_city_background(_active_city, show_sketch=False)

    # ── OLD DASHBOARD LOGIC ──

    st.markdown("""
    <style>
      [data-testid="stSidebarNav"] { display: none !important; }
      [data-testid="stSidebar"] { background: var(--secondary-background-color) !important; }
      [data-testid="collapsedControl"] { display: block !important; }
      .metric-card {
        background: var(--secondary-background-color); border-radius: 12px;
        padding: 16px 20px; margin-bottom: 10px;
        border-left: 4px solid var(--primary-color, #4CAF50);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      }
      .metric-card h4 { margin: 0 0 4px 0; font-size: 13px; color: var(--text-color); opacity: 0.7; }
      .metric-card p  { margin: 0; font-size: 26px; font-weight: 700; color: var(--text-color); }
      .stButton > button {
        width: 100%; background: var(--primary-color, #4CAF50); color: white;
        border: none; border-radius: 8px; padding: 10px;
        font-size: 15px; font-weight: 600;
      }
      .stButton > button:hover { opacity: 0.9; }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("## 🛰️ JatayuX")
        if st.button("↖ Back to Home", key="back_home"):
            st.session_state.view = "home"
            st.rerun()
        st.markdown("---")
        
        # Keep track of the active page in session state so we can jump to Analysis
        current_idx = 0 # default to Place Search
        pages = ["Place Search", "Environmental Analysis", "Job Opportunities", "Vegetation Prediction", "AI Assistant"]
        if "dashboard_page" in st.session_state:
            try:
                current_idx = pages.index(st.session_state.dashboard_page)
            except ValueError:
                current_idx = 0 # Default to Place Search if mismatch

        page = st.radio(
            "Navigate",
            pages,
            index=current_idx,
            label_visibility="collapsed",
            key="dashboard_nav"
        )
        st.session_state.dashboard_page = page

    if page == "Place Search":
        from pages import page1_search
        page1_search.render()
    elif page == "Environmental Analysis":
        from pages import page2_analysis
        page2_analysis.render()
    elif page == "Job Opportunities":
        from pages import page5_jobs
        page5_jobs.render()
    elif page == "Vegetation Prediction":
        from pages import page3_predictions
        page3_predictions.render()
    elif page == "AI Assistant":
        from pages import page4_chat
        page4_chat.render()
