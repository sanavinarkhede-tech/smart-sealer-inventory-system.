
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Digital Sealer Inventory",
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

drums = st.session_state.drums

# ---------------- HEADER ----------------
st.title("🏭 Digital Sealer Inventory Monitoring System")
st.caption("Automotive Body Shop | Sealer Drum Monitoring")

st.warning(
    "SIMULATION MODE: Load-cell readings are simulated. "
    "No physical sensors or SAP system are connected."
)

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ System Settings")
low_stock = st.sidebar.number_input(
    "Low-stock alert (kg)", min_value=1.0, value=50.0
)
st.sidebar.metric(
    "SAP Book Stock (kg)",
    f"{st.session_state.book_stock:.1f}"
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Drum Inventory",
        "Consumption",
        "Transactions",
        "Reports"
    ]
)

# ---------------- DASHBOARD ----------------
if page == "Dashboard":
    st.subheader("📊 Inventory Dashboard")

    total_stock = drums["Remaining (kg)"].sum()
    total_capacity = drums["Capacity (kg)"].sum()
    active_drums = (drums["Remaining (kg)"] > 0).sum()
    low_drums = (drums["Remaining (kg)"] <= low_stock).sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Physical Stock", f"{total_stock:.1f} kg")
    c2.metric("Total Capacity", f"{total_capacity:.0f} kg")
    c3.metric("Active Drums", int(active_drums))
    c4.metric("Low-Stock Drums", int(low_drums))

    st.subheader("Current Drum Levels")
    chart_data = drums.set_index("Drum ID")["Remaining (kg)"]
    st.bar_chart(chart_data)

    st.subheader("📍 Storage Area")
    cols = st.columns(5)

    for i, drum in drums.iterrows():
        with cols[i % 5]:
            remaining = drum["Remaining (kg)"]
            if remaining <= low_stock:
                st.error(f"**{drum['Drum ID']}**")
            else:
                st.success(f"**{drum['Drum ID']}**")

            st.write(f"Location: {drum['Location']}")
            st.write(f"Sealer: {drum['Sealer Type']}")
            st.progress(
                min(1.0, max(0.0, remaining / drum["Capacity (kg)"]))
            )
            st.write(f"{remaining:.1f} kg remaining")

    if low_drums:
        st.warning(f"⚠️ {low_drums} drum(s) have reached the low-stock threshold.")

    st.subheader("Physical vs SAP Book Stock")
    comparison = pd.DataFrame({
        "Stock Type": ["Physical Stock", "SAP Book Stock (simulated)"],
        "Quantity (kg)": [
            total_stock,
            st.session_state.book_stock
        ]
    })
    st.bar_chart(comparison.set_index("Stock Type"))

# ---------------- INVENTORY ----------------
elif page == "Drum Inventory":
    st.subheader("🛢️ Drum Inventory Management")
    st.dataframe(drums, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Simulate Consumption")

    drum_ids = drums["Drum ID"].tolist()
    selected_id = st.selectbox("Select Drum", drum_ids)
    amount = st.number_input(
        "Consumption (kg)",
        min_value=0.1,
        max_value=200.0,
        value=5.0,
        step=1.0
    )

    if st.button("➖ Record Consumption", type="primary"):
        idx = st.session_state.drums.index[
            st.session_state.drums["Drum ID"] == selected_id
        ][0]

        current = st.session_state.drums.at[idx, "Remaining (kg)"]

        if amount > current:
            st.error("Insufficient material in this drum.")
        else:
            st.session_state.drums.at[idx, "Remaining (kg)"] = round(
                current - amount, 2
            )
            st.session_state.book_stock = max(
                0, st.session_state.book_stock - amount
            )

            st.session_state.transactions.append({
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Drum ID": selected_id,
                "Transaction": "Consumption",
                "Quantity (kg)": amount,
                "Physical Stock After (kg)": round(current - amount, 2)
            })

            st.success(f"{amount:.1f} kg consumption recorded.")
            st.rerun()

    st.divider()
    st.subheader("➕ Receive New Drum")

    with st.form("new_drum_form"):
        new_type = st.selectbox(
            "Sealer Type", ["Sealer A", "Sealer B", "Sealer C"]
        )
        new_capacity = st.number_input(
            "Drum Capacity (kg)", min_value=1.0, value=200.0
        )
        tare = st.number_input(
            "Empty Drum Weight (kg)", min_value=0.0, value=10.0
        )
        initial = st.number_input(
            "Initial Sealer Quantity (kg)",
            min_value=0.0,
            value=200.0
        )
        location = st.text_input("Storage Location", value="A3")
        submitted = st.form_submit_button("Add Drum")

        if submitted:
            if tare >= new_capacity or initial > new_capacity:
                st.error("Check the capacity, tare weight and initial quantity.")
            else:
                drum_id = f"DR-{st.session_state.next_id:03d}"
                st.session_state.next_id += 1

                new_row = pd.DataFrame([{
                    "Drum ID": drum_id,
                    "Sealer Type": new_type,
                    "Capacity (kg)": float(new_capacity),
                    "Tare Weight (kg)": float(tare),
                    "Remaining (kg)": float(initial),
                    "Location": location,
                    "Status": "Available"
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
    st.subheader("🗑️ Remove Empty Drum")
    empty_drums = drums.loc[
        drums["Remaining (kg)"] <= 0, "Drum ID"
    ].tolist()

    if empty_drums:
        remove_id = st.selectbox("Select empty drum", empty_drums)
        if st.button("Remove Selected Drum"):
            st.session_state.drums = st.session_state.drums[
                st.session_state.drums["Drum ID"] != remove_id
            ].reset_index(drop=True)
            st.success(f"{remove_id} removed.")
            st.rerun()
    else:
        st.info("No empty drums are available to remove.")

# ---------------- CONSUMPTION ----------------
elif page == "Consumption":
    st.subheader("📉 Consumption Monitoring")

    if st.session_state.transactions:
        tx = pd.DataFrame(st.session_state.transactions)
        consumption = tx[tx["Transaction"] == "Consumption"]

        if not consumption.empty:
            st.metric(
                "Total Recorded Consumption",
                f"{consumption['Quantity (kg)'].sum():.1f} kg"
            )
            st.dataframe(
                consumption, use_container_width=True, hide_index=True
            )
            st.subheader("Consumption by Drum")
            st.bar_chart(
                consumption.groupby("Drum ID")["Quantity (kg)"].sum()
            )
        else:
            st.info("No consumption has been recorded yet.")
    else:
        st.info("Record consumption in Drum Inventory to see reports.")

    st.caption(
        "Consumption is calculated from recorded transactions. "
        "This demo does not automatically read real production or shift data."
    )

# ---------------- TRANSACTIONS ----------------
elif page == "Transactions":
    st.subheader("🧾 Transaction History")

    if st.session_state.transactions:
        tx = pd.DataFrame(st.session_state.transactions)
        st.dataframe(tx, use_container_width=True, hide_index=True)

        csv = tx.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Transactions CSV",
            data=csv,
            file_name="sealer_transactions.csv",
            mime="text/csv"
        )
    else:
        st.info("No transactions recorded yet.")

# ---------------- REPORTS ----------------
elif page == "Reports":
    st.subheader("📑 Inventory Reports")

    total_stock = st.session_state.drums["Remaining (kg)"].sum()
    st.metric("Current Physical Stock", f"{total_stock:.1f} kg")
    st.metric(
        "Current SAP Book Stock (simulated)",
        f"{st.session_state.book_stock:.1f} kg"
    )

    report = st.session_state.drums.copy()
    report["Stock Level (%)"] = (
        report["Remaining (kg)"] / report["Capacity (kg)") * 100
    ).round(1)

    st.dataframe(report, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇️ Download Inventory CSV",
        data=report.to_csv(index=False).encode("utf-8"),
        file_name="sealer_inventory_report.csv",
        mime="text/csv"
    )

st.divider()
st.caption(
    "Digital Sealer Inventory Monitoring System | "
    "Prototype for automotive manufacturing | Simulation only"
)
