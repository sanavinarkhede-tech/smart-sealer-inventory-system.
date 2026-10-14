
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from io import StringIO

# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Digital Sealer Inventory | Industrial IoT",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# INDUSTRIAL THEME
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f3f6fa;
        color: #172b4d;
    }

    [data-testid="stSidebar"] {
        background-color: #10243a;
    }

    [data-testid="stSidebar"] * {
        color: #ffffff;
    }

    .main-title {
        font-size: 32px;
        font-weight: 800;
        color: #10243a;
        margin-bottom: 2px;
    }

    .subtitle {
        color: #62748a;
        font-size: 14px;
        margin-bottom: 22px;
    }

    .section-title {
        font-size: 21px;
        font-weight: 700;
        color: #10243a;
        margin-top: 12px;
    }

    .status-card {
        background: white;
        padding: 16px;
        border-radius: 12px;
        border-left: 5px solid #11a8a0;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(16, 36, 58, 0.06);
    }

    .small-note {
        color: #62748a;
        font-size: 12px;
    }

    div[data-testid="stMetric"] {
        background: #ffffff;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e3eaf2;
    }

    div.stButton > button[kind="primary"] {
        background-color: #087f8c;
        border-color: #087f8c;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# INITIAL DEMO DATA
# =========================================================
def initialize_data():
    if "drums" not in st.session_state:
        st.session_state.drums = [
            {
                "Drum ID": "SD-001",
                "Sealer Type": "Sealer A",
                "Capacity (kg)": 200.0,
                "Remaining (kg)": 145.0,
                "Location": "Storage Zone A",
                "Last Updated": datetime.now(),
            },
            {
                "Drum ID": "SD-002",
                "Sealer Type": "Sealer B",
                "Capacity (kg)": 200.0,
                "Remaining (kg)": 42.0,
                "Location": "Storage Zone A",
                "Last Updated": datetime.now(),
            },
            {
                "Drum ID": "SD-003",
                "Sealer Type": "Sealer A",
                "Capacity (kg)": 180.0,
                "Remaining (kg)": 110.0,
                "Location": "Storage Zone B",
                "Last Updated": datetime.now(),
            },
            {
                "Drum ID": "SD-004",
                "Sealer Type": "Sealer C",
                "Capacity (kg)": 150.0,
                "Remaining (kg)": 18.0,
                "Location": "Storage Zone B",
                "Last Updated": datetime.now(),
            },
            {
                "Drum ID": "SD-005",
                "Sealer Type": "Sealer B",
                "Capacity (kg)": 200.0,
                "Remaining (kg)": 175.0,
                "Location": "Storage Zone C",
                "Last Updated": datetime.now(),
            },
        ]

    if "transactions" not in st.session_state:
        st.session_state.transactions = [
            {
                "Timestamp": datetime.now(),
                "Drum ID": "SD-001",
                "Sealer Type": "Sealer A",
                "Quantity Used (kg)": 10.0,
                "Shift": "A",
                "Notes": "Demo consumption record",
            }
        ]

    if "threshold" not in st.session_state:
        st.session_state.threshold = 20.0

    if "simulated_sap_stock" not in st.session_state:
        st.session_state.simulated_sap_stock = 750.0

    if "next_drum_number" not in st.session_state:
        st.session_state.next_drum_number = 6


initialize_data()

# =========================================================
# DATA HELPERS
# =========================================================
def current_drums():
    """Return current inventory as a DataFrame."""
    columns = [
        "Drum ID",
        "Sealer Type",
        "Capacity (kg)",
        "Remaining (kg)",
        "Location",
        "Last Updated",
    ]

    return pd.DataFrame(
        st.session_state.drums,
        columns=columns,
    )


def stock_status(remaining, threshold):
    """Determine stock status based on remaining quantity."""
    if remaining <= 0:
        return "Empty"
    elif remaining <= threshold:
        return "Critical"
    elif remaining <= threshold * 2:
        return "Low"
    return "Healthy"


def get_stock_report():
    """Create a stock report and safely handle zero-capacity drums."""
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


def record_transaction(
    drum_id,
    quantity,
    shift,
    notes,
):
    """Record consumption and update the selected drum."""
    if quantity <= 0:
        st.error("Consumption quantity must be greater than zero.")
        return False

    for drum in st.session_state.drums:
        if drum["Drum ID"] == drum_id:
            if quantity > drum["Remaining (kg)"]:
                st.error(
                    "Consumption cannot exceed the drum's remaining stock."
                )
                return False

            drum["Remaining (kg)"] = round(
                drum["Remaining (kg)"] - quantity, 2
            )
            drum["Last Updated"] = datetime.now()

            st.session_state.transactions.append(
                {
                    "Timestamp": datetime.now(),
                    "Drum ID": drum["Drum ID"],
                    "Sealer Type": drum["Sealer Type"],
                    "Quantity Used (kg)": float(quantity),
                    "Shift": shift,
                    "Notes": notes,
                }
            )
            return True

    st.error("Selected drum was not found.")
    return False


def transactions_df():
    """Return transaction history as a DataFrame."""
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


def csv_download(df, filename, button_label):
    """Display a CSV download button."""
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=button_label,
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        use_container_width=False,
    )


def section_heading(title, subtitle=None):
    st.markdown(
        f'<div class="section-title">{title}</div>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.caption(subtitle)


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================
with st.sidebar:
    st.markdown("# 🏭 Sealer Monitor")
    st.caption("INDUSTRIAL IoT INVENTORY")
    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Overview",
            "Drum Inventory",
            "Consumption",
            "Transactions",
            "Reports",
        ],
    )

    st.divider()

    st.markdown("### ⚙️ Monitoring Settings")

    st.session_state.threshold = st.number_input(
        "Critical stock threshold (kg)",
        min_value=0.0,
        max_value=500.0,
        value=float(st.session_state.threshold),
        step=5.0,
    )

    st.markdown("---")
    st.markdown("**System status:** 🟢 Online")
    st.caption("Demo mode · Simulated sensor data")

# =========================================================
# HEADER
# =========================================================
st.markdown(
    '<div class="main-title">Digital Sealer Inventory Monitoring</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">'
    'Automotive Body Shop | Drum stock, consumption and inventory visibility'
    '</div>',
    unsafe_allow_html=True,
)

report = get_stock_report()
tx_df = transactions_df()

total_capacity = float(report["Capacity (kg)"].sum())
total_remaining = float(report["Remaining (kg)"].sum())
total_used = float(tx_df["Quantity Used (kg)"].sum()) if not tx_df.empty else 0.0
drum_count = len(report)

critical_count = int(
    report["Status"].isin(["Critical", "Empty"]).sum()
)
low_count = int((report["Status"] == "Low").sum())

# =========================================================
# OVERVIEW DASHBOARD
# =========================================================
if page == "Overview":
    st.subheader("📊 Operations Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Drums",
        drum_count,
        help="Number of drums registered in the inventory.",
    )
    col2.metric(
        "Available Stock",
        f"{total_remaining:,.1f} kg",
    )
    col3.metric(
        "Consumption Recorded",
        f"{total_used:,.1f} kg",
    )
    col4.metric(
        "Critical / Empty",
        critical_count,
        delta=f"{low_count} low stock",
        delta_color="inverse",
    )

    st.divider()

    left, right = st.columns([1.5, 1])

    with left:
        section_heading("📦 Stock by Drum")

        if not report.empty:
            stock_chart = px.bar(
                report,
                x="Drum ID",
                y="Remaining (kg)",
                color="Sealer Type",
                hover_data=[
                    "Capacity (kg)",
                    "Location",
                    "Status",
                ],
                title="Remaining Sealer Material",
                template="plotly_white",
            )
            stock_chart.update_layout(
                margin=dict(l=10, r=10, t=50, b=10),
                legend_title_text="Sealer Type",
            )
            st.plotly_chart(
                stock_chart,
                use_container_width=True,
            )
        else:
            st.info("Add drums to see the stock chart.")

    with right:
        section_heading("🧪 Stock Distribution")

        if total_remaining > 0:
            type_stock = (
                report.groupby("Sealer Type", as_index=False)
                ["Remaining (kg)"]
                .sum()
            )

            pie_chart = px.pie(
                type_stock,
                names="Sealer Type",
                values="Remaining (kg)",
                hole=0.48,
                title="Stock by Sealer Type",
                template="plotly_white",
            )
            pie_chart.update_layout(
                margin=dict(l=10, r=10, t=50, b=10)
            )
            st.plotly_chart(
                pie_chart,
                use_container_width=True,
            )
        else:
            st.info("No stock is currently available.")

    section_heading("🏭 Storage Overview")

    if report.empty:
        st.info("No drums have been registered.")
    else:
        card_columns = st.columns(3)

        for index, drum in report.reset_index(drop=True).iterrows():
            with card_columns[index % 3]:
                status = drum["Status"]

                if status in ["Critical", "Empty"]:
                    status_color = "#dc2626"
                elif status == "Low":
                    status_color = "#d97706"
                else:
                    status_color = "#059669"

                st.markdown(
                    f"""
                    <div class="status-card"
                         style="border-left-color:{status_color}">
                        <b>{drum['Drum ID']}</b><br>
                        <span>{drum['Sealer Type']}</span><br><br>
                        <b>{drum['Remaining (kg)']:.1f} kg</b>
                        / {drum['Capacity (kg)']:.1f} kg<br>
                        <span style="color:{status_color};font-weight:700">
                            {status}
                        </span><br>
                        <span class="small-note">{drum['Location']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.progress(
                    min(
                        max(
                            float(drum["Stock Level (%)"]) / 100,
                            0.0,
                        ),
                        1.0,
                    )
                )

    if critical_count > 0 or low_count > 0:
        st.warning(
            f"Inventory alert: {critical_count} drum(s) are critical or empty, "
            f"and {low_count} drum(s) have low stock."
        )
    else:
        st.success("All drums are above the low-stock threshold.")

    st.divider()

    section_heading("🔄 Physical vs Simulated System Stock")
    sap_col1, sap_col2, sap_col3 = st.columns(3)

    sap_col1.metric(
        "Physical Inventory Total",
        f"{total_remaining:,.1f} kg",
    )
    sap_col2.metric(
        "Simulated SAP Stock",
        f"{st.session_state.simulated_sap_stock:,.1f} kg",
    )
    difference = total_remaining - st.session_state.simulated_sap_stock
    sap_col3.metric(
        "Difference",
        f"{difference:,.1f} kg",
    )

    st.caption(
        "The SAP value is a simulated reference value. "
        "This demo does not connect to a real SAP system or physical load cells."
    )

    with st.expander("Update simulated SAP stock"):
        new_sap_stock = st.number_input(
            "Simulated SAP stock (kg)",
            min_value=0.0,
            value=float(st.session_state.simulated_sap_stock),
            step=10.0,
            key="sap_stock_input",
        )
        if st.button("Update simulated stock"):
            st.session_state.simulated_sap_stock = new_sap_stock
            st.success("Simulated stock updated.")
            st.rerun()

# =========================================================
# DRUM INVENTORY
# =========================================================
elif page == "Drum Inventory":
    section_heading(
        "📋 Drum Inventory",
        "Register, inspect, update and remove drums.",
    )

    search_text = st.text_input(
        "🔍 Search by Drum ID, sealer type or location"
    )

    inventory = get_stock_report()

    if search_text:
        search_mask = (
            inventory["Drum ID"].astype(str).str.contains(
                search_text, case=False, na=False
            )
            | inventory["Sealer Type"].astype(str).str.contains(
                search_text, case=False, na=False
            )
            | inventory["Location"].astype(str).str.contains(
                search_text, case=False, na=False
            )
        )
        inventory = inventory[search_mask]

    st.dataframe(
        inventory,
        use_container_width=True,
        hide_index=True,
    )

    csv_download(
        inventory,
        "sealer_inventory.csv",
        "⬇️ Download Inventory CSV",
    )

    st.divider()

    add_tab, edit_tab, remove_tab = st.tabs(
        ["➕ Add Drum", "✏️ Edit Drum", "🗑️ Remove Drum"]
    )

    with add_tab:
        st.subheader("Register New Drum")

        with st.form("add_drum_form", clear_on_submit=True):
            new_type = st.selectbox(
                "Sealer Type",
                ["Sealer A", "Sealer B", "Sealer C", "Other"],
            )
            new_capacity = st.number_input(
                "Capacity (kg)",
                min_value=0.0,
                value=200.0,
                step=10.0,
            )
            new_remaining = st.number_input(
                "Initial Remaining Stock (kg)",
                min_value=0.0,
                value=200.0,
                step=5.0,
            )
            new_location = st.selectbox(
                "Storage Location",
                [
                    "Storage Zone A",
                    "Storage Zone B",
                    "Storage Zone C",
                    "Production Line",
                    "Other",
                ],
            )

            submitted = st.form_submit_button(
                "➕ Add Drum",
                type="primary",
            )

            if submitted:
                if new_capacity <= 0:
                    st.error("Capacity must be greater than zero.")
                elif new_remaining > new_capacity:
                    st.error(
                        "Remaining stock cannot exceed drum capacity."
                    )
                else:
                    new_id = (
                        f"SD-{st.session_state.next_drum_number:03d}"
                    )

                    st.session_state.drums.append(
                        {
                            "Drum ID": new_id,
                            "Sealer Type": new_type,
                            "Capacity (kg)": float(new_capacity),
                            "Remaining (kg)": float(new_remaining),
                            "Location": new_location,
                            "Last Updated": datetime.now(),
                        }
                    )

                    st.session_state.next_drum_number += 1
                    st.success(f"Drum {new_id} added successfully.")
                    st.rerun()

    with edit_tab:
        st.subheader("Update Drum Details")

        if not st.session_state.drums:
            st.info("No drums are available to edit.")
        else:
            drum_ids = [
                drum["Drum ID"] for drum in st.session_state.drums
            ]

            selected_edit_id = st.selectbox(
                "Select Drum",
                drum_ids,
                key="edit_drum_id",
            )

            selected_drum = next(
                drum for drum in st.session_state.drums
                if drum["Drum ID"] == selected_edit_id
            )

            with st.form("edit_drum_form"):
                edit_type = st.selectbox(
                    "Sealer Type",
                    ["Sealer A", "Sealer B", "Sealer C", "Other"],
                    index=(
                        ["Sealer A", "Sealer B", "Sealer C", "Other"]
                        .index(selected_drum["Sealer Type"])
                        if selected_drum["Sealer Type"]
                        in ["Sealer A", "Sealer B", "Sealer C", "Other"]
                        else 3
                    ),
                )

                edit_capacity = st.number_input(
                    "Capacity (kg)",
                    min_value=0.0,
                    value=float(selected_drum["Capacity (kg)"]),
                    step=10.0,
                )

                edit_remaining = st.number_input(
                    "Remaining Stock (kg)",
                    min_value=0.0,
                    value=float(selected_drum["Remaining (kg)"]),
                    step=5.0,
                )

                edit_location = st.selectbox(
                    "Storage Location",
                    [
                        "Storage Zone A",
                        "Storage Zone B",
                        "Storage Zone C",
                        "Production Line",
                        "Other",
                    ],
                    index=(
                        [
                            "Storage Zone A",
                            "Storage Zone B",
                            "Storage Zone C",
                            "Production Line",
                            "Other",
                        ].index(selected_drum["Location"])
                        if selected_drum["Location"] in [
                            "Storage Zone A",
                            "Storage Zone B",
                            "Storage Zone C",
                            "Production Line",
                            "Other",
                        ]
                        else 0
                    ),
                )

                save_edit = st.form_submit_button(
                    "💾 Save Changes",
                    type="primary",
                )

                if save_edit:
                    if edit_capacity <= 0:
                        st.error("Capacity must be greater than zero.")
                    elif edit_remaining > edit_capacity:
                        st.error(
                            "Remaining stock cannot exceed capacity."
                        )
                    else:
                        selected_drum["Sealer Type"] = edit_type
                        selected_drum["Capacity (kg)"] = float(
                            edit_capacity
                        )
                        selected_drum["Remaining (kg)"] = float(
                            edit_remaining
                        )
                        selected_drum["Location"] = edit_location
                        selected_drum["Last Updated"] = datetime.now()

                        st.success("Drum details updated.")
                        st.rerun()

    with remove_tab:
        st.subheader("Remove Drum")

        if not st.session_state.drums:
            st.info("There are no drums to remove.")
        else:
            remove_id = st.selectbox(
                "Select drum to remove",
                [
                    drum["Drum ID"]
                    for drum in st.session_state.drums
                ],
                key="remove_drum_id",
            )

            remove_record = next(
                drum for drum in st.session_state.drums
                if drum["Drum ID"] == remove_id
            )

            st.write(
                f"Current stock: **{remove_record['Remaining (kg)']:.1f} kg**"
            )

            confirm_remove = st.checkbox(
                "I confirm that I want to remove this drum."
            )

            if st.button(
                "🗑️ Remove Selected Drum",
                type="primary",
            ):
                if not confirm_remove:
                    st.warning("Please confirm the removal first.")
                elif remove_record["Remaining (kg)"] > 0:
                    st.error(
                        "Only empty drums can be removed. "
                        "Record consumption or update the stock first."
                    )
                else:
                    st.session_state.drums = [
                        drum for drum in st.session_state.drums
                        if drum["Drum ID"] != remove_id
                    ]
                    st.success(f"Drum {remove_id} removed.")
                    st.rerun()

# =========================================================
# CONSUMPTION
# =========================================================
elif page == "Consumption":
    section_heading(
        "🧴 Record Sealer Consumption",
        "Record material usage by drum and shift.",
    )

    available_drums = [
        drum for drum in st.session_state.drums
        if drum["Remaining (kg)"] > 0
    ]

    if not available_drums:
        st.warning("No drums have available stock.")
    else:
        with st.form("consumption_form"):
            selected_id = st.selectbox(
                "Select Drum",
                [drum["Drum ID"] for drum in available_drums],
            )

            selected = next(
                drum for drum in available_drums
                if drum["Drum ID"] == selected_id
            )

            st.info(
                f"Sealer: {selected['Sealer Type']} · "
                f"Available stock: {selected['Remaining (kg)']:.1f} kg"
            )

            quick_amount = st.radio(
                "Quick quantity",
                ["5 kg", "10 kg", "20 kg", "Custom"],
                horizontal=True,
            )

            if quick_amount == "Custom":
                amount = st.number_input(
                    "Quantity used (kg)",
                    min_value=0.1,
                    max_value=float(selected["Remaining (kg)"]),
                    value=min(
                        5.0, float(selected["Remaining (kg)"])
                    ),
                    step=0.5,
                )
            else:
                amount = float(quick_amount.replace(" kg", ""))

            shift = st.selectbox(
                "Shift",
                ["A", "B", "C"],
            )

            notes = st.text_area(
                "Notes (optional)",
                placeholder="Example: Production line usage",
            )

            submit_consumption = st.form_submit_button(
                "✅ Record Consumption",
                type="primary",
            )

            if submit_consumption:
                success = record_transaction(
                    selected_id,
                    amount,
                    shift,
                    notes,
                )

                if success:
                    st.success(
                        f"{amount:.1f} kg consumption recorded for {selected_id}."
                    )
                    st.rerun()

    st.divider()
    section_heading("📈 Consumption Analytics")

    tx = transactions_df()

    if tx.empty:
        st.info("No consumption records are available yet.")
    else:
        tx["Timestamp"] = pd.to_datetime(
            tx["Timestamp"], errors="coerce"
        )

        c1, c2 = st.columns(2)

        with c1:
            consumption_by_drum = (
                tx.groupby("Drum ID", as_index=False)
                ["Quantity Used (kg)"]
                .sum()
            )

            chart = px.bar(
                consumption_by_drum,
                x="Drum ID",
                y="Quantity Used (kg)",
                title="Consumption by Drum",
                template="plotly_white",
            )
            st.plotly_chart(chart, use_container_width=True)

        with c2:
            consumption_by_shift = (
                tx.groupby("Shift", as_index=False)
                ["Quantity Used (kg)"]
                .sum()
            )

            chart = px.pie(
                consumption_by_shift,
                names="Shift",
                values="Quantity Used (kg)",
                title="Consumption by Shift",
                hole=0.4,
                template="plotly_white",
            )
            st.plotly_chart(chart, use_container_width=True)

# =========================================================
# TRANSACTION HISTORY
# =========================================================
elif page == "Transactions":
    section_heading(
        "🧾 Transaction History",
        "Review and export recorded consumption transactions.",
    )

    tx = transactions_df()

    if tx.empty:
        st.info("No transactions have been recorded.")
    else:
        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            all_drum_ids = ["All"] + sorted(
                tx["Drum ID"].dropna().unique().tolist()
            )
            drum_filter = st.selectbox(
                "Filter by Drum",
                all_drum_ids,
            )

        with filter_col2:
            shift_filter = st.selectbox(
                "Filter by Shift",
                ["All", "A", "B", "C"],
            )

        filtered_tx = tx.copy()

        if drum_filter != "All":
            filtered_tx = filtered_tx[
                filtered_tx["Drum ID"] == drum_filter
            ]

        if shift_filter != "All":
            filtered_tx = filtered_tx[
                filtered_tx["Shift"] == shift_filter
            ]

        st.dataframe(
            filtered_tx.sort_values(
                "Timestamp", ascending=False
            ),
            use_container_width=True,
            hide_index=True,
        )

        csv_download(
            filtered_tx,
            "sealer_transactions.csv",
            "⬇️ Download Transactions CSV",
        )

        total_filtered = filtered_tx["Quantity Used (kg)"].sum()
        st.metric(
            "Filtered Consumption",
            f"{total_filtered:,.1f} kg",
        )

# =========================================================
# REPORTS
# =========================================================
elif page == "Reports":
    section_heading(
        "📑 Inventory & Consumption Reports",
        "Export current stock levels and consumption data.",
    )

    report = get_stock_report()
    tx = transactions_df()

    st.subheader("Inventory Summary")

    summary1, summary2, summary3 = st.columns(3)
    summary1.metric(
        "Total Capacity",
        f"{report['Capacity (kg)'].sum():,.1f} kg",
    )
    summary2.metric(
        "Remaining Stock",
        f"{report['Remaining (kg)'].sum():,.1f} kg",
    )
    summary3.metric(
        "Utilized Capacity",
        f"{(
            (report['Capacity (kg)'].sum()
             - report['Remaining (kg)'].sum())
            / report['Capacity (kg)'].sum() * 100
            if report['Capacity (kg)'].sum() > 0
            else 0
        ):,.1f}%",
    )

    st.dataframe(
        report,
        use_container_width=True,
        hide_index=True,
    )

    csv_download(
        report,
        "sealer_stock_report.csv",
        "⬇️ Download Stock Report",
    )

    st.divider()
    st.subheader("Consumption Report")

    if tx.empty:
        st.info("No consumption data is available to report.")
    else:
        tx["Timestamp"] = pd.to_datetime(
            tx["Timestamp"], errors="coerce"
        )

        min_date = tx["Timestamp"].min().date()
        max_date = tx["Timestamp"].max().date()

        date_col1, date_col2 = st.columns(2)

        with date_col1:
            start_date = st.date_input(
                "Start date",
                value=min_date,
                key="report_start_date",
            )

        with date_col2:
            end_date = st.date_input(
                "End date",
                value=max_date,
                key="report_end_date",
            )

        if start_date > end_date:
            st.error("Start date must be on or before end date.")
        else:
            filtered_report = tx[
                (tx["Timestamp"].dt.date >= start_date)
                & (tx["Timestamp"].dt.date <= end_date)
            ].copy()

            st.metric(
                "Consumption in Selected Period",
                f"{filtered_report['Quantity Used (kg)'].sum():,.1f} kg",
            )

            st.dataframe(
                filtered_report.sort_values(
                    "Timestamp", ascending=False
                ),
                use_container_width=True,
                hide_index=True,
            )

            csv_download(
                filtered_report,
                "sealer_consumption_report.csv",
                "⬇️ Download Consumption Report",
            )

# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption(
    "Digital Sealer Inventory Monitoring System · "
    "Industrial IoT Demo · Simulated load-cell and SAP values"
)


