"""
Page 5 — Job Opportunities & Cost of Living
Full analysis: salary, affordability, unemployment, tech score,
industry diversity, cost breakdown, city comparisons, top cities ranking
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils.helpers import load_data

# ── Load economic data ────────────────────────────────────────────────────────
@st.cache_data
def load_economic():
    import os
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "economic_data.csv")
    return pd.read_csv(csv_path)

# ── Colour helpers ────────────────────────────────────────────────────────────
def score_color(val, low=20, high=70):
    if val >= high: return "#4CAF50"
    if val >= 40:   return "#FFC107"
    return "#F44336"

def unemp_color(val):
    if val <= 4:  return "#4CAF50"
    if val <= 8:  return "#FFC107"
    if val <= 15: return "#FF9800"
    return "#F44336"

def metric_card(label, value, unit="", color="#4CAF50", sublabel=""):
    st.markdown(
        f"""<div style="background:#1e2130;border-radius:12px;padding:16px 18px;
            margin-bottom:10px;border-left:4px solid {color}">
            <div style="font-size:12px;color:#aaa;margin-bottom:4px">{label}</div>
            <div style="font-size:24px;font-weight:700;color:#fff">
                {value}<span style="font-size:13px;color:#aaa;margin-left:4px">{unit}</span>
            </div>
            {"<div style='font-size:11px;color:#666;margin-top:3px'>"+sublabel+"</div>" if sublabel else ""}
        </div>""",
        unsafe_allow_html=True
    )

def score_ring(label, value, max_val=100, color="#4CAF50"):
    pct = value / max_val * 100
    st.markdown(
        f"""<div style="background:#1e2130;border-radius:12px;padding:16px;
            text-align:center;margin-bottom:10px">
            <div style="font-size:11px;color:#aaa;margin-bottom:8px">{label}</div>
            <div style="font-size:32px;font-weight:800;color:{color}">{value}</div>
            <div style="font-size:11px;color:#555">/ {max_val}</div>
            <div style="background:#333;border-radius:4px;height:5px;margin-top:8px">
                <div style="background:{color};width:{pct}%;height:5px;border-radius:4px"></div>
            </div>
        </div>""",
        unsafe_allow_html=True
    )

# ── Job grade ─────────────────────────────────────────────────────────────────
def job_grade(score):
    if score >= 45: return "A", "#4CAF50"
    if score >= 40: return "B", "#8BC34A"
    if score >= 37: return "C", "#FFC107"
    if score >= 33: return "D", "#FF5722"
    return "F", "#F44336"

# ── Salary vs cost gauge ──────────────────────────────────────────────────────
def salary_cost_chart(salary, cost_idx, city):
    # monthly cost estimate from index (index 100 = ~$2000/month expenses)
    est_monthly_cost = cost_idx * 20
    savings = salary - est_monthly_cost
    savings_color = "#4CAF50" if savings > 0 else "#F44336"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Avg Monthly Salary",
        x=[city], y=[salary],
        marker_color="#4CAF50",
        text=[f"${salary:,}"], textposition="outside"
    ))
    fig.add_trace(go.Bar(
        name="Est. Monthly Expenses",
        x=[city], y=[est_monthly_cost],
        marker_color="#FF5722",
        text=[f"${est_monthly_cost:,.0f}"], textposition="outside"
    ))
    fig.update_layout(
        barmode="group",
        paper_bgcolor="#0f1117", plot_bgcolor="#111827",
        font=dict(color="white"),
        height=280,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(font=dict(color="white"), orientation="h",
                    yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title="USD / month", gridcolor="#333"),
    )
    return fig, savings

# ── Industry radar ────────────────────────────────────────────────────────────
def industry_radar(row):
    # Derive industry scores from available metrics
    tech    = float(row["tech_hub_score"])
    div     = float(row["industry_diversity_score"])
    gdp     = float(row["gdp_per_capita_usd"])
    unemp   = float(row["unemployment_rate"])

    finance   = round(min(10, div * 0.9 + (gdp / 100000) * 3), 1)
    mfg       = round(min(10, (10 - tech) * 0.6 + div * 0.4), 1)
    tourism   = round(min(10, div * 0.7 + np.random.uniform(0.5, 2.0)), 1)
    healthcare= round(min(10, div * 0.8 + (gdp / 120000) * 2), 1)
    govt      = round(min(10, 4 + div * 0.3), 1)

    cats   = ["Technology", "Finance", "Manufacturing", "Tourism", "Healthcare", "Government"]
    vals   = [tech, finance, mfg, tourism, healthcare, govt]
    closed = vals + [vals[0]]
    c_cats = cats + [cats[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=closed, theta=c_cats,
        fill="toself", fillcolor="rgba(76,175,80,0.2)",
        line=dict(color="#4CAF50", width=2),
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0,10],
                            tickfont=dict(size=9, color="#aaa"),
                            gridcolor="#333"),
            angularaxis=dict(tickfont=dict(size=11, color="#ccc"),
                             gridcolor="#333"),
            bgcolor="#0f1117"
        ),
        paper_bgcolor="#0f1117",
        font=dict(color="white"),
        showlegend=False,
        height=300,
        margin=dict(l=40, r=40, t=20, b=20)
    )
    return fig

# ── Top cities ranking chart ──────────────────────────────────────────────────
def top_cities_chart(edf, metric, label, city, n=15):
    top = edf.nlargest(n, metric)[["city", metric]]
    colors = ["#4CAF50" if c == city else "#2a3a4a" for c in top["city"]]
    borders= ["#4CAF50" if c == city else "#4a5a6a" for c in top["city"]]

    fig = go.Figure(go.Bar(
        x=top[metric], y=top["city"],
        orientation="h",
        marker=dict(color=colors, line=dict(color=borders, width=1)),
        text=[f"{v:,.1f}" for v in top[metric]],
        textposition="outside",
        textfont=dict(size=11, color="white")
    ))
    fig.update_layout(
        title=f"Top {n} cities — {label}",
        paper_bgcolor="#0f1117", plot_bgcolor="#111827",
        font=dict(color="white"),
        height=420,
        margin=dict(l=10, r=60, t=45, b=10),
        xaxis=dict(gridcolor="#333"),
        yaxis=dict(autorange="reversed")
    )
    return fig

# ── Salary world map ──────────────────────────────────────────────────────────
def salary_scatter_map(edf, city):
    env = load_data()
    merged = edf.merge(env[["city","latitude","longitude"]], on="city", how="left")
    merged = merged.dropna(subset=["latitude","longitude"])

    fig = px.scatter_mapbox(
        merged,
        lat="latitude", lon="longitude",
        size="avg_monthly_salary_usd",
        color="affordability_score",
        hover_name="city",
        hover_data={
            "avg_monthly_salary_usd": True,
            "affordability_score": True,
            "unemployment_rate": True,
            "latitude": False, "longitude": False
        },
        color_continuous_scale="RdYlGn",
        size_max=30,
        zoom=1,
        mapbox_style="carto-darkmatter",
        title="Global salary & affordability map"
    )
    fig.update_layout(
        paper_bgcolor="#0f1117",
        font=dict(color="white"),
        height=420,
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(title=dict(text="Affordability", font=dict(color="white")),
                                tickfont=dict(color="white"))
    )
    return fig

# ── City background images ────────────────────────────────────────────────────
# Curated landmark images for well-known cities (Unsplash source API or direct)
CITY_BG_MAP = {
    "dubai":        "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1400&q=80",
    "abu dhabi":    "https://images.unsplash.com/photo-1607774451965-2a3b5c5a0a0a?w=1400&q=80",
    "paris":        "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1400&q=80",
    "new york":     "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=1400&q=80",
    "tokyo":        "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1400&q=80",
    "london":       "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1400&q=80",
    "singapore":    "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=1400&q=80",
    "sydney":       "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=1400&q=80",
    "mumbai":       "https://images.unsplash.com/photo-1529253355930-ddbe423a2ac7?w=1400&q=80",
    "delhi":        "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=1400&q=80",
    "bangalore":    "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?w=1400&q=80",
    "chennai":      "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=1400&q=80",
    "zurich":       "https://images.unsplash.com/photo-1515488764276-beab7607c1e6?w=1400&q=80",
    "san francisco":"https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=1400&q=80",
    "seoul":        "https://images.unsplash.com/photo-1538485399081-7191377e8241?w=1400&q=80",
    "bangkok":      "https://images.unsplash.com/photo-1508009603885-50cf31c453dd?w=1400&q=80",
    "cairo":        "https://images.unsplash.com/photo-1572252009286-268acec5ca0a?w=1400&q=80",
    "istanbul":     "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?w=1400&q=80",
    "amsterdam":    "https://images.unsplash.com/photo-1512470876302-972faa2aa9a4?w=1400&q=80",
    "barcelona":    "https://images.unsplash.com/photo-1583422409516-2895a77efded?w=1400&q=80",
    "toronto":      "https://images.unsplash.com/photo-1517090504586-fde19ea6066f?w=1400&q=80",
    "hong kong":    "https://images.unsplash.com/photo-1536599018102-9f803c140fc1?w=1400&q=80",
    "busan":        "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?w=1400&q=80",
    "kuala lumpur": "https://images.unsplash.com/photo-1596422846543-75c6fc197f07?w=1400&q=80",
    "doha":         "https://images.unsplash.com/photo-1545167496-58e8d9e0b413?w=1400&q=80",
    "rio de janeiro":"https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=1400&q=80",
    "cape town":    "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=1400&q=80",
    "vienna":       "https://images.unsplash.com/photo-1516550893923-42d28e5677af?w=1400&q=80",
    "beijing":      "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=1400&q=80",
    "shanghai":     "https://images.unsplash.com/photo-1538428494232-9c0d8a3ab403?w=1400&q=80",
    "moscow":       "https://images.unsplash.com/photo-1513326738677-b964603b136d?w=1400&q=80",
    "rome":         "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=1400&q=80",
}

def get_city_bg_url(city_name: str) -> str:
    """Return a landmark image URL for the city, falling back to Unsplash search."""
    key = city_name.lower().strip()
    if key in CITY_BG_MAP:
        return CITY_BG_MAP[key]
    # Fallback: Unsplash search by city name + landmark
    query = city_name.replace(" ", "%20")
    return f"https://source.unsplash.com/1400x900/?{query},landmark,skyline"

def set_city_background(city_name: str):
    """Inject CSS to set a city landmark as page background with dark overlay."""
    url = get_city_bg_url(city_name)
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image:
                linear-gradient(rgba(10,12,20,0.72) 0%, rgba(10,12,20,0.90) 100%),
                url("{url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER
# ══════════════════════════════════════════════════════════════════════════════
def render():
    st.title("Job Opportunities & Cost of Living")


    edf = load_economic()
    env = load_data()

    cities_list = sorted(edf["city"].tolist())
    session_city = st.session_state.get("place_name", "Chennai")

    # If session city not in dataset, dynamically add it
    found_match = False
    for c in cities_list:
        if session_city.lower() in c.lower() or c.lower() in session_city.lower():
            session_city = c
            found_match = True
            break
            
    if not found_match and session_city:
        from utils.economic_api import get_economic_data
        new_data = get_economic_data(session_city)
        edf = pd.concat([edf, pd.DataFrame([new_data])], ignore_index=True)
        cities_list = sorted(edf["city"].tolist())
        
    # FORCE INJECTION IF ALL ELSE FAILS
    if session_city and not any(session_city.lower() == str(c).lower() for c in cities_list):
        cities_list.append(session_city)
        cities_list = sorted(cities_list)

    default_idx  = next(
        (i for i, c in enumerate(cities_list) if session_city.lower() == str(c).lower()), 0
    )

    # ── City selector ─────────────────────────────────────────────────────────
    c1, c2 = st.columns([4, 1])
    with c1:
        city = st.selectbox("Select city", cities_list, 
                            index=default_idx, 
                            key=f"sel_p5_main_{session_city}")
    with c2:
        live_api = st.toggle("Live API data", value=False,
                             help="Fetch real GDP/unemployment from World Bank")

    # Apply city landmark background immediately after city is known
    # Background is handled globally by app.py

    row  = edf[edf["city"] == city].iloc[0]

    # Live API enrichment
    if live_api:
        try:
            from utils.economic_api import get_economic_data
            live = get_economic_data(city, use_live=True)
            for k in ["gdp_per_capita_usd","avg_monthly_salary_usd",
                      "unemployment_rate","affordability_score","job_market_score"]:
                if k in live:
                    row = row.copy()
                    row[k] = live[k]
            src = live.get("data_source","csv_only")
            if src == "live_api+csv":
                st.success("🌐 Enriched with live World Bank data")
            else:
                st.info("📂 Using synthetic dataset (API unavailable offline)")
        except Exception as e:
            st.warning(f"Live API unavailable: {e}")

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — Summary cards
    # ══════════════════════════════════════════════════════════════════════════
    st.subheader(f"📍 {city} — Economic Overview")

    jg, jc = job_grade(float(row["job_market_score"]))
    uc = unemp_color(float(row["unemployment_rate"]))

    st.markdown(
        f"""<div style="background:#1e2130;border-radius:14px;padding:18px 22px;
            margin-bottom:16px;display:flex;align-items:center;gap:24px;flex-wrap:wrap">
            <div style="text-align:center">
                <div style="font-size:12px;color:#aaa">Job Market Grade</div>
                <div style="font-size:56px;font-weight:900;color:{jc};line-height:1">{jg}</div>
            </div>
            <div style="flex:1;min-width:200px">
                <div style="font-size:13px;color:#ccc;margin-bottom:6px">
                    <b>Job Market Score:</b> {row['job_market_score']}/100 &nbsp;|&nbsp;
                    <b>GDP/capita:</b> ${int(row['gdp_per_capita_usd']):,} &nbsp;|&nbsp;
                    <b>Unemployment:</b>
                    <span style="color:{uc}">{row['unemployment_rate']}%</span>
                </div>
                <div style="font-size:13px;color:#ccc">
                    <b>Tech Hub Score:</b> {row['tech_hub_score']}/10 &nbsp;|&nbsp;
                    <b>Industry Diversity:</b> {row['industry_diversity_score']}/10 &nbsp;|&nbsp;
                    <b>Affordability:</b> {row['affordability_score']}/100
                </div>
            </div>
        </div>""",
        unsafe_allow_html=True
    )

    # 4 metric cards row
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        metric_card("💰 Avg Monthly Salary", f"${int(row['avg_monthly_salary_usd']):,}",
                    "USD", "#4CAF50",
                    f"GDP/capita: ${int(row['gdp_per_capita_usd']):,}/yr")
    with mc2:
        metric_card("🏠 Rent (1BHK)", f"${int(row['rent_1bhk_usd']):,}",
                    "/ month", "#2196F3",
                    f"Transport: ${int(row['transport_monthly_usd'])}/mo")
    with mc3:
        metric_card("📉 Unemployment", f"{row['unemployment_rate']}",
                    "%", unemp_color(float(row['unemployment_rate'])),
                    "Lower = better job availability")
    with mc4:
        metric_card("🎯 Affordability", f"{row['affordability_score']}",
                    "/ 100", score_color(float(row['affordability_score'])),
                    "Salary ÷ cost of living")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — Salary vs Cost + Industry radar
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    left, right = st.columns([1.2, 1])

    with left:
        st.subheader("💵 Salary vs Monthly Expenses")
        fig_sc, savings = salary_cost_chart(
            float(row["avg_monthly_salary_usd"]),
            float(row["cost_of_living_index"]),
            city
        )
        st.plotly_chart(fig_sc, use_container_width=True)

        sav_col = "#4CAF50" if savings > 0 else "#F44336"
        sav_label = "monthly savings" if savings > 0 else "monthly deficit"
        st.markdown(
            f"""<div style="background:#1e2130;border-radius:10px;padding:12px 16px;
                text-align:center;border:1px solid {'#4CAF50' if savings>0 else '#F44336'}22">
                <span style="color:#aaa;font-size:13px">Estimated </span>
                <span style="color:{sav_col};font-size:20px;font-weight:700">
                    {'+'if savings>0 else ''}${savings:,.0f}
                </span>
                <span style="color:#aaa;font-size:13px"> {sav_label}</span>
            </div>""",
            unsafe_allow_html=True
        )

        # Cost breakdown
        st.markdown("#### 🧾 Monthly Cost Breakdown")
        cost_items = {
            "Rent (1BHK)":   float(row["rent_1bhk_usd"]),
            "Food (30 meals)": float(row["meal_cost_usd"]) * 30,
            "Transport":     float(row["transport_monthly_usd"]),
            "Utilities est.":float(row["cost_of_living_index"]) * 2.5,
            "Misc / leisure":float(row["cost_of_living_index"]) * 3.0,
        }
        total_cost = sum(cost_items.values())
        for item, val in cost_items.items():
            pct = val / total_cost * 100
            st.markdown(
                f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
                    <div style="font-size:13px;color:#aaa;width:140px">{item}</div>
                    <div style="flex:1;background:#333;border-radius:3px;height:16px">
                        <div style="background:#2196F3;width:{pct}%;height:16px;
                            border-radius:3px;display:flex;align-items:center;
                            padding-left:6px">
                            <span style="font-size:11px;color:#fff">${val:,.0f}</span>
                        </div>
                    </div>
                    <div style="font-size:11px;color:#666;width:36px">{pct:.0f}%</div>
                </div>""",
                unsafe_allow_html=True
            )

    with right:
        st.subheader("🏭 Industry Strength")
        st.plotly_chart(industry_radar(row), use_container_width=True)

        # Score rings
        r1, r2, r3 = st.columns(3)
        with r1:
            score_ring("Tech Hub", float(row["tech_hub_score"]), 10,
                       score_color(float(row["tech_hub_score"])*10))
        with r2:
            score_ring("Job Market", float(row["job_market_score"]), 100,
                       score_color(float(row["job_market_score"])))
        with r3:
            score_ring("Ind. Diversity", float(row["industry_diversity_score"]), 10,
                       score_color(float(row["industry_diversity_score"])*10))



    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — Global Rankings + Map
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("🌍 Global Rankings")

    tab1, tab2, tab3, tab4 = st.tabs([
        "💰 Highest Salaries", "🎯 Best Affordability",
        "📉 Lowest Unemployment", "🗺️ World Map"
    ])
    with tab1:
        st.plotly_chart(
            top_cities_chart(edf, "avg_monthly_salary_usd", "Avg Monthly Salary (USD)", city),
            use_container_width=True
        )

    with tab2:
        st.plotly_chart(
            top_cities_chart(edf, "affordability_score", "Affordability Score", city),
            use_container_width=True
        )

    with tab3:
        low_unemp = edf.nsmallest(15,"unemployment_rate")[["city","unemployment_rate"]]
        colors = ["#4CAF50" if c==city else "#2a3a4a" for c in low_unemp["city"]]
        fig_u = go.Figure(go.Bar(
            x=low_unemp["unemployment_rate"], y=low_unemp["city"],
            orientation="h",
            marker=dict(color=colors),
            text=[f"{v}%" for v in low_unemp["unemployment_rate"]],
            textposition="outside", textfont=dict(color="white",size=11)
        ))
        fig_u.update_layout(
            title="15 cities with lowest unemployment",
            paper_bgcolor="#0f1117", plot_bgcolor="#111827",
            font=dict(color="white"), height=420,
            margin=dict(l=10,r=60,t=45,b=10),
            xaxis=dict(gridcolor="#333",title="Unemployment %"),
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig_u, use_container_width=True)

    with tab4:
        st.plotly_chart(salary_scatter_map(edf, city), use_container_width=True)
        st.caption("Bubble size = salary · Color = affordability (green = high, red = low)")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 5 — Opportunity Score card
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("🎯 Should You Work Here?")

    sal   = float(row["avg_monthly_salary_usd"])
    aff   = float(row["affordability_score"])
    job   = float(row["job_market_score"])
    unemp = float(row["unemployment_rate"])
    tech  = float(row["tech_hub_score"])

    opportunity_score = round(
        sal/10000*30 + aff*0.25 + job*0.25 + (10-min(unemp,10))/10*20, 1
    )
    opportunity_score = min(100, opportunity_score)

    og, oc = job_grade(opportunity_score)

    pros = []
    if sal > 2000:  pros.append(f"High salary (${sal:,.0f}/mo)")
    if aff > 60:    pros.append(f"Good affordability ({aff}/100)")
    if unemp < 5:   pros.append(f"Low unemployment ({unemp}%)")
    if tech > 7:    pros.append(f"Strong tech industry ({tech}/10)")
    if job > 42:    pros.append(f"Strong job market ({job}/100)")

    col_pros, col_score = st.columns([1, 1])
    with col_pros:
        st.markdown("#### ✅ Pros")
        for p in pros if pros else ["Limited advantages identified"]:
            st.markdown(f"- {p}")
    with col_score:
        st.markdown(
            f"""<div style="background:#1e2130;border-radius:14px;padding:20px;
                text-align:center">
                <div style="font-size:13px;color:#aaa">Opportunity Score</div>
                <div style="font-size:60px;font-weight:900;color:{oc};
                    line-height:1.1">{og}</div>
                <div style="font-size:26px;color:#ddd">{opportunity_score:.1f}/100</div>
                <div style="font-size:12px;color:#666;margin-top:6px">{city}</div>
            </div>""",
            unsafe_allow_html=True
        )
