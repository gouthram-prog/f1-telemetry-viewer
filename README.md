# F1 Telemetry Command Centre v13

A mobile-first FastF1 Streamlit dashboard for engineering-style F1 lap analysis.

## What is retained from v12

- Available-year/event/session filtering
- Up to 5-driver comparison
- Reference-driver delta plots
- Multi-channel telemetry overlays
- Plot Lab with selectable X/Y channels
- Corner minimum speed tables
- Corner-exit / straight acceleration analysis
- Track maps and speed-dominance maps
- Tyre information and stint/run-type statistics
- Power unit proxy tab: tractive force, wheel power, gear ratio and shift map plots
- Export of telemetry, deltas and analysis tables

## v13 improvements

- Polished mobile-first dark UI
- Sticky command header
- KPI ribbon: fastest selected lap, reference driver, top speed, stint laps analysed
- Driver badge strip with team colours and tyre chips
- Improved Plotly styling globally across all charts
- More readable chart containers, legends, hover labels and mobile spacing
- Retains the v12 single-file structure for easier GitHub mobile upload

## Deploy

Upload/replace these files in your GitHub repo:

```text
app.py
requirements.txt
README.md
.streamlit/config.toml
```

Then commit. Streamlit Cloud should redeploy automatically.
