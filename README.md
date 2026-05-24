# F1 Engineering Telemetry Viewer

Streamlit + FastF1 telemetry dashboard for mobile and desktop.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud

Upload/replace these files in your GitHub repo:

- `app.py`
- `requirements.txt`
- `README.md`

Then commit. Streamlit Cloud redeploys automatically.

## v4 additions

- iPhone/mobile-first layout tweaks
- two-colour speed dominance map: faster driver at each track point
- tyre status, tyre life and tyre age bands
- practice stint statistics for long-run vs short/quali-style run identification
- improved mobile plot heights and reduced padding

Notes: FastF1 public telemetry is timing-feed based. Acceleration is derived from speed/time and stint/run-type classification is heuristic because public data does not expose fuel load or team run plan.
