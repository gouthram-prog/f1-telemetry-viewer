from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import fastf1
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    from fastf1 import plotting as f1plotting
except Exception:  # pragma: no cover
    f1plotting = None

# ------------------------------------------------------------
# App config
# ------------------------------------------------------------
st.set_page_config(page_title="F1 Engineering Telemetry Viewer", layout="wide")

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

CHANNELS = ["Speed", "Throttle", "Brake", "nGear", "RPM", "DRS", "Accel_ms2"]
DEFAULT_CHANNELS = ["Speed", "Throttle", "Brake", "nGear"]

FALLBACK_TEAM_COLORS = {
    "Red Bull Racing": "#3671C6",
    "Mercedes": "#27F4D2",
    "Ferrari": "#E80020",
    "McLaren": "#FF8000",
    "Aston Martin": "#229971",
    "Alpine": "#0093CC",
    "Williams": "#64C4FF",
    "RB": "#6692FF",
    "Racing Bulls": "#6692FF",
    "Kick Sauber": "#52E252",
    "Sauber": "#52E252",
    "Haas F1 Team": "#B6BABD",
    "Haas": "#B6BABD",
}

# ------------------------------------------------------------
# Data helpers
# ------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_schedule(year: int) -> pd.DataFrame:
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    return schedule.dropna(subset=["EventName"]).reset_index(drop=True)


@st.cache_resource(show_spinner=False)
def load_session(year: int, event_name: str, session_code: str):
    session = fastf1.get_session(year, event_name, session_code)
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


def td_to_seconds(series: pd.Series) -> pd.Series:
    return pd.to_timedelta(series).dt.total_seconds()


def get_driver_laps(session, drv: str) -> pd.DataFrame:
    laps = session.laps.pick_drivers(drv).copy()
    laps = laps[laps["LapTime"].notna()].copy()
    laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()
    return laps


def select_lap(laps: pd.DataFrame, mode: str, lap_number: Optional[int] = None):
    if laps.empty:
        return None
    if mode == "Fastest valid lap":
        try:
            return laps.pick_fastest()
        except Exception:
            return laps.sort_values("LapTimeSeconds").iloc[0]
    if lap_number is not None:
        chosen = laps[laps["LapNumber"].astype(int) == int(lap_number)]
        if not chosen.empty:
            return chosen.iloc[0]
    return laps.sort_values("LapTimeSeconds").iloc[0]


def telemetry_for_lap(lap) -> pd.DataFrame:
    tel = lap.get_car_data().add_distance().copy()
    if tel.empty:
        return tel
    tel["TimeSeconds"] = tel["Time"].dt.total_seconds()
    # Convert speed km/h to m/s, then differentiate for longitudinal acceleration estimate.
    if "Speed" in tel.columns:
        tel["Speed_ms"] = tel["Speed"] / 3.6
        dt = tel["TimeSeconds"].diff().replace(0, np.nan)
        tel["Accel_ms2"] = tel["Speed_ms"].diff() / dt
        tel["Accel_g"] = tel["Accel_ms2"] / 9.80665
        # Avoid plotting telemetry glitches as physics.
        tel.loc[tel["Accel_ms2"].abs() > 8.0, ["Accel_ms2", "Accel_g"]] = np.nan
    if "Brake" in tel.columns:
        # FastF1 often returns Brake as bool.
        tel["BrakeBinary"] = tel["Brake"].astype(float)
    return tel


def position_for_lap(lap) -> pd.DataFrame:
    tel = lap.get_telemetry().copy()
    if tel.empty:
        return tel
    if "Distance" not in tel.columns:
        tel = tel.add_distance()
    tel["TimeSeconds"] = tel["Time"].dt.total_seconds()
    if "Speed" in tel.columns:
        tel["Speed_ms"] = tel["Speed"] / 3.6
        dt = tel["TimeSeconds"].diff().replace(0, np.nan)
        tel["Accel_ms2"] = tel["Speed_ms"].diff() / dt
        tel.loc[tel["Accel_ms2"].abs() > 8.0, "Accel_ms2"] = np.nan
    return tel


def clean_for_interp(tel: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    needed = ["Distance", *cols]
    available = [c for c in needed if c in tel.columns]
    out = tel[available].dropna(subset=["Distance"]).sort_values("Distance")
    out = out.drop_duplicates(subset=["Distance"], keep="first")
    return out


def delta_to_reference(ref_tel: pd.DataFrame, cmp_tel: pd.DataFrame, ref_label: str, cmp_label: str, n: int = 1500) -> pd.DataFrame:
    ref = clean_for_interp(ref_tel, ["TimeSeconds"])
    cmp = clean_for_interp(cmp_tel, ["TimeSeconds"])
    if ref.empty or cmp.empty:
        return pd.DataFrame()
    max_dist = min(ref["Distance"].max(), cmp["Distance"].max())
    if not np.isfinite(max_dist) or max_dist <= 0:
        return pd.DataFrame()
    grid = np.linspace(0, max_dist, n)
    ref_t = np.interp(grid, ref["Distance"], ref["TimeSeconds"])
    cmp_t = np.interp(grid, cmp["Distance"], cmp["TimeSeconds"])
    return pd.DataFrame({"Distance": grid, "DeltaSeconds": cmp_t - ref_t, "Reference": ref_label, "Driver": cmp_label})


# ------------------------------------------------------------
# Style helpers
# ------------------------------------------------------------
def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v))) for v in rgb)


def adjust_color(hex_color: str, factor: float) -> str:
    """factor <1 darkens, factor >1 lightens towards white."""
    try:
        r, g, b = hex_to_rgb(hex_color)
    except Exception:
        return "#999999"
    if factor < 1:
        return rgb_to_hex((r * factor, g * factor, b * factor))
    return rgb_to_hex((r + (255 - r) * (factor - 1), g + (255 - g) * (factor - 1), b + (255 - b) * (factor - 1)))


def get_driver_team(session, drv: str) -> str:
    try:
        info = session.get_driver(drv)
        return str(info.get("TeamName") or info.get("Team") or "Unknown")
    except Exception:
        row = session.results[session.results["Abbreviation"] == drv]
        if not row.empty and "TeamName" in row.columns:
            return str(row.iloc[0]["TeamName"])
    return "Unknown"


def get_team_base_color(session, team: str) -> str:
    if f1plotting is not None:
        try:
            return f1plotting.get_team_color(team, session=session)
        except Exception:
            pass
    return FALLBACK_TEAM_COLORS.get(team, "#999999")


def build_driver_styles(session, drivers: List[str], reference_driver: str) -> Dict[str, Dict[str, str]]:
    team_counts: Dict[str, int] = {}
    styles = {}
    for drv in drivers:
        team = get_driver_team(session, drv)
        base = get_team_base_color(session, team)
        # Reference/first team car gets darker team colour; second selected team car gets lighter shade.
        if drv == reference_driver:
            shade = 0.72
            role = "reference / darker team shade"
        else:
            idx = team_counts.get(team, 0)
            shade = 1.35 if idx > 0 else 1.12
            role = "comparison / lighter team shade"
        team_counts[team] = team_counts.get(team, 0) + 1
        styles[drv] = {"team": team, "base": base, "color": adjust_color(base, shade), "role": role}
    return styles


# ------------------------------------------------------------
# Analysis helpers
# ------------------------------------------------------------
def detect_corner_minima(tel: pd.DataFrame, min_distance_gap: float = 120.0) -> pd.DataFrame:
    if tel.empty or "Speed" not in tel.columns:
        return pd.DataFrame()
    df = tel[["Distance", "Speed"]].dropna().copy().reset_index(drop=True)
    if len(df) < 7:
        return pd.DataFrame()
    speed = df["Speed"].rolling(7, center=True, min_periods=1).median().to_numpy()
    dist = df["Distance"].to_numpy()
    candidates = []
    for i in range(2, len(df) - 2):
        if speed[i] <= speed[i - 1] and speed[i] <= speed[i + 1] and speed[i] < np.nanpercentile(speed, 55):
            candidates.append((dist[i], speed[i]))
    selected = []
    for d, s in sorted(candidates, key=lambda x: x[1]):
        if all(abs(d - d0) >= min_distance_gap for d0, _ in selected):
            selected.append((d, s))
    selected = sorted(selected, key=lambda x: x[0])
    return pd.DataFrame({"Corner": [f"C{i+1}" for i in range(len(selected))], "Distance": [d for d, _ in selected], "MinSpeed": [s for _, s in selected]})


def corner_min_speed_table(lap_tels: Dict[str, pd.DataFrame], ref_driver: str) -> pd.DataFrame:
    ref_corners = detect_corner_minima(lap_tels[ref_driver])
    if ref_corners.empty:
        return pd.DataFrame()
    rows = []
    for drv, tel in lap_tels.items():
        clean = clean_for_interp(tel, ["Speed"])
        if clean.empty:
            continue
        speeds = np.interp(ref_corners["Distance"], clean["Distance"], clean["Speed"])
        for corner, dist, speed in zip(ref_corners["Corner"], ref_corners["Distance"], speeds):
            rows.append({"Driver": drv, "Corner": corner, "Distance": dist, "MinSpeed_kph": speed})
    return pd.DataFrame(rows)


def detect_corner_exit_segments(tel: pd.DataFrame, min_len_m: float = 120.0) -> pd.DataFrame:
    required = {"Distance", "Speed", "Throttle", "Accel_ms2"}
    if tel.empty or not required.issubset(tel.columns):
        return pd.DataFrame()
    df = tel.copy().dropna(subset=["Distance", "Speed", "Throttle", "Accel_ms2"]).reset_index(drop=True)
    if df.empty:
        return pd.DataFrame()
    brake_ok = True
    if "Brake" in df.columns:
        brake_ok = ~df["Brake"].astype(bool)
    mask = (df["Throttle"] >= 80) & (df["Accel_ms2"] > 0.25) & brake_ok
    segments = []
    start = None
    for i, ok in enumerate(mask.to_numpy()):
        if ok and start is None:
            start = i
        if (not ok or i == len(mask) - 1) and start is not None:
            end = i if ok else i - 1
            seg = df.iloc[start:end + 1]
            length = float(seg["Distance"].iloc[-1] - seg["Distance"].iloc[0]) if len(seg) > 1 else 0.0
            if length >= min_len_m:
                segments.append({
                    "StartDistance": float(seg["Distance"].iloc[0]),
                    "EndDistance": float(seg["Distance"].iloc[-1]),
                    "Length_m": length,
                    "EntrySpeed_kph": float(seg["Speed"].iloc[0]),
                    "ExitSpeed_kph": float(seg["Speed"].iloc[-1]),
                    "SpeedGain_kph": float(seg["Speed"].iloc[-1] - seg["Speed"].iloc[0]),
                    "MeanAccel_ms2": float(seg["Accel_ms2"].mean()),
                    "PeakAccel_ms2": float(seg["Accel_ms2"].max()),
                })
            start = None
    out = pd.DataFrame(segments)
    if out.empty:
        return out
    out.insert(0, "Zone", [f"Exit/Straight {i+1}" for i in range(len(out))])
    return out


def exit_segment_comparison(lap_tels: Dict[str, pd.DataFrame], ref_driver: str) -> pd.DataFrame:
    ref_segments = detect_corner_exit_segments(lap_tels[ref_driver])
    if ref_segments.empty:
        return pd.DataFrame()
    rows = []
    for drv, tel in lap_tels.items():
        for _, seg in ref_segments.iterrows():
            part = tel[(tel["Distance"] >= seg["StartDistance"]) & (tel["Distance"] <= seg["EndDistance"])].copy()
            if part.empty:
                continue
            rows.append({
                "Driver": drv,
                "Zone": seg["Zone"],
                "StartDistance": seg["StartDistance"],
                "EndDistance": seg["EndDistance"],
                "Length_m": seg["Length_m"],
                "EntrySpeed_kph": float(part["Speed"].iloc[0]) if "Speed" in part else np.nan,
                "ExitSpeed_kph": float(part["Speed"].iloc[-1]) if "Speed" in part else np.nan,
                "SpeedGain_kph": float(part["Speed"].iloc[-1] - part["Speed"].iloc[0]) if "Speed" in part else np.nan,
                "MeanAccel_ms2": float(part["Accel_ms2"].mean()) if "Accel_ms2" in part else np.nan,
                "PeakAccel_ms2": float(part["Accel_ms2"].max()) if "Accel_ms2" in part else np.nan,
            })
    return pd.DataFrame(rows)


# ------------------------------------------------------------
# Plot helpers
# ------------------------------------------------------------
def update_fig_layout(fig: go.Figure, height: int = 360, ytitle: Optional[str] = None) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=35, b=25),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title="Distance [m]")
    if ytitle:
        fig.update_yaxes(title=ytitle)
    return fig


def plot_multi_channel(lap_tels: Dict[str, pd.DataFrame], labels: Dict[str, str], styles: Dict[str, Dict[str, str]], channel: str) -> go.Figure:
    fig = go.Figure()
    for drv, tel in lap_tels.items():
        if channel not in tel.columns:
            continue
        fig.add_trace(go.Scatter(x=tel["Distance"], y=tel[channel], mode="lines", name=labels[drv], line=dict(color=styles[drv]["color"])))
    return update_fig_layout(fig, ytitle=channel)


def plot_delta_all(delta_frames: List[pd.DataFrame], styles: Dict[str, Dict[str, str]]) -> go.Figure:
    fig = go.Figure()
    for d in delta_frames:
        if d.empty:
            continue
        drv = d["Driver"].iloc[0]
        fig.add_trace(go.Scatter(x=d["Distance"], y=d["DeltaSeconds"], mode="lines", name=drv, line=dict(color=styles[drv]["color"])))
    fig.add_hline(y=0, line_dash="dash")
    return update_fig_layout(fig, height=420, ytitle="Delta to reference [s]")


def plot_accel_exit(lap_tels: Dict[str, pd.DataFrame], labels: Dict[str, str], styles: Dict[str, Dict[str, str]], segments: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for drv, tel in lap_tels.items():
        if "Accel_ms2" not in tel.columns:
            continue
        fig.add_trace(go.Scatter(x=tel["Distance"], y=tel["Accel_ms2"], mode="lines", name=labels[drv], line=dict(color=styles[drv]["color"])))
    if not segments.empty:
        for _, seg in segments.iterrows():
            fig.add_vrect(x0=seg["StartDistance"], x1=seg["EndDistance"], opacity=0.12, line_width=0)
    return update_fig_layout(fig, height=430, ytitle="Longitudinal acceleration estimate [m/s²]")


def plot_track_map(pos: pd.DataFrame, metric: str, title: str) -> Optional[go.Figure]:
    if pos.empty or not {"X", "Y"}.issubset(pos.columns):
        return None
    color = metric if metric in pos.columns else "Speed"
    hover = [c for c in ["Distance", "Speed", "Throttle", "Brake", "nGear", "RPM", "Accel_ms2"] if c in pos.columns]
    fig = px.scatter(pos, x="X", y="Y", color=color, hover_data=hover, title=title)
    fig.update_traces(marker=dict(size=4))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, visible=False)
    fig.update_xaxes(visible=False)
    fig.update_layout(height=560, margin=dict(l=10, r=10, t=40, b=10), coloraxis_colorbar_title=color)
    return fig


def plot_dominance_map(ref_pos: pd.DataFrame, cmp_tel: pd.DataFrame, cmp_driver: str, ref_driver: str) -> Optional[go.Figure]:
    if ref_pos.empty or cmp_tel.empty or not {"X", "Y", "Distance", "Speed"}.issubset(ref_pos.columns) or "Speed" not in cmp_tel.columns:
        return None
    cmp_clean = clean_for_interp(cmp_tel, ["Speed"])
    ref_clean = ref_pos.dropna(subset=["Distance", "Speed", "X", "Y"]).sort_values("Distance")
    max_dist = min(ref_clean["Distance"].max(), cmp_clean["Distance"].max())
    ref_clean = ref_clean[ref_clean["Distance"] <= max_dist].copy()
    ref_clean["SpeedDelta_kph"] = np.interp(ref_clean["Distance"], cmp_clean["Distance"], cmp_clean["Speed"]) - ref_clean["Speed"]
    fig = px.scatter(ref_clean, x="X", y="Y", color="SpeedDelta_kph", color_continuous_scale="RdBu", color_continuous_midpoint=0,
                     hover_data=["Distance", "Speed", "SpeedDelta_kph"], title=f"Speed dominance map: {cmp_driver} - {ref_driver}")
    fig.update_traces(marker=dict(size=4))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, visible=False)
    fig.update_xaxes(visible=False)
    fig.update_layout(height=560, margin=dict(l=10, r=10, t=40, b=10), coloraxis_colorbar_title="Δ speed [km/h]")
    return fig


def export_csv(lap_tels: Dict[str, pd.DataFrame], labels: Dict[str, str], deltas: List[pd.DataFrame], corner_table: pd.DataFrame, exit_table: pd.DataFrame) -> bytes:
    sections = []
    for drv, tel in lap_tels.items():
        t = tel.copy()
        t.insert(0, "Driver", drv)
        t.insert(1, "Label", labels[drv])
        sections.append(f"# Telemetry {drv}\n" + t.to_csv(index=False))
    if deltas:
        sections.append("# Delta to reference\n" + pd.concat(deltas, ignore_index=True).to_csv(index=False))
    if not corner_table.empty:
        sections.append("# Corner minimum speed table\n" + corner_table.to_csv(index=False))
    if not exit_table.empty:
        sections.append("# Corner exit / straight acceleration table\n" + exit_table.to_csv(index=False))
    return ("\n".join(sections)).encode("utf-8")


# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.title("F1 Engineering Telemetry Viewer")
st.caption("FastF1-powered multi-driver telemetry, reference deltas, corner-exit acceleration, track maps, tyre/stint analysis and exports.")

with st.sidebar:
    st.header("Session")
    current_year = pd.Timestamp.today().year
    year = st.number_input("Year", min_value=2018, max_value=current_year, value=min(current_year, 2025), step=1)

    try:
        schedule = get_schedule(int(year))
    except Exception as e:
        st.error(f"Could not load schedule: {e}")
        st.stop()

    events = schedule["EventName"].tolist()
    event_name = st.selectbox("Grand Prix", events, index=max(0, len(events) - 1))
    session_label = st.selectbox("Session", list(SESSION_TYPES.keys()), index=list(SESSION_TYPES.keys()).index("Qualifying"))
    session_code = SESSION_TYPES[session_label]
    load_btn = st.button("Load session", type="primary")

if "loaded_key" not in st.session_state:
    st.session_state.loaded_key = None

key = (int(year), event_name, session_code)
if not (load_btn or st.session_state.loaded_key == key):
    st.info("Choose a year, event and session, then load the session.")
    st.stop()

st.session_state.loaded_key = key
with st.spinner("Loading FastF1 data. First load can take a while; later loads use cache."):
    try:
        session = load_session(int(year), event_name, session_code)
    except Exception as e:
        st.error(f"Could not load session: {e}")
        st.stop()

drivers = sorted(session.laps["Driver"].dropna().unique().tolist())
if not drivers:
    st.warning("No driver lap data found for this session.")
    st.stop()

st.sidebar.header("Drivers and laps")
default_drivers = drivers[: min(5, len(drivers))]
selected_drivers = st.sidebar.multiselect("Compare up to 5 drivers", drivers, default=default_drivers, max_selections=5)
if not selected_drivers:
    st.warning("Select at least one driver.")
    st.stop()
reference_driver = st.sidebar.selectbox("Reference driver for deltas", selected_drivers, index=0)
selection_mode = st.sidebar.radio("Lap selection", ["Fastest valid lap", "Choose lap per driver"], index=0)

selected_laps = {}
labels = {}
for drv in selected_drivers:
    laps = get_driver_laps(session, drv)
    lap_number = None
    if selection_mode == "Choose lap per driver":
        nums = laps["LapNumber"].astype(int).tolist()
        if nums:
            lap_number = st.sidebar.selectbox(f"{drv} lap", nums, index=0, key=f"lap_{drv}")
    lap = select_lap(laps, selection_mode, lap_number)
    if lap is not None:
        selected_laps[drv] = lap
        labels[drv] = f"{drv} L{int(lap['LapNumber'])} ({fmt_laptime(lap['LapTime'])})"

if reference_driver not in selected_laps:
    st.warning("Reference driver does not have a valid selected lap.")
    st.stop()

styles = build_driver_styles(session, list(selected_laps.keys()), reference_driver)

with st.spinner("Preparing telemetry traces and analysis tables."):
    lap_tels = {drv: telemetry_for_lap(lap) for drv, lap in selected_laps.items()}
    lap_pos = {drv: position_for_lap(lap) for drv, lap in selected_laps.items()}
    ref_tel = lap_tels[reference_driver]
    deltas = [delta_to_reference(ref_tel, tel, reference_driver, drv) for drv, tel in lap_tels.items() if drv != reference_driver]
    corner_table = corner_min_speed_table(lap_tels, reference_driver)
    exit_table = exit_segment_comparison(lap_tels, reference_driver)
    ref_exit_segments = detect_corner_exit_segments(ref_tel)

# Summary cards
st.subheader("Selected laps")
summary_cols = ["Driver", "Team", "Lap", "Lap time", "S1", "S2", "S3", "Compound", "TyreLife", "Stint", "Colour role"]
summary_rows = []
for drv, lap in selected_laps.items():
    summary_rows.append({
        "Driver": drv,
        "Team": styles[drv]["team"],
        "Lap": int(lap["LapNumber"]),
        "Lap time": fmt_laptime(lap["LapTime"]),
        "S1": fmt_laptime(lap.get("Sector1Time")),
        "S2": fmt_laptime(lap.get("Sector2Time")),
        "S3": fmt_laptime(lap.get("Sector3Time")),
        "Compound": lap.get("Compound"),
        "TyreLife": lap.get("TyreLife"),
        "Stint": lap.get("Stint"),
        "Colour role": styles[drv]["role"],
    })
st.dataframe(pd.DataFrame(summary_rows, columns=summary_cols), use_container_width=True, hide_index=True)

legend_cols = st.columns(min(len(selected_laps), 5))
for col, drv in zip(legend_cols, selected_laps.keys()):
    col.markdown(f"<div style='border-left: 14px solid {styles[drv]['color']}; padding-left: 8px'><b>{drv}</b><br>{styles[drv]['team']}</div>", unsafe_allow_html=True)

# Tabs
tabs = st.tabs([
    "Timing",
    "Telemetry overlays",
    "Delta to reference",
    "Corner exits / straights",
    "Track maps",
    "Tyres & stints",
    "Exports",
])

with tabs[0]:
    st.markdown("### Lap time evolution")
    all_laps = session.laps.copy()
    all_laps = all_laps[all_laps["LapTime"].notna()].copy()
    all_laps = all_laps[all_laps["Driver"].isin(selected_laps.keys())]
    all_laps["LapTimeSeconds"] = all_laps["LapTime"].dt.total_seconds()
    fig = go.Figure()
    for drv in selected_laps.keys():
        d = all_laps[all_laps["Driver"] == drv]
        fig.add_trace(go.Scatter(x=d["LapNumber"], y=d["LapTimeSeconds"], mode="lines+markers", name=drv, line=dict(color=styles[drv]["color"])))
    fig.update_layout(height=420, margin=dict(l=20, r=20, t=35, b=25), xaxis_title="Lap", yaxis_title="Lap time [s]", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Full lap table")
    table_cols = ["Driver", "LapNumber", "LapTimeSeconds", "Sector1Time", "Sector2Time", "Sector3Time", "Compound", "TyreLife", "Stint", "PitInTime", "PitOutTime", "IsAccurate"]
    show_cols = [c for c in table_cols if c in all_laps.columns]
    st.dataframe(all_laps[show_cols].sort_values(["LapTimeSeconds", "Driver"]), use_container_width=True, hide_index=True)

with tabs[1]:
    selected_channels = st.multiselect("Channels", [c for c in CHANNELS if any(c in t.columns for t in lap_tels.values())], default=[c for c in DEFAULT_CHANNELS if any(c in t.columns for t in lap_tels.values())])
    for ch in selected_channels:
        st.plotly_chart(plot_multi_channel(lap_tels, labels, styles, ch), use_container_width=True)

    st.markdown("### Gear usage histogram")
    if any("nGear" in t.columns for t in lap_tels.values()):
        gear_rows = []
        for drv, tel in lap_tels.items():
            if "nGear" in tel.columns:
                counts = tel["nGear"].round().astype("Int64").value_counts().sort_index()
                for gear, count in counts.items():
                    gear_rows.append({"Driver": drv, "Gear": int(gear), "Samples": int(count)})
        gear_df = pd.DataFrame(gear_rows)
        fig = px.bar(gear_df, x="Gear", y="Samples", color="Driver", barmode="group", color_discrete_map={d: styles[d]["color"] for d in styles})
        fig.update_layout(height=380, margin=dict(l=20, r=20, t=35, b=25))
        st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    if not deltas:
        st.info("Select at least two drivers to show delta traces.")
    else:
        st.plotly_chart(plot_delta_all(deltas, styles), use_container_width=True)
        st.caption("Positive delta means the compared driver is slower than the selected reference at that distance. Negative means faster.")

    st.markdown("### Corner minimum speed table")
    if corner_table.empty:
        st.info("Could not infer corner minima from the reference lap.")
    else:
        pivot = corner_table.pivot_table(index=["Corner", "Distance"], columns="Driver", values="MinSpeed_kph").reset_index()
        st.dataframe(pivot, use_container_width=True, hide_index=True)
        fig = px.line(corner_table, x="Corner", y="MinSpeed_kph", color="Driver", markers=True, color_discrete_map={d: styles[d]["color"] for d in styles})
        fig.update_layout(height=420, margin=dict(l=20, r=20, t=35, b=25), yaxis_title="Minimum speed [km/h]")
        st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    st.markdown("### Corner exit and straight-line acceleration")
    st.plotly_chart(plot_accel_exit(lap_tels, labels, styles, ref_exit_segments), use_container_width=True)
    st.caption("Shaded zones are inferred from the reference lap where throttle is high, brake is off and speed is rising. Acceleration is estimated from speed/time, so treat it as comparative rather than absolute sensor-grade data.")

    if exit_table.empty:
        st.info("No long corner-exit/straight zones were detected for the selected reference lap.")
    else:
        st.dataframe(exit_table.round(3), use_container_width=True, hide_index=True)
        metric = st.selectbox("Exit-zone metric", ["ExitSpeed_kph", "SpeedGain_kph", "MeanAccel_ms2", "PeakAccel_ms2"], index=2)
        fig = px.bar(exit_table, x="Zone", y=metric, color="Driver", barmode="group", color_discrete_map={d: styles[d]["color"] for d in styles})
        fig.update_layout(height=430, margin=dict(l=20, r=20, t=35, b=25))
        st.plotly_chart(fig, use_container_width=True)

with tabs[4]:
    st.markdown("### Single-driver track map")
    c1, c2 = st.columns(2)
    with c1:
        map_driver = st.selectbox("Driver for track map", list(selected_laps.keys()), index=0)
    with c2:
        possible_metrics = [c for c in ["Speed", "Throttle", "Brake", "nGear", "RPM", "Accel_ms2"] if c in lap_pos[map_driver].columns]
        map_metric = st.selectbox("Colour by", possible_metrics, index=0)
    fig = plot_track_map(lap_pos[map_driver], map_metric, f"{map_driver} track map coloured by {map_metric}")
    if fig is None:
        st.warning("Position data not available for this lap.")
    else:
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Speed dominance map versus reference")
    cmp_options = [d for d in selected_laps.keys() if d != reference_driver]
    if not cmp_options:
        st.info("Select at least two drivers for a dominance map.")
    else:
        cmp_driver = st.selectbox("Compare driver", cmp_options, index=0)
        fig = plot_dominance_map(lap_pos[reference_driver], lap_tels[cmp_driver], cmp_driver, reference_driver)
        if fig is None:
            st.warning("Could not create dominance map for this comparison.")
        else:
            st.plotly_chart(fig, use_container_width=True)

with tabs[5]:
    st.markdown("### Race pace / stint view")
    all_laps = session.laps.copy()
    all_laps = all_laps[all_laps["LapTime"].notna() & all_laps["Driver"].isin(selected_laps.keys())].copy()
    all_laps["LapTimeSeconds"] = all_laps["LapTime"].dt.total_seconds()
    if all_laps.empty:
        st.info("No lap data available.")
    else:
        fig = px.box(all_laps, x="Driver", y="LapTimeSeconds", color="Compound" if "Compound" in all_laps.columns else "Driver", points="all")
        fig.update_layout(height=430, margin=dict(l=20, r=20, t=35, b=25), yaxis_title="Lap time [s]")
        st.plotly_chart(fig, use_container_width=True)

        if "TyreLife" in all_laps.columns:
            fig = px.scatter(all_laps, x="TyreLife", y="LapTimeSeconds", color="Driver", symbol="Compound" if "Compound" in all_laps.columns else None, trendline=None, color_discrete_map={d: styles[d]["color"] for d in styles})
            fig.update_layout(height=430, margin=dict(l=20, r=20, t=35, b=25), xaxis_title="Tyre life [laps]", yaxis_title="Lap time [s]")
            st.plotly_chart(fig, use_container_width=True)

with tabs[6]:
    st.markdown("### Export")
    file_base = f"telemetry_{year}_{event_name}_{session_code}_{'_'.join(selected_laps.keys())}".replace(" ", "_").replace("/", "-")
    st.download_button(
        "Download telemetry, deltas and analysis CSV",
        data=export_csv(lap_tels, labels, deltas, corner_table, exit_table),
        file_name=f"{file_base}.csv",
        mime="text/csv",
    )

    st.markdown("### Notes")
    st.write(
        "FastF1 public telemetry is excellent for comparative analysis, but it is still reconstructed/public timing feed data. "
        "Acceleration is calculated from speed/time, and some position/telemetry channels may be interpolated depending on the FastF1 method used."
    )
