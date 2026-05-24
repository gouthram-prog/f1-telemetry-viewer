# F1 Telemetry Studio v11

A mobile-first FastF1 telemetry dashboard built for Streamlit Cloud.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Highlights

- completed event/session filtering
- mobile-first dark UI
- driver cards, tyre chips and team colours
- lap heatmap and accurate sector timings
- flexible telemetry overlay lab
- reference-driver delta plots
- speed-based track dominance
- stint and tyre-life analysis
- PU-style proxy plots: shift map and acceleration-vs-speed
- automated insight tables
- CSV export

## Note

Public FastF1 data does not normally include true ERS SOC/harvest/deployment channels. The Power Unit tab therefore uses available public telemetry to derive proxies.
