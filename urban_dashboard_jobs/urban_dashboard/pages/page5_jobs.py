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
    return pd.read_csv("data/economic_data.csv")

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
        coloraxis_colorbar=dict(title="Affordability", tickfont=dict(color="white"),
                                titlefont=dict(color="white"))
    )
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER
# ══════════════════════════════════════════════════════════════════════════════
def render():
    st.title("💼 Job Opportunities & Cost of Living")

    edf = load_economic()
    env = load_data()

    cities_list = sorted(edf["city"].tolist())
    session_city = st.session_state.get("place_name", "Chennai")
    default_idx  = next(
        (i for i, c in enumerate(cities_list) if session_city.lower() in c.lower()), 0
    )

    # ── City selector + compare ───────────────────────────────────────────────
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        city = st.selectbox("Select city", cities_list, index=default_idx)
    with c2:
        compare_on = st.checkbox("Compare with another city")
        city2 = None
        if compare_on:
            city2 = st.selectbox("Compare with",
                                 [c for c in cities_list if c != city])
    with c3:
        live_api = st.toggle("Live API data", value=False,
                             help="Fetch real GDP/unemployment from World Bank")

    row  = edf[edf["city"] == city].iloc[0]
    row2 = edf[edf["city"] == city2].iloc[0] if city2 else None

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
    # SECTION 3 — Comparison
    # ══════════════════════════════════════════════════════════════════════════
    if city2 and row2 is not None:
        st.markdown("---")
        st.subheader(f"⚖️ {city} vs {city2}")

        compare_cols = ["avg_monthly_salary_usd","affordability_score",
                        "job_market_score","unemployment_rate",
                        "tech_hub_score","industry_diversity_score"]
        labels = ["Salary (USD)","Affordability","Job Market",
                  "Unemployment %","Tech Score","Industry Div."]

        fig_cmp = go.Figure()
        v1 = [float(row[c])  for c in compare_cols]
        v2 = [float(row2[c]) for c in compare_cols]

        # Normalise for radar
        maxv = [max(a,b,1) for a,b in zip(v1,v2)]
        v1n  = [a/m*100 for a,m in zip(v1,maxv)]
        v2n  = [a/m*100 for a,m in zip(v2,maxv)]

        fig_cmp.add_trace(go.Scatterpolar(
            r=v1n+[v1n[0]], theta=labels+[labels[0]],
            fill="toself", fillcolor="rgba(76,175,80,0.2)",
            line=dict(color="#4CAF50",width=2), name=city
        ))
        fig_cmp.add_trace(go.Scatterpolar(
            r=v2n+[v2n[0]], theta=labels+[labels[0]],
            fill="toself", fillcolor="rgba(244,67,54,0.2)",
            line=dict(color="#F44336",width=2), name=city2
        ))
        fig_cmp.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0,100],
                                tickfont=dict(size=9,color="#aaa"),
                                gridcolor="#333"),
                angularaxis=dict(tickfont=dict(size=11,color="#ccc"),
                                 gridcolor="#333"),
                bgcolor="#0f1117"
            ),
            paper_bgcolor="#0f1117", font=dict(color="white"),
            height=380, showlegend=True,
            legend=dict(font=dict(color="white")),
            margin=dict(l=50,r=50,t=20,b=20)
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

        # Side by side numbers
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(f"**{city}**")
            for label, col in zip(labels, compare_cols):
                val = float(row[col])
                unit = "%" if col == "unemployment_rate" else ("$" if "salary" in col else "")
                prefix = unit if unit == "$" else ""
                suffix = unit if unit == "%" else ""
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"padding:4px 0;border-bottom:1px solid #222;font-size:13px'>"
                    f"<span style='color:#aaa'>{label}</span>"
                    f"<span style='color:#4CAF50'>{prefix}{val:,.1f}{suffix}</span></div>",
                    unsafe_allow_html=True
                )
        with sc2:
            st.markdown(f"**{city2}**")
            for label, col in zip(labels, compare_cols):
                val = float(row2[col])
                unit = "%" if col == "unemployment_rate" else ("$" if "salary" in col else "")
                prefix = unit if unit == "$" else ""
                suffix = unit if unit == "%" else ""
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"padding:4px 0;border-bottom:1px solid #222;font-size:13px'>"
                    f"<span style='color:#aaa'>{label}</span>"
                    f"<span style='color:#F44336'>{prefix}{val:,.1f}{suffix}</span></div>",
                    unsafe_allow_html=True
                )

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
        # Find city rank
        rank = edf.sort_values("avg_monthly_salary_usd", ascending=False).reset_index()
        city_rank = rank[rank["city"]==city].index[0]+1
        st.info(f"📍 **{city}** ranks **#{city_rank}** out of 273 cities for average salary.")

    with tab2:
        st.plotly_chart(
            top_cities_chart(edf, "affordability_score", "Affordability Score", city),
            use_container_width=True
        )
        rank = edf.sort_values("affordability_score", ascending=False).reset_index()
        city_rank = rank[rank["city"]==city].index[0]+1
        st.info(f"📍 **{city}** ranks **#{city_rank}** out of 273 cities for affordability.")

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

    pros, cons = [], []
    if sal > 2000:  pros.append(f"High salary (${sal:,.0f}/mo)")
    if aff > 60:    pros.append(f"Good affordability ({aff}/100)")
    if unemp < 5:   pros.append(f"Low unemployment ({unemp}%)")
    if tech > 7:    pros.append(f"Strong tech industry ({tech}/10)")
    if job > 42:    pros.append(f"Strong job market ({job}/100)")

    if sal < 800:   cons.append(f"Low salary (${sal:,.0f}/mo)")
    if aff < 40:    cons.append(f"Low affordability ({aff}/100)")
    if unemp > 10:  cons.append(f"High unemployment ({unemp}%)")
    if tech < 5:    cons.append(f"Limited tech jobs ({tech}/10)")

    col_pros, col_score, col_cons = st.columns([1, 1, 1])
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
    with col_cons:
        st.markdown("#### ⚠️ Cons")
        for c in cons if cons else ["No major drawbacks identified"]:
            st.markdown(f"- {c}")
