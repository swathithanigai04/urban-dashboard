"""
Page 2 — Environmental Analysis
Shows all metrics, interactive folium map with overlays, city comparison
"""
import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import plotly.express as px
from utils.helpers import load_data, compute_extended_metrics, grade, aqi_label
from utils.economic_api import get_economic_data
# from utils.city_background import set_city_background <-- REMOVED

# ── Colour helpers ────────────────────────────────────────────────────────────
def ndvi_color(v):
    if v > 0.5: return "#1B5E20"
    if v > 0.3: return "#4CAF50"
    if v > 0.15: return "#CDDC39"
    return "#FF5722"

def metric_card(label, value, unit="", colour="#4CAF50", help_text=""):
    title_attr = f' title="{help_text}"' if help_text else ""
    label_style = ' style="border-bottom: 1px dotted #888; cursor: help;"' if help_text else ""
    st.markdown(
        f"""<div class="metric-card" style="border-left-color:{colour}; background: var(--secondary-background-color); color: var(--text-color);" {title_attr}>
              <h4{label_style} style="color: var(--text-color); opacity: 0.7;">{label}</h4>
              <p style="color: var(--text-color);">{value} <span style="font-size:14px; opacity: 0.6;">{unit}</span></p>
            </div>""",
        unsafe_allow_html=True
    )

# ── Radar chart ───────────────────────────────────────────────────────────────
def radar_chart(metrics_dict, city_name):
    categories = ["NDVI×100", "Climate\nResilience", "Livability",
                  "Green\nCover", "Rainfall\n/31", "AQI\nInverse"]
    values = [
        metrics_dict["NDVI"] * 100,
        metrics_dict["Climate Resilience"],
        metrics_dict["Livability"],
        metrics_dict["Green Cover (%)"],
        np.clip(metrics_dict["Rainfall"] / 31.19, 0, 100),
        (6 - metrics_dict["AQI"]) / 5 * 100,
    ]
    values_closed = values + [values[0]]
    cats_closed   = categories + [categories[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed, theta=cats_closed,
        fill="toself", fillcolor="rgba(76,175,80,0.25)",
        line=dict(color="#4CAF50", width=2),
        name=city_name
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(size=10),
                            gridcolor="#444444"),
            angularaxis=dict(tickfont=dict(size=11)),
            bgcolor="rgba(0,0,0,0)"
        ),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=50, r=50, t=30, b=30),
        height=320
    )
    return fig

# ── Trend sparkline from dataset ──────────────────────────────────────────────
def sparkline(df, metric, city_name):
    top = df.nlargest(15, metric)[["city", metric]].sort_values(metric)
    highlight = [c == city_name for c in top["city"]]
    colors = ["#4CAF50" if h else "#555" for h in highlight]
    fig = px.bar(top, x="city", y=metric,
                 color=colors, color_discrete_map="identity",
                 title=f"Top 15 cities — {metric}")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=80),
        height=280,
        xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
    )
    return fig

def render():
    st.title("Environmental Analysis")

    df = load_data()

    # ── City selector ─────────────────────────────────────────────────────────
    col_sel, col_cmp = st.columns([2, 2])

    with col_sel:
        session_city = st.session_state.get("place_name", "Chennai")
        cities_list = sorted(df["city"].tolist())
        default_idx = next(
            (i for i, c in enumerate(cities_list) if session_city.lower() in c.lower()), 0
        )
        city1 = st.selectbox("Primary city", cities_list, index=default_idx, key=f"sel_p2_{session_city}")

    # Background is handled globally by app.py

    with col_cmp:
        compare = st.checkbox("Compare with another city")
        city2 = None
        if compare:
            other_cities = [c for c in cities_list if c != city1]
            city2 = st.selectbox("Compare with", other_cities)

    row1 = df[df["city"] == city1].iloc[0]
    m1   = compute_extended_metrics(row1)

    row2, m2 = None, None
    if city2:
        row2 = df[df["city"] == city2].iloc[0]
        m2   = compute_extended_metrics(row2)

    st.markdown("---")

    # ── Layout: metrics left, map right ──────────────────────────────────────
    left, right = st.columns([1, 1])

    with left:
        st.subheader(f"📍 {city1}")

        # City Health Score (composite 0–100)
        health = round(
            m1["NDVI"] * 20 +
            (1 - m1["AQI"] / 5) * 20 +
            m1["Livability"] / 84 * 20 +
            m1["Climate Resilience"] / 100 * 20 +
            np.clip(1 - m1["Heat Stress (0-10)"] / 10, 0, 1) * 20,
            1
        )
        g, gc = grade(m1["Livability"], "Livability")
        aq_label, aq_col = aqi_label(m1["AQI"])

        st.markdown(
            f"""<div style="background:var(--secondary-background-color);border-radius:12px;padding:16px;
                margin-bottom:14px;text-align:center;box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="font-size:13px;color:var(--text-color);opacity:0.7;margin-bottom:4px">City Health Score</div>
            <div style="font-size:52px;font-weight:800;color:#4CAF50">{health}</div>
            <div style="font-size:14px;color:var(--text-color);opacity:0.6">/100</div>
            <span style="background:{gc};color:#fff;padding:3px 14px;
                border-radius:20px;font-weight:700;margin-top:8px;display:inline-block">
                Grade {g}</span>
            </div>""",
            unsafe_allow_html=True
        )

        # Metric cards in 2 columns
        mc1, mc2 = st.columns(2)
        with mc1:
            metric_card("🌿 NDVI", f"{m1['NDVI']:.3f}", colour=ndvi_color(m1["NDVI"]), help_text="Normalized Difference Vegetation Index: Measures healthy green vegetation. Closer to 1 means more greenery.")
            metric_card("🏙️ Urbanization", f"{m1['Urbanization Score']:.0f}", "/100", "#FF9800", help_text="Level of urban development. Higher score means more built-up city areas and concrete.")
            metric_card("🌡️ Land Temp", f"{m1['Land Surface Temp']:.1f}", "°C", "#FF5722", help_text="Surface temperature of the ground. Usually higher in cities due to concrete buildings absorbing heat.")
            metric_card("☔ Rainfall", f"{m1['Rainfall']:.0f}", "mm", "#2196F3", help_text="Average precipitation amount in millimeters.")
        with mc2:
            metric_card("🏗️ NDBI", f"{m1['NDBI']:.3f}", colour="#795548", help_text="Normalized Difference Built-up Index: Measures density of buildings and concrete. Higher values mean more artificial surfaces.")
            metric_card("🔥 Heat Stress", f"{m1['Heat Stress (0-10)']:.1f}", "/10", "#FF5722", help_text="Risk level for extreme heat events and thermal discomfort. 10 is the highest risk.")
            metric_card("🌊 Flood Risk", f"{m1['Flood Risk (0-10)']:.1f}", "/10", "#1565C0", help_text="Vulnerability to flooding events. 10 is the highest risk.")
            metric_card("🛡️ Climate Resilience", f"{m1['Climate Resilience']:.0f}", "/100", "#009688", help_text="Overall ability of the city to withstand and recover from climate-related hazards.")

        st.markdown(
            f"""<div class="metric-card" style="border-left-color:{aq_col}" title="Measures air pollution levels. Lower index means cleaner, healthier air for breathing.">
                <h4 style="border-bottom: 1px dotted #888; cursor: help;">💨 Air Quality Index (AQI)</h4>
                <p>{int(m1['AQI'])} <span style="font-size:14px;color:{aq_col}">
                {aq_label}</span></p></div>""",
            unsafe_allow_html=True
        )
        st.markdown(
            f"""<div class="metric-card" style="border-left-color:#9C27B0; background: var(--secondary-background-color); color: var(--text-color);" title="Overall score out of 100 estimating quality of life based on environmental and urban factors.">
                <h4 style="border-bottom: 1px dotted #888; cursor: help; color: var(--text-color); opacity: 0.7;">🏡 Livability Score</h4>
                <p style="color: var(--text-color);">{m1['Livability']:.2f} <span style="font-size:14px; opacity: 0.6;">/100</span>
                </p></div>""",
            unsafe_allow_html=True
        )

    with right:
        st.subheader("🗺️ Interactive Map")
        lat = float(row1["latitude"])
        lon = float(row1["longitude"])
        m = folium.Map(location=[lat, lon], zoom_start=10, tiles="CartoDB dark_matter")

        # City marker
        folium.CircleMarker(
            location=[lat, lon], radius=14,
            color=ndvi_color(m1["NDVI"]), fill=True,
            fill_color=ndvi_color(m1["NDVI"]), fill_opacity=0.6,
            popup=folium.Popup(
                f"<b>{city1}</b><br>"
                f"NDVI: {m1['NDVI']:.3f}<br>"
                f"AQI: {int(m1['AQI'])} ({aqi_label(m1['AQI'])[0]})<br>"
                f"Livability: {m1['Livability']:.1f}",
                max_width=200
            )
        ).add_to(m)

        # All dataset cities as small dots
        for _, r in df.iterrows():
            if r["city"] == city1:
                continue
            folium.CircleMarker(
                location=[float(r["latitude"]), float(r["longitude"])],
                radius=5,
                color=ndvi_color(float(r["NDVI"])),
                fill=True, fill_opacity=0.5,
                popup=folium.Popup(
                    f"<b>{r['city']}</b><br>NDVI: {r['NDVI']:.3f}", max_width=150
                )
            ).add_to(m)

        # Compare city marker
        if city2 and row2 is not None:
            folium.Marker(
                location=[float(row2["latitude"]), float(row2["longitude"])],
                popup=city2,
                icon=folium.Icon(color="red", icon="star", prefix="fa")
            ).add_to(m)

        st_folium(m, height=420, use_container_width=True)

        # Radar chart
        st.plotly_chart(radar_chart(m1, city1), use_container_width=True)

    # ── Comparison section ────────────────────────────────────────────────────
    if city2 and m2:
        st.markdown("---")
        st.subheader(f"⚖️ {city1} vs {city2}")
        compare_metrics = [
            "NDVI", "Livability", "Climate Resilience",
            "Urbanization Score", "Heat Stress (0-10)",
            "Flood Risk (0-10)", "Green Cover (%)"
        ]
        c1vals = [m1[k] for k in compare_metrics]
        c2vals = [m2[k] for k in compare_metrics]

        fig = go.Figure()
        fig.add_trace(go.Bar(name=city1, x=compare_metrics, y=c1vals,
                             marker_color="#4CAF50"))
        fig.add_trace(go.Bar(name=city2, x=compare_metrics, y=c2vals,
                             marker_color="#F44336"))
        fig.update_layout(
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=350,
            margin=dict(l=20, r=20, t=20, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Economic Analysis ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("💸 Economic Insights")
    econ1 = get_economic_data(city1)
    
    ec1, ec2, ec3, ec4 = st.columns(4)
    with ec1:
        metric_card("💰 Avg Salary", f"${econ1['avg_monthly_salary_usd']:,}", "/mo", "#4CAF50", help_text="Average monthly salary after tax in USD.")
    with ec2:
        metric_card("🏙️ Cost of Living", f"{econ1['cost_of_living_index']:.1f}", "idx", "#FF9800", help_text="Relative indicator of consumer goods prices. New York City is typically 100.")
    with ec3:
        metric_card("💎 Affordability", f"{econ1['affordability_score']:.1f}", "/100", "#2196F3", help_text="Score based on local purchasing power compared to cost of living.")
    with ec4:
        metric_card("🏦 GDP p.c.", f"${econ1['gdp_per_capita_usd']:,}", "", "#9C27B0", help_text="Gross Domestic Product per capita in USD.")
        
    st.caption(f"Data Source: **{econ1['data_source']}**")
    
    if city2 and m2:
        econ2 = get_economic_data(city2)
        st.markdown(f"**⚖️ Compare Economic with {city2}**")
        ce1, ce2 = st.columns(2)
        ce1.metric(f"Avg Salary ({city2})", f"${econ2['avg_monthly_salary_usd']:,}")
        ce2.metric(f"Affordability ({city2})", f"{econ2['affordability_score']:.1f}")

    # ── Dataset-wide charts ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📈 Dataset Insights")
    tab1, tab2, tab3 = st.tabs(["NDVI Rankings", "Livability Rankings", "Temp vs NDVI"])

    with tab1:
        st.plotly_chart(sparkline(df, "NDVI", city1), use_container_width=True)
    with tab2:
        st.plotly_chart(sparkline(df, "Livability", city1), use_container_width=True)
    with tab3:
        fig2 = px.scatter(
            df, x="Temperature", y="NDVI", color="Livability",
            hover_name="city", size="Rainfall",
            color_continuous_scale="Viridis",
            title="Temperature vs NDVI (bubble size = Rainfall)"
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=380
        )
        st.plotly_chart(fig2, use_container_width=True)
