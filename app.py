
import random
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Sealer Inventory | Operations",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#17324D"
TEAL = "#087F8C"
MUTED = "#64748B"
BORDER = "#DCE4EC"
RED = "#C2413B"
AMBER = "#B7791F"
GREEN = "#237A57"


# =========================================================
# PROFESSIONAL STYLING
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background: #F5F7FA;
        color: #1E293B;
    }

    [data-testid="stSidebar"] {
        background: #17324D;
    }

    [data-testid="stSidebar"] * {
        color: #F8FAFC;
    }

    [data-testid="stSidebar"] input {
        background: #FFFFFF !important;
        color: #17324D !important;
        -webkit-text-fill-color: #17324D !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] * {
        color: #17324D;
    }

    .page-title {
        font-size: 29px;
        font-weight: 750;
        letter-spacing: -0.7px;
        color: #17324D;
        margin-bottom: 2px;
    }

    .page-subtitle {
        font-size: 14px;
        color: #64748B;
        margin-bottom: 22px;
    }

    .eyebrow {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: #087F8C;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .section-heading {
        font-size: 19px;
        font-weight: 700;
        color: #17324D;
        margin-top: 12px;
        margin-bottom: 5px;
    }

    .section-caption {
        font-size: 13px;
        color: #64748B;
        margin-bottom: 14px;
    }

    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #DCE4EC;
        border-radius: 8px;
        padding: 15px 17px;
    }

    [data-testid="stMetricLabel"] {
        color: #64748B;
    }

    [data-testid="stMetricValue"] {
        color: #17324D;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #DCE4EC;
        border-radius: 7px;
        overflow: hidden;
    }

    div.stButton > button[kind="primary"],
    div.stFormSubmitButton > button[kind="primary"] {
        background: #087F8C;
        border-color: #087F8C;
        color: #FFFFFF;
    }

    hr {
        border-color: #DCE4EC;
    }

    #MainMenu, footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SESSION DATA
# =========================================================
def initialize_data():
    if "drums" not in st.session_state:
        st.session_state.drums = [
            {
                "Drum ID": "SD-001",
                "Sealer Type": "Sealer A",
                "Capacity (kg)": 200.0,
                "Remaining (kg)": 145.0,
                "Location": "Zone A",
                "Last Updated": datetime.now(),
            },
            {
                "Drum ID": "SD-002",
                "Sealer Type": "Sealer B",
                "Capacity (kg)": 200.0,
                "Remaining (kg)": 42.0,
                "Location": "Zone A",
                "Last Updated": datetime.now(),
            },
            {
                "Drum ID": "SD-003",
                "Sealer Type": "Sealer A",
                "Capacity (kg)": 180.0,
                "Remaining (kg)": 110.0,
                "Location": "Zone B",
                "Last Updated": datetime.now(),
            },
            {
                "Drum ID": "SD-004",
                "Sealer Type": "Sealer C",
                "Capacity (kg)": 150.0,
                "Remaining (kg)": 18.0,
                "Location": "Zone B",
                "Last Updated": datetime.now(),
            },
            {
                "Drum ID": "SD-005",
                "Sealer Type": "Sealer B",
                "Capacity (kg)": 200.0,
                "Remaining (kg)": 175.0,
                "Location": "Zone C",
                "Last Updated": datetime.now(),
            },
        ]

    if "transactions" not in st.session_state:
        st.session_state.transactions = []

    if "threshold" not in st.session_state:
        st.session_state.threshold = 20.0

    if "next_drum_number" not in st.session_state:
        st.session_state.next_drum_number = 6

    if "simulated_sap_stock" not in st.session_state:
        st.session_state.simulated_sap_stock = 750.0

    if "sensor_history" not in st.session_state:
        st.session_state.sensor_history = {}


initialize_data()


# =========================================================
# DATA FUNCTIONS
# =========================================================
def current_drums():
    columns = [
        "Drum ID",
        "Sealer Type",
        "Capacity (kg)",
        "Remaining (kg)",
        "Location",
        "Last Updated",
    ]
    return pd.DataFrame(st.session_state.drums, columns=columns)


def stock_status(remaining, threshold):
    if remaining <= 0:
        return "Empty"
    if remaining <= threshold:
        return "Critical"
    if remaining <= threshold * 2:
        return "Low"
    return "Healthy"


def get_stock_report():
    report = current_drums()

    report["Status"] = report["Remaining (kg)"].apply(
        lambda value: stock_status(
            value, st.session_state.threshold
        )
    )

    report["Stock Level (%)"] = (
        report["Remaining (kg)"]
        .div(
            report["Capacity (kg)"].where(
                report["Capacity (kg)"] > 0
            )
        )
        .mul(100)
        .fillna(0)
        .round(1)
    )

    return report


def transactions_df():
    columns = [
        "Timestamp",
        "Drum ID",
        "Sealer Type",
        "Quantity Used (kg)",
        "Shift",
        "Notes",
    ]
    return pd.DataFrame(
        st.session_state.transactions,
        columns=columns,
    )


def record_transaction(drum_id, quantity, shift, notes):
    if quantity <= 0:
        st.error("Quantity must be greater than zero.")
        return False

    for drum in st.session_state.drums:
        if drum["Drum ID"] == drum_id:
            if quantity > drum["Remaining (kg)"]:
                st.error("Quantity exceeds available stock.")
                return False

            drum["Remaining (kg)"] = round(
                drum["Remaining (kg)"] - quantity, 2
            )
            drum["Last Updated"] = datetime.now()

            st.session_state.transactions.append({
                "Timestamp": datetime.now(),
                "Drum ID": drum_id,
                "Sealer Type": drum["Sealer Type"],
                "Quantity Used (kg)": float(quantity),
                "Shift": shift,
                "Notes": notes,
            })
            return True

    st.error("Drum not found.")
    return False


def download_csv(df, filename, label):
    st.download_button(
        label=label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def heading(title, description=None):
    st.markdown(
        f'<div class="section-heading">{title}</div>',
        unsafe_allow_html=True,
    )
    if description:
        st.markdown(
            f'<div class="section-caption">{description}</div>',
            unsafe_allow_html=True,
        )


# =========================================================
# LIVE SENSOR CHART
# =========================================================
@st.fragment(run_every="2s")
def live_sensor_chart():
    if not st.session_state.drums:
        st.info("Add a drum to start monitoring.")
        return

    drum_ids = [
        drum["Drum ID"] for drum in st.session_state.drums
    ]

    selected_id = st.selectbox(
        "Select monitored drum",
        drum_ids,
        key="sensor_drum_select",
    )

    drum = next(
        item for item in st.session_state.drums
        if item["Drum ID"] == selected_id
    )

    actual_weight = float(drum["Remaining (kg)"])
    capacity = float(drum["Capacity (kg)"])

    history = st.session_state.sensor_history.setdefault(
        selected_id, []
    )

    # Measurement noise is simulated; inventory is not changed.
    reading = max(
        0.0,
        actual_weight + random.uniform(-0.8, 0.8),
    )

    history.append({
        "Time": datetime.now(),
        "Weight (kg)": round(reading, 2),
    })

    st.session_state.sensor_history[selected_id] = history[-60:]

    sensor_df = pd.DataFrame(
        st.session_state.sensor_history[selected_id]
    )

    left, middle, right = st.columns(3)

    left.metric("Sensor Reading", f"{reading:.2f} kg")
    middle.metric("Recorded Inventory", f"{actual_weight:.2f} kg")
    right.metric("Drum Capacity", f"{capacity:.1f} kg")

    fig = px.line(
        sensor_df,
        x="Time",
        y="Weight (kg)",
        template="plotly_white",
    )

    fig.update_traces(
        line=dict(color=TEAL, width=2.5),
        marker=dict(size=4),
    )

    # Keep the scale focused enough to see sensor variation.
    low = max(0, actual_weight - 3)
    high = max(actual_weight + 3, low + 1)

    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=15, b=10),
        xaxis_title=None,
        yaxis_title="Weight (kg)",
        yaxis=dict(range=[low, high]),
        showlegend=False,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"sensor_chart_{selected_id}",
    )

    threshold = st.session_state.threshold

    if actual_weight <= threshold:
        st.error(
            f"Critical stock: {selected_id} has "
            f"{actual_weight:.1f} kg remaining."
        )
    elif actual_weight <= threshold * 2:
        st.warning(
            f"Low stock: {selected_id} has "
            f"{actual_weight:.1f} kg remaining."
        )

    st.caption(
        "Simulation only. Random fluctuations represent sensor noise; "
        "connect a real load cell for actual measurements."
    )


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("## SEALER MONITOR")
    st.caption("BODY SHOP  /  MATERIAL OPERATIONS")
    st.divider()

    page = st.radio(
        "WORKSPACE",
        [
            "Overview",
            "Inventory",
            "Consumption",
            "Transactions",
            "Reports",
        ],
        label_visibility="visible",
    )

    st.divider()
    st.markdown("### Monitoring settings")

    st.session_state.threshold = st.number_input(
        "Critical stock threshold (kg)",
        min_value=0.0,
        max_value=500.0,
        value=float(st.session_state.threshold),
        step=5.0,
    )

    st.divider()
    st.caption("DEMO ENVIRONMENT")
    st.caption("Sensor status: Simulation active")


# =========================================================
# PAGE HEADER
# =========================================================
st.markdown(
    '<div class="eyebrow">INDUSTRIAL OPERATIONS / INVENTORY CONTROL</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="page-title">Digital Sealer Inventory</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="page-subtitle">'
    'Automotive Body Shop · Material monitoring and consumption control'
    '</div>',
    unsafe_allow_html=True,
)

report = get_stock_report()
tx = transactions_df()

total_capacity = float(report["Capacity (kg)"].sum())
total_stock = float(report["Remaining (kg)"].sum())
total_used = (
    float(tx["Quantity Used (kg)"].sum())
    if not tx.empty else 0.0
)

critical_count = int(
    report["Status"].isin(["Critical", "Empty"]).sum()
)
low_count = int((report["Status"] == "Low").sum())


# =========================================================
# OVERVIEW
# =========================================================
if page == "Overview":
    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Registered Drums", len(report))
    k2.metric("Available Material", f"{total_stock:,.1f} kg")
    k3.metric("Recorded Consumption", f"{total_used:,.1f} kg")
    k4.metric("Critical / Empty Drums", critical_count)

    st.divider()

    heading(
        "Live monitoring",
        "Simulated load-cell readings for the selected drum.",
    )
    live_sensor_chart()

    st.divider()

    heading(
        "Inventory position",
        "Remaining stock by drum and sealer type.",
    )

    chart_col, table_col = st.columns([1, 1.25])

    with chart_col:
        if not report.empty:
            fig = px.bar(
                report,
                x="Drum ID",
                y="Remaining (kg)",
                color="Sealer Type",
                template="plotly_white",
            )
            fig.update_layout(
                height=330,
                margin=dict(l=5, r=5, t=15, b=5),
                xaxis_title=None,
                legend_title=None,
            )
            st.plotly_chart(fig, use_container_width=True)

    with table_col:
        display_cols = [
            "Drum ID",
            "Sealer Type",
            "Remaining (kg)",
            "Stock Level (%)",
            "Status",
        ]
        st.dataframe(
            report[display_cols],
            use_container_width=True,
            hide_index=True,
        )

    if critical_count:
        st.error(
            f"{critical_count} drum(s) require immediate stock review."
        )
    elif low_count:
        st.warning(
            f"{low_count} drum(s) are approaching the critical threshold."
        )
    else:
        st.success("All drums are above the low-stock range.")

    with st.expander("Simulated SAP comparison"):
        a, b, c = st.columns(3)
        a.metric("Inventory Total", f"{total_stock:,.1f} kg")
        b.metric(
            "Simulated SAP Stock",
            f"{st.session_state.simulated_sap_stock:,.1f} kg",
        )
        c.metric(
            "Difference",
            f"{total_stock - st.session_state.simulated_sap_stock:,.1f} kg",
        )

        new_sap = st.number_input(
            "Update simulated SAP stock (kg)",
            min_value=0.0,
            value=float(st.session_state.simulated_sap_stock),
            step=10.0,
            key="new_sap_stock",
        )

        if st.button("Save reference stock"):
            st.session_state.simulated_sap_stock = new_sap
            st.rerun()


# =========================================================
# INVENTORY
# =========================================================
elif page == "Inventory":
    heading(
        "Drum inventory",
        "Manage registered drums and their storage locations.",
    )

    search = st.text_input(
        "Search inventory",
        placeholder="Enter drum ID, sealer type or location",
    )

    inventory = get_stock_report()

    if search:
        mask = (
            inventory["Drum ID"].astype(str).str.contains(
                search, case=False, na=False
            )
            | inventory["Sealer Type"].astype(str).str.contains(
                search, case=False, na=False
            )
            | inventory["Location"].astype(str).str.contains(
                search, case=False, na=False
            )
        )
        inventory = inventory[mask]

    st.dataframe(
        inventory,
        use_container_width=True,
        hide_index=True,
    )

    download_csv(
        inventory,
        "sealer_inventory.csv",
        "Export inventory CSV",
    )

    st.divider()

    add_tab, edit_tab, remove_tab = st.tabs(
        ["Add drum", "Edit drum", "Remove empty drum"]
    )

    with add_tab:
        with st.form("add_drum", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                new_type = st.selectbox(
                    "Sealer type",
                    ["Sealer A", "Sealer B", "Sealer C", "Other"],
                )
                capacity = st.number_input(
                    "Capacity (kg)", min_value=1.0, value=200.0
                )

            with col2:
                remaining = st.number_input(
                    "Initial stock (kg)", min_value=0.0, value=200.0
                )
                location = st.selectbox(
                    "Storage location",
                    ["Zone A", "Zone B", "Zone C", "Production Line", "Other"],
                )

            submitted = st.form_submit_button(
                "Add drum", type="primary"
            )

            if submitted:
                if remaining > capacity:
                    st.error("Initial stock cannot exceed capacity.")
                else:
                    drum_id = (
                        f"SD-{st.session_state.next_drum_number:03d}"
                    )

                    st.session_state.drums.append({
                        "Drum ID": drum_id,
                        "Sealer Type": new_type,
                        "Capacity (kg)": float(capacity),
                        "Remaining (kg)": float(remaining),
                        "Location": location,
                        "Last Updated": datetime.now(),
                    })

                    st.session_state.next_drum_number += 1
                    st.success(f"{drum_id} added.")
                    st.rerun()

    with edit_tab:
        if not st.session_state.drums:
            st.info("No drums available.")
        else:
            ids = [
                drum["Drum ID"] for drum in st.session_state.drums
            ]
            edit_id = st.selectbox("Select drum", ids)
            selected = next(
                drum for drum in st.session_state.drums
                if drum["Drum ID"] == edit_id
            )

            types = ["Sealer A", "Sealer B", "Sealer C", "Other"]
            locations = [
                "Zone A", "Zone B", "Zone C",
                "Production Line", "Other",
            ]

            with st.form("edit_drum"):
                col1, col2 = st.columns(2)

                with col1:
                    current_type = selected["Sealer Type"]
                    type_index = (
                        types.index(current_type)
                        if current_type in types else 3
                    )
                    edit_type = st.selectbox(
                        "Sealer type", types, index=type_index
                    )
                    edit_capacity = st.number_input(
                        "Capacity (kg)",
                        min_value=1.0,
                        value=max(
                            1.0, float(selected["Capacity (kg)"])
                        ),
                    )

                with col2:
                    edit_remaining = st.number_input(
                        "Remaining stock (kg)",
                        min_value=0.0,
                        value=float(selected["Remaining (kg)"]),
                    )
                    current_location = selected["Location"]
                    location_index = (
                        locations.index(current_location)
                        if current_location in locations else 0
                    )
                    edit_location = st.selectbox(
                        "Location", locations, index=location_index
                    )

                save = st.form_submit_button(
                    "Save changes", type="primary"
                )

                if save:
                    if edit_remaining > edit_capacity:
                        st.error("Stock cannot exceed capacity.")
                    else:
                        selected["Sealer Type"] = edit_type
                        selected["Capacity (kg)"] = float(edit_capacity)
                        selected["Remaining (kg)"] = float(edit_remaining)
                        selected["Location"] = edit_location
                        selected["Last Updated"] = datetime.now()
                        st.success("Drum updated.")
                        st.rerun()

    with remove_tab:
        if not st.session_state.drums:
            st.info("No drums available.")
        else:
            remove_id = st.selectbox(
                "Select empty drum",
                [
                    drum["Drum ID"]
                    for drum in st.session_state.drums
                ],
                key="remove_id",
            )

            selected = next(
                drum for drum in st.session_state.drums
                if drum["Drum ID"] == remove_id
            )

            st.write(
                f"Remaining stock: {selected['Remaining (kg)']:.1f} kg"
            )

            confirmed = st.checkbox(
                "Confirm removal", key="confirm_remove"
            )

            if st.button("Remove drum", type="primary"):
                if not confirmed:
                    st.warning("Confirm removal first.")
                elif selected["Remaining (kg)"] > 0:
                    st.error(
                        "Only empty drums can be removed."
                    )
                else:
                    st.session_state.drums = [
                        drum for drum in st.session_state.drums
                        if drum["Drum ID"] != remove_id
                    ]
                    st.session_state.sensor_history.pop(remove_id, None)
                    st.success("Drum removed.")
                    st.rerun()


# =========================================================
# CONSUMPTION
# =========================================================
elif page == "Consumption":
    heading(
        "Record consumption",
        "Record sealer material used during each production shift.",
    )

    available = [
        drum for drum in st.session_state.drums
        if drum["Remaining (kg)"] > 0
    ]

    if not available:
        st.info("No drums have available stock.")
    else:
        with st.form("consumption_form"):
            drum_id = st.selectbox(
                "Drum ID",
                [drum["Drum ID"] for drum in available],
            )

            selected = next(
                drum for drum in available
                if drum["Drum ID"] == drum_id
            )

            st.caption(
                f"{selected['Sealer Type']} · "
                f"Available stock: {selected['Remaining (kg)']:.1f} kg"
            )

            quantity_mode = st.radio(
                "Quantity",
                ["5 kg", "10 kg", "20 kg", "Custom"],
                horizontal=True,
            )

            if quantity_mode == "Custom":
                quantity = st.number_input(
                    "Quantity used (kg)",
                    min_value=0.1,
                    max_value=float(selected["Remaining (kg)"]),
                    value=min(
                        5.0, float(selected["Remaining (kg)"])
                    ),
                )
            else:
                quantity = float(
                    quantity_mode.replace(" kg", "")
                )

            shift = st.selectbox("Shift", ["A", "B", "C"])
            notes = st.text_input("Notes", placeholder="Optional")

            submitted = st.form_submit_button(
                "Record consumption", type="primary"
            )

            if submitted:
                if record_transaction(
                    drum_id, quantity, shift, notes
                ):
                    st.success("Consumption recorded.")
                    st.rerun()

    st.divider()

    tx = transactions_df()

    heading("Consumption analysis")

    if tx.empty:
        st.info("Consumption charts will appear after transactions are recorded.")
    else:
        left, right = st.columns(2)

        with left:
            by_drum = (
                tx.groupby("Drum ID", as_index=False)
                ["Quantity Used (kg)"]
                .sum()
            )
            fig = px.bar(
                by_drum,
                x="Drum ID",
                y="Quantity Used (kg)",
                template="plotly_white",
            )
            fig.update_layout(
                height=320,
                margin=dict(l=5, r=5, t=15, b=5),
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            by_shift = (
                tx.groupby("Shift", as_index=False)
                ["Quantity Used (kg)"]
                .sum()
            )
            fig = px.pie(
                by_shift,
                names="Shift",
                values="Quantity Used (kg)",
                hole=0.55,
                template="plotly_white",
            )
            fig.update_layout(
                height=320,
                margin=dict(l=5, r=5, t=15, b=5),
            )
            st.plotly_chart(fig, use_container_width=True)


# =========================================================
# TRANSACTIONS
# =========================================================
elif page == "Transactions":
    heading(
        "Transaction history",
        "Review and export recorded material consumption.",
    )

    tx = transactions_df()

    if tx.empty:
        st.info("No transactions recorded yet.")
    else:
        c1, c2 = st.columns(2)

        with c1:
            drum_filter = st.selectbox(
                "Drum",
                ["All"] + sorted(tx["Drum ID"].unique().tolist()),
            )

        with c2:
            shift_filter = st.selectbox(
                "Shift",
                ["All", "A", "B", "C"],
            )

        filtered = tx.copy()

        if drum_filter != "All":
            filtered = filtered[filtered["Drum ID"] == drum_filter]

        if shift_filter != "All":
            filtered = filtered[filtered["Shift"] == shift_filter]

        filtered = filtered.sort_values(
            "Timestamp", ascending=False
        )

        st.metric(
            "Filtered consumption",
            f"{filtered['Quantity Used (kg)'].sum():,.1f} kg",
        )

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
        )

        download_csv(
            filtered,
            "sealer_transactions.csv",
            "Export transactions CSV",
        )


# =========================================================
# REPORTS
# =========================================================
elif page == "Reports":
    heading(
        "Reports and exports",
        "Generate inventory summaries and date-filtered consumption reports.",
    )

    report = get_stock_report()
    tx = transactions_df()

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Total capacity",
        f"{report['Capacity (kg)'].sum():,.1f} kg",
    )
    c2.metric(
        "Remaining stock",
        f"{report['Remaining (kg)'].sum():,.1f} kg",
    )

    capacity_total = report["Capacity (kg)"].sum()
    utilized = (
        (
            capacity_total - report["Remaining (kg)"].sum()
        ) / capacity_total * 100
        if capacity_total > 0 else 0
    )

    c3.metric("Capacity utilized", f"{utilized:.1f}%")

    st.subheader("Inventory report")
    st.dataframe(
        report,
        use_container_width=True,
        hide_index=True,
    )

    download_csv(
        report,
        "sealer_stock_report.csv",
        "Export inventory report",
    )

    st.divider()
    st.subheader("Consumption report")

    if tx.empty:
        st.info("No consumption records are available.")
    else:
        tx["Timestamp"] = pd.to_datetime(
            tx["Timestamp"], errors="coerce"
        )

        valid = tx["Timestamp"].dropna()

        if valid.empty:
            st.info("No valid transaction dates found.")
        else:
            first_date = valid.min().date()
            last_date = valid.max().date()

            c1, c2 = st.columns(2)

            with c1:
                start_date = st.date_input(
                    "From",
                    value=first_date,
                    key="report_from",
                )

            with c2:
                end_date = st.date_input(
                    "To",
                    value=last_date,
                    key="report_to",
                )

            if start_date > end_date:
                st.error("The start date must not be after the end date.")
            else:
                period = tx[
                    tx["Timestamp"].notna()
                    & (tx["Timestamp"].dt.date >= start_date)
                    & (tx["Timestamp"].dt.date <= end_date)
                ]

                st.metric(
                    "Consumption in selected period",
                    f"{period['Quantity Used (kg)'].sum():,.1f} kg",
                )

                st.dataframe(
                    period,
                    use_container_width=True,
                    hide_index=True,
                )

                download_csv(
                    period,
                    "sealer_consumption_report.csv",
                    "Export consumption report",
                )


# =========================================================
# FOOTER
# =========================================================
st.divider()

st.caption(
    "Digital Sealer Inventory Monitoring System  |  "
    "Prototype environment  |  Simulated sensor and SAP data"
)
