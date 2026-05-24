from __future__ import annotations

import math
import html
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

st.markdown(
    """
    <style>
    /* Mobile-first Streamlit layout: reduce wasted space and keep controls usable on iPhone Pro Max. */
    .block-container {
        padding-top: 0.8rem;
        padding-left: 0.65rem;
        padding-right: 0.65rem;
        padding-bottom: 1.5rem;
        max-width: 1500px;
    }
    h1 { font-size: clamp(1.35rem, 5vw, 2.35rem) !important; line-height: 1.15; }
    h2 { font-size: clamp(1.15rem, 4vw, 1.75rem) !important; }
    h3 { font-size: clamp(1.0rem, 3.6vw, 1.35rem) !important; }
    div[data-testid="stMetricValue"] { font-size: clamp(1.0rem, 4vw, 1.5rem); }
    div[data-testid="stDataFrame"] { font-size: 0.78rem; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.2rem;
        overflow-x: auto;
        flex-wrap: nowrap;
    }
    .stTabs [data-baseweb="tab"] {
        padding-left: 0.45rem;
        padding-right: 0.45rem;
        min-width: max-content;
        font-size: 0.86rem;
    }
    section[data-testid="stSidebar"] { min-width: 18rem; }
    @media (max-width: 760px) {
        .block-container { padding-left: 0.45rem; padding-right: 0.45rem; }
        div[data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
        div[data-testid="stHorizontalBlock"] { gap: 0.25rem; }
        div[data-testid="stPlotlyChart"] { margin-bottom: 0.35rem; }
    }

    .f1-hero {border:1px solid rgba(255,255,255,.10); border-radius:16px; padding:14px 14px 10px 14px; background:linear-gradient(135deg, rgba(20,30,42,.98), rgba(7,11,18,.98)); margin-bottom:14px; box-shadow:0 8px 28px rgba(0,0,0,.24);} 
    .f1-brand {display:flex; align-items:center; gap:12px; font-weight:800; font-size:clamp(1.15rem, 5.3vw, 2rem); letter-spacing:.2px;}
    .f1-logo {color:#ff1e1e; font-style:italic; font-weight:900; font-size:1.25em;}
    .f1-subtitle {color:rgba(255,255,255,.62); margin-top:7px; font-size:clamp(.84rem, 3.5vw, 1rem);} 
    .f1-card {border:1px solid rgba(255,255,255,.10); border-radius:14px; padding:12px; background:linear-gradient(180deg, rgba(25,32,42,.94), rgba(10,14,21,.94)); margin:10px 0; box-shadow:0 5px 18px rgba(0,0,0,.18);} 
    .f1-card-title {font-weight:760; margin-bottom:9px; font-size:1.02rem;}
    .f1-table {width:100%; border-collapse:collapse; font-size:.86rem; overflow:hidden; border-radius:12px;}
    .f1-table th {background:rgba(255,255,255,.08); padding:8px 6px; color:rgba(255,255,255,.78); font-weight:650; text-align:left;}
    .f1-table td {padding:8px 6px; border-top:1px solid rgba(255,255,255,.08); vertical-align:middle;}
    .f1-drivercell {display:flex; gap:8px; align-items:center; min-width:92px;}
    .f1-rank {width:4px; min-height:40px; border-radius:3px; display:inline-block;}
    .f1-small {font-size:.72rem; color:rgba(255,255,255,.65);}
    .f1-team {font-size:.78rem; font-weight:650;}
    .f1-delta-pos {color:#ff5555; font-weight:700;}
    .f1-delta-neg {color:#32d083; font-weight:700;}
    .f1-chip {display:inline-flex; align-items:center; justify-content:center; min-width:23px; height:23px; padding:0 6px; border-radius:999px; border:1px solid rgba(255,255,255,.18); font-weight:800; font-size:.72rem;}
    .f1-chip-soft {color:#ff4d5a; border-color:#ff4d5a;}
    .f1-chip-medium {color:#ffd21f; border-color:#ffd21f;}
    .f1-chip-hard {color:#f0f0f0; border-color:#f0f0f0;}
    .f1-chip-intermediate {color:#43d47c; border-color:#43d47c;}
    .f1-chip-wet {color:#4aa3ff; border-color:#4aa3ff;}
    .f1-kpi-grid {display:grid; grid-template-columns:repeat(5,minmax(110px,1fr)); gap:10px;}
    .f1-kpi {border:1px solid rgba(255,255,255,.10); border-radius:12px; padding:10px; background:rgba(255,255,255,.035);} 
    .f1-kpi b {display:block; font-size:.82rem; margin-bottom:5px;}
    @media (max-width: 760px) {
        .f1-table {font-size:.78rem;}
        .f1-table th, .f1-table td {padding:7px 5px;}
        .f1-hide-mobile {display:none;}
        .f1-kpi-grid {grid-template-columns:repeat(2,minmax(0,1fr));}
        .stTabs [data-baseweb="tab"] {font-size:.78rem; padding-left:.35rem; padding-right:.35rem;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

SESSION_TYPES = {
    "Practice 1": "FP1",
    "Practice 2": "FP2",
    "Practice 3": "FP3",
    "Sprint Shootout": "SQ",
    "Sprint Qualifying": "SQ",
    "Sprint": "S",
    "Qualifying": "Q",
    "Race": "R",
}

SESSION_DATE_COLUMNS = ["Session1Date", "Session2Date", "Session3Date", "Session4Date", "Session5Date"]
SESSION_NAME_COLUMNS = ["Session1", "Session2", "Session3", "Session4", "Session5"]

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


def _to_timestamp_utc(value) -> Optional[pd.Timestamp]:
    if pd.isna(value):
        return None
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts


def event_has_available_data(row: pd.Series, now_utc: Optional[pd.Timestamp] = None) -> bool:
    """Return True if at least one session should have public timing data available."""
    now_utc = now_utc or pd.Timestamp.now(tz="UTC")
    for col in SESSION_DATE_COLUMNS:
        if col not in row.index:
            continue
        ts = _to_timestamp_utc(row.get(col))
        # Add a small grace period: sessions are often available shortly after running.
        if ts is not None and ts <= now_utc + pd.Timedelta(hours=2):
            return True
    return False


def available_events(schedule: pd.DataFrame) -> List[str]:
    now_utc = pd.Timestamp.now(tz="UTC")
    rows = schedule[schedule.apply(lambda r: event_has_available_data(r, now_utc), axis=1)].copy()
    return rows["EventName"].dropna().tolist()


def available_sessions_for_event(schedule: pd.DataFrame, event_name: str) -> List[str]:
    """Return available FastF1 session display names for the selected event only."""
    match = schedule[schedule["EventName"] == event_name]
    if match.empty:
        return []
    row = match.iloc[0]
    now_utc = pd.Timestamp.now(tz="UTC")
    sessions: List[str] = []
    for name_col, date_col in zip(SESSION_NAME_COLUMNS, SESSION_DATE_COLUMNS):
        if name_col not in row.index or date_col not in row.index:
            continue
        session_name = row.get(name_col)
        session_date = _to_timestamp_utc(row.get(date_col))
        if pd.isna(session_name) or session_date is None:
            continue
        if session_date <= now_utc + pd.Timedelta(hours=2):
            label = str(session_name)
            if label in SESSION_TYPES and label not in sessions:
                sessions.append(label)
    return sessions


def session_code_from_label(label: str) -> str:
    return SESSION_TYPES.get(label, label)


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


def format_lap_table(laps: pd.DataFrame) -> pd.DataFrame:
    """Make Streamlit tables show exact sector/lap times instead of fuzzy timedelta text."""
    out = laps.copy()
    for col in ["LapTime", "Sector1Time", "Sector2Time", "Sector3Time", "PitInTime", "PitOutTime"]:
        if col in out.columns:
            out[col] = out[col].apply(fmt_laptime)
    if "LapTimeSeconds" not in out.columns and "LapTime" in laps.columns:
        out["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()
    for col in ["LapTimeSeconds"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(3)
    return out


def add_sector_seconds(laps: pd.DataFrame) -> pd.DataFrame:
    out = laps.copy()
    for col in ["Sector1Time", "Sector2Time", "Sector3Time"]:
        if col in out.columns:
            out[col.replace("Time", "Seconds")] = out[col].dt.total_seconds().round(3)
    return out


def classify_fresh_tyre(value) -> str:
    if pd.isna(value):
        return "Unknown"
    if isinstance(value, (bool, np.bool_)):
        return "Fresh" if bool(value) else "Used"
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "fresh", "new"}:
        return "Fresh"
    if text in {"false", "0", "no", "used", "old"}:
        return "Used"
    return str(value)


def add_tyre_columns(laps: pd.DataFrame) -> pd.DataFrame:
    out = laps.copy()
    if "FreshTyre" in out.columns:
        out["TyreStatus"] = out["FreshTyre"].apply(classify_fresh_tyre)
    else:
        # Fallback: tyre life 1 is usually a fresh-set first timed lap; higher values mean used/aged.
        out["TyreStatus"] = np.where(pd.to_numeric(out.get("TyreLife", pd.Series(index=out.index)), errors="coerce") <= 1, "Likely fresh", "Used/aged")
    if "TyreLife" in out.columns:
        tl = pd.to_numeric(out["TyreLife"], errors="coerce")
        out["TyreAgeBand"] = pd.cut(tl, bins=[-np.inf, 2, 6, 12, np.inf], labels=["New 0-2", "Low 3-6", "Medium 7-12", "High 13+"])
    return out


def classify_run_type(lap_count: int, median_lap: float, best_lap: float, session_best: float, compound: str) -> str:
    # Heuristic only: public FastF1 does not expose fuel load or run plan.
    if lap_count >= 5:
        return "Long run / race-pace candidate"
    if lap_count <= 3 and np.isfinite(best_lap) and np.isfinite(session_best) and best_lap <= session_best + 1.8:
        return "Quali/low-fuel candidate"
    if lap_count <= 4:
        return "Short run"
    return "Mixed run"


def build_stint_statistics(laps: pd.DataFrame) -> pd.DataFrame:
    if laps.empty or "Stint" not in laps.columns:
        return pd.DataFrame()
    work = add_tyre_columns(laps.copy())
    work = work[work["LapTime"].notna()].copy()
    if work.empty:
        return pd.DataFrame()
    work["LapTimeSeconds"] = work["LapTime"].dt.total_seconds()
    # Remove obvious in/out laps from pace statistics where columns are available.
    clean = work.copy()
    if "PitInTime" in clean.columns:
        clean = clean[clean["PitInTime"].isna()]
    if "PitOutTime" in clean.columns:
        clean = clean[clean["PitOutTime"].isna()]
    if "IsAccurate" in clean.columns:
        clean = clean[clean["IsAccurate"].fillna(True).astype(bool)]
    session_best = float(clean["LapTimeSeconds"].min()) if not clean.empty else np.nan
    group_cols = ["Driver", "Stint"]
    rows = []
    for (drv, stint), g_all in work.groupby(group_cols):
        g_clean = clean[(clean["Driver"] == drv) & (clean["Stint"] == stint)]
        g_stats = g_clean if not g_clean.empty else g_all
        compound = str(g_all["Compound"].dropna().iloc[0]) if "Compound" in g_all.columns and not g_all["Compound"].dropna().empty else "Unknown"
        tyre_status = str(g_all["TyreStatus"].dropna().iloc[0]) if "TyreStatus" in g_all.columns and not g_all["TyreStatus"].dropna().empty else "Unknown"
        tyre_life_start = pd.to_numeric(g_all.get("TyreLife", pd.Series(dtype=float)), errors="coerce").min()
        tyre_life_end = pd.to_numeric(g_all.get("TyreLife", pd.Series(dtype=float)), errors="coerce").max()
        lap_count = int(g_stats["LapTimeSeconds"].notna().sum())
        best = float(g_stats["LapTimeSeconds"].min()) if lap_count else np.nan
        median = float(g_stats["LapTimeSeconds"].median()) if lap_count else np.nan
        mean = float(g_stats["LapTimeSeconds"].mean()) if lap_count else np.nan
        std = float(g_stats["LapTimeSeconds"].std()) if lap_count > 1 else 0.0
        rows.append({
            "Driver": drv,
            "Stint": int(stint) if pd.notna(stint) else stint,
            "RunType": classify_run_type(lap_count, median, best, session_best, compound),
            "Compound": compound,
            "TyreStatus": tyre_status,
            "TyreLifeStart": tyre_life_start,
            "TyreLifeEnd": tyre_life_end,
            "TimedLapsUsed": lap_count,
            "BestLap_s": best,
            "MedianLap_s": median,
            "MeanLap_s": mean,
            "StdDev_s": std,
            "LapRange": f"{int(g_all['LapNumber'].min())}-{int(g_all['LapNumber'].max())}" if "LapNumber" in g_all.columns else "",
        })
    return pd.DataFrame(rows).sort_values(["RunType", "Driver", "Stint"])


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
    """Return the team name for a 3-letter driver abbreviation.

    FastF1 versions differ: session.get_driver() is not consistently keyed by
    abbreviation, so session.results is the most reliable source after load().
    """
    try:
        results = getattr(session, "results", None)
        if results is not None and not results.empty:
            for key in ["Abbreviation", "BroadcastName", "DriverNumber"]:
                if key in results.columns:
                    row = results[results[key].astype(str).str.upper() == str(drv).upper()]
                    if not row.empty:
                        for team_col in ["TeamName", "Team", "ConstructorName"]:
                            if team_col in row.columns and pd.notna(row.iloc[0].get(team_col)):
                                team = str(row.iloc[0].get(team_col)).strip()
                                if team and team.lower() != "nan":
                                    return team
    except Exception:
        pass
    try:
        info = session.get_driver(drv)
        for team_col in ["TeamName", "Team", "ConstructorName"]:
            value = info.get(team_col) if hasattr(info, "get") else None
            if value is not None and pd.notna(value):
                return str(value)
    except Exception:
        pass
    return "Unknown"


def get_driver_last_name(session, drv: str) -> str:
    try:
        results = getattr(session, "results", None)
        if results is not None and not results.empty and "Abbreviation" in results.columns:
            row = results[results["Abbreviation"].astype(str).str.upper() == str(drv).upper()]
            if not row.empty:
                for col in ["LastName", "LastName", "FullName"]:
                    if col in row.columns and pd.notna(row.iloc[0].get(col)):
                        val = str(row.iloc[0].get(col)).strip()
                        if val:
                            return val.split()[-1]
    except Exception:
        pass
    return drv


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
    fig.update_layout(height=460, margin=dict(l=5, r=5, t=35, b=5), coloraxis_colorbar_title=color)
    return fig


def plot_dominance_map(ref_pos: pd.DataFrame, cmp_tel: pd.DataFrame, cmp_driver: str, ref_driver: str, styles: Optional[Dict[str, Dict[str, str]]] = None) -> Optional[go.Figure]:
    """Two-colour track dominance: each point is coloured by which driver has higher speed there."""
    required_ref = {"X", "Y", "Distance", "Speed"}
    if ref_pos.empty or cmp_tel.empty or not required_ref.issubset(ref_pos.columns) or "Speed" not in cmp_tel.columns:
        return None
    cmp_clean = clean_for_interp(cmp_tel, ["Speed"])
    ref_clean = ref_pos.dropna(subset=["Distance", "Speed", "X", "Y"]).sort_values("Distance").drop_duplicates("Distance")
    if cmp_clean.empty or ref_clean.empty:
        return None
    max_dist = min(ref_clean["Distance"].max(), cmp_clean["Distance"].max())
    ref_clean = ref_clean[ref_clean["Distance"] <= max_dist].copy()
    if ref_clean.empty:
        return None
    cmp_speed = np.interp(ref_clean["Distance"], cmp_clean["Distance"], cmp_clean["Speed"])
    ref_clean["ReferenceSpeed_kph"] = ref_clean["Speed"]
    ref_clean["CompareSpeed_kph"] = cmp_speed
    ref_clean["SpeedDelta_kph"] = ref_clean["CompareSpeed_kph"] - ref_clean["ReferenceSpeed_kph"]
    ref_clean["FasterDriver"] = np.where(ref_clean["SpeedDelta_kph"] > 0, cmp_driver, ref_driver)
    color_map = {ref_driver: "#00D1FF", cmp_driver: "#FF4B4B"}
    if styles:
        color_map = {ref_driver: styles.get(ref_driver, {}).get("color", color_map[ref_driver]), cmp_driver: styles.get(cmp_driver, {}).get("color", color_map[cmp_driver])}
    fig = px.scatter(
        ref_clean,
        x="X",
        y="Y",
        color="FasterDriver",
        color_discrete_map=color_map,
        hover_data={
            "Distance": ":.1f",
            "ReferenceSpeed_kph": ":.1f",
            "CompareSpeed_kph": ":.1f",
            "SpeedDelta_kph": ":+.1f",
            "X": False,
            "Y": False,
        },
        title=f"Speed dominance: faster car at each track point",
    )
    fig.update_traces(marker=dict(size=4.5))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, visible=False)
    fig.update_xaxes(visible=False)
    fig.update_layout(
        height=460,
        margin=dict(l=5, r=5, t=35, b=5),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig




def export_csv(lap_tels: Dict[str, pd.DataFrame], labels: Dict[str, str], deltas: List[pd.DataFrame], corner_table: pd.DataFrame, exit_table: pd.DataFrame, stint_table: Optional[pd.DataFrame] = None) -> bytes:
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
    if stint_table is not None and not stint_table.empty:
        sections.append("# Tyre and stint statistics\n" + stint_table.to_csv(index=False))
    return ("\n".join(sections)).encode("utf-8")


# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.markdown("""
<div class="f1-hero">
  <div class="f1-brand"><span class="f1-logo">F1</span><span>Telemetry Viewer</span></div>
  <div class="f1-subtitle">FastF1 engineering dashboard: multi-driver telemetry, reference deltas, corner exits, track dominance, tyres, stints and exports.</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="f1-card"><div class="f1-card-title">Session selection</div>', unsafe_allow_html=True)
current_year = pd.Timestamp.today().year
c1, c2, c3 = st.columns([0.85, 1.6, 1.1])
with c1:
    year = st.number_input("Year", min_value=2018, max_value=current_year, value=min(current_year, 2025), step=1)

try:
    schedule = get_schedule(int(year))
except Exception as e:
    st.error(f"Could not load schedule: {e}")
    st.stop()

events = available_events(schedule)
if not events:
    st.warning("No completed sessions with public FastF1 data are available for this year yet.")
    st.stop()

with c2:
    event_name = st.selectbox("Grand Prix", events, index=max(0, len(events) - 1))
available_session_labels = available_sessions_for_event(schedule, event_name)
if not available_session_labels:
    st.warning("No available sessions found for this Grand Prix yet.")
    st.stop()

default_session = "Race" if "Race" in available_session_labels else available_session_labels[-1]
with c3:
    session_label = st.selectbox("Session", available_session_labels, index=available_session_labels.index(default_session))
session_code = session_code_from_label(session_label)
info_col, btn_col = st.columns([2.6, .9])
with info_col:
    st.caption(f"Data: FastF1. Available sessions for this GP: {', '.join(available_session_labels)}")
with btn_col:
    load_btn = st.button("Load / refresh", type="primary", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

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

st.markdown('<div class="f1-card"><div class="f1-card-title">Drivers and lap selection</div>', unsafe_allow_html=True)
default_drivers = drivers[: min(5, len(drivers))]
selected_drivers = st.multiselect("Compare up to 5 drivers", drivers, default=default_drivers, max_selections=5)
if not selected_drivers:
    st.warning("Select at least one driver.")
    st.stop()
d1, d2 = st.columns([1, 1])
with d1:
    reference_driver = st.selectbox("Reference driver for deltas", selected_drivers, index=0)
with d2:
    selection_mode = st.radio("Lap selection", ["Fastest valid lap", "Choose lap per driver"], index=0, horizontal=True)

selected_laps = {}
labels = {}
if selection_mode == "Choose lap per driver":
    lap_cols = st.columns(min(len(selected_drivers), 5))
else:
    lap_cols = []
for i, drv in enumerate(selected_drivers):
    laps = get_driver_laps(session, drv)
    lap_number = None
    if selection_mode == "Choose lap per driver":
        nums = laps["LapNumber"].astype(int).tolist()
        if nums:
            with lap_cols[i % len(lap_cols)]:
                lap_number = st.selectbox(f"{drv} lap", nums, index=0, key=f"lap_{drv}")
    lap = select_lap(laps, selection_mode, lap_number)
    if lap is not None:
        selected_laps[drv] = lap
        labels[drv] = f"{drv} L{int(lap['LapNumber'])} ({fmt_laptime(lap['LapTime'])})"
st.markdown('</div>', unsafe_allow_html=True)

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
    stint_export_laps = session.laps.copy()
    stint_export_laps = stint_export_laps[stint_export_laps["LapTime"].notna() & stint_export_laps["Driver"].isin(selected_laps.keys())].copy()
    stint_export = build_stint_statistics(stint_export_laps)

# Summary cards
st.subheader("Selected laps")
summary_cols = ["Driver", "Team", "Lap", "Lap time", "S1", "S2", "S3", "Compound", "TyreLife", "TyreStatus", "FreshTyre", "Stint", "Colour role"]
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
        "TyreStatus": classify_fresh_tyre(lap.get("FreshTyre")) if "FreshTyre" in lap.index else ("Likely fresh" if pd.to_numeric(pd.Series([lap.get("TyreLife")]), errors="coerce").iloc[0] <= 1 else "Used/aged"),
        "FreshTyre": lap.get("FreshTyre") if "FreshTyre" in lap.index else None,
        "Stint": lap.get("Stint"),
        "Colour role": styles[drv]["role"],
    })
summary_df = pd.DataFrame(summary_rows, columns=summary_cols)
# A compact HTML summary is much more usable than a dataframe on iPhone.
ref_time = seconds(selected_laps[reference_driver]["LapTime"])
rows_html = []
for rank, (drv, lap) in enumerate(selected_laps.items(), start=1):
    colour = styles[drv]["color"]
    team = styles[drv]["team"]
    team_safe = html.escape(str(team))
    name_safe = html.escape(str(get_driver_last_name(session, drv)))
    lt = seconds(lap["LapTime"])
    delta = "REF" if drv == reference_driver or ref_time is None or lt is None else f"{lt - ref_time:+.3f}"
    delta_class = "" if delta == "REF" else ("f1-delta-neg" if str(delta).startswith("-") else "f1-delta-pos")
    comp = str(lap.get("Compound") or "").upper()
    chip_class = f"f1-chip-{comp.lower()}" if comp else ""
    tyre_life = lap.get("TyreLife")
    tyre_txt = "" if pd.isna(tyre_life) else f"<span class='f1-small'> {int(tyre_life)} laps</span>"
    rows_html.append(f"""
    <tr>
      <td><div class='f1-drivercell'><span class='f1-rank' style='background:{colour}'></span><div><b>{html.escape(str(drv))}</b><div class='f1-small'>{name_safe}</div></div></div></td>
      <td><span class='f1-team' style='color:{colour}'>{team_safe}</span></td>
      <td>{int(lap['LapNumber'])}</td>
      <td><b>{fmt_laptime(lap['LapTime'])}</b><br><span class='{delta_class}'>{delta}</span></td>
      <td>{fmt_laptime(lap.get('Sector1Time'))}</td>
      <td>{fmt_laptime(lap.get('Sector2Time'))}</td>
      <td>{fmt_laptime(lap.get('Sector3Time'))}</td>
      <td><span class='f1-chip {chip_class}'>{html.escape(comp[:1] or '—')}</span>{tyre_txt}</td>
    </tr>
    """)
summary_html = """
<div class='f1-card'>
  <div class='f1-card-title'>Selected laps <span class='f1-small'>(reference: {ref})</span></div>
  <div style='overflow-x:auto'>
  <table class='f1-table'>
    <thead><tr><th>Driver</th><th>Team</th><th>Lap</th><th>Lap time</th><th>S1</th><th>S2</th><th>S3</th><th>Tyre</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
</div>
""".format(ref=html.escape(reference_driver), rows="".join(rows_html))
st.markdown(summary_html, unsafe_allow_html=True)

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
    all_laps = add_tyre_columns(add_sector_seconds(all_laps))
    all_laps["LapTimeSeconds"] = all_laps["LapTime"].dt.total_seconds().round(3)
    fig = go.Figure()
    for drv in selected_laps.keys():
        d = all_laps[all_laps["Driver"] == drv]
        fig.add_trace(go.Scatter(x=d["LapNumber"], y=d["LapTimeSeconds"], mode="lines+markers", name=drv, line=dict(color=styles[drv]["color"])))
    fig.update_layout(height=420, margin=dict(l=20, r=20, t=35, b=25), xaxis_title="Lap", yaxis_title="Lap time [s]", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Full lap table")
    table_cols = [
        "Driver", "LapNumber", "LapTime", "LapTimeSeconds",
        "Sector1Time", "Sector1Seconds", "Sector2Time", "Sector2Seconds", "Sector3Time", "Sector3Seconds",
        "Compound", "TyreLife", "TyreStatus", "FreshTyre", "Stint", "PitInTime", "PitOutTime", "IsAccurate"
    ]
    show_cols = [c for c in table_cols if c in all_laps.columns]
    full_table = format_lap_table(all_laps[show_cols]).sort_values(["LapTimeSeconds", "Driver"])
    st.dataframe(full_table, use_container_width=True, hide_index=True)

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
        fig = plot_dominance_map(lap_pos[reference_driver], lap_tels[cmp_driver], cmp_driver, reference_driver, styles)
        if fig is None:
            st.warning("Could not create dominance map for this comparison.")
        else:
            st.plotly_chart(fig, use_container_width=True)

with tabs[5]:
    st.markdown("### Tyres and stint analysis")
    all_laps = session.laps.copy()
    all_laps = all_laps[all_laps["LapTime"].notna() & all_laps["Driver"].isin(selected_laps.keys())].copy()
    all_laps = add_tyre_columns(all_laps)
    all_laps["LapTimeSeconds"] = all_laps["LapTime"].dt.total_seconds()
    if all_laps.empty:
        st.info("No lap data available.")
    else:
        tyre_cols = [c for c in ["Driver", "LapNumber", "Stint", "Compound", "TyreLife", "TyreAgeBand", "TyreStatus", "FreshTyre", "LapTime", "LapTimeSeconds", "IsAccurate"] if c in all_laps.columns]
        st.markdown("#### Tyre information by lap")
        tyre_table = format_lap_table(all_laps[tyre_cols]).sort_values(["Driver", "LapNumber"])
        st.dataframe(tyre_table, use_container_width=True, hide_index=True)

        st.markdown("#### Stint statistics")
        stint_stats = build_stint_statistics(all_laps)
        if stint_stats.empty:
            st.info("Stint statistics are not available for this session.")
        else:
            st.dataframe(stint_stats.round(3), use_container_width=True, hide_index=True)
            st.caption("Run type is a heuristic from stint length and lap time relative to the session best. Public data does not include fuel load or actual run plan.")

        st.markdown("#### Pace spread")
        fig = px.box(
            all_laps,
            x="Driver",
            y="LapTimeSeconds",
            color="Compound" if "Compound" in all_laps.columns else "Driver",
            points="all",
            hover_data=[c for c in ["LapNumber", "Stint", "TyreLife", "TyreStatus"] if c in all_laps.columns],
        )
        fig.update_layout(height=390, margin=dict(l=10, r=10, t=30, b=20), yaxis_title="Lap time [s]")
        st.plotly_chart(fig, use_container_width=True)

        if "TyreLife" in all_laps.columns:
            st.markdown("#### Tyre age vs lap time")
            fig = px.scatter(
                all_laps,
                x="TyreLife",
                y="LapTimeSeconds",
                color="Driver",
                symbol="Compound" if "Compound" in all_laps.columns else None,
                hover_data=[c for c in ["LapNumber", "Stint", "TyreStatus", "TyreAgeBand"] if c in all_laps.columns],
                color_discrete_map={d: styles[d]["color"] for d in styles},
            )
            fig.update_layout(height=390, margin=dict(l=10, r=10, t=30, b=20), xaxis_title="Tyre life [laps]", yaxis_title="Lap time [s]")
            st.plotly_chart(fig, use_container_width=True)

        if session_code in {"FP1", "FP2", "FP3"} and not build_stint_statistics(all_laps).empty:
            st.markdown("#### Practice run-type summary")
            stats = build_stint_statistics(all_laps)
            fig = px.scatter(
                stats,
                x="TimedLapsUsed",
                y="MedianLap_s",
                color="RunType",
                symbol="Compound",
                hover_data=["Driver", "Stint", "TyreStatus", "TyreLifeStart", "TyreLifeEnd", "BestLap_s"],
                size="TimedLapsUsed",
            )
            fig.update_layout(height=390, margin=dict(l=10, r=10, t=30, b=20), xaxis_title="Timed laps in stint", yaxis_title="Median lap [s]")
            st.plotly_chart(fig, use_container_width=True)

with tabs[6]:
    st.markdown("### Export")
    file_base = f"telemetry_{year}_{event_name}_{session_code}_{'_'.join(selected_laps.keys())}".replace(" ", "_").replace("/", "-")
    st.download_button(
        "Download telemetry, deltas and analysis CSV",
        data=export_csv(lap_tels, labels, deltas, corner_table, exit_table, stint_export),
        file_name=f"{file_base}.csv",
        mime="text/csv",
    )

    st.markdown("### Notes")
    st.write(
        "FastF1 public telemetry is excellent for comparative analysis, but it is still reconstructed/public timing feed data. "
        "Acceleration is calculated from speed/time, and some position/telemetry channels may be interpolated depending on the FastF1 method used."
    )
