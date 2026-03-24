"""
Page 4 — Gemini AI Chat Assistant
Context-aware chat: city metrics are injected into system prompt automatically.
"""
import streamlit as st
import google.generativeai as genai
from utils.helpers import load_data, compute_extended_metrics, aqi_label
from utils.economic_api import get_economic_data
from utils.city_background import set_city_background

GEMINI_MODEL = "gemini-2.0-flash"   # user key specific allowed model

def get_city_context(city_name: str, df) -> str:
    """Build a context string for Gemini about the selected city."""
    row = df[df["city"] == city_name]
    if row.empty:
        return f"The user is asking about {city_name}. No dataset entry found."
    row = row.iloc[0]
    m = compute_extended_metrics(row)
    aq, _ = aqi_label(m["AQI"])
    econ = get_economic_data(city_name)
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

== ECONOMIC METRICS ==
• Avg Monthly Salary:   ${econ['avg_monthly_salary_usd']:,} USD
• Cost of Living Index: {econ['cost_of_living_index']:.1f}
• Affordability Score:  {econ['affordability_score']:.1f} / 100
• Data Source:          {econ['data_source']}

== YOUR ROLE ==
Answer questions about this city's environment, compare it to others when asked,
explain what the metrics mean, suggest urban planning improvements, and discuss
climate risks. Be insightful, concise, and data-driven. Format key numbers in bold.
If asked about a different city, let the user know you have full data for 273 cities.
"""

def mock_gemini_response(user_input, city_name, df_row):
    import time
    time.sleep(1.0) # simulate typing
    m = compute_extended_metrics(df_row)
    q = user_input.lower()
    
    if "livability" in q:
        status = "strong" if m['Livability'] > 60 else "moderate" if m['Livability'] > 40 else "vulnerable"
        return f"**{city_name}'s livability score of {m['Livability']:.1f}/100** is considered **{status}**.\n\nThis is primarily driven by its local environmental conditions. For instance, the **NDVI (Vegetation) is {m['NDVI']:.3f}**, offering {'plenty of green spaces' if m['NDVI'] > 0.3 else 'highly limited green cover'}. The **Air Quality Index is categorized at {int(m['AQI'])}/5**, which plays a major part in public health outcomes. Furthermore, local Heat stress sits at {m['Heat Stress (0-10)']:.1f}/10, directly affecting daily comfort for residents."
    
    if "top 3" in q or "risk" in q:
        risks = []
        if m['AQI'] > 2: risks.append(f"**Air Quality ({int(m['AQI'])}/5):** Harmful levels of pollution due to urban emissions.")
        if m['Heat Stress (0-10)'] > 4.5: risks.append(f"**Heat Stress ({m['Heat Stress (0-10)']:.1f}/10):** Elevated Urban Heat Island effect driven by {m['Land Surface Temp']:.1f}°C surface temperatures.")
        if m['Flood Risk (0-10)'] > 4: risks.append(f"**Flood Vulnerability ({m['Flood Risk (0-10)']:.1f}/10):** Heavy annualized rainfall combined with high built-up index ({m['NDBI']:.3f}) reduces natural drainage.")
        if m['NDVI'] < 0.25: risks.append(f"**Deforestation (NDVI {m['NDVI']:.3f}):** Critically low natural vegetation cover limits carbon capture.")
        
        if len(risks) == 0:
            return f"{city_name} is performing excellently across all metrics! However, general risks include sustained urbanization (NDBI: {m['NDBI']:.3f}) and shifting seasonal rainfalls."
        else:
            return f"Based on the live spatial metrics for **{city_name}**, the top environmental risks are:\n\n* " + "\n* ".join(risks[:3])
            
    if "ndvi" in q or "green" in q:
        return f"To improve its NDVI ({m['NDVI']:.3f}), **{city_name}** must focus on rigorous urban afforestation. Since the NDBI (built-up area) is at {m['NDBI']:.3f}, the city has heavily prioritized concrete infrastructure over its natural canopy. \n\nImplementing rooftop gardens, vertical greenery, and converting unused paved zones into micro-parks can significantly boost the overall green cover ({m['Green Cover (%)']:.1f}%) and lower the {m['Land Surface Temp']:.1f}°C surface heat."
        
    if "continue" in q or "happen" in q or "urbanization" in q:
        return f"If **{city_name}** continues its current urbanization trajectory (NDBI: {m['NDBI']:.3f}), it will rapidly exacerbate the Urban Heat Island effect, pushing Heat Stress significantly above {m['Heat Stress (0-10)']:.1f}/10. \n\nThis unchecked expansion will inherently degrade the Livability Score ({m['Livability']:.1f}), fracture the city's Climate Resilience ({m['Climate Resilience']:.1f}/100), and systematically escalate local flooding risks."
        
    return f"*(Offline AI Simulation Mode)*\n\nThe environmental footprint of **{city_name}** consists of {m['Livability']:.1f} Livability, {int(m['AQI'])}/5 Air Quality, and {m['NDVI']:.3f} Vegetation density.\n\nBalancing these indicators through smart-city policies is crucial to mitigating its {m['Heat Stress (0-10)']:.1f}/10 spatial heat intensity."

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
                                     key=f"chat_city_{session_city}")
    
    set_city_background(selected_city)
    api_key = st.secrets.get("GEMINI_API_KEY", "")

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
        try:
            genai.configure(api_key=api_key)
            # Build full conversation for Gemini
            system_ctx = get_city_context(selected_city, df)
            history_for_gemini = []
            for msg in st.session_state.chat_history[:-1]:  # exclude current
                role = "user" if msg["role"] == "user" else "model"
                history_for_gemini.append({
                    "role": role,
                    "parts": [msg["content"]]
                })

            full_prompt = system_ctx + "\n\n== USER QUESTION ==\n" + user_input \
                if len(st.session_state.chat_history) == 1 else user_input

            with st.spinner("🛰️ Analyzing..."):
                models_to_try = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-pro-latest", "gemini-flash-latest"]
                reply = None
                last_err = None
                for m_name in models_to_try:
                    try:
                        model = genai.GenerativeModel(m_name)
                        chat = model.start_chat(history=history_for_gemini)
                        response = chat.send_message(full_prompt)
                        reply = response.text
                        break
                    except Exception as inner_e:
                        last_err = inner_e
                        err_str = str(inner_e)
                        if "404" in err_str or "not found" in err_str or "429" in err_str or "quota" in err_str.lower():
                            continue
                        raise inner_e
                
                if reply is None:
                    # Fallback to automated expert simulation if all models are quota restricted!
                    row_data = df[df["city"] == selected_city]
                    reply = mock_gemini_response(user_input, selected_city, row_data.iloc[0] if not row_data.empty else None)

        except Exception as e:
            # Absolute fallback guarantee
            row_data = df[df["city"] == selected_city]
            reply = mock_gemini_response(user_input, selected_city, row_data.iloc[0] if not row_data.empty else None)

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
