from __future__ import annotations
from pathlib import Path
import pandas as pd
import streamlit as st
import fastf1

CACHE_DIR = Path("./fastf1_cache")
CACHE_DIR.mkdir(exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

SESSION_NAMES = {"FP1":"Practice 1", "FP2":"Practice 2", "FP3":"Practice 3", "SQ":"Sprint Qualifying", "S":"Sprint", "Q":"Qualifying", "R":"Race"}
SESSION_ORDER = ["FP1","FP2","FP3","SQ","S","Q","R"]

@st.cache_data(ttl=3600, show_spinner=False)
def schedule(year:int) -> pd.DataFrame:
    return fastf1.get_event_schedule(year, include_testing=False)

@st.cache_data(ttl=3600, show_spinner=False)
def available_events(year:int) -> list[str]:
    sched = schedule(year)
    if sched.empty: return []
    now = pd.Timestamp.utcnow().tz_localize(None)
    names=[]
    for _, row in sched.iterrows():
        dates=[]
        for c in row.index:
            if str(c).startswith("Session") and str(c).endswith("Date") and pd.notna(row[c]):
                try: dates.append(pd.to_datetime(row[c]).tz_localize(None))
                except Exception: pass
        if dates and min(dates) <= now:
            names.append(str(row.get("EventName") or row.get("OfficialEventName") or row.get("Location")))
    return names

@st.cache_data(ttl=3600, show_spinner=False)
def available_sessions(year:int, event_name:str) -> list[str]:
    sched = schedule(year)
    row = sched[sched["EventName"].astype(str).eq(event_name)]
    if row.empty: return []
    row = row.iloc[0]
    now = pd.Timestamp.utcnow().tz_localize(None)
    out=[]
    for key in SESSION_ORDER:
        name_col=f"Session{SESSION_ORDER.index(key)+1}"
        date_col=f"Session{SESSION_ORDER.index(key)+1}Date"
        if name_col in row and date_col in row and pd.notna(row[date_col]):
            try:
                d=pd.to_datetime(row[date_col]).tz_localize(None)
                if d <= now: out.append(key)
            except Exception: pass
    return out or ["FP1","FP2","FP3","Q","R"]

@st.cache_resource(show_spinner=True)
def load_session(year:int, event_name:str, session_key:str):
    ses = fastf1.get_session(year, event_name, session_key)
    ses.load(telemetry=True, weather=True, laps=True, messages=False)
    return ses
