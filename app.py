from datetime import timedelta

import pandas as pd
import streamlit as st


# ------------------------------------------------------------
# Page setup
# ------------------------------------------------------------
st.set_page_config(
    page_title="PeMS Freeway Sensor Dashboard",
    page_icon="🚗",
    layout="wide",
)


# ------------------------------------------------------------
# Simple page styling
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f4f7fb;
        color: #1f2937;
    }

    h1 {
        color: #12355b;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
    }

    h2, h3 {
        color: #1f4e79;
    }

    [data-testid="stSidebar"] {
        background-color: #eaf1f8;
    }

    [data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #d7e2ee;
        padding: 18px;
        border-radius: 12px;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #12355b;
        margin-top: 10px;
        margin-bottom: 8px;
    }

    .section-box {
        background-color: white;
        border: 1px solid #d7e2ee;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 14px;
    }

    .small-note {
        font-size: 0.9rem;
        color: #5b6573;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Data
# ------------------------------------------------------------
@st.cache_data
def load_data():
    """Read the PeMS parquet file and reuse it across Streamlit reruns."""
    data = pd.read_parquet("data/pems.parquet")
    data["time"] = pd.to_datetime(data["time"])
    return data


def show_blind_spots(number_of_sensors):
    with st.container(border=True):
        st.markdown(
            '<div class="section-title">What this dashboard cannot tell you</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"- **Conditions away from these detectors.** "
            f"The file contains {number_of_sensors} fixed sensor locations, so roads "
            "without one of these sensors are outside this dashboard."
        )

        st.markdown(
            "- **Why traffic slowed down.** This file contains speed, flow, and "
            "occupancy, but it does not contain weather, crash, construction, or "
            "event information."
        )

        st.markdown(
            "- **What individual vehicles did.** Each row is an aggregate for a "
            "5-minute interval, so a mean speed does not show the speed of each "
            "individual vehicle."
        )


df = load_data()


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
st.title("PeMS District 4 Freeway Sensor Dashboard")

st.markdown(
    """
    <div class="section-box">
        <b>Dashboard purpose:</b> Explore freeway traffic conditions using speed,
        traffic flow, and detector occupancy for one PeMS sensor at a time.
        Use the filters in the sidebar to change the sensor, date range, and hour
        range shown in the dashboard.
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Sidebar controls
# ------------------------------------------------------------
with st.sidebar:
    st.header("Dashboard Controls")

    sensor = st.selectbox(
        "Sensor",
        sorted(df["sensor"].dropna().unique()),
    )

    first_day = df["time"].min().date()
    last_day = df["time"].max().date()
    default_end = min(first_day + timedelta(days=6), last_day)

    date_range = st.date_input(
        "Date range",
        value=(first_day, default_end),
        min_value=first_day,
        max_value=last_day,
    )

    hour_range = st.slider(
        "Hour of day",
        min_value=0,
        max_value=23,
        value=(0, 23),
        help="0 means midnight and 23 means 11 PM.",
    )

    st.divider()

    st.subheader("About the filters")
    st.caption(
        "All three controls change which observations are included in the "
        "dashboard. They do not simply change the appearance of a chart."
    )

    st.divider()

    st.subheader("Why caching is used")
    st.caption(
        "The parquet loader uses @st.cache_data because Streamlit reruns the "
        "script after every filter change. Caching avoids reading the same file "
        "from disk again each time."
    )


# ------------------------------------------------------------
# Date range handling
# ------------------------------------------------------------
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_day, end_day = date_range
elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
    start_day = end_day = date_range[0]
else:
    start_day = end_day = date_range


start_time = pd.Timestamp(start_day)
end_time = pd.Timestamp(end_day) + pd.Timedelta(days=1)

start_hour, end_hour = hour_range


# ------------------------------------------------------------
# Filter data
# ------------------------------------------------------------
selected = df[
    (df["sensor"] == sensor)
    & (df["time"] >= start_time)
    & (df["time"] < end_time)
    & (df["time"].dt.hour >= start_hour)
    & (df["time"].dt.hour <= end_hour)
].copy()


if selected.empty:
    st.warning(
        "No rows match the current filters. Try a wider date range or hour range."
    )
    st.stop()


selected["occupancy_pct"] = selected["occupancy"] * 100


# ------------------------------------------------------------
# Current selection summary
# ------------------------------------------------------------
st.markdown(
    '<div class="section-title">Current Selection</div>',
    unsafe_allow_html=True,
)

st.write(
    f"Sensor **{sensor}** · "
    f"{start_day:%b %d, %Y} to {end_day:%b %d, %Y} · "
    f"Hours **{start_hour}:00–{end_hour}:59**"
)


# ------------------------------------------------------------
# Summary metrics
# ------------------------------------------------------------
st.markdown(
    '<div class="section-title">Traffic Summary</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Mean speed",
    f"{selected['speed'].mean():.1f} mph",
)

c2.metric(
    "Median flow",
    f"{selected['flow'].median():.0f} veh / 5 min",
)

c3.metric(
    "Mean occupancy",
    f"{selected['occupancy_pct'].mean():.1f}%",
)

c4.metric(
    "5-minute records",
    f"{len(selected):,}",
)


# ------------------------------------------------------------
# Extra summary row
# ------------------------------------------------------------
c5, c6, c7 = st.columns(3)

c5.metric(
    "Minimum speed",
    f"{selected['speed'].min():.1f} mph",
)

c6.metric(
    "Maximum speed",
    f"{selected['speed'].max():.1f} mph",
)

c7.metric(
    "Maximum flow",
    f"{selected['flow'].max():.0f} veh / 5 min",
)


# ------------------------------------------------------------
# Main charts
# ------------------------------------------------------------
st.markdown(
    '<div class="section-title">Traffic Patterns</div>',
    unsafe_allow_html=True,
)

speed_tab, flow_tab, relation_tab, data_tab = st.tabs(
    [
        "Speed over time",
        "Hourly traffic flow",
        "Flow vs. occupancy",
        "Filtered data",
    ]
)


# ------------------------------------------------------------
# Speed tab
# ------------------------------------------------------------
with speed_tab:
    st.subheader("Speed through time")

    speed_plot = selected[["time", "speed"]].rename(
        columns={
            "time": "Time",
            "speed": "Speed (mph)",
        }
    )

    st.line_chart(
        speed_plot,
        x="Time",
        y="Speed (mph)",
        height=430,
    )

    st.caption(
        "Each observation is one 5-minute detector interval. "
        "Lower sections of the line indicate periods of slower traffic."
    )


# ------------------------------------------------------------
# Flow tab
# ------------------------------------------------------------
with flow_tab:
    st.subheader("Median traffic flow by hour")

    hourly_flow = (
        selected.assign(hour=selected["time"].dt.hour)
        .groupby("hour", as_index=False)["flow"]
        .median()
        .rename(
            columns={
                "hour": "Hour of day",
                "flow": "Median flow (vehicles / 5 min)",
            }
        )
    )

    st.bar_chart(
        hourly_flow,
        x="Hour of day",
        y="Median flow (vehicles / 5 min)",
        height=430,
    )

    st.caption(
        "Each bar shows the median 5-minute traffic flow observed during that hour "
        "within the selected date range."
    )


# ------------------------------------------------------------
# Relationship tab
# ------------------------------------------------------------
with relation_tab:
    st.subheader("Traffic flow and detector occupancy")

    relation = selected[["occupancy_pct", "flow"]].rename(
        columns={
            "occupancy_pct": "Occupancy (%)",
            "flow": "Flow (vehicles / 5 min)",
        }
    )

    st.scatter_chart(
        relation,
        x="Occupancy (%)",
        y="Flow (vehicles / 5 min)",
        height=430,
    )

    st.caption(
        "Each point represents one 5-minute interval. "
        "The plot shows how measured flow changes as detector occupancy changes."
    )


# ------------------------------------------------------------
# Data tab
# ------------------------------------------------------------
with data_tab:
    st.subheader("Filtered observations")

    show = selected[
        ["time", "sensor", "speed", "flow", "occupancy"]
    ].copy()

    show = show.rename(
        columns={
            "time": "time",
            "sensor": "sensor",
            "speed": "speed_mph",
            "flow": "flow_veh_per_5min",
            "occupancy": "occupancy_fraction",
        }
    )

    st.dataframe(
        show,
        hide_index=True,
        width="stretch",
    )

    st.download_button(
        "Download filtered rows as CSV",
        data=show.to_csv(index=False).encode("utf-8"),
        file_name=f"pems_{sensor}_filtered.csv",
        mime="text/csv",
    )


# ------------------------------------------------------------
# Small overview section
# ------------------------------------------------------------
st.markdown(
    '<div class="section-title">How to Read This Dashboard</div>',
    unsafe_allow_html=True,
)

left, middle, right = st.columns(3)

with left:
    with st.container(border=True):
        st.subheader("Speed")
        st.write(
            "Speed is reported in miles per hour. The time-series chart helps "
            "identify when traffic becomes slower or faster."
        )

with middle:
    with st.container(border=True):
        st.subheader("Flow")
        st.write(
            "Flow is the number of vehicles recorded during each 5-minute interval. "
            "The hourly chart summarizes typical traffic volume by hour."
        )

with right:
    with st.container(border=True):
        st.subheader("Occupancy")
        st.write(
            "Occupancy is the fraction of time the loop detector is covered by a "
            "vehicle. Here it is displayed as a percentage."
        )


# ------------------------------------------------------------
# Provenance
# ------------------------------------------------------------
with st.expander("Dataset provenance and measurement details"):
    st.markdown(
        "**Source:** California Department of Transportation, PeMS, District 4."
    )

    st.write(
        f"The course file covers the San Francisco Bay Area from "
        f"{df['time'].min():%B %d, %Y} through {df['time'].max():%B %d, %Y}."
    )

    st.write(
        "Measurements are stored in 5-minute intervals from inductive loop detectors."
    )

    st.write(
        "The variables used in this dashboard are timestamp, sensor ID, traffic "
        "flow, occupancy, and speed."
    )

    st.write(
        "This dashboard uses the course-provided PeMS parquet file directly. "
        "No additional dataset is combined with it."
    )


# ------------------------------------------------------------
# Blind spots
# ------------------------------------------------------------
show_blind_spots(df["sensor"].nunique())


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------
st.divider()

st.caption(
    "CIVL 6962 · Homework 1 · PeMS District 4 Freeway Sensor Dashboard"
)