"""
Page 4 — Gemini AI Chat Assistant
Context-aware chat: city metrics are injected into system prompt automatically.
"""
import streamlit as st
import google.generativeai as genai
from utils.helpers import load_data, compute_extended_metrics, aqi_label

GEMINI_MODEL = "gemini-1.5-flash"   # free-tier friendly

def get_city_context(city_name: str, df) -> str:
    """Build a context string for Gemini about the selected city."""
    row = df[df["city"] == city_name]
    if row.empty:
        return f"The user is asking about {city_name}. No dataset entry found."
    row = row.iloc[0]
    m = compute_extended_metrics(row)
    aq, _ = aqi_label(m["AQI"])
    return f"""
You are an Urban Environmental Intelligence Assistant embedded in a data science dashboard.

The user is currently analyzing: {city_name}

== LIVE METRICS FOR {city_name.upper()} ==
• Livability Score:     {m['Livability']:.2f} / 100
• NDVI (Vegetation):    {m['NDVI']:.4f}  (0=barren, 1=dense forest)
• NDBI (Built-up):      {m['NDBI']:.4f}  (positive=more urbanized)
• Rainfall:             {m['Rainfall']:.0f} mm / year
• Temperature (mean):   {m['Temperature']:.1f} °C
• Air Quality (AQI):    {int(m['AQI'])} / 5  ({aq})
• Heat Stress:          {m['Heat Stress (0-10)']:.2f} / 10
• Flood Risk:           {m['Flood Risk (0-10)']:.2f} / 10
• Climate Resilience:   {m['Climate Resilience']:.1f} / 100
• Urbanization Score:   {m['Urbanization Score']:.1f} / 100
• Green Cover:          {m['Green Cover (%)']:.1f} %
• Land Surface Temp:    {m['Land Surface Temp']:.1f} °C

== YOUR ROLE ==
Answer questions about this city's environment, compare it to others when asked,
explain what the metrics mean, suggest urban planning improvements, and discuss
climate risks. Be insightful, concise, and data-driven. Format key numbers in bold.
If asked about a different city, let the user know you have full data for 273 cities.
"""

def render():
    st.title("💬 AI Urban Assistant")
    st.markdown("Ask anything about your city's environment, metrics, or future risks.")

    df = load_data()
    cities_list = sorted(df["city"].tolist())

    # ── Sidebar-like controls in a top bar ────────────────────────────────────
    col_city, col_key = st.columns([2, 2])
    with col_city:
        session_city = st.session_state.get("place_name", "Chennai")
        default_idx  = next(
            (i for i, c in enumerate(cities_list) if session_city.lower() in c.lower()), 0
        )
        selected_city = st.selectbox("City context", cities_list, index=default_idx,
                                     key="chat_city")
    with col_key:
        api_key = st.text_input(
            "Gemini API key",
            type="password",
            placeholder="AIza...",
            help="Get a free key at https://aistudio.google.com"
        )

    # ── Initialize chat history ───────────────────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "last_city" not in st.session_state:
        st.session_state.last_city = None

    # Reset chat if city changes
    if st.session_state.last_city != selected_city:
        st.session_state.chat_history = []
        st.session_state.last_city = selected_city

    # ── Preset question buttons ───────────────────────────────────────────────
    st.markdown("**Quick questions:**")
    presets = [
        f"Why is {selected_city}'s livability score what it is?",
        f"What are the top 3 environmental risks in {selected_city}?",
        f"How can {selected_city} improve its NDVI and green cover?",
        f"What will happen to {selected_city} if urbanization continues at this rate?",
        f"Compare {selected_city}'s climate resilience with global averages.",
    ]
    cols = st.columns(3)
    for i, q in enumerate(presets[:3]):
        if cols[i].button(q[:45] + "...", key=f"preset_{i}"):
            st.session_state.preset_question = q

    # ── Display chat messages ─────────────────────────────────────────────────
    st.markdown("---")
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"],
                                 avatar="🛰️" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])

    # ── Input ─────────────────────────────────────────────────────────────────
    preset = st.session_state.pop("preset_question", None)
    user_input = st.chat_input("Ask about the city's environment...") or preset

    if user_input:
        # Show user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # ── Call Gemini ───────────────────────────────────────────────────────
        if not api_key:
            reply = (
                "⚠️ Please enter your **Gemini API key** above to enable the AI assistant. "
                "Get a free key at https://aistudio.google.com — it takes 30 seconds."
            )
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(GEMINI_MODEL)

                # Build full conversation for Gemini
                system_ctx = get_city_context(selected_city, df)
                history_for_gemini = []
                for msg in st.session_state.chat_history[:-1]:  # exclude current
                    role = "user" if msg["role"] == "user" else "model"
                    history_for_gemini.append({
                        "role": role,
                        "parts": [msg["content"]]
                    })

                chat = model.start_chat(history=history_for_gemini)
                # First message always carries city context
                full_prompt = system_ctx + "\n\n== USER QUESTION ==\n" + user_input \
                    if len(st.session_state.chat_history) == 1 else user_input

                with st.spinner("🛰️ Analyzing..."):
                    response = chat.send_message(full_prompt)
                    reply = response.text

            except Exception as e:
                reply = f"❌ Error calling Gemini: {str(e)}\n\nPlease check your API key."

        with st.chat_message("assistant", avatar="🛰️"):
            st.markdown(reply)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})

    # ── Clear chat ────────────────────────────────────────────────────────────
    if st.session_state.chat_history:
        if st.button("🗑️ Clear conversation"):
            st.session_state.chat_history = []
            st.rerun()

    # ── City data snapshot ────────────────────────────────────────────────────
    with st.expander(f"📊 Current context: {selected_city} metrics"):
        row = df[df["city"] == selected_city]
        if not row.empty:
            m = compute_extended_metrics(row.iloc[0])
            import pandas as pd
            snapshot = pd.DataFrame([
                {"Metric": k, "Value": v} for k, v in m.items()
            ])
            st.dataframe(snapshot, use_container_width=True, hide_index=True)
