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
######################

# Adding second dataframestre
df2 = pd.read_csv("global-warming-by-gas-and-source.csv")

# # Testing new dataset for consistancy of developing and developed nations
# df_long = pd.read_csv("temp_change_df (1).csv")
# df_long.rename(columns={'DevStaus':'DevStatus'},inplace=True)

# Loading monthly data & contribution dataset
df_monthly = pd.read_csv("df_monthly_long.csv")
df_monthly['Date'] = pd.to_datetime(df_monthly[['Year', 'Month']].assign(DAY=1)) # Adding a date column for better plotting
df_monthly.rename(columns={'Mean_Temp':'Monthly Average Temperature Change (°C)',}, inplace=True)

# Loading contributions dataset
df_contribution = pd.read_csv("contributions-global-temp-change.csv")

# ─── Lists for filters ─────────────────────────────────────
# Creating a list of countries that are found across all datasets
data_long_list = list(df_long["Country"].unique())
data_contribution_list = list(df_contribution['Entity'].unique())
df_monthly_list =list(df_monthly["Entity"].unique())
df2_list = list(df2['Entity'].unique())

# Perfoming list comprehesion
in_all = [x for x in data_long_list if x in data_contribution_list and x in df_monthly_list and x in df2_list]


all_countries = ["All"] + sorted(in_all)
all_years     = ["All"] + sorted(df_long["Year"].unique())
year_min, year_max = int(df_long["Year"].min()), int(df_long["Year"].max())

# ─── Sidebar: two independent filter sections ──────────────
with st.sidebar.expander("📊 Charts Filters", expanded=True):
    chart_country = st.selectbox("Country", all_countries, key="chart_country")
    #chart_year    = st.selectbox("Year", all_years,     key="chart_year")

with st.sidebar.expander("🌐 Select Time Period", expanded=False):
    dev_year_range = st.slider("Year Range",
                               min_value=year_min,
                               max_value=year_max,
                               value=(year_min, year_max),
                               step=1,
                               key="dev_year_range")

# ── Data after filters ─────────────────────────────────────

# df_long year filter
filtered_chart = df_long[
    (df_long["Year"] >= dev_year_range[0]) &
    (df_long["Year"] <= dev_year_range[1])
].copy()

# Dropdown filters
if chart_country != "All":
    filtered_chart = filtered_chart[filtered_chart["Country"] == chart_country]
# if chart_year != "All":
#     filtered_chart = filtered_chart[filtered_chart["Year"] == int(chart_year)]

# Monthly Average Temperature Change 'Year' Filter
filtered_chart_monthly = df_monthly[
    (df_monthly["Year"] >= dev_year_range[0]) &
    (df_monthly["Year"] <= dev_year_range[1])
].copy()

filtered_chart_2 = df_long[
    (df_long["Year"] >= dev_year_range[0]) &
    (df_long["Year"] <= dev_year_range[1])
].copy()


# Dropdown filters - Monthly Average Temperature Change
# if chart_year != "All":
#     filtered_chart_monthly = filtered_chart_monthly[filtered_chart_monthly["Year"] == int(chart_year)]

# Gas 'Year' Filter
df2 = df2[
    (df2["Year"] >= dev_year_range[0]) &
    (df2["Year"] <= dev_year_range[1])
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
        sample_countries = filtered_chart["Country"].unique()[:10]
        scatter_src = filtered_chart[filtered_chart["Country"].isin(sample_countries)]
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
        ).add_params(sel_country)
        #.transform_filter(sel_country)
        .properties(
            width=750, height=400,
            title=f"Temperature Change Over Time – "
                  f"{chart_country if chart_country!='All' else 'All Countries'}"
        )
    )
    # Plot monthly temperature change
    
    if chart_country == "All":
        df_monthly_filtered = filtered_chart_monthly[filtered_chart_monthly["Entity"] == 'World']
        name = "All"
        
    else:
        df_monthly_filtered = filtered_chart_monthly[filtered_chart_monthly["Entity"] == chart_country]
        name = chart_country
        # Needed for streamlit to evaluate world correctly when selected
        df_monthly_filtered['Entity'].unique()=='World'

    # Creating a selection for the monthly line chart
    sel_year = alt.selection_point(on='pointerover',fields=['Year'], nearest=True, empty=True)
    
    # Creating a new column to calculate the yearly average temperature change for each country
    yearly_averages = df_monthly_filtered.groupby(['Year','Entity'])["Monthly Average Temperature Change (°C)"].agg('mean').reset_index().rename(columns={"Monthly Average Temperature Change (°C)": "Yearly Average Temperature Change (°C)"})
    
    # Merging
    df_monthly_filtered = pd.merge(df_monthly_filtered, yearly_averages, on=['Year','Entity'], how='left')

    base = alt.Chart(df_monthly_filtered).encode(
        x=alt.X("Month_named:N", 
        sort=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'], title='Month'), #axis=alt.Axis(labelAngle=0)),
        y="Monthly Average Temperature Change (°C):Q")
    
    points = base.mark_circle().encode(
        opacity=alt.value(0),
        tooltip=["Year", "Monthly Average Temperature Change (°C)"]
    ).add_params(
        sel_year
    )
    lines = base.mark_line().encode(
        color=alt.Color("Yearly Average Temperature Change (°C)",scale=alt.Scale(scheme='reds'), legend=alt.Legend(title="Yearly Average Temperature Change(°C)")),
        opacity=alt.condition(sel_year, alt.value(1), alt.value(0.20)),
        tooltip=["Year", "Monthly Average Temperature Change (°C)"]
    ).properties(
        width=750, height=400,
        title=f"Monthly Average Temperature Change – {name}",
    ).interactive()

    monthly_line = points + lines




    # 2️⃣ Bar plot: countries with decreasing variability
    stats_base = df_long.copy()
    if chart_country == "All":
        stats_base = df_long.copy()

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
    else:
        bar=None
    


    # Stacked area chart for global warming by gas and source (world)
    # world = df2[df2["Code"] == "OWID_WRL"].copy()
    # world.drop(columns=["Entity", "Code"], inplace=True)

    def gas_data(entity):
        name = "World" if entity == "All" else entity
        g = df2[df2["Entity"] == name].copy()
        return g

    # Column names in the raw dataset are too verbose
    # FF&I = Fossil Fuels & Industry
    # AgLU = Agriculture and Land Use

    gas_cols = [c for c in df2.columns if c.startswith("Change in")]
    
    
    shortened_columns = {
        col: (
            "N2O_FF&I" if "nitrous oxide" in col and "fossil fuels" in col else
            "N2O_AgLU" if "nitrous oxide" in col else
            "CH4_FF&I" if "methane" in col and "fossil fuels" in col else
            "CH4_AgLU" if "methane" in col else
            "CO2_FF&I" if "fossil fuels" in col else 
            "CO2_AgLU"
        )
        for col in gas_cols
    }
    
    gas_df = gas_data(chart_country)
    gas_df.drop(columns=["Code"], inplace=True)
    gas_df.rename(columns=shortened_columns, inplace=True)

    gas_long = gas_df.melt(
        id_vars="Year",
        value_vars=list(shortened_columns.values()),
        var_name="series",
        value_name="Temp Change"
    )

    label_map = {
        "CO2_FF&I": "CO₂ (Fossil Fuels & Industry)",
        "CO2_AgLU": "CO₂ (Agriculture & Land Use)",
        "CH4_FF&I": "CH₄ (Fossil Fuels & Industry)",
        "CH4_AgLU": "CH₄ (Agriculture & Land Use)",
        "N2O_FF&I": "N₂O (Fossil Fuels & Industry)",
        "N2O_AgLU": "N₂O (Agriculture & Land Use)"
    }
    gas_long["series_label"] = gas_long["series"].map(label_map)
    
    # Selection
    selection = alt.selection_point(fields=['series'])
    condition = alt.condition(selection, 'series_label:N', alt.ColorValue('grey'))

    area = alt.Chart(gas_long).mark_area().encode(
        x="Year:O",
        y="Temp Change:Q",
        color=condition,
        order="series_label:N",
        tooltip=['Year:O','series_label:N','Temp Change:Q']
    ).add_params(selection).properties(title=f"Warming by Gas and Source ({chart_country})",autosize=alt.AutoSizeParams(
            type='fit-x',
            contains='padding',
            resize=True
        ))
    
    # Top ten chart
    top10 = filtered_chart_2.groupby('Country')['TempChange'].mean().nlargest(10).reset_index()
    bar_chart = alt.Chart(top10).mark_circle(size=100).encode(
        x=alt.X("TempChange:Q", title="Avg Temp Change (°C)").axis(alt.Axis(grid=False)),
        y=alt.Y("Country:N", sort='-x').axis(alt.Axis(grid=True)),
        tooltip=["Country:N", "TempChange"]
    ).properties(
        width=400, height=600,
        title="Top 10 Countries by Avg Temp Change"
    )
    

    
    # Plotting the charts
    st.altair_chart(
        alt.vconcat(scatter, monthly_line).properties(autosize=alt.AutoSizeParams(
            type='fit-x',
            contains='padding',
            resize=True
        )).resolve_scale(color="independent"),
        use_container_width=True
    )
    # Plotting bar by itself as it can be of 'None' value raising an exception
    show_decreasing_var = (dev_year_range[0] == year_min) and (dev_year_range[1] == year_max)
    if bar!= None and show_decreasing_var:
        st.altair_chart(alt.hconcat(bar_chart, bar).resolve_scale(color="independent"))
        st.altair_chart(area,use_container_width=True)
    else:
        st.altair_chart(area, use_container_width=True)

    
     
                
                     

# ───────────────────────────────────────────────────────────
# 🌐 DEVELOPED vs DEVELOPING TAB
# ───────────────────────────────────────────────────────────
with tab_dev:
    st.subheader("Average Temperature Change: Developed vs Developing")

    # 🔄 Interactive selection on DevStatus
    dev_sel = alt.selection_point(fields=["DevStatus"])

    # 1️⃣ Line chart (yearly averages)
    dev_avg = (df_long
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
            width=650, height=400
        )
    )
    #st.altair_chart(line_chart, use_container_width=True)

    # 2️⃣ Bar chart (5‑year grouped averages)
    df_long["YearGroup"] = (df_long["Year"] // 5) * 5
    dev_bar = (df_long
               .groupby(["YearGroup", "DevStatus"])["TempChange"]
               .mean()
               .reset_index())

    bar_chart = (
        alt.Chart(dev_bar)
        .mark_bar()
        .encode(
            x=alt.X("YearGroup:O", title="5‑Year Group"),
            y=alt.Y("TempChange:Q", title="Avg Temp Change (°C)", scale=alt.Scale(zero=True)),
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
            width=650, height=400
        )
    )
    st.altair_chart(bar_chart|line_chart)#, use_container_width=True)

    # Filtering dataset
    filt_contribution = df_contribution[(df_contribution['Entity'].isin(['OECD (Jones et al.)', 'Least developed countries (Jones et al.)']))]
    filt_contribution = filt_contribution[(filt_contribution['Year'] >= dev_year_range[0]) & (filt_contribution['Year'] <= dev_year_range[1])]

    # Creating interactive brush element
    brush = alt.selection_interval(encodings=['x'])
    conditonal = alt.condition(brush, alt.value(1.0),alt.value(.25))
        
    radio = st.radio("Select Chart", ('Overview','Detailed'))

    if radio == 'Overview':
        # Creating an area line chart    
        Background = alt.Chart(filt_contribution).mark_area().encode(
        x='Year:O',
        y='Share of contribution to global warming:Q',
        #opacity = conditonal,
        color='Entity')

        # highlight = alt.Chart(filt_contribution).mark_area().encode(
        # x='Year:O',
        # y='Share of contribution to global warming:Q',
        # color='Entity'
        # ).transform_filter(brush)
        
        # selected = base.transform_filter(brush).mark_area(color='goldenrod')

        # background + selected
        chart = Background #+ highlight
        st.subheader("Comparison of Share of Contribution to Global Warming - Developing Versus Developed")
        st.altair_chart(chart, use_container_width=True)
    elif radio =='Detailed':       
        # Creating line chart of individual OECD Nations
        oecd_list = [
        "Australia", "Austria", "Belgium", "Canada", "Chile", "Colombia", "Costa Rica",
        "Czech Republic", "Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
        "Hungary", "Iceland", "Ireland", "Israel", "Italy", "Japan", "Latvia", "Lithuania",
        "Luxembourg", "Mexico", "Netherlands", "New Zealand", "Norway", "Poland", "Portugal",
        "Slovakia", "Slovenia", "South Korea", "Spain", "Sweden", "Switzerland", "Turkey",
        "United Kingdom", "United States"]



        ldc_countries = [
        # Africa (32)
        "Angola", "Benin", "Burkina Faso", "Burundi", "Central African Republic", "Chad",
        "Comoros", "Democratic Republic of the Congo", "Djibouti", "Eritrea", "Ethiopia",
        "Gambia", "Guinea", "Guinea-Bissau", "Lesotho", "Liberia", "Madagascar", "Malawi",
        "Mali", "Mauritania", "Mozambique", "Niger", "Rwanda", "Senegal", "Sierra Leone",
        "Somalia", "South Sudan", "Sudan", "Togo", "Uganda", "United Republic of Tanzania", "Zambia",

        # Asia (8)
        "Afghanistan", "Bangladesh", "Cambodia", "Lao People’s Democratic Republic",
        "Myanmar", "Nepal", "Timor-Leste", "Yemen",

        # Pacific (3)
        "Kiribati", "Solomon Islands", "Tuvalu",

        # Caribbean (1)
        "Haiti"]
        ######
        # Creating a LDC df
        df_contribution_lcd = df_contribution[df_contribution['Entity'].isin(ldc_countries)]
        df_contribution_lcd = df_contribution_lcd[(df_contribution_lcd['Year'] >= dev_year_range[0]) & (df_contribution_lcd['Year'] <= dev_year_range[1])]
        # Groupby to get top 10
        group = df_contribution_lcd.groupby('Entity')['Share of contribution to global warming'].mean().sort_values(ascending=False)

        # Top 10 countries
        top_10_countries_LDC = group.reset_index().iloc[:10]

        # Creating a list of top 10
        top_10_countries_LDC = list(top_10_countries_LDC['Entity'].unique())

        # Filtering the df again
        df_contribution_lcd = df_contribution_lcd[df_contribution_lcd['Entity'].isin(top_10_countries_LDC)]

        ######
        
        # Creating a OECD df
        df_contribution_oecd = df_contribution[df_contribution['Entity'].isin(oecd_list)]
        df_contribution_oecd = df_contribution_oecd[(df_contribution_oecd['Year'] >= dev_year_range[0]) & (df_contribution_oecd['Year'] <= dev_year_range[1])]
        
        # Groupby to get top 10
        group = df_contribution_oecd.groupby('Entity')['Share of contribution to global warming'].mean().sort_values(ascending=False)

        # Top 10 countries
        top_10_countries = group.reset_index().iloc[:10]

        # Creating a list of top 10
        top_10_countries_list = list(top_10_countries['Entity'].unique())

        # Filtering the df again
        df_contribution_oecd = df_contribution_oecd[df_contribution_oecd['Entity'].isin(top_10_countries_list)]
        #######
        # Estabilshing new interactions
        brush_new = alt.selection_interval(encodings=['x'],resolve='global')
        conditonal = alt.condition(brush_new, alt.value(1.0),alt.value(0.25)) 
        
        # Creating temporal heat map
        # base = alt.Chart(df_contribution_oecd).encode(
        #     x=alt.X('Year:O'),,
        #     color=alt.condition(brush_new, 'Entity:N', alt.ColorValue('gray')),
        #     tooltip=['Entity:N', 'Share of contribution to global warming:Q', 'Year']
        # ).add_params(brush_new)

        ##### Removing heatmap
        # heatmap = alt.Chart(df_contribution_oecd).mark_rect().encode(
        #     x=alt.X('Year:O'),
        #     y=alt.Y('Entity:N', sort=top_10_countries_list),
        #     color= alt.Color('Share of contribution to global warming:Q',scale=alt.Scale(scheme='reds')),
        #     opacity=alt.condition(brush_new, alt.value(1.0), alt.value(0.25)),
        # ).add_params(brush_new).properties(height=400)
        # st.subheader("Comparison of Share of Contribution to Global Warming - Top 10 OECD Nations")

        # Creating an area line chart    
        overview = alt.Chart(filt_contribution).mark_area().encode(
        x='Year:O',
        y='Share of contribution to global warming:Q',
        #opacity = conditonal,
        color='Entity').properties(width=650+650).add_params(brush_new)

        # Creating chart
        background_OECD = alt.Chart(df_contribution_oecd, title='Share of Contribution to Global Warming- OECD Nations').mark_line().encode(
            x=alt.X('Year:O'),
            y=alt.Y('Share of contribution to global warming:Q'),
            #color=alt.Color('Entity:N'),
            opacity=conditonal,
            color=alt.condition(brush_new, 'Entity:N', alt.ColorValue('gray')),
            tooltip=['Entity:N','Share of contribution to global warming:Q','Year']
        ).properties(width=650,height=300).add_params(brush_new).interactive()
        
        # Creating a highlight chart
        highlight_OECD = alt.Chart(df_contribution_oecd).mark_line().encode(
            x=alt.X('Year:O'),
            y=alt.Y('Share of contribution to global warming:Q'),
            color=alt.Color('Entity:N'),
        
            tooltip=['Entity:N','Share of contribution to global warming:Q','Year']
        ).transform_filter(brush_new)


         # Creating chart
        background_LDC = alt.Chart(df_contribution_lcd, title='Share of Contribution to Global Warming- LDC Nations').mark_line().encode(
            x=alt.X('Year:O'),
            y=alt.Y('Share of contribution to global warming:Q'),
            #color=alt.Color('Entity:N'),
            opacity=conditonal,
            color=alt.condition(brush_new, 'Entity:N', alt.ColorValue('gray')),
            tooltip=['Entity:N','Share of contribution to global warming:Q','Year']
        ).properties(width=650,height=300).add_params(brush_new).interactive()
        
        # Creating a highlight chart
        highlight_LDC = alt.Chart(df_contribution_lcd).mark_line().encode(
            x=alt.X('Year:O'),
            y=alt.Y('Share of contribution to global warming:Q'),
            color=alt.Color('Entity:N'),
        
            tooltip=['Entity:N','Share of contribution to global warming:Q','Year']
        ).transform_filter(brush_new)
        
        # combining the two charts
        st.subheader("Comparison of Share of Contribution to Global Warming - Developing Versus Developed")
        chart_OECD = background_OECD + highlight_OECD
        chart_LDC = background_LDC + highlight_LDC
        chart = alt.hconcat(chart_LDC,chart_OECD).resolve_scale(color='independent',y='shared')

        st.altair_chart(chart)
        st.altair_chart(alt.vconcat(overview,alt.hconcat(chart_LDC,chart_OECD)).resolve_scale(color='independent'))
      


    # Creating a radio button to toggle between the two charts

# ───────────────────────────────────────────────────────────
# 📋 DATA TAB
# ───────────────────────────────────────────────────────────
with tab_data:
    st.subheader("Filtered Data Table (Charts Filters)")
    st.dataframe(filtered_chart)

with tab_data:
    st.subheader("Data Table (Global Warming by Gas and Source)")
    st.dataframe(gas_df)

with tab_data:
    st.subheader("Data Table (Monthly Average Surface Temperatures by Year)")
    st.dataframe(df_monthly_filtered)

with tab_data:
    st.subheader("Data Table (Contributions to Global Climate Change)")
    st.dataframe(df_contribution)