# F1 Telemetry Viewer

A local Streamlit telemetry viewer powered by FastF1.

## Features

- Load F1 sessions from 2018 onwards
- Compare any two driver laps
- Fastest-lap or manual lap selection
- Speed, throttle, brake, gear, RPM and DRS overlays
- Distance-based delta trace
- Track map coloured by telemetry channel
- Lap timing table
- CSV export for selected laps and delta trace

## Install

```bash
cd f1_telemetry_viewer
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Notes

- First load of a session can be slow because FastF1 downloads timing and telemetry data. Later loads use `./fastf1_cache`.
- Some older or unusual sessions may have incomplete telemetry.
- The delta trace is an engineering-useful approximation based on interpolating lap time over distance.
- FastF1 does not expose every channel a real team would have, such as steering angle, brake pressure, engine torque maps, ERS deployment internals, suspension potentiometers, etc.
