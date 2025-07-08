# ───────────────────────────────────────────────────────────
#  🌍  GLOBAL TEMPERATURE STORY DASHBOARD  (Streamlit + Altair)
# ───────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import altair as alt

# ─── Page set‑up ────────────────────────────────────────────
st.set_page_config(page_title="Global Temperature Dashboard",
                   page_icon="🌍",
                   layout="wide")
st.title("🌍 Global Temperature Story  🌡️")

# ─── Data load & reshape ───────────────────────────────────
df = pd.read_csv(
    "Indicator_3_1_Climate_Indicators_Annual_Mean_Global_Surface_Temperature_577579683071085080.csv"
)

year_cols = [c for c in df.columns if c.isdigit()]
df_long = df.melt(
    id_vars=["Country", "ISO2", "ISO3", "Indicator", "Unit"],
    value_vars=year_cols,
    var_name="Year",
    value_name="TempChange"
)
df_long["Year"] = df_long["Year"].astype(int)

# ─── Development Status Mapping ────────────────────────────
developed_iso3 = ["USA", "CAN", "GBR", "DEU", "FRA", "JPN",
                  "AUS", "NZL", "NOR", "SWE", "CHE"]
df_long["DevStatus"] = df_long["ISO3"].apply(
    lambda x: "Developed" if x in developed_iso3 else "Developing"
)

# ─── Lists for filters ─────────────────────────────────────
all_countries = ["All"] + sorted(df_long["Country"].unique())
all_years     = ["All"] + sorted(df_long["Year"].unique())
year_min, year_max = int(df_long["Year"].min()), int(df_long["Year"].max())

# ─── Sidebar: two independent filter sections ──────────────
with st.sidebar.expander("📊 Charts Filters", expanded=True):
    chart_country = st.selectbox("Country", all_countries, key="chart_country")
    chart_year    = st.selectbox("Year", all_years,     key="chart_year")

with st.sidebar.expander("🌐 DevStatus Filters", expanded=False):
    dev_year_range = st.slider("Year Range",
                               min_value=year_min,
                               max_value=year_max,
                               value=(year_min, year_max),
                               step=1,
                               key="dev_year_range")

# ── Data after filters ─────────────────────────────────────
filtered_chart = df_long.copy()
if chart_country != "All":
    filtered_chart = filtered_chart[filtered_chart["Country"] == chart_country]
if chart_year != "All":
    filtered_chart = filtered_chart[filtered_chart["Year"] == int(chart_year)]

filtered_dev = df_long[
    (df_long["Year"] >= dev_year_range[0]) &
    (df_long["Year"] <= dev_year_range[1])
].copy()

# ─── Tabs layout ───────────────────────────────────────────
tab_charts, tab_dev, tab_data = st.tabs(
    ["📊 Charts", "🌐 Developed vs Developing", "📋 Data"]
)

# ─── Altair settings ───────────────────────────────────────
alt.data_transformers.disable_max_rows()
sel_country = alt.selection_point(fields=["Country"], empty="all")

# ───────────────────────────────────────────────────────────
# 📊 CHARTS TAB
# ───────────────────────────────────────────────────────────
with tab_charts:

    # 1️⃣ Scatter plot
    if chart_country == "All":
        sample_countries = df_long["Country"].unique()[:10]
        scatter_src = df_long[df_long["Country"].isin(sample_countries)]
    else:
        scatter_src = filtered_chart

    scatter = (
        alt.Chart(scatter_src)
        .mark_circle(size=60)
        .encode(
            x=alt.X("Year:O", axis=alt.Axis(labelAngle=0)),
            y="TempChange:Q",
            color=alt.Color("TempChange:Q",
                            scale=alt.Scale(scheme="redblue",
                                            reverse=True,
                                            domainMid=0),
                            legend=alt.Legend(title="Temp Change (°C)")),
            opacity=alt.condition(sel_country, alt.value(1), alt.value(0.15)),
            tooltip=["Country", "Year", "TempChange"]
        )
        .transform_filter(sel_country)
        .properties(
            width=750, height=400,
            title=f"Temperature Change Over Time – "
                  f"{chart_country if chart_country!='All' else 'All Countries'}"
        )
    )

    # 2️⃣ Bar plot: countries with decreasing variability
    stats_base = df_long.copy()
    if chart_country != "All":
        stats_base = stats_base[stats_base["Country"] == chart_country]

    early = (stats_base[stats_base["Year"] <= 1992]
             .groupby("Country")["TempChange"].std()
             .reset_index(name="Std_Early"))
    late  = (stats_base[stats_base["Year"] >= 1993]
             .groupby("Country")["TempChange"].std()
             .reset_index(name="Std_Late"))

    std_comp = early.merge(late, on="Country")
    std_comp["Delta_Std"] = std_comp["Std_Late"] - std_comp["Std_Early"]
    decreasing = std_comp[std_comp["Delta_Std"] < 0].sort_values("Delta_Std")
    xmin = decreasing["Delta_Std"].min() if not decreasing.empty else -0.1

    bar = (
        alt.Chart(decreasing)
        .mark_bar()
        .encode(
            x=alt.X("Delta_Std:Q",
                    scale=alt.Scale(domain=[0, xmin]),
                    title="Δ Std Dev (1993–2024 – 1961–1992)"),
            y=alt.Y("Country:N", sort="-x"),
            color=alt.Color("Delta_Std:Q",
                            scale=alt.Scale(scheme="redblue",
                                            reverse=True,
                                            domainMid=0),
                            legend=alt.Legend(title="Δ Std Dev")),
            opacity=alt.condition(sel_country, alt.value(1), alt.value(0.4)),
            stroke=alt.condition(sel_country, alt.value("white"), alt.value(None)),
            tooltip=["Country", "Std_Early", "Std_Late", "Delta_Std"]
        )
        .add_params(sel_country)
        .properties(width=750, height=600,
                    title="Countries with Decreasing Temperature Variability")
    )

    st.altair_chart(
        alt.vconcat(scatter, bar).resolve_scale(color="independent"),
        use_container_width=True
    )

# ───────────────────────────────────────────────────────────
# 🌐 DEVELOPED vs DEVELOPING TAB
# ───────────────────────────────────────────────────────────
with tab_dev:
    st.subheader("Average Temperature Change: Developed vs Developing")

    # 🔄 Interactive selection on DevStatus
    dev_sel = alt.selection_multi(fields=["DevStatus"], bind="legend")

    # 1️⃣ Line chart (yearly averages)
    dev_avg = (filtered_dev
               .groupby(["Year", "DevStatus"])["TempChange"]
               .mean()
               .reset_index())

    line_chart = (
        alt.Chart(dev_avg)
        .mark_line(point=True)
        .encode(
            x=alt.X("Year:O", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("TempChange:Q", title="Avg Temp Change (°C)"),
            color=alt.Color("DevStatus:N",
                            scale=alt.Scale(domain=["Developed", "Developing"],
                                            range=["#2ca02c", "#ff7f0e"]),
                            legend=alt.Legend(title="Group")),
            opacity=alt.condition(dev_sel, alt.value(1.0), alt.value(0.15)),
            tooltip=["Year", "DevStatus", "TempChange"]
        )
        .add_params(dev_sel)
        .properties(
            title=f"Average Temp Change ({dev_year_range[0]}–{dev_year_range[1]})",
            width=750, height=400
        )
    )
    st.altair_chart(line_chart, use_container_width=True)

    # 2️⃣ Bar chart (5‑year grouped averages)
    filtered_dev["YearGroup"] = (filtered_dev["Year"] // 5) * 5
    dev_bar = (filtered_dev
               .groupby(["YearGroup", "DevStatus"])["TempChange"]
               .mean()
               .reset_index())

    bar_chart = (
        alt.Chart(dev_bar)
        .mark_bar()
        .encode(
            x=alt.X("YearGroup:O", title="5‑Year Group"),
            y=alt.Y("TempChange:Q", title="Avg Temp Change (°C)"),
            color=alt.Color("DevStatus:N",
                            scale=alt.Scale(domain=["Developed", "Developing"],
                                            range=["#2ca02c", "#ff7f0e"]),
                            legend=None),
            opacity=alt.condition(dev_sel, alt.value(1.0), alt.value(0.25)),
            tooltip=["YearGroup", "DevStatus", "TempChange"]
        )
        .add_params(dev_sel)
        .properties(
            title="5‑Year Avg Temp Change by Development Status",
            width=750, height=400
        )
    )
    st.altair_chart(bar_chart, use_container_width=True)

# ───────────────────────────────────────────────────────────
# 📋 DATA TAB
# ───────────────────────────────────────────────────────────
with tab_data:
    st.subheader("Filtered Data Table (Charts Filters)")
    st.dataframe(filtered_chart)
