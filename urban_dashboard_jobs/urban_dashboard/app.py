import streamlit as st

st.set_page_config(
    page_title="Urban Intelligence Dashboard",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
  [data-testid="stSidebar"] { background: #0f1117; }
  .metric-card {
    background: #1e2130; border-radius: 12px;
    padding: 16px 20px; margin-bottom: 10px;
    border-left: 4px solid #4CAF50;
  }
  .metric-card h4 { margin: 0 0 4px 0; font-size: 13px; color: #aaa; }
  .metric-card p  { margin: 0; font-size: 26px; font-weight: 700; color: #fff; }
  .stButton > button {
    width: 100%; background: #4CAF50; color: white;
    border: none; border-radius: 8px; padding: 10px;
    font-size: 15px; font-weight: 600;
  }
  .stButton > button:hover { background: #388E3C; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🛰️ Urban Intelligence")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["🔍 Place Search",
         "📊 Analysis",
         "💼 Job Opportunities",
         "🤖 Predictions",
         "💬 AI Assistant"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("**Dataset:** 273 global cities")
    st.markdown("**Models:** RF · XGBoost · UNet Sim")
    st.markdown("**APIs:** Maps · Gemini · World Bank")

if   page == "🔍 Place Search":
    from pages.page1_search import render; render()
elif page == "📊 Analysis":
    from pages.page2_analysis import render; render()
elif page == "💼 Job Opportunities":
    from pages.page5_jobs import render; render()
elif page == "🤖 Predictions":
    from pages.page3_predictions import render; render()
elif page == "💬 AI Assistant":
    from pages.page4_chat import render; render()
