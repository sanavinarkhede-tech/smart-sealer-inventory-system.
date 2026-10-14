
import streamlit as st
import pandas as pd
from datetime import datetime

# ---------------- PAGE CONFIGURATION ----------------
st.set_page_config(
    page_title="Digital Sealer Inventory System",
    page_icon="🏭",
    layout="wide"
)

# ---------------- SESSION STATE ----------------
if "drums" not in st.session_state:
    st.session_state.drums = pd.DataFrame({
        "Drum ID": ["DR-001", "DR-002", "DR-003", "DR-004", "DR-005"],
        "Sealer Type": ["Sealer A", "Sealer A", "Sealer B", "Sealer B", "Sealer C"],
        "Capacity (kg)": [200.0] * 5,
        "Tare Weight (kg)": [10.0] * 5,
        "Remaining (kg)": [180.0, 150.0, 120.0, 80.0, 40.0],
        "Location": ["A1", "A2", "B1", "B2", "C1"],
        "Status": ["Available"] * 5
    })

if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "next_id" not in st.session_state:
    st.session_state.next_id = 6

if "book_stock" not in st.session_state:
    st.session_state.book_stock = 570.0

# ---------------- CUSTOM STYLE ----------------
st.markdown("""
<style>
    .main {
        background-color: #f5f7fb;
    }
    h1 {
        color: #17365d;
    }
    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e0e6ef;
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.title("🏭 Digital Sealer Inventory Monitoring System")
st.caption("Automotive Manufacturing | Body Shop Sealer Storage")

st.warning(
    "SIMULATION MODE: Load-cell readings and SAP book stock are simulated. "
    "No real sensors or SAP system are connected."
)

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Control Panel")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Drum Inventory",
        "Consumption Monitoring",
        "Transactions",
        "Reports"
    ]
)

low_stock = st.sidebar.number_input(
    "Low-stock alert threshold (kg)",
    min_value=1.0,
    max_value=200.0,
    value=50.0,
    step=5.0
)

st.sidebar.metric(
    "Simulated SAP Book Stock",
    f"{st.session_state.book_stock:.1f} kg"
)

st.sidebar.caption("Prototype version | Simulation only")

# ---------------- DASHBOARD ----------------
if page == "Dashboard":
    st.subheader("📊 Inventory Dashboard")

    drums = st.session_state.drums

    total_stock = drums["Remaining (kg)"].sum()
    total_capacity = drums["Capacity (kg)"].sum()
    active_drums = (drums["Remaining (kg)"] > 0).sum()
    low_drums = (drums["Remaining (kg)"] <= low_stock).sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Physical Stock", f"{total_stock:.1f} kg")
    col2.metric("Total Capacity", f"{total_capacity:.1f} kg")
    col3.metric("Active Drums", int(active_drums))
    col4.metric("Low-Stock Drums", int(low_drums))

    st.divider()

    st.subheader("📈 Drum Inventory Levels")

    chart_data = drums.set_index("Drum ID")["Remaining (kg)"]
    st.bar_chart(chart_data)

    st.subheader("📍 Storage Area Visualization")

    columns = st.columns(5)

    for i, (_, drum) in enumerate(drums.iterrows()):
        with columns[i % 5]:
            remaining = float(drum["Remaining (kg)"])
            capacity = float(drum["Capacity (kg)"])
            level = remaining / capacity if capacity > 0 else 0

            if remaining <= low_stock:
                st.error(f"**{drum['Drum ID']}**")
            else:
                st.success(f"**{drum['Drum ID']}**")

            st.write(f"Location: {drum['Location']}")
            st.write(f"Type: {drum['Sealer Type']}")
            st.progress(max(0.0, min(1.0, level)))
            st.write(f"{remaining:.1f} / {capacity:.1f} kg")

    if low_drums > 0:
        st.warning(
            f"⚠️ Reorder alert: {low_drums} drum(s) are at or below "
            f"{low_stock:.1f} kg."
        )
    else:
        st.success("All drums are above the low-stock threshold.")

    st.divider()

    st.subheader("Physical Stock vs SAP Book Stock")

    comparison = pd.DataFrame({
        "Stock Type": ["Physical Stock", "SAP Book Stock (simulated)"],
        "Quantity (kg)": [
            total_stock,
            st.session_state.book_stock
        ]
    })

    st.bar_chart(comparison.set_index("Stock Type"))

    difference = total_stock - st.session_state.book_stock

    st.metric("Physical vs Book Stock Difference", f"{difference:.1f} kg")

# ---------------- DRUM INVENTORY ----------------
elif page == "Drum Inventory":
    st.subheader("🛢️ Drum Inventory Management")

    drums = st.session_state.drums

    st.dataframe(
        drums,
        use_container_width=True,
        hide_index=True
    )

    st.divider()
    st.subheader("➖ Simulate Sealer Consumption")

    drum_ids = drums["Drum ID"].tolist()

    if drum_ids:
        selected_id = st.selectbox("Select Drum", drum_ids)

        amount = st.number_input(
            "Consumption quantity (kg)",
            min_value=0.1,
            max_value=200.0,
            value=5.0,
            step=1.0
        )

        if st.button("Record Consumption", type="primary"):
            matching_rows = st.session_state.drums.index[
                st.session_state.drums["Drum ID"] == selected_id
            ]

            idx = matching_rows[0]

            current = float(
                st.session_state.drums.at[idx, "Remaining (kg)"]
            )

            if amount > current:
                st.error(
                    f"Insufficient material. Only {current:.1f} kg remains."
                )
            else:
                updated = round(current - amount, 2)

                st.session_state.drums.at[
                    idx, "Remaining (kg)"
                ] = updated

                st.session_state.book_stock = max(
                    0.0,
                    st.session_state.book_stock - amount
                )

                st.session_state.transactions.append({
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Drum ID": selected_id,
                    "Transaction": "Consumption",
                    "Quantity (kg)": float(amount),
                    "Physical Stock After (kg)": updated
                })

                st.success(
                    f"{amount:.1f} kg consumed from {selected_id}."
                )
                st.rerun()

    st.divider()
    st.subheader("➕ Receive a New Drum")

    with st.form("new_drum_form"):
        new_type = st.selectbox(
            "Sealer Type",
            ["Sealer A", "Sealer B", "Sealer C"]
        )

        new_capacity = st.number_input(
            "Drum Capacity (kg)",
            min_value=1.0,
            value=200.0
        )

        tare = st.number_input(
            "Empty Drum Weight (kg)",
            min_value=0.0,
            value=10.0
        )

        initial = st.number_input(
            "Initial Sealer Quantity (kg)",
            min_value=0.0,
            value=200.0
        )

        location = st.text_input(
            "Storage Location",
            value="A3"
        )

        submitted = st.form_submit_button("Add New Drum")

        if submitted:
            if tare >= new_capacity:
                st.error("Tare weight must be less than drum capacity.")
            elif initial > new_capacity:
                st.error("Initial quantity cannot exceed drum capacity.")
            elif not location.strip():
                st.error("Please enter a storage location.")
            else:
                drum_id = f"DR-{st.session_state.next_id:03d}"
                st.session_state.next_id += 1

                new_row = pd.DataFrame([{
                    "Drum ID": drum_id,
                    "Sealer Type": new_type,
                    "Capacity (kg)": float(new_capacity),
                    "Tare Weight (kg)": float(tare),
                    "Remaining (kg)": float(initial),
                    "Location": location.strip(),
                    "Status": "Available" if initial > 0 else "Empty"
                }])

                st.session_state.drums = pd.concat(
                    [st.session_state.drums, new_row],
                    ignore_index=True
                )

                st.session_state.book_stock += float(initial)

                st.session_state.transactions.append({
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Drum ID": drum_id,
                    "Transaction": "Drum Received",
                    "Quantity (kg)": float(initial),
                    "Physical Stock After (kg)": float(initial)
                })

                st.success(f"Drum {drum_id} added successfully.")
                st.rerun()

    st.divider()
    st.subheader("🗑️ Remove an Empty Drum")

    empty_drums = st.session_state.drums.loc[
        st.session_state.drums["Remaining (kg)"] <= 0,
        "Drum ID"
    ].tolist()

    if empty_drums:
        remove_id = st.selectbox(
            "Select empty drum to remove",
            empty_drums
        )

        if st.button("Remove Selected Drum"):
            st.session_state.drums = st.session_state.drums[
                st.session_state.drums["Drum ID"] != remove_id
            ].reset_index(drop=True)

            st.success(f"{remove_id} removed.")
            st.rerun()
    else:
        st.info("There are currently no empty drums to remove.")

# ---------------- CONSUMPTION MONITORING ----------------
elif page == "Consumption Monitoring":
    st.subheader("📉 Sealer Consumption Monitoring")

    if st.session_state.transactions:
        tx = pd.DataFrame(st.session_state.transactions)

        consumption = tx[
            tx["Transaction"] == "Consumption"
        ].copy()

        if not consumption.empty:
            total_consumption = consumption["Quantity (kg)"].sum()

            col1, col2 = st.columns(2)

            col1.metric(
                "Total Recorded Consumption",
                f"{total_consumption:.1f} kg"
            )

            col2.metric(
                "Consumption Transactions",
                len(consumption)
            )

            st.subheader("Consumption by Drum")

            by_drum = consumption.groupby("Drum ID")[
                "Quantity (kg)"
            ].sum()

            st.bar_chart(by_drum)

            st.subheader("Consumption Transaction Details")

            st.dataframe(
                consumption,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No consumption transactions recorded yet.")
    else:
        st.info(
            "No transactions available. Record consumption in "
            "Drum Inventory to view reports."
        )

    st.caption(
        "This prototype reports recorded consumption. "
        "Automatic shift-wise consumption requires production or sensor data."
    )

# ---------------- TRANSACTIONS ----------------
elif page == "Transactions":
    st.subheader("🧾 Transaction History")

    if st.session_state.transactions:
        tx = pd.DataFrame(st.session_state.transactions)

        st.dataframe(
            tx.sort_values("Time", ascending=False),
            use_container_width=True,
            hide_index=True
        )

        csv_data = tx.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Download Transaction History CSV",
            data=csv_data,
            file_name="sealer_transactions.csv",
            mime="text/csv"
        )
    else:
        st.info("No transactions have been recorded yet.")

# ---------------- REPORTS ----------------
elif page == "Reports":
    st.subheader("📑 Inventory Reports")

    report = st.session_state.drums.copy()

    total_stock = report["Remaining (kg)"].sum()

    col1, col2 = st.columns(2)

    col1.metric(
        "Current Physical Stock",
        f"{total_stock:.1f} kg"
    )

    col2.metric(
        "Simulated SAP Book Stock",
        f"{st.session_state.book_stock:.1f} kg"
    )

    # Corrected stock-level calculation
    report["Stock Level (%)"] = (
        report["Remaining (kg)"] / report["Capacity (kg)"] * 100
    ).round(1)

    report["Stock Level (%)"] = report["Stock Level (%)"].fillna(0)

    st.dataframe(
        report,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        label="⬇️ Download Inventory Report CSV",
        data=report.to_csv(index=False).encode("utf-8"),
        file_name="sealer_inventory_report.csv",
        mime="text/csv"
    )

    st.subheader("📊 Stock Level by Drum")
    st.bar_chart(
        report.set_index("Drum ID")["Stock Level (%)"]
    )

# ---------------- FOOTER ----------------
st.divider()

st.caption(
    "Digital Sealer Inventory Monitoring System | "
    "Automotive Body Shop Prototype | Simulation Mode"
)

