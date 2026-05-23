# F1 Engineering Telemetry Viewer

A Streamlit + FastF1 telemetry dashboard designed for engineering-style lap comparison.

## Features

- Compare up to 5 drivers
- Reference-driver delta traces
- Team-colour plotting with darker reference / lighter comparison shades
- Speed, throttle, brake, gear, RPM, DRS and estimated acceleration overlays
- Corner minimum speed comparison
- Corner exit and straight acceleration analysis
- Track map coloured by selected telemetry channels
- Speed dominance map versus the reference driver
- Lap-time evolution and full lap table
- Race pace, stint and tyre-life plots
- CSV export for selected telemetry, delta traces and analysis tables

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud

1. Upload `app.py`, `requirements.txt` and this `README.md` to your GitHub repo.
2. Go to Streamlit Community Cloud.
3. Create a new app using `app.py` as the main file.
4. Streamlit will install the dependencies from `requirements.txt`.

## Notes

FastF1 public telemetry is very useful for comparative analysis, but it is not the same as raw team telemetry. Acceleration is estimated from speed/time and should be treated as comparative rather than sensor-grade.
