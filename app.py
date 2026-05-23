from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

import fastf1
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------
# App config
# ------------------------------------------------------------
st.set_page_config(page_title="F1 Telemetry Viewer", layout="wide")

CACHE_DIR = Path("./fastf1_cache")
CACHE_DIR.mkdir(exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

SESSION_TYPES = {
    "Practice 1": "FP1",
    "Practice 2": "FP2",
    "Practice 3": "FP3",
    "Sprint Shootout / Sprint Quali": "SQ",
    "Sprint": "S",
    "Qualifying": "Q",
    "Race": "R",
}

CHANNELS = ["Speed", "Throttle", "Brake", "nGear", "RPM", "DRS"]

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_schedule(year: int) -> pd.DataFrame:
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    # Drop non-GP placeholders if present
    return schedule.dropna(subset=["EventName"]).reset_index(drop=True)


@st.cache_resource(show_spinner=False)
def load_session(year: int, event_name: str, session_code: str):
    session = fastf1.get_session(year, event_name, session_code)
    # telemetry=True is important for car data; weather/messages are useful but can slow loading.
    session.load(laps=True, telemetry=True, weather=True, messages=False)
    return session


def seconds(td) -> Optional[float]:
    if pd.isna(td):
        return None
    return float(pd.to_timedelta(td).total_seconds())


def fmt_laptime(td) -> str:
    s = seconds(td)
    if s is None:
        return "—"
    minutes = int(s // 60)
    rem = s - 60 * minutes
    return f"{minutes}:{rem:06.3f}"


def get_driver_laps(session, drv: str) -> pd.DataFrame:
    laps = session.laps.pick_drivers(drv).copy()
    laps = laps[laps["LapTime"].notna()].copy()
    laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()
    return laps


def select_lap(laps: pd.DataFrame, mode: str, lap_number: Optional[int] = None):
    if laps.empty:
        return None
    if mode == "Fastest valid lap":
        return laps.pick_fastest()
    if lap_number is not None:
        chosen = laps[laps["LapNumber"] == lap_number]
        if not chosen.empty:
            return chosen.iloc[0]
    return laps.pick_fastest()


def lap_telemetry(lap) -> pd.DataFrame:
    # get_car_data gives car channels; add_distance gives a usable x-axis for overlays.
    tel = lap.get_car_data().add_distance().copy()
    # Some sessions/channels may be missing; keep only columns present.
    tel["TimeSeconds"] = tel["Time"].dt.total_seconds()
    return tel


def lap_position(lap) -> pd.DataFrame:
    # get_telemetry merges car + position channels and gives X/Y for track map.
    tel = lap.get_telemetry().copy()
    if "Distance" not in tel.columns:
        tel = tel.add_distance()
    tel["TimeSeconds"] = tel["Time"].dt.total_seconds()
    return tel


def resample_for_delta(ref: pd.DataFrame, cmp: pd.DataFrame, n: int = 1200) -> pd.DataFrame:
    """Approximate delta trace by interpolating Time vs Distance onto a common distance grid."""
    ref = ref.dropna(subset=["Distance", "TimeSeconds"]).sort_values("Distance")
    cmp = cmp.dropna(subset=["Distance", "TimeSeconds"]).sort_values("Distance")
    max_dist = min(ref["Distance"].max(), cmp["Distance"].max())
    grid = np.linspace(0, max_dist, n)
    ref_t = np.interp(grid, ref["Distance"], ref["TimeSeconds"])
    cmp_t = np.interp(grid, cmp["Distance"], cmp["TimeSeconds"])
    return pd.DataFrame({"Distance": grid, "DeltaSeconds": cmp_t - ref_t})


def plot_channel_overlay(tel_a: pd.DataFrame, tel_b: pd.DataFrame, label_a: str, label_b: str, channel: str):
    fig = go.Figure()
    if channel in tel_a.columns:
        fig.add_trace(go.Scatter(x=tel_a["Distance"], y=tel_a[channel], name=label_a, mode="lines"))
    if channel in tel_b.columns:
        fig.add_trace(go.Scatter(x=tel_b["Distance"], y=tel_b[channel], name=label_b, mode="lines"))
    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=35, b=20),
        xaxis_title="Distance [m]",
        yaxis_title=channel,
        hovermode="x unified",
    )
    return fig


def plot_delta(delta: pd.DataFrame, label_a: str, label_b: str):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=delta["Distance"], y=delta["DeltaSeconds"], mode="lines", name=f"{label_b} - {label_a}"))
    fig.add_hline(y=0, line_dash="dash")
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=35, b=20),
        xaxis_title="Distance [m]",
        yaxis_title="Delta [s]",
        hovermode="x unified",
    )
    return fig


def plot_track_map(pos: pd.DataFrame, metric: str):
    if not {"X", "Y"}.issubset(pos.columns):
        return None
    color = metric if metric in pos.columns else "Speed"
    fig = px.scatter(pos, x="X", y="Y", color=color, hover_data=[c for c in ["Distance", "Speed", "Throttle", "Brake", "nGear", "RPM"] if c in pos.columns])
    fig.update_traces(marker=dict(size=4))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, visible=False)
    fig.update_xaxes(visible=False)
    fig.update_layout(height=550, margin=dict(l=10, r=10, t=30, b=10), coloraxis_colorbar_title=color)
    return fig


def make_export(tel_a: pd.DataFrame, tel_b: pd.DataFrame, label_a: str, label_b: str, delta: pd.DataFrame) -> bytes:
    a = tel_a.copy()
    b = tel_b.copy()
    a.insert(0, "Trace", label_a)
    b.insert(0, "Trace", label_b)
    delta2 = delta.copy()
    delta2.insert(0, "Trace", f"Delta: {label_b} - {label_a}")
    export = pd.concat([a, b], ignore_index=True, sort=False)
    # Write simple CSV sections
    return (
        "# Telemetry\n" + export.to_csv(index=False) + "\n# Delta\n" + delta2.to_csv(index=False)
    ).encode("utf-8")

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.title("F1 Telemetry Viewer")
st.caption("FastF1-powered lap timing, telemetry overlay, delta trace and track map.")

with st.sidebar:
    st.header("Session")
    current_year = pd.Timestamp.today().year
    year = st.number_input("Year", min_value=2018, max_value=current_year, value=min(current_year, 2025), step=1)

    schedule = get_schedule(int(year))
    events = schedule["EventName"].tolist()
    event_name = st.selectbox("Grand Prix", events, index=max(0, len(events) - 1))
    session_label = st.selectbox("Session", list(SESSION_TYPES.keys()), index=list(SESSION_TYPES.keys()).index("Qualifying"))
    session_code = SESSION_TYPES[session_label]

    load_btn = st.button("Load session", type="primary")

if "loaded_key" not in st.session_state:
    st.session_state.loaded_key = None

key = (int(year), event_name, session_code)
if load_btn or st.session_state.loaded_key == key:
    st.session_state.loaded_key = key
    with st.spinner("Loading FastF1 data. First load can take a while; later loads use cache."):
        try:
            session = load_session(int(year), event_name, session_code)
        except Exception as e:
            st.error(f"Could not load session: {e}")
            st.stop()

    drivers = sorted(session.laps["Driver"].dropna().unique().tolist())
    if len(drivers) < 1:
        st.warning("No driver lap data found for this session.")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        driver_a = st.selectbox("Reference driver", drivers, index=0)
    with c2:
        driver_b = st.selectbox("Compare driver", drivers, index=min(1, len(drivers) - 1))

    laps_a = get_driver_laps(session, driver_a)
    laps_b = get_driver_laps(session, driver_b)
    lap_nums_a = laps_a["LapNumber"].astype(int).tolist()
    lap_nums_b = laps_b["LapNumber"].astype(int).tolist()

    with c3:
        mode_a = st.selectbox("Reference lap mode", ["Fastest valid lap", "Choose lap"], index=0)
        lap_num_a = st.selectbox("Reference lap", lap_nums_a, index=0, disabled=(mode_a == "Fastest valid lap")) if lap_nums_a else None
    with c4:
        mode_b = st.selectbox("Compare lap mode", ["Fastest valid lap", "Choose lap"], index=0)
        lap_num_b = st.selectbox("Compare lap", lap_nums_b, index=0, disabled=(mode_b == "Fastest valid lap")) if lap_nums_b else None

    lap_a = select_lap(laps_a, mode_a, lap_num_a)
    lap_b = select_lap(laps_b, mode_b, lap_num_b)
    if lap_a is None or lap_b is None:
        st.warning("Could not select valid laps for both drivers.")
        st.stop()

    label_a = f"{driver_a} L{int(lap_a['LapNumber'])} ({fmt_laptime(lap_a['LapTime'])})"
    label_b = f"{driver_b} L{int(lap_b['LapNumber'])} ({fmt_laptime(lap_b['LapTime'])})"

    tel_a = lap_telemetry(lap_a)
    tel_b = lap_telemetry(lap_b)
    pos_a = lap_position(lap_a)
    delta = resample_for_delta(tel_a, tel_b)

    st.subheader("Lap summary")
    summary_cols = ["Driver", "LapNumber", "LapTime", "Sector1Time", "Sector2Time", "Sector3Time", "Compound", "TyreLife", "Stint"]
    summary = pd.DataFrame([lap_a, lap_b])[summary_cols].copy()
    for col in ["LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]:
        summary[col] = summary[col].apply(fmt_laptime)
    st.dataframe(summary, use_container_width=True, hide_index=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Telemetry overlay", "Delta", "Track map", "Lap tables"])

    with tab1:
        selected_channels = st.multiselect("Channels", CHANNELS, default=["Speed", "Throttle", "Brake", "nGear"])
        for ch in selected_channels:
            st.plotly_chart(plot_channel_overlay(tel_a, tel_b, label_a, label_b, ch), use_container_width=True)

    with tab2:
        st.plotly_chart(plot_delta(delta, label_a, label_b), use_container_width=True)
        st.caption("Positive delta means the compare lap is slower than the reference lap at that distance.")

    with tab3:
        metric = st.selectbox("Colour track by", [c for c in ["Speed", "Throttle", "Brake", "nGear", "RPM"] if c in pos_a.columns])
        fig = plot_track_map(pos_a, metric)
        if fig is None:
            st.warning("Position data not available for this lap.")
        else:
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.markdown("#### Driver lap table")
        all_laps = session.laps.copy()
        all_laps = all_laps[all_laps["LapTime"].notna()].copy()
        all_laps["LapTimeSeconds"] = all_laps["LapTime"].dt.total_seconds()
        table_cols = ["Driver", "LapNumber", "LapTimeSeconds", "Sector1Time", "Sector2Time", "Sector3Time", "Compound", "TyreLife", "Stint", "PitInTime", "PitOutTime"]
        st.dataframe(all_laps[table_cols].sort_values("LapTimeSeconds"), use_container_width=True, hide_index=True)

    st.download_button(
        "Download selected telemetry + delta CSV",
        data=make_export(tel_a, tel_b, label_a, label_b, delta),
        file_name=f"telemetry_{year}_{event_name}_{session_code}_{driver_a}_vs_{driver_b}.csv".replace(" ", "_"),
        mime="text/csv",
    )
else:
    st.info("Choose a year, event and session, then load the session.")
