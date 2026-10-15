
import streamlit as st
import pandas as pd
import plotly.express as px
import random
from datetime import datetime, date, timedelta

st.set_page_config(
    page_title="Digital Sealer Inventory",
    page_icon="🏭",
    layout="wide"
)

st.markdown("""
<style>
.stApp {background-color: #f4f7fb;}
[data-testid="stSidebar"] {
    background-color: #14283e;
}
[data-testid="stSidebar"] * {
    color: white;
}
h1, h2, h3 {color: #17324d;}
div[data-testid="stMetric"] {
    background: white;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #e1e8f0;
}
.stButton button {
    border-radius: 8px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# ---------------- SESSION DATA ----------------

def initialize():
    if "drums" not in st.session_state:
        st.session_state.drums = pd.DataFrame([
            {
                "Drum ID": "SD-001",
                "Sealer Type": "PVC",
                "Capacity (kg)": 200.0,
                "Tare (kg)": 18.0,
                "Remaining (kg)": 200.0,
                "Location": "Rack A1"
            },
            {
                "Drum ID": "SD-002",
                "Sealer Type": "PVC",
                "Capacity (kg)": 200.0,
                "Tare (kg)": 18.0,
                "Remaining (kg)": 150.0,
                "Location": "Rack A2"
            },
            {
                "Drum ID": "SD-003",
                "Sealer Type": "PU",
                "Capacity (kg)": 200.0,
                "Tare (kg)": 19.0,
                "Remaining (kg)": 90.0,
                "Location": "Rack B1"
            },
            {
                "Drum ID": "SD-004",
                "Sealer Type": "PVC",
                "Capacity (kg)": 200.0,
                "Tare (kg)": 18.0,
                "Remaining (kg)": 35.0,
                "Location": "Rack B2"
            }
        ])

    if "transactions" not in st.session_state:
        st.session_state.transactions = pd.DataFrame(
            columns=[
                "Date/Time", "Drum ID", "Type",
                "Quantity (kg)", "Shift", "Operator", "Remarks"
            ]
        )

    if "consumption" not in st.session_state:
        st.session_state.consumption = pd.DataFrame(
            columns=[
                "Date", "Drum ID", "Shift", "Operator",
                "Vehicles Produced", "Quantity (kg)", "Remarks"
            ]
        )

    if "sensor_history" not in st.session_state:
        st.session_state.sensor_history = {}


initialize()


# ---------------- HELPERS ----------------

def log_transaction(drum_id, transaction_type, quantity,
                    shift, operator, remarks):
    new_row = {
        "Date/Time": datetime.now(),
        "Drum ID": drum_id,
        "Type": transaction_type,
        "Quantity (kg)": float(quantity),
        "Shift": shift,
        "Operator": operator,
        "Remarks": remarks
    }

    st.session_state.transactions = pd.concat(
        [
            st.session_state.transactions,
            pd.DataFrame([new_row])
        ],
        ignore_index=True
    )


def stock_status(remaining, capacity):
    if remaining <= 0:
        return "Empty"
    if remaining <= capacity * 0.20:
        return "Low Stock"
    if remaining >= capacity * 0.995:
        return "Full"
    return "In Use"


def current_inventory():
    df = st.session_state.drums.copy()

    if df.empty:
        df["Status"] = pd.Series(dtype=str)
        df["Stock Level (%)"] = pd.Series(dtype=float)
        return df

    df["Remaining (kg)"] = pd.to_numeric(
        df["Remaining (kg)"], errors="coerce"
    ).fillna(0).clip(lower=0)

    df["Remaining (kg)"] = df.apply(
        lambda row: min(
            row["Remaining (kg)"],
            row["Capacity (kg)"]
        ),
        axis=1
    )

    df["Stock Level (%)"] = (
        df["Remaining (kg)"]
        / df["Capacity (kg)"].replace(0, 1)
        * 100
    ).round(1)

    df["Status"] = df.apply(
        lambda row: stock_status(
            row["Remaining (kg)"],
            row["Capacity (kg)"]
        ),
        axis=1
    )

    return df


def record_consumption(
    drum_id, quantity, shift, operator,
    vehicles, remarks, production_date
):
    drums = st.session_state.drums
    matches = drums.index[drums["Drum ID"] == drum_id]

    if len(matches) == 0:
        st.error("Selected drum was not found.")
        return False

    idx = matches[0]
    available = float(drums.at[idx, "Remaining (kg)"])

    if quantity <= 0:
        st.error("Consumption must be greater than zero.")
        return False

    if quantity > available:
        st.error(
            f"Insufficient stock. Only {available:.2f} kg is available."
        )
        return False

    # Deduct material from the selected drum.
    st.session_state.drums.at[idx, "Remaining (kg)"] = (
        available - quantity
    )

    consumption_row = {
        "Date": production_date,
        "Drum ID": drum_id,
        "Shift": shift,
        "Operator": operator,
        "Vehicles Produced": int(vehicles),
        "Quantity (kg)": float(quantity),
        "Remarks": remarks
    }

    st.session_state.consumption = pd.concat(
        [
            st.session_state.consumption,
            pd.DataFrame([consumption_row])
        ],
        ignore_index=True
    )

    log_transaction(
        drum_id,
        "Material Issued",
        quantity,
        shift,
        operator,
        remarks or "Production consumption"
    )

    return True


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.title("🏭 SEALER OPS")
    st.caption("AUTOMOTIVE BODY SHOP")
    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Overview",
            "Drum Inventory",
            "Consumption",
            "Sensor Monitoring",
            "Transactions",
            "Reports"
        ]
    )

    st.divider()
    st.caption("SIMULATION MODE")
    st.caption("No physical sensors or SAP connected.")


# ---------------- CALCULATIONS ----------------

inventory = current_inventory()
consumption = st.session_state.consumption.copy()
transactions = st.session_state.transactions.copy()

total_stock = (
    float(inventory["Remaining (kg)"].sum())
    if not inventory.empty else 0.0
)

today = date.today()

if not consumption.empty:
    consumption["Date"] = pd.to_datetime(
        consumption["Date"]
    ).dt.date

    today_consumption = float(
        consumption.loc[
            consumption["Date"] == today,
            "Quantity (kg)"
        ].sum()
    )
else:
    today_consumption = 0.0

avg_daily = (
    float(consumption.groupby("Date")["Quantity (kg)"].sum().mean())
    if not consumption.empty else 0.0
)

stock_days = total_stock / avg_daily if avg_daily > 0 else 0


# ---------------- HEADER ----------------

st.markdown("""
<div style="
background: linear-gradient(110deg,#14283e,#087f8c);
padding: 25px;
border-radius: 16px;
color: white;
margin-bottom: 22px;">
<h1 style="color:white;margin-bottom:8px;">
DIGITAL SEALER INVENTORY MONITORING
</h1>
<p style="color:#e0f2f5;margin:0;">
Automotive Manufacturing | Body Shop | Sealer Storage Area
</p>
<p style="
display:inline-block;
background:#ffdb8a;
color:#47320a;
padding:5px 10px;
border-radius:20px;
font-size:12px;
font-weight:bold;">
SIMULATION MODE
</p>
</div>
""", unsafe_allow_html=True)


# ---------------- OVERVIEW ----------------

if page == "Overview":
    st.subheader("Operations Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Registered Drums", len(inventory))
    c2.metric("Available Stock", f"{total_stock:.1f} kg")
    c3.metric("Today's Consumption", f"{today_consumption:.1f} kg")
    c4.metric("Estimated Stock Cover", f"{stock_days:.1f} days")

    st.divider()

    left, right = st.columns([1.4, 1])

    with left:
        st.subheader("Stock by Drum")

        if not inventory.empty:
            fig = px.bar(
                inventory,
                x="Drum ID",
                y="Remaining (kg)",
                color="Status",
                text="Remaining (kg)",
                color_discrete_map={
                    "Full": "#15966b",
                    "In Use": "#2878b5",
                    "Low Stock": "#e5a126",
                    "Empty": "#929eab"
                }
            )
            fig.update_layout(
                height=350,
                plot_bgcolor="white",
                paper_bgcolor="white"
            )
            st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Stock Alerts")

        low_stock = inventory[
            inventory["Status"].isin(["Low Stock", "Empty"])
        ]

        if low_stock.empty:
            st.success("All drums are above the low-stock threshold.")
        else:
            for _, row in low_stock.iterrows():
                st.warning(
                    f"{row['Drum ID']}: "
                    f"{row['Remaining (kg)']:.1f} kg remaining"
                )

        st.info(
            "Consumption recorded in the Consumption section "
            "automatically reduces physical inventory."
        )

    st.subheader("Recent Transactions")
    st.dataframe(
        transactions.head(10),
        use_container_width=True,
        hide_index=True
    )


# ---------------- DRUM INVENTORY ----------------

elif page == "Drum Inventory":
    st.subheader("Drum Inventory Management")

    st.dataframe(
        inventory,
        use_container_width=True,
        hide_index=True
    )

    st.divider()
    st.subheader("Add New Drum")

    with st.form("add_drum_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)

        drum_id = c1.text_input("Drum ID")
        sealer_type = c2.selectbox(
            "Sealer Type", ["PVC", "PU", "Wax", "Silicone", "Other"]
        )
        location = c3.text_input("Storage Location")

        c1, c2, c3 = st.columns(3)

        capacity = c1.number_input(
            "Capacity (kg)", min_value=1.0, value=200.0
        )
        tare = c2.number_input(
            "Empty Drum Tare (kg)", min_value=0.0, value=18.0
        )
        remaining = c3.number_input(
            "Initial Sealer Quantity (kg)",
            min_value=0.0,
            value=200.0
        )

        submitted = st.form_submit_button(
            "Add Drum", type="primary"
        )

        if submitted:
            existing = st.session_state.drums["Drum ID"].tolist()

            if not drum_id.strip():
                st.error("Please enter a drum ID.")
            elif drum_id.strip() in existing:
                st.error("This drum ID already exists.")
            elif remaining > capacity:
                st.error("Remaining quantity cannot exceed capacity.")
            else:
                new_drum = {
                    "Drum ID": drum_id.strip(),
                    "Sealer Type": sealer_type,
                    "Capacity (kg)": float(capacity),
                    "Tare (kg)": float(tare),
                    "Remaining (kg)": float(remaining),
                    "Location": location.strip() or "Unassigned"
                }

                st.session_state.drums = pd.concat(
                    [
                        st.session_state.drums,
                        pd.DataFrame([new_drum])
                    ],
                    ignore_index=True
                )

                log_transaction(
                    drum_id.strip(),
                    "Opening Stock",
                    remaining,
                    "General",
                    "Store Team",
                    "New drum registered"
                )

                st.success("Drum added successfully.")
                st.rerun()

    st.divider()
    st.subheader("Export Inventory")

    st.download_button(
        "Download Inventory CSV",
        inventory.to_csv(index=False).encode("utf-8"),
        file_name="sealer_inventory.csv",
        mime="text/csv"
    )


# ---------------- CONSUMPTION ----------------

elif page == "Consumption":
    st.subheader("Consumption Management")
    st.write(
        "Record actual sealer usage by drum and shift. "
        "Saving a record automatically deducts the quantity from inventory."
    )

    if inventory.empty:
        st.warning("Add a drum before recording consumption.")
    else:
        with st.form("consumption_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)

            drum_id = c1.selectbox(
                "Select Drum",
                inventory["Drum ID"].tolist()
            )

            shift = c2.selectbox(
                "Production Shift", ["A", "B", "C", "General"]
            )

            production_date = c3.date_input(
                "Production Date", value=date.today()
            )

            selected_row = inventory[
                inventory["Drum ID"] == drum_id
            ].iloc[0]

            st.info(
                f"Available stock in {drum_id}: "
                f"{selected_row['Remaining (kg)']:.2f} kg"
            )

            c1, c2, c3 = st.columns(3)

            quantity = c1.number_input(
                "Consumed Quantity (kg)",
                min_value=0.0,
                max_value=float(selected_row["Remaining (kg)"]),
                value=0.0,
                step=0.5
            )

            vehicles = c2.number_input(
                "Vehicles Produced",
                min_value=0,
                value=120,
                step=1
            )

            operator = c3.text_input(
                "Operator Name", value="Production Team"
            )

            remarks = st.text_input(
                "Remarks", placeholder="Optional production notes"
            )

            submitted = st.form_submit_button(
                "Record Consumption & Update Stock",
                type="primary",
                use_container_width=True
            )

            if submitted:
                success = record_consumption(
                    drum_id,
                    float(quantity),
                    shift,
                    operator.strip() or "Production Team",
                    int(vehicles),
                    remarks,
                    production_date
                )

                if success:
                    st.success(
                        f"{quantity:.2f} kg recorded for {drum_id}. "
                        "Inventory has been updated."
                    )
                    st.rerun()

    st.divider()
    st.subheader("Consumption Summary")

    consumption = st.session_state.consumption.copy()

    if consumption.empty:
        st.info("No consumption records yet. Add your first record above.")
    else:
        total_consumed = float(consumption["Quantity (kg)"].sum())

        c1, c2, c3 = st.columns(3)

        c1.metric("Total Consumption", f"{total_consumed:.1f} kg")
        c2.metric("Consumption Records", len(consumption))

        total_vehicles = int(consumption["Vehicles Produced"].sum())
        kg_per_vehicle = (
            total_consumed / total_vehicles
            if total_vehicles > 0 else 0
        )

        c3.metric("Average per Vehicle", f"{kg_per_vehicle:.3f} kg")

        left, right = st.columns(2)

        with left:
            daily = (
                consumption.groupby("Date", as_index=False)["Quantity (kg)"]
                .sum()
                .sort_values("Date")
            )

            fig = px.line(
                daily,
                x="Date",
                y="Quantity (kg)",
                markers=True,
                title="Daily Consumption Trend"
            )
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white"
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            shift_data = (
                consumption.groupby("Shift", as_index=False)["Quantity (kg)"]
                .sum()
            )

            fig = px.pie(
                shift_data,
                names="Shift",
                values="Quantity (kg)",
                title="Shift-wise Consumption"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Consumption History")

        st.dataframe(
            consumption.sort_values("Date", ascending=False),
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Consumption CSV",
            consumption.to_csv(index=False).encode("utf-8"),
            file_name="consumption_report.csv",
            mime="text/csv"
        )


# ---------------- SENSOR MONITORING ----------------

elif page == "Sensor Monitoring":
    st.subheader("Simulated Load Cell Monitoring")

    st.warning(
        "SIMULATION ONLY — No physical sensor or industrial hardware is connected."
    )

    if inventory.empty:
        st.info("Add a drum to begin monitoring.")
    else:
        drum_id = st.selectbox(
            "Select Drum",
            inventory["Drum ID"].tolist(),
            key="sensor_drum"
        )

        row = inventory[inventory["Drum ID"] == drum_id].iloc[0]
        actual = float(row["Remaining (kg)"])

        simulated = max(
            0.0,
            actual + random.uniform(-0.8, 0.8)
        )

        history = st.session_state.sensor_history.setdefault(
            drum_id, []
        )

        history.append({
            "Time": datetime.now(),
            "Simulated Reading (kg)": simulated
        })

        st.session_state.sensor_history[drum_id] = history[-60:]

        c1, c2, c3 = st.columns(3)

        c1.metric("Actual Recorded Stock", f"{actual:.2f} kg")
        c2.metric("Simulated Sensor Reading", f"{simulated:.2f} kg")
        c3.metric("Drum Status", row["Status"])

        chart_data = pd.DataFrame(
            st.session_state.sensor_history[drum_id]
        )

        fig = px.line(
            chart_data,
            x="Time",
            y="Simulated Reading (kg)",
            markers=True,
            title=f"Simulated Weight Trend — {drum_id}"
        )

        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white"
        )

        st.plotly_chart(fig, use_container_width=True)

        if st.button("Refresh Simulated Reading"):
            st.rerun()

        st.caption(
            "Readings change when refreshed. They do not change the actual "
            "inventory quantity. Consumption records update inventory."
        )


# ---------------- TRANSACTIONS ----------------

elif page == "Transactions":
    st.subheader("Transaction History")

    transactions = st.session_state.transactions.copy()

    if transactions.empty:
        st.info("No transactions recorded yet.")
    else:
        types = sorted(transactions["Type"].dropna().unique())

        selected_types = st.multiselect(
            "Filter by Transaction Type",
            types,
            default=types
        )

        filtered = transactions[
            transactions["Type"].isin(selected_types)
        ]

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Transactions CSV",
            filtered.to_csv(index=False).encode("utf-8"),
            file_name="sealer_transactions.csv",
            mime="text/csv"
        )


# ---------------- REPORTS ----------------

elif page == "Reports":
    st.subheader("Inventory & Consumption Reports")

    inventory = current_inventory()
    consumption = st.session_state.consumption.copy()

    st.markdown("### Inventory Report")

    st.dataframe(
        inventory,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Export Inventory CSV",
        inventory.to_csv(index=False).encode("utf-8"),
        file_name="inventory_report.csv",
        mime="text/csv"
    )

    st.divider()
    st.markdown("### Low Stock Report")

    low_stock = inventory[
        inventory["Status"].isin(["Low Stock", "Empty"])
    ]

    if low_stock.empty:
        st.success("No low-stock drums.")
    else:
        st.dataframe(
            low_stock,
            use_container_width=True,
            hide_index=True
        )

    st.download_button(
        "Export Low Stock CSV",
        low_stock.to_csv(index=False).encode("utf-8"),
        file_name="low_stock_report.csv",
        mime="text/csv"
    )

    st.divider()
    st.markdown("### Consumption Report")

    if consumption.empty:
        st.info("No consumption records available.")
    else:
        st.dataframe(
            consumption,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Export Consumption CSV",
            consumption.to_csv(index=False).encode("utf-8"),
            file_name="consumption_report.csv",
            mime="text/csv"
        )


# ---------------- FOOTER ----------------

st.divider()

st.caption(
    "DIGITAL SEALER INVENTORY MONITORING SYSTEM | "
    "SIMULATION MODE | NO PHYSICAL SENSOR OR SAP CONNECTION"
)
