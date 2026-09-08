# CIVL 6962 Homework 1: PeMS Freeway Sensor Dashboard

A small Streamlit dashboard built from the PeMS District 4 course dataset.

## What the dashboard includes

- one dataset: `data/pems.parquet`
- three filters in the sidebar: sensor, date range, and hour-of-day range
- three chart types: line, bar, and scatter
- units in chart labels
- `@st.cache_data` on the loader
- metric cards, tabs, an expander, and a download button
- dataset provenance
- a three-item blind-spot panel

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Deploy on Streamlit Community Cloud

1. Push this folder to a GitHub repository.
2. In Streamlit Community Cloud, create a new app from that repository.
3. Set the entry point to `app.py`.
4. Deploy and test the public URL in a private/incognito browser window.

The `data/pems.parquet` file must remain in the repository because the app reads it with the relative path `data/pems.parquet`.
