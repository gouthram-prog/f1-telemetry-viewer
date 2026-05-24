from __future__ import annotations

TEAM_COLORS = {
    "Red Bull Racing": "#3671C6", "Mercedes": "#27F4D2", "Ferrari": "#E8002D",
    "McLaren": "#FF8000", "Aston Martin": "#229971", "Alpine": "#FF87BC",
    "Williams": "#64C4FF", "RB": "#6692FF", "Racing Bulls": "#6692FF",
    "Haas F1 Team": "#B6BABD", "Kick Sauber": "#52E252", "Sauber": "#52E252",
    "Alfa Romeo": "#900000", "AlphaTauri": "#5E8FAA", "Renault": "#FFF500",
}

TYRE_COLORS = {"SOFT":"#ff2b3a", "MEDIUM":"#ffd12a", "HARD":"#f4f4f4", "INTERMEDIATE":"#26d07c", "WET":"#2996ff", "UNKNOWN":"#7f8794"}
TYRE_LABELS = {"SOFT":"S", "MEDIUM":"M", "HARD":"H", "INTERMEDIATE":"I", "WET":"W", "UNKNOWN":"?"}

GEAR_COLORS = {
    1:"#ff2b3a", 2:"#ff8c00", 3:"#ffd12a", 4:"#29d17d", 5:"#00d2ff", 6:"#3671c6", 7:"#9b5cff", 8:"#ff4fd8"
}

CSS = """
<style>
:root{--bg:#05080d;--panel:#0b1320;--panel2:#101b2b;--line:rgba(255,255,255,.11);--text:#f5f7fb;--muted:rgba(245,247,251,.62);--red:#ff2b3a;--green:#26d07c;--yellow:#ffd12a;}
html,body,[data-testid="stAppViewContainer"]{background:radial-gradient(circle at 20% -10%, rgba(45,140,255,.18), transparent 38%),linear-gradient(180deg,#05080d,#070b12)!important;color:var(--text)}
[data-testid="stHeader"]{background:transparent}.block-container{padding: .55rem .55rem 1.2rem .55rem;max-width:1180px}.stTabs [data-baseweb="tab-list"]{gap:.35rem;overflow-x:auto}.stTabs [data-baseweb="tab"]{background:#0b1320;border:1px solid var(--line);border-radius:999px;padding:.45rem .8rem;height:auto;color:var(--muted)}.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#ff2b3a,#ff8c00)!important;color:#fff!important}h1{font-size:clamp(1.25rem,5vw,2rem)!important}.hero{border:1px solid var(--line);background:linear-gradient(135deg,rgba(255,43,58,.2),rgba(54,113,198,.16)),#08101b;border-radius:24px;padding:16px;margin:4px 0 12px 0;box-shadow:0 18px 45px rgba(0,0,0,.24)}.hero-title{font-size:clamp(1.25rem,6vw,2.1rem);font-weight:900;letter-spacing:-.02em}.hero-sub{color:var(--muted);font-size:.9rem;margin-top:5px}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:10px 0}@media(max-width:760px){.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.metric-card{padding:10px!important}.hide-mobile{display:none!important}}
.metric-card{background:linear-gradient(180deg,rgba(255,255,255,.04),rgba(255,255,255,.015));border:1px solid var(--line);border-radius:18px;padding:13px}.metric-label{font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}.metric-value{font-size:1.18rem;font-weight:850;margin-top:4px}.card{background:linear-gradient(180deg,rgba(255,255,255,.04),rgba(255,255,255,.015));border:1px solid var(--line);border-radius:20px;padding:13px;margin:8px 0}.driver-card{display:flex;gap:10px;align-items:center;border:1px solid var(--line);background:#0b1320;border-radius:18px;padding:10px;margin:6px 0}.driver-num{width:42px;height:42px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-weight:900;color:#061018}.driver-meta{flex:1}.driver-name{font-weight:850}.driver-sub{color:var(--muted);font-size:.82rem}.chip{display:inline-flex;align-items:center;gap:5px;border:1px solid var(--line);background:#101b2b;border-radius:999px;padding:.25rem .55rem;margin:.15rem;font-size:.78rem}.tyre{width:24px;height:24px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:.72rem;font-weight:900;color:#061018;border:2px solid rgba(255,255,255,.35)}div[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:18px;overflow:hidden}.stPlotlyChart{background:#08101b;border:1px solid var(--line);border-radius:20px;padding:4px;margin:8px 0}code{white-space:pre-wrap!important}
</style>
"""
