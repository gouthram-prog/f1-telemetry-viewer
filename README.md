# F1 Engineering Telemetry Viewer v14

Streamlit + FastF1 telemetry viewer.

v14 keeps the v13/v12 historical-analysis workflow and adds an f1-dash-inspired overview UI:

- timing-wall style driver rows
- gap to reference driver
- sector chips
- tyre compound rings
- selected-lap command centre
- retained telemetry, plot lab, delta, corner-exit, track-map, tyre/stint, PU and export tabs

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

Upload all files including `.streamlit/config.toml` to GitHub and deploy through Streamlit Community Cloud.
