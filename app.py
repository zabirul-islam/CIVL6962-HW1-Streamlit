from datetime import timedelta

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="PeMS Freeway Sensor Dashboard",
    page_icon="🚗",
    layout="wide",
)


@st.cache_data
def load_data():
    """Read the course PeMS file once and reuse it across Streamlit reruns."""
    data = pd.read_parquet("data/pems.parquet")
    data["time"] = pd.to_datetime(data["time"])
    return data


def show_blind_spots(number_of_sensors):
    with st.container(border=True):
        st.subheader("What this dashboard cannot tell you")
        st.markdown(
            f"- **Conditions away from these detectors.** The file contains "
            f"{number_of_sensors} fixed sensor locations, so roads without one of these "
            "sensors are outside this dashboard."
        )
        st.markdown(
            "- **Why traffic slowed down.** This file has speed, flow, and occupancy, "
            "but it does not contain weather, crash, construction, or event information."
        )
        st.markdown(
            "- **What individual vehicles did.** Each row is an aggregate for a 5-minute "
            "interval. A mean speed does not show the speed of each individual vehicle."
        )


# Load once. Streamlit reruns this script whenever a control changes, but the
# parquet read is cached instead of being repeated on every interaction.
df = load_data()

st.title("PeMS District 4 Freeway Sensor Dashboard")
st.write(
    "This dashboard explores speed, traffic flow, and loop-detector occupancy "
    "for one PeMS sensor at a time."
)


# ------------------------------- sidebar filters
with st.sidebar:
    st.header("Filters")

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
        help="Use 0 for midnight and 23 for 11 PM.",
    )

    st.divider()
    st.caption(
        "The parquet loader uses `@st.cache_data` because Streamlit reruns the "
        "script after every filter change. Caching avoids reading the same file "
        "from disk again each time."
    )


# st.date_input can temporarily return one date while the user is choosing a range.
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_day, end_day = date_range
elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
    start_day = end_day = date_range[0]
else:
    start_day = end_day = date_range

start_time = pd.Timestamp(start_day)
end_time = pd.Timestamp(end_day) + pd.Timedelta(days=1)
start_hour, end_hour = hour_range

selected = df[
    (df["sensor"] == sensor)
    & (df["time"] >= start_time)
    & (df["time"] < end_time)
    & (df["time"].dt.hour >= start_hour)
    & (df["time"].dt.hour <= end_hour)
].copy()

if selected.empty:
    st.warning("No rows match the current filters. Try a wider date or hour range.")
    st.stop()

selected["occupancy_pct"] = selected["occupancy"] * 100


# ------------------------------- summary numbers
c1, c2, c3, c4 = st.columns(4)
c1.metric("Mean speed", f"{selected['speed'].mean():.1f} mph")
c2.metric("Median flow", f"{selected['flow'].median():.0f} veh / 5 min")
c3.metric("Mean occupancy", f"{selected['occupancy_pct'].mean():.1f}%")
c4.metric("5-minute records", f"{len(selected):,}")


# ------------------------------- charts
speed_tab, flow_tab, relation_tab, data_tab = st.tabs(
    ["Speed over time", "Hourly flow", "Flow vs. occupancy", "Filtered data"]
)

with speed_tab:
    speed_plot = selected[["time", "speed"]].rename(
        columns={"time": "Time", "speed": "Speed (mph)"}
    )
    st.line_chart(speed_plot, x="Time", y="Speed (mph)", height=380)
    st.caption("Each point represents one 5-minute detector interval.")

with flow_tab:
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
        height=380,
    )
    st.caption("The bar height is the median flow for each hour in the filtered period.")

with relation_tab:
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
        height=380,
    )
    st.caption(
        "This plot shows how detector occupancy and traffic flow change together "
        "for the selected sensor and time period."
    )

with data_tab:
    show = selected[["time", "sensor", "speed", "flow", "occupancy"]].copy()
    show = show.rename(
        columns={
            "time": "time",
            "sensor": "sensor",
            "speed": "speed_mph",
            "flow": "flow_veh_per_5min",
            "occupancy": "occupancy_fraction",
        }
    )
    st.dataframe(show, hide_index=True, width="stretch")
    st.download_button(
        "Download filtered rows as CSV",
        data=show.to_csv(index=False).encode("utf-8"),
        file_name=f"pems_{sensor}_filtered.csv",
        mime="text/csv",
    )


# ------------------------------- provenance and limitations
with st.expander("Dataset provenance"):
    st.markdown("**Source:** California Department of Transportation, PeMS, District 4.")
    st.write(
        f"The course file covers the San Francisco Bay Area from "
        f"{df['time'].min():%B %d, %Y} through {df['time'].max():%B %d, %Y}. "
        "Measurements are stored in 5-minute intervals from inductive loop detectors."
    )
    st.write(
        "The variables used here are timestamp, sensor ID, traffic flow, occupancy, "
        "and speed."
    )

show_blind_spots(df["sensor"].nunique())

st.caption("CIVL 6962 · Homework 1 · Streamlit dashboard")
