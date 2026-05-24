from __future__ import annotations
import colorsys
import numpy as np
import pandas as pd


def fmt_time(x):
    if x is None or (isinstance(x, float) and np.isnan(x)): return "—"
    try:
        td = pd.to_timedelta(x)
        s = td.total_seconds()
    except Exception:
        try: s = float(x)
        except Exception: return str(x)
    if not np.isfinite(s): return "—"
    m = int(s//60); sec = s - 60*m
    return f"{m}:{sec:06.3f}" if m else f"{sec:.3f}s"


def seconds(x):
    try: return pd.to_timedelta(x).total_seconds()
    except Exception:
        try: return float(x)
        except Exception: return np.nan


def lighten(hex_color: str, amount: float = .45) -> str:
    h = hex_color.strip('#')
    if len(h) != 6: return hex_color
    r,g,b = tuple(int(h[i:i+2], 16)/255 for i in (0,2,4))
    hh,ll,ss = colorsys.rgb_to_hls(r,g,b)
    ll = min(1, ll + amount*(1-ll))
    r,g,b = colorsys.hls_to_rgb(hh,ll,ss)
    return '#%02x%02x%02x' % (int(r*255),int(g*255),int(b*255))


def safe_cols(df, cols):
    return [c for c in cols if c in df.columns]
