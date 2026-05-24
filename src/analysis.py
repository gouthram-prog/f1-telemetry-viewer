from __future__ import annotations
import numpy as np
import pandas as pd
from .utils import seconds


def lap_table(session, drivers):
    laps = session.laps.pick_drivers(drivers).copy()
    if laps.empty: return pd.DataFrame()
    for c in ["LapTime","Sector1Time","Sector2Time","Sector3Time"]:
        if c in laps.columns: laps[c+"Seconds"] = laps[c].apply(seconds)
    keep = ["Driver","Team","LapNumber","LapTimeSeconds","Sector1TimeSeconds","Sector2TimeSeconds","Sector3TimeSeconds","Compound","TyreLife","FreshTyre","Stint","IsAccurate"]
    keep = [c for c in keep if c in laps.columns]
    return laps[keep].sort_values(["Driver","LapNumber"])


def best_laps(session, drivers):
    rows=[]
    for d in drivers:
        dl = session.laps.pick_drivers([d]).pick_quicklaps()
        if dl.empty: dl = session.laps.pick_drivers([d])
        if dl.empty: continue
        lap = dl.pick_fastest()
        rows.append(lap)
    return rows


def telemetry_for_lap(lap):
    tel = lap.get_car_data().add_distance().copy()
    tel["LapTimeSeconds"] = tel["Time"].dt.total_seconds()
    tel["Accel"] = tel["Speed"].diff() / 3.6 / tel["LapTimeSeconds"].diff()
    tel["Accel"] = tel["Accel"].replace([np.inf,-np.inf], np.nan).rolling(5, min_periods=1).median()
    return tel


def align_delta(ref_tel, cmp_tel):
    max_d = min(ref_tel["Distance"].max(), cmp_tel["Distance"].max())
    grid = np.linspace(0, max_d, 1200)
    rt = np.interp(grid, ref_tel["Distance"], ref_tel["LapTimeSeconds"])
    ct = np.interp(grid, cmp_tel["Distance"], cmp_tel["LapTimeSeconds"])
    rs = np.interp(grid, ref_tel["Distance"], ref_tel["Speed"])
    cs = np.interp(grid, cmp_tel["Distance"], cmp_tel["Speed"])
    return pd.DataFrame({"Distance":grid,"Delta":ct-rt,"RefSpeed":rs,"CmpSpeed":cs,"SpeedDiff":cs-rs})


def stint_stats(session, drivers):
    laps = session.laps.pick_drivers(drivers).copy()
    if laps.empty: return pd.DataFrame()
    laps["LapSeconds"] = laps["LapTime"].apply(seconds)
    laps = laps[laps["LapSeconds"].notna()]
    if "Deleted" in laps.columns: laps = laps[~laps["Deleted"].fillna(False)]
    rows=[]
    for keys, grp in laps.groupby(["Driver","Stint","Compound"], dropna=False):
        drv, stint, comp = keys
        q = grp["LapSeconds"].quantile(.20)
        clean = grp[grp["LapSeconds"] <= grp["LapSeconds"].quantile(.85)]
        n=len(grp)
        typ = "Long run" if n>=6 else ("Quali sim" if n<=3 and q < laps["LapSeconds"].quantile(.35) else "Short/mixed")
        rows.append({"Driver":drv,"Stint":stint,"Compound":comp,"Laps":n,"Best":grp["LapSeconds"].min(),"Median":grp["LapSeconds"].median(),"Mean clean":clean["LapSeconds"].mean(),"Std":grp["LapSeconds"].std(),"Tyre life start":grp.get("TyreLife",pd.Series([np.nan])).min(),"Tyre life end":grp.get("TyreLife",pd.Series([np.nan])).max(),"Run type":typ})
    return pd.DataFrame(rows)


def corner_exit_zones(tel, min_speed_kmh=90, throttle=80):
    t=tel.copy()
    t["LocalMin"] = (t["Speed"].shift(1)>t["Speed"]) & (t["Speed"].shift(-1)>t["Speed"])
    mins=t[t["LocalMin"] & (t["Speed"]>40) & (t["Speed"]<min_speed_kmh+80)]
    rows=[]
    for _, r in mins.iterrows():
        d0=r["Distance"]; seg=t[(t["Distance"]>=d0)&(t["Distance"]<=d0+250)]
        if len(seg)<5: continue
        accel=seg[(seg.get("Throttle",0)>=throttle) & (seg["Accel"].notna())]
        rows.append({"Exit distance":d0,"Min speed":r["Speed"],"Speed +100m":np.interp(min(d0+100,t["Distance"].max()),t["Distance"],t["Speed"]),"Speed +200m":np.interp(min(d0+200,t["Distance"].max()),t["Distance"],t["Speed"]),"Mean accel":accel["Accel"].mean() if not accel.empty else np.nan})
    return pd.DataFrame(rows).drop_duplicates(subset=["Exit distance"]).head(20)
