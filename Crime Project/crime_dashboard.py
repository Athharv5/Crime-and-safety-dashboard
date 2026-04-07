import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Crime & Safety Dashboard", layout="wide")

# -----------------------------
# PAGE STYLING
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #071421 0%, #0b1d2d 100%);
        color: white;
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }
    h1, h2, h3, h4, h5, h6, p, label, div {
        color: white !important;
    }
    [data-testid="stSidebar"] {
        background: #0a1624;
    }
    [data-testid="metric-container"] {
        background: #102235;
        border: 1px solid #1e3a56;
        padding: 15px;
        border-radius: 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.25);
    }
    .chart-card {
        background: #102235;
        border: 1px solid #1e3a56;
        border-radius: 14px;
        padding: 10px 14px 4px 14px;
        margin-bottom: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("crime_safety_dataset.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["month"] = df["date"].dt.strftime("%b %Y")
    df["year"] = df["date"].dt.year.astype("Int64")
    return df


df = load_data().copy()

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.title("Filters")

state_options = sorted(df["state"].dropna().unique())
crime_options = sorted(df["crime_type"].dropna().unique())
gender_options = sorted(df["victim_gender"].dropna().unique())
city_options = sorted(df["city"].dropna().unique())

selected_states = st.sidebar.multiselect("State", state_options, default=state_options[:6] if len(state_options) > 6 else state_options)
selected_crimes = st.sidebar.multiselect("Crime Type", crime_options, default=crime_options)
selected_gender = st.sidebar.multiselect("Victim Gender", gender_options, default=gender_options)
selected_cities = st.sidebar.multiselect("City", city_options, default=city_options)

min_date = df["date"].min()
max_date = df["date"].max()
selected_dates = st.sidebar.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

filtered_df = df.copy()
if selected_states:
    filtered_df = filtered_df[filtered_df["state"].isin(selected_states)]
if selected_crimes:
    filtered_df = filtered_df[filtered_df["crime_type"].isin(selected_crimes)]
if selected_gender:
    filtered_df = filtered_df[filtered_df["victim_gender"].isin(selected_gender)]
if selected_cities:
    filtered_df = filtered_df[filtered_df["city"].isin(selected_cities)]
if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = pd.to_datetime(selected_dates[0]), pd.to_datetime(selected_dates[1])
    filtered_df = filtered_df[(filtered_df["date"] >= start_date) & (filtered_df["date"] <= end_date)]

if filtered_df.empty:
    st.warning("No records match the selected filters. Please change the filters.")
    st.stop()

# -----------------------------
# KPI VALUES
# -----------------------------
total_cases = len(filtered_df)
most_common_crime = filtered_df["crime_type"].mode().iloc[0]
num_cities = filtered_df["city"].nunique()
avg_victim_age = round(filtered_df["victim_age"].mean(), 1)

# -----------------------------
# HEADER
# -----------------------------
st.markdown("<h1 style='margin-bottom:0;'>Crime & Safety Dashboard</h1>", unsafe_allow_html=True)

# -----------------------------
# KPI ROW
# -----------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Cases", f"{total_cases:,}")
k2.metric("Most Common Crime", most_common_crime)
k3.metric("Cities Covered", num_cities)
k4.metric("Avg Victim Age", avg_victim_age)

# -----------------------------
# CHART DATA
# -----------------------------
monthly_cases = (
    filtered_df.dropna(subset=["date"])
    .groupby(filtered_df["date"].dt.to_period("M"))
    .size()
    .reset_index(name="cases")
)
monthly_cases["date"] = monthly_cases["date"].astype(str)

crime_counts = (
    filtered_df["crime_type"]
    .value_counts()
    .reset_index()
)
crime_counts.columns = ["crime_type", "count"]

city_counts = filtered_df["city"].value_counts().head(8).reset_index()
city_counts.columns = ["city", "count"]

gender_counts = filtered_df["victim_gender"].value_counts().reset_index()
gender_counts.columns = ["victim_gender", "count"]
race_counts = filtered_df["victim_race"].value_counts().reset_index()
race_counts.columns = ["victim_race", "count"]
location_counts = filtered_df["location_description"].value_counts().head(6).reset_index()
location_counts.columns = ["location_description", "count"]

# -----------------------------
# PLOTLY THEME
# -----------------------------
def dark_fig(fig):
    fig.update_layout(
        template="plotly",
        paper_bgcolor="#102235",
        plot_bgcolor="#102235",
        font=dict(color="white"),
        margin=dict(l=20, r=20, t=45, b=20),
        title_font=dict(size=18, color="white"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        title_font=dict(color="white"),
        tickfont=dict(color="white")
    )
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        title_font=dict(color="white"),
        tickfont=dict(color="white")
    )
    if fig.layout.annotations:
        fig.update_annotations(font=dict(color="white"))
    return fig

# -----------------------------
# ROW 1
# -----------------------------
col1, col2, col3 = st.columns([1.3, 1.05, 1.05])

with col1:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    fig1 = px.bar(
        crime_counts,
        x="count",
        y="crime_type",
        orientation="h",
        title="Crime by Type",
        color="count",
        color_continuous_scale=[[0, "#1f77ff"], [1, "#23c6ff"]]
    )
    fig1.update_layout(coloraxis_showscale=False, yaxis=dict(categoryorder="total ascending"), height=340)
    st.plotly_chart(dark_fig(fig1), use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    fig2 = px.pie(
        gender_counts,
        names="victim_gender",
        values="count",
        hole=0.55,
        title="Victim Gender Split",
        color_discrete_sequence=["#ff8c42", "#31c48d", "#c0c7d1", "#6aa9ff"]
    )
    fig2.update_traces(textposition="inside", textinfo="percent", textfont=dict(color="white", size=14))
    fig2.update_layout(height=340)
    st.plotly_chart(dark_fig(fig2), use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    fig3 = px.bar(
        race_counts,
        x="victim_race",
        y="count",
        title="Victim Race Analysis",
        color="count",
        color_continuous_scale=[[0, "#ff8c42"], [1, "#ffb36b"]]
    )
    fig3.update_layout(coloraxis_showscale=False, height=340)
    st.plotly_chart(dark_fig(fig3), use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# ROW 2
# -----------------------------
col4, col5 = st.columns([1.35, 1])

with col4:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    fig4 = px.line(
        monthly_cases,
        x="date",
        y="cases",
        title="Crime Trend by Month",
        markers=True
    )
    fig4.update_traces(line=dict(color="#23c6ff", width=3), marker=dict(size=7, color="#ff8c42"))
    fig4.update_layout(height=340)
    st.plotly_chart(dark_fig(fig4), use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

with col5:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    fig5 = px.bar(
        city_counts,
        x="city",
        y="count",
        title="Top 8 Crime Cities",
        color="count",
        color_continuous_scale=[[0, "#ff8c42"], [1, "#ffb36b"]]
    )
    fig5.update_layout(coloraxis_showscale=False, height=340)
    st.plotly_chart(dark_fig(fig5), use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# ROW 3
# -----------------------------
col6, col7 = st.columns([1.2, 1.15])

with col6:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    fig6 = px.bar(
        location_counts,
        x="location_description",
        y="count",
        title="Top Crime Locations",
        color="count",
        color_continuous_scale=[[0, "#1f77ff"], [1, "#23c6ff"]]
    )
    fig6.update_layout(coloraxis_showscale=False, height=320)
    st.plotly_chart(dark_fig(fig6), use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

with col7:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    age_bins = pd.cut(filtered_df["victim_age"], bins=[0, 18, 30, 45, 60, 100], labels=["0-18", "19-30", "31-45", "46-60", "60+"])
    age_counts = age_bins.value_counts().sort_index().reset_index()
    age_counts.columns = ["Age Group", "count"]
    fig7 = px.bar(
        age_counts,
        x="Age Group",
        y="count",
        title="Victim Age Group Distribution",
        color="count",
        color_continuous_scale=[[0, "#ff8c42"], [1, "#ffb36b"]]
    )
    fig7.update_layout(coloraxis_showscale=False, height=320)
    st.plotly_chart(dark_fig(fig7), use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# FOOTER INSIGHTS
# -----------------------------
top_city = city_counts.iloc[0]["city"] if not city_counts.empty else "N/A"
top_location = location_counts.iloc[0]["location_description"] if not location_counts.empty else "N/A"

st.markdown(
    f"""
    <div style="background:#102235; border:1px solid #1e3a56; padding:14px 18px; border-radius:14px; margin-top:8px;">
    <b>Quick insights:</b> The most common crime in the current selection is <span style="color:#ffb36b;">{most_common_crime}</span>. 
    <span style="color:#23c6ff;">{top_city}</span> appears as the leading city by case count, and <span style="color:#23c6ff;">{top_location}</span> is the most frequent location category. 
    This layout is ideal for taking a clean screenshot and placing it directly into your presentation.
    </div>
    """,
    unsafe_allow_html=True
)
