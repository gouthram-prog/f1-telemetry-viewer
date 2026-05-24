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
import plotly.io as pio
import streamlit as st
from streamlit.components.v1 import html as components_html

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
pio.templates.default = "plotly_dark"

st.markdown(
    """
    <style>
    :root {
        --f1-bg:#070b12;
        --f1-panel:#0c1420;
        --f1-panel2:#111b29;
        --f1-line:rgba(255,255,255,.105);
        --f1-text:#f5f7fb;
        --f1-muted:rgba(245,247,251,.62);
        --f1-red:#ff383f;
        --f1-green:#27e782;
        --f1-yellow:#ffd21f;
    }
    html, body, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 20% 0%, rgba(0, 144, 255, .12), transparent 35%), linear-gradient(180deg, #05080d 0%, #080d15 100%) !important;
        color: var(--f1-text);
    }
    .block-container {
        padding-top: 0.55rem;
        padding-left: 0.55rem;
        padding-right: 0.55rem;
        padding-bottom: 1.2rem;
        max-width: 1120px;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #070b12; }
    h1,h2,h3 { letter-spacing: .2px; }
    h1 { font-size: clamp(1.22rem, 5vw, 1.95rem) !important; line-height:1.1; }
    h2 { font-size: clamp(1.05rem, 4vw, 1.45rem) !important; }
    h3 { font-size: clamp(.95rem, 3.6vw, 1.2rem) !important; }
    .stTabs [data-baseweb="tab-list"] { gap: .15rem; overflow-x: auto; flex-wrap: nowrap; border-bottom:1px solid rgba(255,255,255,.08); }
    .stTabs [data-baseweb="tab"] { min-width: max-content; padding: .55rem .65rem; border-radius:10px 10px 0 0; font-size:.88rem; }
    .stTabs [aria-selected="true"] { color:#ff4048 !important; border-bottom:2px solid #ff4048; }
    div[data-testid="stSelectbox"] > div, div[data-testid="stMultiSelect"] > div, div[data-testid="stNumberInput"] > div, div[data-testid="stRadio"] {
        border-radius: 14px;
    }
    .stButton > button, .stDownloadButton > button {
        border-radius: 12px !important;
        background: linear-gradient(180deg, rgba(255,255,255,.08), rgba(255,255,255,.03)) !important;
        border:1px solid rgba(255,255,255,.12) !important;
    }
    .f1-shell {
        border:1px solid var(--f1-line);
        border-radius:18px;
        background:linear-gradient(145deg, rgba(18,29,43,.94), rgba(5,10,17,.96));
        box-shadow:0 12px 34px rgba(0,0,0,.33), inset 0 0 0 1px rgba(255,255,255,.035);
        padding:12px;
        margin-bottom:12px;
    }
    .f1-header { display:flex; align-items:center; justify-content:space-between; gap:10px; }
    .f1-brand { display:flex; align-items:center; gap:12px; font-weight:900; letter-spacing:.5px; font-size:clamp(1.1rem, 4.6vw, 1.7rem); }
    .f1-logo-text { color:#ff1e1e; font-style:italic; font-weight:1000; font-size:1.4em; letter-spacing:-2px; text-shadow:0 0 18px rgba(255,30,30,.35); }
    .f1-menu { font-size:1.35rem; color:rgba(255,255,255,.78); }
    .f1-sub { color:var(--f1-muted); font-size:.82rem; margin-top:8px; }
    .f1-green { color:var(--f1-green); }
    .f1-red { color:var(--f1-red); }
    .f1-control-note { color:var(--f1-muted); font-size:.78rem; padding:.1rem .2rem; }
    .f1-section-title { font-weight:850; text-transform:uppercase; letter-spacing:.8px; font-size:.95rem; margin: 2px 0 8px 2px; }
    .f1-card { border:1px solid var(--f1-line); border-radius:16px; background:linear-gradient(180deg, rgba(19,29,42,.92), rgba(8,13,21,.96)); padding:12px; margin:10px 0; box-shadow:0 8px 24px rgba(0,0,0,.2); }
    div[data-testid="stDataFrame"] { border:1px solid rgba(255,255,255,.08); border-radius:14px; overflow:hidden; }

    /* polished dashboard table/cards */
    .f1-hero { border:1px solid var(--f1-line); border-radius:18px; padding:14px; margin-bottom:12px; background:linear-gradient(145deg, rgba(9,23,35,.96), rgba(6,10,16,.98)); box-shadow:0 10px 32px rgba(0,0,0,.35), inset 0 0 40px rgba(0,184,255,.045); }
    .f1-logo { color:#ff1e1e; font-style:italic; font-weight:1000; font-size:1.35em; letter-spacing:-2px; margin-right:.25rem; text-shadow:0 0 18px rgba(255,30,30,.35); }
    .f1-subtitle { color:var(--f1-muted); font-size:.84rem; margin-top:.35rem; line-height:1.35; }
    .f1-card-title { font-weight:900; text-transform:uppercase; letter-spacing:.7px; font-size:1.02rem; margin-bottom:.65rem; display:flex; align-items:center; gap:.5rem; }
    .f1-pill { display:inline-flex; align-items:center; justify-content:center; border-radius:999px; padding:.18rem .52rem; font-size:.76rem; font-weight:850; background:#c8102e; color:#fff; line-height:1; }
    .f1-table { width:100%; border-collapse:collapse; font-size:.88rem; overflow:hidden; border-radius:14px; }
    .f1-table th { text-transform:uppercase; font-size:.72rem; color:rgba(255,255,255,.78); background:linear-gradient(180deg, rgba(255,255,255,.10), rgba(255,255,255,.045)); border:1px solid rgba(255,255,255,.07); padding:.58rem .5rem; white-space:nowrap; text-align:left; }
    .f1-table td { border:1px solid rgba(255,255,255,.07); padding:.58rem .5rem; vertical-align:middle; white-space:nowrap; }
    .f1-table tr:nth-child(even) td { background:rgba(255,255,255,.018); }
    .f1-drivercell { display:flex; align-items:center; gap:.55rem; min-width:7.2rem; }
    .f1-rank { width:2.3rem; height:2.3rem; border-radius:7px; display:inline-flex; align-items:center; justify-content:center; font-weight:950; color:#fff; box-shadow: inset 0 -8px 20px rgba(0,0,0,.18), 0 4px 14px rgba(0,0,0,.22); }
    .f1-small { font-size:.74rem; color:rgba(255,255,255,.62); font-weight:500; }
    .f1-team { font-weight:850; display:inline-flex; align-items:center; gap:.35rem; }
    .f1-team-badge { display:inline-flex; align-items:center; justify-content:center; width:1.85rem; height:1.85rem; border-radius:.4rem; background:rgba(255,255,255,.075); border:1px solid rgba(255,255,255,.12); font-weight:900; }
    .f1-delta-pos { color:#ff4b4b; font-weight:800; }
    .f1-delta-neg { color:#28e48a; font-weight:800; }
    .f1-delta-ref { color:#d840ff; font-weight:900; }
    .f1-chip { display:inline-flex; align-items:center; justify-content:center; width:1.62rem; height:1.62rem; border-radius:999px; font-size:.76rem; font-weight:950; margin-right:.25rem; border:2px solid #c9ccd1; color:#fff; background:#111821; box-shadow:0 0 14px rgba(255,255,255,.06); }
    .f1-chip-soft { border-color:#ff3241; color:#ff3241; }
    .f1-chip-medium { border-color:#ffd21f; color:#ffd21f; }
    .f1-chip-hard { border-color:#d7d7d7; color:#d7d7d7; }
    .f1-chip-intermediate { border-color:#18d65b; color:#18d65b; }
    .f1-chip-wet { border-color:#38a6ff; color:#38a6ff; }
    .f1-status-fresh { color:#25e67e; background:rgba(37,230,126,.16); border-radius:999px; padding:.15rem .45rem; font-size:.72rem; font-weight:900; }
    .f1-status-used { color:#ffd21f; background:rgba(255,210,31,.13); border-radius:999px; padding:.15rem .45rem; font-size:.72rem; font-weight:900; }
    .f1-grid { display:grid; gap:.75rem; }
    .f1-grid-5 { grid-template-columns:repeat(5, minmax(0, 1fr)); }
    .f1-grid-3 { grid-template-columns:repeat(3, minmax(0, 1fr)); }
    .f1-stat { border:1px solid rgba(255,255,255,.09); border-radius:13px; background:linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02)); padding:.8rem; min-height:5.4rem; }
    .f1-stat-title { text-transform:uppercase; font-size:.73rem; letter-spacing:.5px; color:rgba(255,255,255,.68); font-weight:800; }
    .f1-stat-main { font-size:1.3rem; font-weight:950; margin-top:.35rem; }
    .f1-bar { height:.82rem; border-radius:999px; background:rgba(255,255,255,.08); overflow:hidden; min-width:7rem; display:flex; }
    .f1-bar-fill { height:100%; border-radius:999px; }
    @media (max-width:760px) {
      .f1-card { padding:.75rem; border-radius:16px; }
      .f1-card-title { font-size:.95rem; }
      .f1-table { font-size:.82rem; }
      .f1-table th { font-size:.66rem; padding:.48rem .42rem; }
      .f1-table td { padding:.50rem .42rem; }
      .f1-drivercell { min-width:6.6rem; gap:.45rem; }
      .f1-rank { width:2.1rem; height:2.1rem; }
      .f1-grid-5, .f1-grid-3 { grid-template-columns:repeat(2, minmax(0, 1fr)); }
    }

    @media (max-width: 760px) {
        .block-container { padding-left:.42rem; padding-right:.42rem; }
        .stTabs [data-baseweb="tab"] { font-size:.76rem; padding:.47rem .5rem; }
        div[data-testid="column"] { width:100% !important; flex:1 1 100% !important; }
        div[data-testid="stHorizontalBlock"] { gap:.35rem; }
        div[data-testid="stPlotlyChart"] { margin-bottom:.25rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_html(markup: str):
    """Render trusted app-generated HTML without exposing it as code."""
    try:
        st.html(markup)
    except Exception:
        st.markdown(markup, unsafe_allow_html=True)


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


DRIVER_TEAM_FALLBACK = {
    "VER":"Red Bull Racing", "TSU":"Red Bull Racing", "PER":"Red Bull Racing",
    "RUS":"Mercedes", "ANT":"Mercedes", "HAM":"Ferrari", "LEC":"Ferrari",
    "NOR":"McLaren", "PIA":"McLaren",
    "ALO":"Aston Martin", "STR":"Aston Martin",
    "GAS":"Alpine", "COL":"Alpine", "OCO":"Haas F1 Team", "BEA":"Haas F1 Team",
    "ALB":"Williams", "SAI":"Williams", "SAR":"Williams",
    "HAD":"RB", "LAW":"RB", "RIC":"RB",
    "HUL":"Kick Sauber", "BOR":"Kick Sauber", "BOT":"Kick Sauber", "ZHO":"Kick Sauber",
}

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


def _driver_info_row(session, drv: str) -> dict:
    """Find FastF1 driver metadata robustly across FastF1 versions."""
    d = str(drv).upper()
    try:
        results = getattr(session, "results", None)
        if results is not None and not results.empty:
            # Try direct columns first.
            for key in ["Abbreviation", "BroadcastName", "Tla", "DriverId", "FullName"]:
                if key in results.columns:
                    mask = results[key].astype(str).str.upper().str.contains(d, regex=False)
                    row = results[mask]
                    if not row.empty:
                        return row.iloc[0].to_dict()
            # Try index, sometimes results are indexed by driver number or abbreviation.
            try:
                idx = results.index.astype(str).str.upper()
                row = results[idx == d]
                if not row.empty:
                    return row.iloc[0].to_dict()
            except Exception:
                pass
    except Exception:
        pass

    try:
        for ident in getattr(session, "drivers", []):
            info = session.get_driver(ident)
            if hasattr(info, "to_dict"):
                info = info.to_dict()
            if not isinstance(info, dict):
                continue
            vals = [str(info.get(k, "")).upper() for k in ["Abbreviation", "BroadcastName", "Tla", "FullName", "LastName"]]
            if d in vals or any(v.endswith(d) for v in vals):
                return info
    except Exception:
        pass
    return {}


def get_driver_team(session, drv: str) -> str:
    info = _driver_info_row(session, drv)
    for team_col in ["TeamName", "Team", "ConstructorName", "TeamId"]:
        value = info.get(team_col)
        if value is not None and pd.notna(value):
            team = str(value).strip()
            if team and team.lower() != "nan":
                # Normalise a few public-data variations for FastF1 colours.
                aliases = {
                    "Red Bull": "Red Bull Racing",
                    "Racing Bulls": "RB",
                    "Visa Cash App RB": "RB",
                    "Kick Sauber": "Kick Sauber",
                }
                return aliases.get(team, team)
    fallback = DRIVER_TEAM_FALLBACK.get(str(drv).upper())
    if fallback:
        return fallback
    return "Unknown"


def get_driver_last_name(session, drv: str) -> str:
    info = _driver_info_row(session, drv)
    for col in ["LastName", "BroadcastName", "FullName", "DriverId"]:
        val = info.get(col)
        if val is not None and pd.notna(val):
            text = str(val).strip()
            if text:
                return text.split()[-1].title()
    return str(drv)


def get_driver_full_name(session, drv: str) -> str:
    info = _driver_info_row(session, drv)
    for col in ["FullName", "BroadcastName", "DriverId"]:
        val = info.get(col)
        if val is not None and pd.notna(val):
            text = str(val).strip()
            if text:
                return text.title()
    return str(drv)


TEAM_BADGES = {
    "Red Bull Racing": "RB",
    "Mercedes": "★",
    "Ferrari": "SF",
    "McLaren": "▸",
    "Aston Martin": "AM",
    "Alpine": "A",
    "Williams": "W",
    "RB": "VC",
    "Kick Sauber": "KS",
    "Sauber": "KS",
    "Haas F1 Team": "H",
    "Haas": "H",
    "Unknown": "?",
}


def team_badge(team: str) -> str:
    return TEAM_BADGES.get(team, team[:2].upper() if team else "?")


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




def find_energy_channels(lap_tels: Dict[str, pd.DataFrame]) -> List[str]:
    """Return any telemetry columns that look like ERS/energy channels.

    Public FastF1 car telemetry normally does not include true MGU-K deployment,
    harvesting or SOC channels. This hook keeps the tab future-proof if a loaded
    dataset ever exposes such columns.
    """
    keys = ["ers", "energy", "soc", "deploy", "harvest", "mguk", "mguh", "battery", "charge"]
    found = []
    for tel in lap_tels.values():
        for col in tel.columns:
            c = str(col).lower()
            if any(k in c for k in keys) and col not in found:
                found.append(col)
    return found


def gear_ratio_proxy_table(lap_tels: Dict[str, pd.DataFrame], labels: Dict[str, str]) -> pd.DataFrame:
    """Estimate relative gear ratios from RPM and speed.

    Absolute gearbox ratios require tyre radius and final-drive details, which are
    not present in public FastF1 data. RPM / vehicle speed is still useful to
    compare gear spacing and identify shifts.
    """
    rows = []
    for drv, tel in lap_tels.items():
        if not {"RPM", "Speed_ms", "nGear"}.issubset(tel.columns):
            continue
        df = tel[["RPM", "Speed_ms", "nGear"]].dropna().copy()
        df = df[(df["Speed_ms"] > 12.0) & (df["RPM"] > 1000) & (df["nGear"] >= 1)]
        if df.empty:
            continue
        df["Gear"] = df["nGear"].round().astype(int)
        df["RatioProxy_rpm_per_ms"] = df["RPM"] / df["Speed_ms"]
        for gear, g in df.groupby("Gear"):
            if len(g) < 8:
                continue
            rows.append({
                "Driver": drv,
                "Label": labels.get(drv, drv),
                "Gear": int(gear),
                "MedianRatioProxy_rpm_per_ms": float(g["RatioProxy_rpm_per_ms"].median()),
                "P10": float(g["RatioProxy_rpm_per_ms"].quantile(0.10)),
                "P90": float(g["RatioProxy_rpm_per_ms"].quantile(0.90)),
                "Samples": int(len(g)),
            })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    # Normalise within each driver to 8th gear, or highest available gear.
    norm_rows = []
    for drv, g in out.groupby("Driver"):
        highest = int(g["Gear"].max())
        base_gear = 8 if 8 in set(g["Gear"]) else highest
        base = float(g.loc[g["Gear"] == base_gear, "MedianRatioProxy_rpm_per_ms"].iloc[0])
        gg = g.copy()
        gg["RelativeToTopGear"] = gg["MedianRatioProxy_rpm_per_ms"] / base if base else np.nan
        norm_rows.append(gg)
    return pd.concat(norm_rows, ignore_index=True)


def tractive_force_dataframe(lap_tels: Dict[str, pd.DataFrame], labels: Dict[str, str], mass_kg: float, cda: float, crr: float, rho: float = 1.20) -> pd.DataFrame:
    """Create tractive-force estimates from speed and acceleration.

    This is a longitudinal estimate: F = m*a + aero_drag + rolling_resistance.
    It does not know fuel mass, wind, gradient, tyre radius, drivetrain losses,
    brake pressure or ERS torque split. Good for comparative traces, not absolute PU validation.
    """
    rows = []
    for drv, tel in lap_tels.items():
        required = {"Distance", "Speed", "Speed_ms", "Accel_ms2"}
        if not required.issubset(tel.columns):
            continue
        cols = ["Distance", "Speed", "Speed_ms", "Accel_ms2"]
        for optional in ["Throttle", "Brake", "nGear", "RPM", "DRS"]:
            if optional in tel.columns:
                cols.append(optional)
        df = tel[cols].dropna(subset=["Distance", "Speed_ms", "Accel_ms2"]).copy()
        if df.empty:
            continue
        df = df[(df["Speed_ms"] > 5.0) & (df["Accel_ms2"].abs() < 8.0)]
        if df.empty:
            continue
        drag = 0.5 * rho * cda * df["Speed_ms"] ** 2
        rolling = mass_kg * 9.80665 * crr
        df["InertialForce_N"] = mass_kg * df["Accel_ms2"]
        df["AeroDrag_N"] = drag
        df["RollingResistance_N"] = rolling
        df["TractiveForce_N"] = df["InertialForce_N"] + df["AeroDrag_N"] + df["RollingResistance_N"]
        df["Power_kW"] = df["TractiveForce_N"] * df["Speed_ms"] / 1000.0
        df["Driver"] = drv
        df["Label"] = labels.get(drv, drv)
        rows.append(df)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def acceleration_zone_summary(force_df: pd.DataFrame) -> pd.DataFrame:
    if force_df.empty:
        return pd.DataFrame()
    df = force_df.copy()
    if "Throttle" in df.columns:
        df = df[df["Throttle"].fillna(0) >= 80]
    if "Brake" in df.columns:
        try:
            df = df[~df["Brake"].astype(bool)]
        except Exception:
            pass
    df = df[(df["Accel_ms2"] > 0.15) & (df["Speed"] > 80)]
    if df.empty:
        return pd.DataFrame()
    rows = []
    for drv, g in df.groupby("Driver"):
        rows.append({
            "Driver": drv,
            "Samples": int(len(g)),
            "MeanAccel_ms2": float(g["Accel_ms2"].mean()),
            "PeakAccel_ms2": float(g["Accel_ms2"].max()),
            "MeanTractiveForce_N": float(g["TractiveForce_N"].mean()),
            "PeakTractiveForce_N": float(g["TractiveForce_N"].max()),
            "MeanPower_kW": float(g["Power_kW"].mean()),
            "PeakPower_kW": float(g["Power_kW"].max()),
        })
    return pd.DataFrame(rows)


def plot_tractive_force(force_df: pd.DataFrame, styles: Dict[str, Dict[str, str]]) -> go.Figure:
    fig = go.Figure()
    if force_df.empty:
        return update_fig_layout(fig, height=420, ytitle="Estimated tractive force [N]")
    for drv, g in force_df.groupby("Driver"):
        fig.add_trace(go.Scatter(
            x=g["Speed"], y=g["TractiveForce_N"], mode="markers", name=drv,
            marker=dict(size=5, opacity=0.62, color=styles.get(drv, {}).get("color", "#aaa")),
            customdata=np.stack([g["Distance"].to_numpy()], axis=-1),
            hovertemplate="%{fullData.name}<br>Speed=%{x:.1f} km/h<br>F=%{y:.0f} N<br>Distance=%{customdata[0]:.0f} m<extra></extra>",
        ))
    fig.update_layout(height=420, margin=dict(l=20, r=20, t=35, b=35), xaxis_title="Speed [km/h]", yaxis_title="Estimated tractive force [N]", legend=dict(orientation="h", y=1.05))
    return fig


def plot_power_speed(force_df: pd.DataFrame, styles: Dict[str, Dict[str, str]]) -> go.Figure:
    fig = go.Figure()
    if force_df.empty:
        return fig
    for drv, g in force_df.groupby("Driver"):
        g2 = g.copy()
        g2["SpeedBin"] = (g2["Speed"] / 5).round() * 5
        b = g2.groupby("SpeedBin", as_index=False)["Power_kW"].median()
        fig.add_trace(go.Scatter(x=b["SpeedBin"], y=b["Power_kW"], mode="lines+markers", name=drv, line=dict(color=styles.get(drv, {}).get("color", "#aaa"))))
    fig.update_layout(height=390, margin=dict(l=20, r=20, t=35, b=35), xaxis_title="Speed [km/h]", yaxis_title="Estimated power at wheels [kW]", hovermode="x unified", legend=dict(orientation="h", y=1.05))
    return fig


def plot_gear_ratio_bars(ratio_df: pd.DataFrame, styles: Dict[str, Dict[str, str]]) -> go.Figure:
    fig = go.Figure()
    if ratio_df.empty:
        return fig
    for drv, g in ratio_df.groupby("Driver"):
        fig.add_trace(go.Bar(x=g["Gear"], y=g["RelativeToTopGear"], name=drv, marker_color=styles.get(drv, {}).get("color", "#aaa")))
    fig.update_layout(height=390, margin=dict(l=20, r=20, t=35, b=35), xaxis_title="Gear", yaxis_title="Relative ratio proxy vs top gear", barmode="group", legend=dict(orientation="h", y=1.05))
    return fig


def plot_shift_map_compare(
    lap_tels: Dict[str, pd.DataFrame],
    driver_1: str,
    driver_2: Optional[str],
    labels: Dict[str, str],
) -> go.Figure:
    """Clean WOT-only RPM-vs-speed shift map with robust inferred gear lines.

    FastF1 public telemetry does not provide true gear ratios. This plot infers a
    ratio proxy from the near-linear relationship between RPM and speed inside
    each gear, using only full-throttle samples to avoid lift/coast/braking noise.

    Noise reduction used here:
      - throttle >= 99% only
      - brake == false where available
      - stable gear samples only, excluding immediate shift transitions
      - speed-binned median RPM before fitting
      - robust residual filter before the final linear trend
    """
    fig = go.Figure()
    gear_colors = {
        1: "#ff2d55",
        2: "#ff9500",
        3: "#ffd60a",
        4: "#32d74b",
        5: "#64d2ff",
        6: "#0a84ff",
        7: "#bf5af2",
        8: "#b8bcc2",
    }

    def _prep(driver: str) -> pd.DataFrame:
        tel = lap_tels.get(driver, pd.DataFrame())
        required = {"Speed", "RPM", "nGear", "Throttle"}
        if tel.empty or not required.issubset(tel.columns):
            return pd.DataFrame()

        cols = ["Speed", "RPM", "nGear", "Throttle"]
        if "Brake" in tel.columns:
            cols.append("Brake")
        if "Distance" in tel.columns:
            cols.append("Distance")
        df = tel[cols].dropna().copy()
        if df.empty:
            return df

        df["Gear"] = df["nGear"].round().astype(int)
        df = df[df["Gear"].between(1, 8)]
        df = df[(df["Speed"] > 35) & (df["RPM"] > 5500) & (df["Throttle"] >= 99)]

        if "Brake" in df.columns:
            # FastF1 Brake is usually boolean. This also handles 0/1 numeric.
            df = df[~df["Brake"].astype(bool)]

        # Remove points immediately around shifts. Gear must be stable for the
        # previous and next sample. This removes most clutch/shift transients.
        gear = df["Gear"]
        stable = gear.eq(gear.shift(1)) & gear.eq(gear.shift(-1))
        df = df[stable].copy()
        return df

    def _binned_clean(g: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[Tuple[float, float, np.ndarray, np.ndarray]]]:
        """Return filtered scatter samples and robust line coefficients."""
        if len(g) < 10:
            return pd.DataFrame(), None

        g = g.sort_values("Speed").copy()
        # Bin every 2 km/h and use medians to suppress wheel-slip/GPS/RPM noise.
        g["SpeedBin"] = (g["Speed"] / 2.0).round() * 2.0
        b = g.groupby("SpeedBin", as_index=False).agg(
            Speed=("Speed", "median"),
            RPM=("RPM", "median"),
            Count=("RPM", "size"),
        )
        b = b[b["Count"] >= 2]
        if len(b) < 4:
            # Low-sample gears such as G1 may have sparse bins. Fall back to raw.
            b = g[["Speed", "RPM"]].copy()
        if len(b) < 4 or b["Speed"].max() - b["Speed"].min() < 10:
            return pd.DataFrame(), None

        # First fit on binned medians.
        x0 = b["Speed"].to_numpy(dtype=float)
        y0 = b["RPM"].to_numpy(dtype=float)
        slope0, intercept0 = np.polyfit(x0, y0, 1)
        resid = y0 - (slope0 * x0 + intercept0)
        med = np.nanmedian(resid)
        mad = np.nanmedian(np.abs(resid - med))
        sigma = 1.4826 * mad if mad > 1e-6 else np.nanstd(resid)
        if not np.isfinite(sigma) or sigma < 80:
            sigma = 180.0
        keep_bins = np.abs(resid - med) <= max(2.5 * sigma, 250.0)
        b2 = b[keep_bins].copy()
        if len(b2) < 4:
            b2 = b.copy()

        x = b2["Speed"].to_numpy(dtype=float)
        y = b2["RPM"].to_numpy(dtype=float)
        slope, intercept = np.polyfit(x, y, 1)

        # Apply the same robust envelope to raw scatter points so the cloud is
        # readable but still reflects the measured samples.
        raw_resid = g["RPM"].to_numpy(dtype=float) - (slope * g["Speed"].to_numpy(dtype=float) + intercept)
        raw_med = np.nanmedian(raw_resid)
        raw_mad = np.nanmedian(np.abs(raw_resid - raw_med))
        raw_sigma = 1.4826 * raw_mad if raw_mad > 1e-6 else np.nanstd(raw_resid)
        if not np.isfinite(raw_sigma) or raw_sigma < 100:
            raw_sigma = 220.0
        g_clean = g[np.abs(raw_resid - raw_med) <= max(2.8 * raw_sigma, 350.0)].copy()

        # Cap point count per gear/driver for mobile readability.
        if len(g_clean) > 90:
            g_clean = g_clean.iloc[:: max(1, len(g_clean)//90)].copy()

        x_line = np.linspace(np.nanpercentile(x, 3), np.nanpercentile(x, 97), 32)
        y_line = slope * x_line + intercept
        return g_clean, (float(slope), float(intercept), x_line, y_line)

    driver_specs = [(driver_1, "circle", "solid", 0.74, "Driver 1")]
    if driver_2 and driver_2 != driver_1:
        driver_specs.append((driver_2, "diamond", "dash", 0.58, "Driver 2"))

    # Dummy legend entries make driver style obvious without repeating every gear.
    for idx, (driver, symbol, dash, opacity, driver_text) in enumerate(driver_specs):
        dlabel = labels.get(driver, driver)
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers+lines",
            name=f"{dlabel}: {'dots/solid' if idx == 0 else 'diamonds/dashed'}",
            marker=dict(symbol=symbol, size=8, color="rgba(245,247,251,0.85)"),
            line=dict(color="rgba(245,247,251,0.85)", width=1.3, dash=dash),
            showlegend=True,
        ))

    legend_seen = set()
    for driver, marker_symbol, dash_style, opacity, driver_text in driver_specs:
        df = _prep(driver)
        if df.empty:
            continue
        dlabel = labels.get(driver, driver)
        for gear in range(1, 9):
            g = df[df["Gear"] == gear].copy()
            g_clean, trend = _binned_clean(g)
            if g_clean.empty or trend is None:
                continue
            slope, intercept, x_line, y_line = trend
            show_gear_legend = gear not in legend_seen
            legend_seen.add(gear)
            hover_cols = ["Distance"] if "Distance" in g_clean.columns else []

            fig.add_trace(go.Scatter(
                x=g_clean["Speed"],
                y=g_clean["RPM"],
                mode="markers",
                name=f"G{gear}" if show_gear_legend else f"G{gear} {dlabel}",
                legendgroup=f"G{gear}",
                showlegend=show_gear_legend,
                marker=dict(
                    color=gear_colors[gear],
                    size=4.8 if marker_symbol == "circle" else 5.6,
                    symbol=marker_symbol,
                    opacity=opacity,
                    line=dict(width=0.25, color="rgba(255,255,255,0.28)"),
                ),
                customdata=g_clean[hover_cols] if hover_cols else None,
                hovertemplate=(
                    f"<b>{dlabel}</b><br>Gear {gear}<br>WOT filtered<br>Speed=%{{x:.1f}} km/h<br>RPM=%{{y:.0f}}"
                    + ("<br>Distance=%{customdata[0]:.0f} m" if hover_cols else "")
                    + "<extra></extra>"
                ),
            ))

            fig.add_trace(go.Scatter(
                x=x_line,
                y=y_line,
                mode="lines",
                name=f"{dlabel} G{gear} trend",
                legendgroup=f"trend-{driver}",
                showlegend=False,
                line=dict(color=gear_colors[gear], width=1.35, dash=dash_style),
                opacity=0.95 if dash_style == "solid" else 0.75,
                hovertemplate=f"<b>{dlabel}</b><br>Gear {gear} WOT trend<br>RPM = {slope:.1f} × Speed + {intercept:.0f}<extra></extra>",
            ))

    fig.update_layout(
        height=500,
        margin=dict(l=20, r=20, t=55, b=35),
        xaxis_title="Speed [km/h]",
        yaxis_title="RPM",
        legend=dict(orientation="h", y=1.16, x=0, font=dict(size=11), itemsizing="constant"),
        hovermode="closest",
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.12)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.12)")
    fig.add_annotation(
        xref="paper", yref="paper", x=0, y=1.05, showarrow=False, align="left",
        text="Filtered to throttle ≥99%, brake off, stable gear samples. Lines use speed-binned median RPM with outlier rejection.",
        font=dict(size=11, color="rgba(245,247,251,0.66)"),
    )
    return fig


def plot_energy_channels(lap_tels: Dict[str, pd.DataFrame], labels: Dict[str, str], styles: Dict[str, Dict[str, str]], channel: str) -> go.Figure:
    fig = go.Figure()
    for drv, tel in lap_tels.items():
        if channel in tel.columns and "Distance" in tel.columns:
            fig.add_trace(go.Scatter(x=tel["Distance"], y=tel[channel], mode="lines", name=labels.get(drv, drv), line=dict(color=styles.get(drv, {}).get("color", "#aaa"))))
    return update_fig_layout(fig, height=360, ytitle=channel)


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
render_html("""
<div class="f1-hero">
  <div class="f1-brand"><span class="f1-logo">F1</span><span>Telemetry Viewer</span></div>
  <div class="f1-subtitle">FastF1 engineering dashboard: multi-driver telemetry, reference deltas, corner exits, track dominance, tyres, stints and exports.</div>
</div>
""")

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
    badge = html.escape(team_badge(team))
    rows_html.append(
        f"<tr>"
        f"<td><div class='f1-drivercell'><span class='f1-rank' style='background:{colour}'>{rank}</span><div><b>{html.escape(str(drv))}</b><div class='f1-small'>{name_safe}</div></div></div></td>"
        f"<td><span class='f1-team' style='color:{colour}'><span class='f1-team-badge'>{badge}</span>{team_safe}</span></td>"
        f"<td>{int(lap['LapNumber'])}</td>"
        f"<td><b>{fmt_laptime(lap['LapTime'])}</b><br><span class='{delta_class}'>{delta}</span></td>"
        f"<td>{fmt_laptime(lap.get('Sector1Time')).replace('0:', '')}</td>"
        f"<td>{fmt_laptime(lap.get('Sector2Time')).replace('0:', '')}</td>"
        f"<td>{fmt_laptime(lap.get('Sector3Time')).replace('0:', '')}</td>"
        f"<td><span class='f1-chip {chip_class}'>{html.escape(comp[:1] or '—')}</span>{tyre_txt}</td>"
        f"</tr>"
    )
summary_html = """
<div class='f1-card'>
  <div class='f1-card-title'>Selected laps <span class='f1-small'>(reference: {ref})</span><span class='f1-pill'>{count}/5</span></div>
  <div style='overflow-x:auto'>
  <table class='f1-table'>
    <thead><tr><th>Pos</th><th>Team</th><th>Lap</th><th>Lap time</th><th>S1</th><th>S2</th><th>S3</th><th>Tyre</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
</div>
""".format(ref=html.escape(reference_driver), count=len(selected_laps), rows="".join(rows_html))
render_html(summary_html)

# Tabs
tabs = st.tabs([
    "Overview",
    "Telemetry",
    "Delta",
    "Corner exits",
    "Track maps",
    "Tyres & stints",
    "Power unit",
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
        # Visual tyre summary cards, closer to an F1 timing-screen style than a raw dataframe.
        compound_palette = {
            "SOFT": ("S", "#ff3241", "C3/C4/C5 Soft"),
            "MEDIUM": ("M", "#ffd21f", "C2/C3 Medium"),
            "HARD": ("H", "#d7d7d7", "C1/C2 Hard"),
            "INTERMEDIATE": ("I", "#18d65b", "Intermediate"),
            "WET": ("W", "#38a6ff", "Wet"),
        }
        total_laps_for_tyre = max(1, len(all_laps))
        compound_counts = all_laps.get("Compound", pd.Series(dtype=object)).fillna("UNKNOWN").astype(str).str.upper().value_counts()
        card_parts = []
        for compound in ["HARD", "MEDIUM", "SOFT", "INTERMEDIATE", "WET"]:
            count = int(compound_counts.get(compound, 0))
            pct = round(100 * count / total_laps_for_tyre)
            letter, color, label = compound_palette[compound]
            card_parts.append(
                f"<div class='f1-stat'>"
                f"<div class='f1-chip f1-chip-{compound.lower()}' style='border-color:{color}; color:{color};'>{letter}</div>"
                f"<div class='f1-stat-title' style='color:{color}'>{label}</div>"
                f"<div class='f1-stat-main'>{pct}%</div>"
                f"<div class='f1-small'>{count} timed laps</div>"
                f"</div>"
            )
        render_html("<div class='f1-card'><div class='f1-card-title'>Tyre information</div><div class='f1-grid f1-grid-5'>" + "".join(card_parts) + "</div></div>")

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
    st.markdown("### Power unit metrics")
    st.caption(
        "Public FastF1 data does not normally expose true PU internals such as MGU-K deployment, MGU-H harvest, battery SOC, fuel flow or torque. "
        "This tab uses speed, RPM and gear traces to derive comparative longitudinal metrics. Treat absolute force/power values as model estimates."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        mass_kg = st.number_input("Assumed car mass incl. driver/fuel [kg]", min_value=650.0, max_value=950.0, value=798.0, step=5.0)
    with c2:
        cda = st.number_input("CdA estimate [m²]", min_value=0.5, max_value=2.2, value=1.15, step=0.05)
    with c3:
        crr = st.number_input("Rolling resistance coefficient", min_value=0.005, max_value=0.030, value=0.013, step=0.001, format="%.3f")

    force_df = tractive_force_dataframe(lap_tels, labels, mass_kg=mass_kg, cda=cda, crr=crr)
    ratio_df = gear_ratio_proxy_table(lap_tels, labels)
    energy_channels = find_energy_channels(lap_tels)

    metric_cards = []
    summary = acceleration_zone_summary(force_df)
    if not summary.empty:
        best_acc = summary.sort_values("MeanAccel_ms2", ascending=False).iloc[0]
        best_power = summary.sort_values("PeakPower_kW", ascending=False).iloc[0]
        metric_cards.append(f"<div class='f1-stat'><div class='f1-stat-title'>Best accel driver</div><div class='f1-stat-main'>{html.escape(str(best_acc['Driver']))}</div><div class='f1-small'>{best_acc['MeanAccel_ms2']:.2f} m/s² avg WOT accel</div></div>")
        metric_cards.append(f"<div class='f1-stat'><div class='f1-stat-title'>Peak est. wheel power</div><div class='f1-stat-main'>{best_power['PeakPower_kW']:.0f} kW</div><div class='f1-small'>{html.escape(str(best_power['Driver']))}</div></div>")
    metric_cards.append(f"<div class='f1-stat'><div class='f1-stat-title'>ERS channels found</div><div class='f1-stat-main'>{len(energy_channels)}</div><div class='f1-small'>{'available' if energy_channels else 'not in public feed'}</div></div>")
    metric_cards.append(f"<div class='f1-stat'><div class='f1-stat-title'>Gear ratios</div><div class='f1-stat-main'>{'OK' if not ratio_df.empty else '—'}</div><div class='f1-small'>RPM / speed proxy</div></div>")
    render_html("<div class='f1-card'><div class='f1-card-title'>PU derived summary</div><div class='f1-grid f1-grid-4'>" + "".join(metric_cards) + "</div></div>")

    st.markdown("#### Tractive force diagram")
    if force_df.empty:
        st.info("Speed/acceleration telemetry is not available for the selected laps.")
    else:
        st.plotly_chart(plot_tractive_force(force_df, styles), use_container_width=True)
        st.plotly_chart(plot_power_speed(force_df, styles), use_container_width=True)
        st.markdown("#### Acceleration-zone summary")
        st.dataframe(summary.round(3), use_container_width=True, hide_index=True)

    st.markdown("#### Gear ratio plots")
    if ratio_df.empty:
        st.info("RPM, gear or speed data is not available for a gear-ratio proxy plot.")
    else:
        st.plotly_chart(plot_gear_ratio_bars(ratio_df, styles), use_container_width=True)
        st.dataframe(ratio_df.round(3), use_container_width=True, hide_index=True)

        shift_options = list(selected_laps.keys())
        c1, c2 = st.columns(2)
        with c1:
            shift_driver_1 = st.selectbox("Shift map driver 1", shift_options, index=0)
        with c2:
            default_second = 1 if len(shift_options) > 1 else 0
            shift_driver_2 = st.selectbox("Shift map driver 2", shift_options, index=default_second)
        st.plotly_chart(plot_shift_map_compare(lap_tels, shift_driver_1, shift_driver_2, labels), use_container_width=True)
        st.caption("Shift map uses discrete gear colours. Dots/solid trend lines are driver 1; diamonds/dashed trend lines are driver 2. Trend lines are inferred linear RPM-vs-speed fits per gear.")

    st.markdown("#### Energy deployment / harvest")
    if not energy_channels:
        st.info("No ERS deployment, harvest, SOC or battery-energy channels were found in the loaded FastF1 telemetry. Public F1 timing data normally does not expose these channels.")
    else:
        ch = st.selectbox("Energy channel", energy_channels)
        st.plotly_chart(plot_energy_channels(lap_tels, labels, styles, ch), use_container_width=True)


with tabs[7]:
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
