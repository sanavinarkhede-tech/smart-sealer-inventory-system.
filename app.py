import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Sealer Drum Flow - Digital Twin", layout="wide")

# Simulated Sealer Drum Database (Steps 6 & 7: Inventory & FEFO)
drum_data = [
    {"Drum ID": "D001", "Lot No.": "L123", "Expiry Date": "12-2026", "Quantity": "200 L", "Status": "In Storage"},
    {"Drum ID": "D002", "Lot No.": "L124", "Expiry Date": "01-2027", "Quantity": "200 L", "Status": "Next (FEFO)"},
    {"Drum ID": "D003", "Lot No.": "L125", "Expiry Date": "03-2027", "Quantity": "200 L", "Status": "In Storage"}
]
df = pd.DataFrame(drum_data)

# Header
st.title("Sealer Drum Flow & Storage Area")
st.markdown("**Plant Process & Digital Twin Simulation (Arrival to Line Issue)**")
st.success("Streamlit Cloud Deployment Active")

# Metrics Grid
col1, col2, col3, col4 = st.columns(4)
col1.metric("Active Drums in Storage", "3")
col2.metric("Active Line Consumption", "182 L")
col3.metric("Active Logic Rule", "FEFO")
col4.metric("System Alerts", "None")

st.markdown("---")

# Inventory Table
st.subheader("Inventory Monitoring & FIFO/FEFO Queue")
st.dataframe(df, use_container_width=True)

# Process Overview
st.info(
    "Process Overview: Covers all stages from Plant Arrival (Step 1) -> Quality Check & SAP GRN (Steps 2-3) "
    "-> Storage & Tagging (Steps 4-5) -> Real-time Monitoring & FEFO Issue (Steps 6-8) "
    "-> Line-Side Consumption via Load Cells (Step 9) to Empty Return (Steps 10-11)."
)
