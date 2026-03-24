""" Shared city landmark background helper. """
import streamlit as st
import base64, os

# ── Static Background Helper ────────────────────────────────────────────────
def get_base64_image(image_path):
    # Try multiple common relative paths for robustness
    paths_to_try = [
        os.path.join(os.path.dirname(__file__), "..", image_path),
        image_path
    ]
    for p in paths_to_try:
        if os.path.exists(p):
            with open(p, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
    return ""

# ── Curated landmark photos (Unsplash direct links) ───────────────────────────
CITY_BG_MAP = {
    "dubai":         "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1600&q=80",
    "abu dhabi":     "https://images.unsplash.com/photo-1607774451965-2a3b5c5a0a0a?w=1600&q=80",
    "paris":         "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1600&q=80",
    "new york":      "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=1600&q=80",
    "tokyo":         "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1600&q=80",
    "london":        "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1600&q=80",
    "singapore":     "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=1600&q=80",
    "sydney":        "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=1600&q=80",
    "mumbai":        "https://images.unsplash.com/photo-1529253355930-ddbe423a2ac7?w=1600&q=80",
    "delhi":         "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=1600&q=80",
    "bangalore":     "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?w=1600&q=80",
    "chennai":       "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=1600&q=80",
    "zurich":        "https://images.unsplash.com/photo-1515488764276-beab7607c1e6?w=1600&q=80",
    "san francisco": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=1600&q=80",
    "seoul":         "https://images.unsplash.com/photo-1538485399081-7191377e8241?w=1600&q=80",
    "bangkok":       "https://images.unsplash.com/photo-1508009603885-50cf31c453dd?w=1600&q=80",
    "cairo":         "https://images.unsplash.com/photo-1572252009286-268acec5ca0a?w=1600&q=80",
    "istanbul":      "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?w=1600&q=80",
    "amsterdam":     "https://images.unsplash.com/photo-1512470876302-972faa2aa9a4?w=1600&q=80",
    "barcelona":     "https://images.unsplash.com/photo-1583422409516-2895a77efded?w=1600&q=80",
    "toronto":       "https://images.unsplash.com/photo-1517090504586-fde19ea6066f?w=1600&q=80",
    "hong kong":     "https://images.unsplash.com/photo-1536599018102-9f803c140fc1?w=1600&q=80",
    "busan":         "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?w=1600&q=80",
    "kuala lumpur":  "https://images.unsplash.com/photo-1596422846543-75c6fc197f07?w=1600&q=80",
    "doha":          "https://images.unsplash.com/photo-1545167496-58e8d9e0b413?w=1600&q=80",
    "rio de janeiro":"https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=1600&q=80",
    "cape town":     "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=1600&q=80",
    "vienna":        "https://images.unsplash.com/photo-1516550893923-42d28e5677af?w=1600&q=80",
    "beijing":       "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=1600&q=80",
    "shanghai":      "https://images.unsplash.com/photo-1538428494232-9c0d8a3ab403?w=1600&q=80",
    "moscow":        "https://images.unsplash.com/photo-1513326738677-b964603b136d?w=1600&q=80",
    "rome":          "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=1600&q=80",
    "hyderabad":     "https://images.unsplash.com/photo-1563448927462-80c78a30b345?w=1600&q=80",
    "kolkata":       "https://images.unsplash.com/photo-1558431382-27e303142255?w=1600&q=80",
    "nairobi":       "https://images.unsplash.com/photo-1611348524140-53c9a25263d6?w=1600&q=80",
    "johannesburg":  "https://images.unsplash.com/photo-1577948000111-9c970dfe3743?w=1600&q=80",
    "los angeles":   "https://images.unsplash.com/photo-1534430480872-3498386e7856?w=1600&q=80",
    "chicago":       "https://images.unsplash.com/photo-1494522855154-9297ac14b55f?w=1600&q=80",
    "jakarta":       "https://images.unsplash.com/photo-1555899434-94d1368aa7af?w=1600&q=80",
    "miami":         "https://images.unsplash.com/photo-1506966953602-c20cc11f75e3?w=1600&q=80",
    "prague":        "https://images.unsplash.com/photo-1541849546-216549ae216d?w=1600&q=80",
    "budapest":      "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1600&q=80",
    "athens":        "https://images.unsplash.com/photo-1555993539-1732b0258235?w=1600&q=80",
    "lisbon":        "https://images.unsplash.com/photo-1548707309-dcebeab9ea9b?w=1600&q=80",
    # ── Additional Indian Cities ─────────────────────────────────────────────
    "ahmedabad":      "https://images.unsplash.com/photo-1599831773041-396599b45e99?w=1600&q=80",
    "pune":           "https://images.unsplash.com/photo-1582234032481-6fdf3586cd5b?w=1600&q=80",
    "jaipur":         "https://images.unsplash.com/photo-1599661046289-e31887846eac?w=1600&q=80",
    "surat":          "https://images.unsplash.com/photo-1586716039498-8ec1f5313a0c?w=1600&q=80",
    "lucknow":        "https://images.unsplash.com/photo-1618173423719-74d6f83ec381?w=1600&q=80",
    "varanasi":       "https://images.unsplash.com/photo-1561359313-0639aad49ca6?w=1600&q=80",
    "amritsar":       "https://images.unsplash.com/photo-1514222134-b57cbb8ce073?w=1600&q=80",
    "chandigarh":     "https://images.unsplash.com/photo-1603566164227-2c91a0391d1e?w=1600&q=80",
    "guwahati":       "https://images.unsplash.com/photo-1620842512140-1049c336582f?w=1600&q=80",
    "kochi":          "https://images.unsplash.com/photo-1593444211110-1886162391ce?w=1600&q=80",
    "trivandrum":     "https://images.unsplash.com/photo-1589133869970-dcb74c43a08b?w=1600&q=80",
    "patna":          "https://images.unsplash.com/photo-1624443916243-7f61e2b5883d?w=1600&q=80",
    "ranchi":         "https://images.unsplash.com/photo-1619448858227-8a4704cc1831?w=1600&q=80",
    "bhopal":         "https://images.unsplash.com/photo-1619541570773-ce85c08f9293?w=1600&q=80",
    "indore":         "https://images.unsplash.com/photo-1618252277864-7fcd88fe3142?w=1600&q=80",
    "nagpur":         "https://images.unsplash.com/photo-1608688407421-4f1659929849?w=1600&q=80",
    "vishakhapatnam": "https://images.unsplash.com/photo-1617415136893-60f64c1f964a?w=1600&q=80",
    # ── Additional Global Cities ─────────────────────────────────────────────
    "las vegas":      "https://images.unsplash.com/photo-1581351123004-757df051db8e?w=1600&q=80",
    "seattle":        "https://images.unsplash.com/photo-1502175353174-a7a70e73b362?w=1600&q=80",
    "vancouver":      "https://images.unsplash.com/photo-1559511260-66a654ae982a?w=1600&q=80",
    "madrid":         "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=1600&q=80",
    "berlin":         "https://images.unsplash.com/photo-1528728329032-2972f65dfb3f?w=1600&q=80",
    "munich":         "https://images.unsplash.com/photo-1595146059296-107769fcb632?w=1600&q=80",
    "stockholm":      "https://images.unsplash.com/photo-1509356843151-3e7d96241e11?w=1600&q=80",
    "oslo":           "https://images.unsplash.com/photo-1513519245088-0e12902e35ca?w=1600&q=80",
    "copenhagen":     "https://images.unsplash.com/photo-1513622470522-26c3c8a854bc?w=1600&q=80",
    "dublin":         "https://images.unsplash.com/photo-1549918830-11ec3d405f67?w=1600&q=80",
    "mexico city":    "https://images.unsplash.com/photo-1518105779142-d97bd210940c?w=1600&q=80",
    "buenos aires":   "https://images.unsplash.com/photo-1589909202802-8f4aadce1849?w=1600&q=80",
    "sao paulo":      "https://images.unsplash.com/photo-1543059180-a1285032f849?w=1600&q=80",
    "manila":         "https://images.unsplash.com/photo-1540324151706-e0f10c14c5a0?w=1600&q=80",
    "ho chi minh city":"https://images.unsplash.com/photo-1555928487-703422ad39ec?w=1600&q=80",
    "taipei":         "https://images.unsplash.com/photo-1552912006-b3337f772ba6?w=1600&q=80",
    "osaka":          "https://images.unsplash.com/photo-1590253553890-392d7b884968?w=1600&q=80",
    "kyoto":          "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=1600&q=80",
    "tel aviv":       "https://images.unsplash.com/photo-1544971587-b842c27f8e14?w=1600&q=80",
    "riyadh":         "https://images.unsplash.com/photo-1586724237569-f3d021dd6c32?w=1600&q=80",
    "casablanca":     "https://images.unsplash.com/photo-1539020140153-e479b8c22e70?w=1600&q=80",
    "marrakesh":      "https://images.unsplash.com/photo-1597212618440-8062a4729cc5?w=1600&q=80",
    "torre":          "https://images.unsplash.com/photo-1536599018102-9f803c140fc1?w=1600&q=80",}


def get_city_bg_url(city_name: str) -> str:
    """Return the best available landmark image URL for a city."""
    key = city_name.lower().strip()
    if key in CITY_BG_MAP:
        return CITY_BG_MAP[key]
    # Generic fallback via Unsplash search
    query = city_name.replace(" ", "%20")
    return f"https://images.unsplash.com/photo-1449034446853-66c86144b0ad?w=1600&q=80&sig={query}"


def set_city_background(city_name: str, overlay_opacity: float = 0.70, show_sketch: bool = True):
    """
    Inject CSS that sets a landmark photo + premium sketch as the background.
    """
    city_url = get_city_bg_url(city_name)
    sketch_b64 = get_base64_image("assets/home_bg.png")
    
    o1 = overlay_opacity
    
    sketch_css = ""
    if show_sketch:
        sketch_css = f"""
    /* Layer 2: The Blueprint Sketch (on top of photo) */
    .stApp::after {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("data:image/png;base64,{sketch_b64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        opacity: 0.15;
        pointer-events: none;
        z-index: -1;
        mix-blend-mode: screen;
    }}
    """
    
    css = f"""
    <style>
    /* Absolute base background for the entire app */
    .stApp {{
        background-color: var(--background-color) !important;
    }}

    /* Layer 1: The Landmark Photo (at the very bottom) */
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("{city_url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
        /* Use opacity to blend with the background-color of the container */
        opacity: {1 - o1:.2f}; 
        z-index: -2;
    }}

    {sketch_css}

    /* Force all intermediate Streamlit layers to be transparent */
    [data-testid="stHeader"], .main, .block-container {{
        background: transparent !important;
        background-color: transparent !important;
    }}
    
    /* Ensure content is readable */
    .main > div {{
        position: relative;
        z-index: 10;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
