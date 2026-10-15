
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

st.set_page_config(
    page_title="Digital Sealer Inventory",
    page_icon="🏭",
    layout="wide"
)

# ---------------- DESIGN ----------------
st.markdown("""
<style>
.stApp {
    background-color: #f3f6fa;
}
[data-testid="stSidebar"] {
    background-color: #14243b;
}
[data-testid="stSidebar"] * {
    color: white;
}
.metric {
    background: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e1e7ef;
}
.metric-label {
    color: #607086;
    font-size: 13px;
}
.metric-value {
    color: #12304a;
    font-size: 28px;
    font-weight: 800;
}
</style>
""", unsafe_allow_html=True)

# ---------------- INITIAL DATA ----------------
if "drums" not in st.session_state:
    st.session_state.drums = pd.DataFrame([
        ["SEA-001", "Body Sealer A", 200.0, 156.0, "Rack A-01"],
        ["SEA-002", "Body Sealer A", 200.0, 82.0, "Rack A-02"],
        ["SEA-003", "Body Sealer A", 200.0, 34.0, "Line Supply"],
        ["SEA-004", "Body Sealer B", 200.0, 200.0, "Rack B-01"],
        ["SEA-005", "Body Sealer B", 200.0, 0.0, "Rack B-02"],
        ["SEA-006", "Body Sealer A", 200.0, 118.0, "Line Supply"],
    ], columns=[
        "Drum ID", "Sealer Type", "Capacity (kg)",
        "Remaining (kg)", "Location"
    ])

if "transactions" not in st.session_state:
    st.session_state.transactions = pd.DataFrame(
        columns=["Time", "Transaction", "Drum ID",
                 "Quantity (kg)", "Remarks"]
    )

if "threshold" not in st.session_state:
    st.session_state.threshold = 50.0

# ---------------- SIDEBAR ----------------
st.sidebar.title("🏭 SEALER MONITOR")
st.sidebar.caption("BODY SHOP | STORAGE AREA")

page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Drum Inventory",
     "Consumption", "Transaction History"]
)

st.session_state.threshold = st.sidebar.number_input(
    "Low stock threshold (kg)",
    min_value=1.0,
    max_value=200.0,
    value=float(st.session_state.threshold),
    step=5.0
)

st.sidebar.info(
    "Demo version: inventory changes are simulated. "
    "No physical sensor is connected."
)

# ---------------- CALCULATIONS ----------------
drums = st.session_state.drums.copy()

drums["Remaining (kg)"] = drums.apply(
    lambda r: min(
        float(r["Capacity (kg)"]),
        max(0.0, float(r["Remaining (kg)"]))
    ),
    axis=1
)

drums["Level (%)"] = (
    drums["Remaining (kg)"] /
    drums["Capacity (kg)"] * 100
)

def get_status(row):
    if row["Remaining (kg)"] <= 0:
        return "EMPTY"
    if row["Remaining (kg)"] <= st.session_state.threshold:
        return "LOW STOCK"
    return "NORMAL"

drums["Status"] = drums.apply(get_status, axis=1)

total_stock = drums["Remaining (kg)"].sum()
total_capacity = drums["Capacity (kg)"].sum()
active_drums = (drums["Remaining (kg)"] > 0).sum()
low_drums = (drums["Status"] == "LOW STOCK").sum()

today = datetime.now().date()
tx = st.session_state.transactions.copy()

if not tx.empty:
    tx["Time"] = pd.to_datetime(tx["Time"])
    consumed_today = tx[
        (tx["Transaction"] == "Consumption") &
        (tx["Time"].dt.date == today)
    ]["Quantity (kg)"].sum()
else:
    consumed_today = 0.0

# ---------------- HEADER ----------------
st.markdown("""
<div style="
background:linear-gradient(110deg,#12243d,#17647a);
padding:25px;border-radius:15px;color:white;">
<div style="font-size:12px;letter-spacing:2px;">
SIMULATION MODE | DIGITAL INVENTORY
</div>
<h1 style="color:white;margin-bottom:5px;">
Digital Sealer Inventory Monitoring System
</h1>
<div>Automotive Manufacturing | Body Shop | Sealer Storage</div>
</div>
""", unsafe_allow_html=True)

st.caption(
    "Dashboard timestamp: " +
    datetime.now().strftime("%d %b %Y, %H:%M:%S")
)

# ---------------- OVERVIEW ----------------
if page == "Overview":

    if low_drums:
        st.warning(
            f"{low_drums} drum(s) are at or below "
            f"the {st.session_state.threshold:.0f} kg threshold."
        )

    if total_stock == 0:
        st.error("No sealer material available.")

    c1, c2, c3, c4 = st.columns(4)

    metrics = [
        (c1, "TOTAL AVAILABLE STOCK", f"{total_stock:.1f} kg"),
        (c2, "ACTIVE DRUMS", str(active_drums)),
        (c3, "CONSUMPTION TODAY", f"{consumed_today:.1f} kg"),
        (c4, "LOW-STOCK DRUMS", str(low_drums)),
    ]

    for col, label, value in metrics:
        with col:
            st.markdown(
                f'<div class="metric">'
                f'<div class="metric-label">{label}</div>'
                f'<div class="metric-value">{value}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.write("")
    left, right = st.columns([1.3, 1])

    with left:
        st.subheader("Drum-wise Inventory")

        chart = alt.Chart(drums).mark_bar(
            cornerRadiusTopLeft=5,
            cornerRadiusTopRight=5
        ).encode(
            x=alt.X("Drum ID:N", title="Drum ID"),
            y=alt.Y("Remaining (kg):Q", title="Remaining (kg)"),
            color=alt.condition(
                alt.datum["Remaining (kg)"] <=
                st.session_state.threshold,
                alt.value("#e59b32"),
                alt.value("#078b8b")
            ),
            tooltip=[
                "Drum ID",
                "Sealer Type",
                "Remaining (kg)",
                "Capacity (kg)",
                "Location"
            ]
        ).properties(height=330)

        st.altair_chart(chart, use_container_width=True)

    with right:
        st.subheader("Storage Status")

        for _, row in drums.iterrows():
            st.markdown(f"**{row['Drum ID']} — {row['Location']}**")
            st.progress(
                float(row["Level (%)"]) / 100,
                text=(
                    f"{row['Remaining (kg)']:.1f} kg / "
                    f"{row['Capacity (kg)']:.0f} kg"
                    f" · {row['Status']}"
                )
            )

    st.subheader("Quick Demo Actions")

    a, b = st.columns(2)

    with a:
        selected = st.selectbox(
            "Select drum for consumption",
            drums.loc[
                drums["Remaining (kg)"] > 0, "Drum ID"
            ].tolist(),
            key="quick_drum"
        )

        quantity = st.number_input(
            "Consumption quantity (kg)",
            min_value=0.1,
            max_value=200.0,
            value=10.0,
            step=1.0,
            key="quick_quantity"
        )

        if st.button("▶ Simulate Consumption", type="primary"):
            idx = st.session_state.drums.index[
                st.session_state.drums["Drum ID"] == selected
            ][0]

            available = float(
                st.session_state.drums.loc[idx, "Remaining (kg)"]
            )

            if quantity > available:
                st.error(f"Only {available:.1f} kg is available.")
            else:
                st.session_state.drums.loc[
                    idx, "Remaining (kg)"
                ] = available - quantity

                new_tx = pd.DataFrame([{
                    "Time": datetime.now(),
                    "Transaction": "Consumption",
                    "Drum ID": selected,
                    "Quantity (kg)": quantity,
                    "Remarks": "Simulated running-line usage"
                }])

                st.session_state.transactions = pd.concat(
                    [st.session_state.transactions, new_tx],
                    ignore_index=True
                )
                st.success("Demo consumption recorded.")
                st.rerun()

    with b:
        st.write("Receive a new full drum")
        new_id = st.text_input("New drum ID", value="SEA-007")
        capacity = st.number_input(
            "New drum capacity (kg)",
            min_value=1.0,
            value=200.0,
            step=10.0
        )

        if st.button("＋ Receive Drum"):
            if new_id in st.session_state.drums["Drum ID"].values:
                st.error("Drum ID already exists.")
            else:
                new_row = pd.DataFrame([{
                    "Drum ID": new_id,
                    "Sealer Type": "Body Sealer A",
                    "Capacity (kg)": capacity,
                    "Remaining (kg)": capacity,
                    "Location": "New Receipt"
                }])

                st.session_state.drums = pd.concat(
                    [st.session_state.drums, new_row],
                    ignore_index=True
                )

                new_tx = pd.DataFrame([{
                    "Time": datetime.now(),
                    "Transaction": "Receipt",
                    "Drum ID": new_id,
                    "Quantity (kg)": capacity,
                    "Remarks": "Simulated material receipt"
                }])

                st.session_state.transactions = pd.concat(
                    [st.session_state.transactions, new_tx],
                    ignore_index=True
                )

                st.success("New drum received.")
                st.rerun()

    st.download_button(
        "⬇ Download Inventory CSV",
        data=drums.to_csv(index=False).encode("utf-8"),
        file_name="sealer_inventory.csv",
        mime="text/csv"
    )

# ---------------- DRUM INVENTORY ----------------
elif page == "Drum Inventory":

    st.subheader("Drum Inventory Register")

    edited = st.data_editor(
        drums,
        use_container_width=True,
        hide_index=True,
        disabled=["Level (%)", "Status"],
        column_config={
            "Remaining (kg)": st.column_config.NumberColumn(
                min_value=0.0, max_value=2000.0, step=1.0
            ),
            "Capacity (kg)": st.column_config.NumberColumn(
                min_value=1.0, max_value=2000.0, step=10.0
            ),
            "Level (%)": st.column_config.ProgressColumn(
                min_value=0, max_value=100, format="%.1f%%"
            )
        }
    )

    if st.button("Save Inventory Changes", type="primary"):
        edited["Remaining (kg)"] = edited.apply(
            lambda r: min(
                float(r["Capacity (kg)"]),
                max(0.0, float(r["Remaining (kg)"]))
            ),
            axis=1
        )

        st.session_state.drums = edited[
            ["Drum ID", "Sealer Type", "Capacity (kg)",
             "Remaining (kg)", "Location"]
        ].copy()

        st.success("Inventory updated.")
        st.rerun()

    st.download_button(
        "Download Inventory CSV",
        data=drums.to_csv(index=False).encode("utf-8"),
        file_name="sealer_inventory.csv",
        mime="text/csv"
    )

# ---------------- CONSUMPTION ----------------
elif page == "Consumption":

    st.subheader("Consumption Analytics")

    st.metric("Recorded consumption today", f"{consumed_today:.1f} kg")

    if tx.empty:
        st.info("No consumption recorded yet. Use the Overview page to simulate usage.")
    else:
        usage = tx[tx["Transaction"] == "Consumption"].copy()

        if not usage.empty:
            by_drum = usage.groupby(
                "Drum ID", as_index=False
            )["Quantity (kg)"].sum()

            st.altair_chart(
                alt.Chart(by_drum).mark_bar(
                    cornerRadiusTopLeft=5,
                    cornerRadiusTopRight=5
                ).encode(
                    x=alt.X("Drum ID:N", title="Drum ID"),
                    y=alt.Y("Quantity (kg):Q", title="Recorded consumption (kg)"),
                    color=alt.value("#087e8b"),
                    tooltip=["Drum ID", "Quantity (kg)"]
                ).properties(height=350),
                use_container_width=True
            )

            st.dataframe(usage, use_container_width=True, hide_index=True)

            st.download_button(
                "Download Consumption CSV",
                data=usage.to_csv(index=False).encode("utf-8"),
                file_name="sealer_consumption.csv",
                mime="text/csv"
            )

# ---------------- TRANSACTION HISTORY ----------------
elif page == "Transaction History":

    st.subheader("Material Movement History")

    if tx.empty:
        st.info("No transactions recorded.")
    else:
        st.dataframe(
            tx.sort_values("Time", ascending=False),
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Transaction CSV",
            data=tx.to_csv(index=False).encode("utf-8"),
            file_name="sealer_transactions.csv",
            mime="text/csv"
        )

st.markdown("---")
st.caption(
    "Digital Sealer Inventory Demo | Simulated data only | "
    "Not connected to physical sensors or production systems"
)
