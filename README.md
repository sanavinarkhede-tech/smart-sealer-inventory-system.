
# Digital Sealer Inventory Monitoring System

An Industrial IoT-style Streamlit application for monitoring sealer drum inventory in an automotive Body Shop.

## Features

- Industrial dashboard and inventory KPIs
- Drum inventory management (add, edit, remove empty drums)
- Simulated stock consumption recording
- Drum-wise and shift-wise consumption analytics
- Transaction history with filters
- Low-stock and critical-stock alerts
- Inventory and consumption CSV reports
- Simulated SAP stock comparison
- Responsive charts and storage overview

## Tech Stack

- Python
- Streamlit
- Pandas
- Plotly

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Important Note

This version uses demo data and Streamlit session state. It does not connect to physical load cells, a real SAP system, or a persistent database. Data may reset when the app session restarts.
