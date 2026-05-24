from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from .styles import TEAM_COLORS, TYRE_COLORS, GEAR_COLORS
from .utils import lighten

PLOT_BG = '#08101b'
PAPER_BG = 'rgba(0,0,0,0)'
GRID = 'rgba(255,255,255,.10)'
TXT = '#f5f7fb'
MUTED = 'rgba(245,247,251,.58)'


def base_fig(height=430, title=None):
    fig = go.Figure()
    fig.update_layout(
        template='plotly_dark', paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        height=height, margin=dict(l=42,r=18,t=54 if title else 24,b=42),
        font=dict(color=TXT, family='Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0, bgcolor='rgba(0,0,0,0)'),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, title_font=dict(color=MUTED), tickfont=dict(color=MUTED)),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, title_font=dict(color=MUTED), tickfont=dict(color=MUTED)),
    )
    if title: fig.update_layout(title=dict(text=title, x=0, font=dict(size=17)))
    return fig


def team_color(session, drv, idx=0):
    try:
        res = session.results
        row = res[res['Abbreviation'].eq(drv)].iloc[0]
        team = row.get('TeamName') or row.get('Team') or ''
        return TEAM_COLORS.get(team, px.colors.qualitative.Bold[idx % len(px.colors.qualitative.Bold)]), team
    except Exception:
        return px.colors.qualitative.Bold[idx % len(px.colors.qualitative.Bold)], 'Unknown'


def telemetry_overlay(tel_map, session, channels, x='Distance', reference=None):
    fig = base_fig(height=460, title='Telemetry overlay')
    axis_names = {'Speed':'Speed [km/h]','Throttle':'Throttle [%]','Brake':'Brake','RPM':'RPM','nGear':'Gear','DRS':'DRS','Accel':'Accel [m/s²]'}
    for ci, ch in enumerate(channels):
        yaxis = 'y' if ci == 0 else f'y{ci+1}'
        for i,(drv,tel) in enumerate(tel_map.items()):
            if ch not in tel.columns or x not in tel.columns: continue
            col,_ = team_color(session, drv, i)
            if reference and drv != reference: col = lighten(col, .25)
            fig.add_trace(go.Scatter(
                x=tel[x], y=tel[ch], name=f'{drv} · {ch}', mode='lines',
                line=dict(color=col, width=2 if drv==reference or reference is None else 1.4),
                opacity=0.95 if drv==reference or reference is None else .68,
                yaxis=yaxis
            ))
        if ci > 0:
            fig.update_layout(**{f'yaxis{ci+1}': dict(title=axis_names.get(ch,ch), overlaying='y', side='right' if ci%2 else 'left', position=max(0.03, 1-ci*.05), showgrid=False)})
    fig.update_yaxes(title=axis_names.get(channels[0], channels[0]) if channels else '')
    fig.update_xaxes(title=x)
    return fig


def delta_plot(delta_df, ref, cmp):
    fig = base_fig(height=320, title=f'Delta to reference: {cmp} − {ref}')
    fig.add_trace(go.Scatter(x=delta_df['Distance'], y=delta_df['Delta'], mode='lines', name='Delta', line=dict(color='#ffd12a', width=2.4)))
    fig.add_hline(y=0, line_width=1, line_dash='dash', line_color='rgba(255,255,255,.45)')
    fig.update_yaxes(title='Delta [s]')
    fig.update_xaxes(title='Distance [m]')
    return fig


def speed_dominance_track(ref_tel, cmp_tel, ref, cmp, ref_color='#ff2b3a', cmp_color='#27F4D2'):
    max_d = min(ref_tel['Distance'].max(), cmp_tel['Distance'].max())
    grid = np.linspace(0, max_d, 700)
    rx = np.interp(grid, ref_tel['Distance'], ref_tel['X']) if 'X' in ref_tel else None
    ry = np.interp(grid, ref_tel['Distance'], ref_tel['Y']) if 'Y' in ref_tel else None
    if rx is None or ry is None:
        return base_fig(height=340, title='Track dominance unavailable: missing position X/Y')
    rs = np.interp(grid, ref_tel['Distance'], ref_tel['Speed'])
    cs = np.interp(grid, cmp_tel['Distance'], cmp_tel['Speed'])
    faster = rs >= cs
    fig = base_fig(height=430, title=f'Track dominance by local speed: {ref} vs {cmp}')
    for val, name, col in [(True, ref, ref_color), (False, cmp, cmp_color)]:
        mask = faster == val
        fig.add_trace(go.Scatter(x=rx[mask], y=ry[mask], mode='markers', name=f'Faster: {name}', marker=dict(size=4, color=col, opacity=.95)))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False, scaleanchor='x', scaleratio=1)
    fig.update_layout(margin=dict(l=5,r=5,t=54,b=5))
    return fig


def lap_heatmap(lap_df):
    if lap_df.empty or 'LapTimeSeconds' not in lap_df: return base_fig(title='Lap heatmap')
    pivot = lap_df.pivot_table(index='Driver', columns='LapNumber', values='LapTimeSeconds', aggfunc='min')
    fig = go.Figure(data=go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index, colorscale='Turbo', colorbar=dict(title='s'), hovertemplate='Driver %{y}<br>Lap %{x}<br>%{z:.3f}s<extra></extra>'))
    fig.update_layout(template='plotly_dark', paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG, height=300, margin=dict(l=35,r=10,t=25,b=35), font=dict(color=TXT))
    return fig


def stint_plot(stats):
    fig = base_fig(height=390, title='Stint pace: median and spread')
    if stats.empty: return fig
    for _, r in stats.iterrows():
        comp = str(r.get('Compound','UNKNOWN')).upper()
        col = TYRE_COLORS.get(comp, '#8b96a8')
        fig.add_trace(go.Bar(x=[f"{r['Driver']} S{int(r['Stint']) if pd.notna(r['Stint']) else '?'}"], y=[r.get('Median')], name=f"{r['Driver']} {comp}", marker_color=col, text=[r.get('Run type','')], textposition='outside', showlegend=False, error_y=dict(type='data', array=[r.get('Std') if pd.notna(r.get('Std')) else 0])))
    fig.update_yaxes(title='Lap time [s]')
    fig.update_xaxes(title='Stint')
    return fig


def tyre_life_scatter(laps):
    fig = base_fig(height=390, title='Tyre life vs lap time')
    if laps.empty or 'TyreLife' not in laps or 'LapTimeSeconds' not in laps: return fig
    for drv, grp in laps.groupby('Driver'):
        fig.add_trace(go.Scatter(x=grp['TyreLife'], y=grp['LapTimeSeconds'], mode='markers+lines', name=drv, marker=dict(size=7, color=[TYRE_COLORS.get(str(c).upper(),'#888') for c in grp.get('Compound', [])], line=dict(width=1,color='white'))))
    fig.update_xaxes(title='Tyre life [laps]'); fig.update_yaxes(title='Lap time [s]')
    return fig


def shift_map(tel_map, session):
    fig = base_fig(height=480, title='RPM vs speed shift map')
    symbols = ['circle','diamond']
    dashes = ['solid','dash']
    for di,(drv,tel) in enumerate(list(tel_map.items())[:2]):
        if not {'Speed','RPM','nGear'}.issubset(tel.columns): continue
        data = tel[(tel['Speed']>20)&(tel['RPM']>3000)&(tel['nGear'].between(1,8))].copy()
        for gear, grp in data.groupby('nGear'):
            gear = int(gear); col = GEAR_COLORS.get(gear,'#aaa')
            fig.add_trace(go.Scatter(x=grp['Speed'], y=grp['RPM'], mode='markers', name=f'{drv} G{gear}', legendgroup=f'G{gear}', marker=dict(color=col, size=3.0 if di==0 else 4.2, symbol=symbols[min(di,1)], opacity=.22 if di==0 else .30), showlegend=(di==0)))
            if len(grp) > 20:
                q1,q99 = grp['Speed'].quantile([.03,.97])
                fit = grp[(grp['Speed']>=q1)&(grp['Speed']<=q99)]
                if len(fit)>20:
                    m,b = np.polyfit(fit['Speed'], fit['RPM'], 1)
                    xs = np.linspace(fit['Speed'].min(), fit['Speed'].max(), 40)
                    fig.add_trace(go.Scatter(x=xs, y=m*xs+b, mode='lines', name=f'{drv} G{gear} fit', legendgroup=f'G{gear}', line=dict(color=col, width=1.25, dash=dashes[min(di,1)]), opacity=.95, showlegend=False))
    fig.update_xaxes(title='Speed [km/h]'); fig.update_yaxes(title='RPM')
    return fig


def tractive_force_proxy(tel_map, session):
    fig = base_fig(height=410, title='Longitudinal acceleration vs speed — tractive-force proxy')
    for i,(drv,tel) in enumerate(tel_map.items()):
        if not {'Speed','Accel','Throttle'}.issubset(tel.columns): continue
        col,_=team_color(session,drv,i)
        data=tel[(tel['Throttle']>85)&(tel['Accel'].notna())&(tel['Accel']>-3)&(tel['Accel']<8)&(tel['Speed']>40)]
        fig.add_trace(go.Scatter(x=data['Speed'], y=data['Accel'], mode='markers', name=drv, marker=dict(color=col,size=4,opacity=.28)))
        if len(data)>50:
            bins=np.linspace(data['Speed'].min(),data['Speed'].max(),28)
            data=data.assign(bin=pd.cut(data['Speed'],bins))
            prof=data.groupby('bin', observed=False).agg(Speed=('Speed','median'), Accel=('Accel','median')).dropna()
            fig.add_trace(go.Scatter(x=prof['Speed'], y=prof['Accel'], mode='lines', name=f'{drv} median', line=dict(color=col,width=2.5)))
    fig.update_xaxes(title='Speed [km/h]'); fig.update_yaxes(title='Acceleration [m/s²]')
    return fig


def corner_exit_plot(exit_map):
    fig = base_fig(height=390, title='Corner-exit acceleration summary')
    for drv, df in exit_map.items():
        if df.empty: continue
        fig.add_trace(go.Scatter(x=df['Exit distance'], y=df['Speed +200m']-df['Min speed'], mode='markers+lines', name=f'{drv}: ΔV 200m', marker=dict(size=8)))
    fig.update_xaxes(title='Corner exit distance [m]'); fig.update_yaxes(title='Speed gain over 200 m [km/h]')
    return fig
