from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st

from src.styles import CSS, TEAM_COLORS, TYRE_COLORS, TYRE_LABELS
from src.utils import fmt_time, safe_cols
from src.data_loader import available_events, available_sessions, load_session
from src.analysis import lap_table, best_laps, telemetry_for_lap, align_delta, stint_stats, corner_exit_zones
from src import plotting as pl

st.set_page_config(page_title='F1 Telemetry Studio', page_icon='🏎️', layout='wide', initial_sidebar_state='collapsed')
st.markdown(CSS, unsafe_allow_html=True)


def htmlesc(s):
    return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')


def card(label, value, sub=''):
    st.markdown(f"""<div class='metric-card'><div class='metric-label'>{htmlesc(label)}</div><div class='metric-value'>{htmlesc(value)}</div><div class='driver-sub'>{htmlesc(sub)}</div></div>""", unsafe_allow_html=True)


def tyre_chip(comp, fresh=None, life=None):
    comp = str(comp or 'UNKNOWN').upper()
    col = TYRE_COLORS.get(comp, TYRE_COLORS['UNKNOWN'])
    lbl = TYRE_LABELS.get(comp, '?')
    extra=[]
    if life is not None and pd.notna(life): extra.append(f'{int(life)}L')
    if fresh is not None and pd.notna(fresh): extra.append('new' if bool(fresh) else 'used')
    return f"<span class='chip'><span class='tyre' style='background:{col}'>{lbl}</span>{comp.title()} {' · '.join(extra)}</span>"


def driver_badge(session, drv, idx, lap=None):
    try:
        res=session.results; row=res[res['Abbreviation'].eq(drv)].iloc[0]
        team = row.get('TeamName') or row.get('Team') or 'Unknown'
        num = row.get('DriverNumber') or drv
        full = row.get('FullName') or row.get('BroadcastName') or drv
    except Exception:
        team='Unknown'; num=drv; full=drv
    col=TEAM_COLORS.get(team, '#8b96a8')
    tyre=''
    if lap is not None:
        tyre=tyre_chip(lap.get('Compound','UNKNOWN'), lap.get('FreshTyre',None), lap.get('TyreLife',None))
    st.markdown(f"""<div class='driver-card'><div class='driver-num' style='background:{col}'>{htmlesc(num)}</div><div class='driver-meta'><div class='driver-name'>{htmlesc(drv)} · {htmlesc(full)}</div><div class='driver-sub'>{htmlesc(team)}</div><div>{tyre}</div></div></div>""", unsafe_allow_html=True)


def pick_lap(laps, mode, manual_lap):
    use=laps.copy()
    if use.empty: return None
    if mode == 'Fastest accurate lap':
        acc = use[use.get('IsAccurate', True).fillna(True)] if 'IsAccurate' in use else use
        if acc.empty: acc=use
        return acc.pick_fastest()
    if mode == 'Fastest lap':
        return use.pick_fastest()
    m=use[use['LapNumber'].eq(manual_lap)]
    return m.iloc[0] if not m.empty else use.pick_fastest()


st.markdown("""<div class='hero'><div class='hero-title'>F1 Telemetry Studio</div><div class='hero-sub'>FastF1-powered race engineering dashboard: lap comparison, deltas, tyre/stint intelligence, track dominance and PU-style proxies.</div></div>""", unsafe_allow_html=True)

with st.sidebar:
    st.header('Session')
    year = st.selectbox('Year', list(range(2026, 2017, -1)), index=1)
    events = available_events(year)
    if not events:
        st.error('No completed events found for this year yet.')
        st.stop()
    event = st.selectbox('Grand Prix', events)
    sessions = available_sessions(year, event)
    session_key = st.selectbox('Session', sessions, format_func=lambda s: {'FP1':'Practice 1','FP2':'Practice 2','FP3':'Practice 3','SQ':'Sprint Qualifying','S':'Sprint','Q':'Qualifying','R':'Race'}.get(s,s))
    st.divider()
    st.caption('Driver selection')

with st.spinner('Loading FastF1 session data...'):
    session = load_session(year, event, session_key)

try:
    drivers = list(session.laps['Driver'].dropna().unique())
except Exception:
    drivers = list(session.drivers)

with st.sidebar:
    selected = st.multiselect('Compare drivers, max 5', drivers, default=drivers[:2], max_selections=5)
    if not selected:
        st.stop()
    ref_driver = st.selectbox('Reference driver', selected, index=0)
    lap_mode = st.radio('Lap selection', ['Fastest accurate lap','Fastest lap','Manual lap'], horizontal=False)
    manual_lap = int(st.number_input('Manual lap number', min_value=1, max_value=100, value=1, disabled=(lap_mode!='Manual lap')))
    st.caption('Plot flexibility')
    channels = st.multiselect('Telemetry channels', ['Speed','Throttle','Brake','RPM','nGear','DRS','Accel'], default=['Speed','Throttle','Brake'])
    x_axis = st.selectbox('Telemetry X-axis', ['Distance','LapTimeSeconds','Speed'], index=0, format_func=lambda x: {'Distance':'Distance','LapTimeSeconds':'Time','Speed':'Speed'}.get(x,x))

laps_all = lap_table(session, selected)
best = {}
tel_map = {}
for drv in selected:
    dlaps = session.laps.pick_drivers([drv])
    lap = pick_lap(dlaps, lap_mode, manual_lap)
    if lap is not None:
        best[drv] = lap
        try: tel_map[drv] = telemetry_for_lap(lap)
        except Exception as e: st.warning(f'Could not load telemetry for {drv}: {e}')

if not best:
    st.error('No usable laps found for selected drivers.')
    st.stop()

st.markdown("<div class='grid'>", unsafe_allow_html=True)
cols = st.columns(4)
fastest_driver = min(best, key=lambda d: pd.to_timedelta(best[d].get('LapTime', pd.NaT)).total_seconds() if pd.notna(best[d].get('LapTime', pd.NaT)) else 9999)
with cols[0]: card('Event', event, f'{year} · {session_key}')
with cols[1]: card('Reference', ref_driver, 'delta baseline')
with cols[2]: card('Fastest selected', fastest_driver, fmt_time(best[fastest_driver].get('LapTime')))
with cols[3]: card('Drivers', str(len(selected)), 'comparison set')
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
dcols = st.columns(min(5, len(selected)))
for i, drv in enumerate(selected):
    with dcols[i % len(dcols)]:
        driver_badge(session, drv, i, best.get(drv))
st.markdown("</div>", unsafe_allow_html=True)

tabs = st.tabs(['Overview','Delta','Telemetry Lab','Track Maps','Tyres & Stints','Power Unit','Insights','Export'])

with tabs[0]:
    c1,c2 = st.columns([1.2,1])
    with c1:
        st.plotly_chart(pl.lap_heatmap(laps_all), use_container_width=True)
    with c2:
        rows=[]
        for d,lap in best.items():
            rows.append({'Driver':d,'Lap':int(lap.get('LapNumber',0)),'Lap time':fmt_time(lap.get('LapTime')),'S1':fmt_time(lap.get('Sector1Time')),'S2':fmt_time(lap.get('Sector2Time')),'S3':fmt_time(lap.get('Sector3Time')),'Tyre':str(lap.get('Compound','')),'Life':lap.get('TyreLife',np.nan),'Fresh':lap.get('FreshTyre','')})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.plotly_chart(pl.telemetry_overlay(tel_map, session, ['Speed'], x='Distance', reference=ref_driver), use_container_width=True)

with tabs[1]:
    ref_tel = tel_map.get(ref_driver)
    if ref_tel is None: st.warning('Reference telemetry unavailable.')
    else:
        for cmp in [d for d in selected if d != ref_driver and d in tel_map]:
            delta = align_delta(ref_tel, tel_map[cmp])
            st.plotly_chart(pl.delta_plot(delta, ref_driver, cmp), use_container_width=True)
            gain = delta['Delta'].iloc[-1]
            st.caption(f'{cmp} final delta to {ref_driver}: {gain:+.3f} s. Negative means comparison driver is ahead of reference.')

with tabs[2]:
    st.plotly_chart(pl.telemetry_overlay(tel_map, session, channels or ['Speed'], x=x_axis, reference=ref_driver), use_container_width=True)
    st.caption('Select any channel stack from the sidebar. This is intended as the flexible “plot lab” for overlays, not a fixed chart.')

with tabs[3]:
    pairs=[d for d in selected if d != ref_driver and d in tel_map]
    if pairs and ref_driver in tel_map:
        cmp=st.selectbox('Compare against reference on track map', pairs)
        ref_col,_=pl.team_color(session, ref_driver, 0); cmp_col,_=pl.team_color(session, cmp, 1)
        st.plotly_chart(pl.speed_dominance_track(tel_map[ref_driver], tel_map[cmp], ref_driver, cmp, ref_col, cmp_col), use_container_width=True)
    else:
        st.info('Select at least two drivers with telemetry to show dominance map.')

with tabs[4]:
    stats = stint_stats(session, selected)
    c1,c2=st.columns([1,1])
    with c1: st.plotly_chart(pl.stint_plot(stats), use_container_width=True)
    with c2: st.plotly_chart(pl.tyre_life_scatter(laps_all), use_container_width=True)
    st.subheader('Stint intelligence')
    show = stats.copy()
    for c in ['Best','Median','Mean clean','Std']:
        if c in show: show[c]=show[c].map(lambda v: round(v,3) if pd.notna(v) else v)
    st.dataframe(show, use_container_width=True, hide_index=True)

with tabs[5]:
    st.plotly_chart(pl.shift_map({k:v for k,v in tel_map.items() if k in selected[:2]}, session), use_container_width=True)
    st.plotly_chart(pl.tractive_force_proxy(tel_map, session), use_container_width=True)
    st.caption('FastF1 public car telemetry generally exposes speed, throttle, brake, RPM, gear and DRS. True ERS SOC/harvest/deploy channels are normally not public, so this tab uses inferred PU/driveline proxies where possible.')

with tabs[6]:
    st.subheader('Automated insights')
    insights=[]
    if ref_driver in tel_map:
        ref_tel=tel_map[ref_driver]
        for cmp in [d for d in selected if d!=ref_driver and d in tel_map]:
            delta=align_delta(ref_tel, tel_map[cmp])
            max_loss=delta.loc[delta['Delta'].idxmax()]
            max_gain=delta.loc[delta['Delta'].idxmin()]
            insights.append({'Comparison':f'{cmp} vs {ref_driver}','Largest loss distance [m]':round(max_loss['Distance'],1),'Loss [s]':round(max_loss['Delta'],3),'Largest gain distance [m]':round(max_gain['Distance'],1),'Gain [s]':round(max_gain['Delta'],3),'Top speed diff avg [km/h]':round((delta['SpeedDiff']).mean(),2)})
    st.dataframe(pd.DataFrame(insights), use_container_width=True, hide_index=True)
    exits={}
    for d,t in tel_map.items():
        exits[d]=corner_exit_zones(t)
    st.plotly_chart(pl.corner_exit_plot(exits), use_container_width=True)
    with st.expander('Corner-exit tables'):
        for d,df in exits.items():
            st.markdown(f'**{d}**')
            st.dataframe(df.round(3), use_container_width=True, hide_index=True)

with tabs[7]:
    st.subheader('Export')
    st.download_button('Download selected lap table CSV', data=laps_all.to_csv(index=False).encode('utf-8'), file_name=f'{year}_{event}_{session_key}_laps.csv', mime='text/csv')
    for d,tel in tel_map.items():
        st.download_button(f'Download telemetry CSV · {d}', data=tel.to_csv(index=False).encode('utf-8'), file_name=f'{year}_{event}_{session_key}_{d}_telemetry.csv', mime='text/csv')
