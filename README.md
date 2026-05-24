# F1 Telemetry Viewer v6

Mobile-first Streamlit telemetry dashboard powered by FastF1.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud

Upload/replace these files in your GitHub repo:

- `app.py`
- `requirements.txt`
- `README.md`

Streamlit Cloud will redeploy automatically after the commit.

## Main changes in v6

- Full dark F1-style mobile-first UI
- No raw HTML/code snippets displayed
- Colour-coded selected-lap table
- Team colours and driver fallback mapping
- Tyre chips and tyre summary cards
- Delta to reference driver
- Multi-driver telemetry overlays
- Corner-exit and straight acceleration analysis
- Two-colour speed-dominance track map
- Practice stint/run-type analysis
- CSV export


## v8 update

- Shift map can compare two drivers.
- Gear colours are discrete from 1 to 8.
- Driver 1 uses dot markers and solid inferred trend lines.
- Driver 2 uses diamond markers and dashed inferred trend lines.
- Trend lines are linear RPM-vs-speed fits per gear.
