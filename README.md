# F1 Telemetry Viewer v5

Mobile-first FastF1 telemetry dashboard for iPhone and desktop.

## Updates in v5

- Fixed team detection from FastF1 `session.results`, so teams should no longer show as `Unknown` when metadata is available.
- Added a more polished F1-style dark UI.
- Moved session and driver controls into the main page so they are easier to use on iPhone.
- Reworked the selected-laps summary into a compact colour-coded table.
- Retained v4 features: multi-driver comparison, deltas, two-driver speed-dominance track map, tyre/stint info, practice stint classification and exports.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

Upload/replace `app.py`, `requirements.txt` and `README.md` in your GitHub repo. Streamlit Cloud will redeploy automatically.
