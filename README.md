# F1 Engineering Telemetry Viewer v12

Mobile-first Streamlit + FastF1 telemetry dashboard.

## Features retained from v10
- Filtered year / Grand Prix / session availability
- Up to 5-driver comparison
- Accurate lap and sector times
- Telemetry overlays
- Delta-to-reference plots
- Corner minimum speed table
- Corner-exit acceleration and straight-line summaries
- Track map and two-driver speed-dominance map
- Tyre age/fresh-used information
- Practice stint classification for long-run/quali-style runs
- Power unit proxy tab: tractive force, power-speed, gear ratios, shift map, ERS-channel detection
- CSV export

## v12 improvements
- Restored v10 feature set after the failed v11 rebuild
- Removed risky HTML wrappers around widgets that could show code snippets
- Added Plot Lab for flexible overlays of channels vs distance/time/lap percent/speed
- Added automatic Insights tab
- Included `.streamlit/config.toml` theme file
- More robust single-file app for easier GitHub upload

## Deploy
Upload these files/folders to GitHub:

```text
app.py
requirements.txt
README.md
.streamlit/config.toml
```

Streamlit main file path:

```text
app.py
```
