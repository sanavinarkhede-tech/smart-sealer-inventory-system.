
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Sealer IQ | Industrial Inventory",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# INDUSTRIAL IOT THEME
# =========================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: #F3F6FA;
    }

    [data-testid="stHeader"] {
        background: rgba(243, 246, 250, 0.95);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #10243A 0%, #173B56 100%);
        border-right: 1px solid #27465D;
    }

    section[data-testid="stSidebar"] * {
        color: #EDF5FC;
    }

    section[data-testid="stSidebar"] hr {
        border-color: #34536A;
    }

    .brand {
        background: linear-gradient(135deg, #163A54, #087F8C);
        padding: 22px 20px;
        border-radius: 16px;
        color: white;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(8, 127, 140, 0.16);
    }

    .brand-title {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: 1px;
        margin: 0;
    }

    .brand-subtitle {
        font-size: 11px;
        letter-spacing: 1.6px;
        color: #CBE8F2;
        margin-top: 5px;
    }

    .section-label {
        color: #64748B;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin: 8px 0 12px 0;
    }

    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 17px 18px;
        box-shadow: 0 4px 16px rgba(15, 35, 55, 0.035);
    }

    div[data-testid="stMetricLabel"] {
        color: #64748B;
        font-size: 13px;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #173B56;
        font-size: 28px;
        font-weight: 800;
    }

    div[data-testid="stMetricDelta"] {
        font-size: 12px;
    }

    div.stButton > button,
    div.stDownloadButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        border-radius: 9px;
        min-height: 40px;
        font-weight: 600;
        border: 1px solid #D5E1EB;
    }

    div.stButton > button[kind="primary"] {
        background: #087F8C;
        border-color: #087F8C;
        color: white;
    }

    div.stButton > button[kind="primary"]:hover {
        background: #066A75;
        border-color: #066A75;
        color: white;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        overflow: hidden;
    }

    div[data-testid="stPlotlyChart"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 8px;
    }

    .status-strip {
        background: #E4F6F2;
        color: #087F68;
        border: 1px solid #B6E8DB;
        padding: 11px 15px;
        border-radius: 10px;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 16px;
    }

    .info-panel {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 13px;
        padding: 16px;
    }

    .small-muted {
        color: #64748B;
        font-size: 12px;
    }

    #MainMenu, footer {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# INITIAL DEMO DATA
# =========================================================
def initialise_state():
    if "drums" not in st.session_state:
        st.session_state.drums = pd.DataFrame({
            "Drum ID": [
                "DR-001", "DR-002", "DR-003", "DR-004", "DR-005"
            ],
            "Sealer Type": [
                "Sealer A", "Sealer A", "Sealer B", "Sealer B", "Sealer C"
            ],
            "Capacity (kg)": [200.0] * 5,
            "Tare Weight (kg)": [10.0] * 5,
            "Remaining (kg)": [180.0, 150.0, 120.0, 80.0, 40.0],
            "Location": ["A1", "A2", "B1", "B2", "C1"]
        })

    if "transactions" not in st.session_state:
        st.session_state.transactions = []

    if "next_id" not in st.session_state:
        st.session_state.next_id = 6

    if "book_stock" not in st.session_state:
        st.session_state.book_stock = float(
            st.session_state.drums["Remaining (kg)"].sum()
        )

    if "threshold" not in st.session_state:
        st.session_state.threshold = 50.0

    if "last_sensor_reading" not in st.session_state:
        st.session_state.last_sensor_reading = {}

initialise_state()


# =========================================================
# HELPER FUNCTIONS
# =========================================================
def current_drums():
    return st.session_state.drums.copy()


def stock_status(remaining, threshold):
    if remaining <= 0:
        return "Empty"
    if remaining <= threshold * 0.5:
        return "Critical"
    if remaining <= threshold:
        return "Low Stock"
    return "Available"


def add_transaction(drum_id, transaction_type, quantity,
                    physical_after, shift="General", note=""):
    st.session_state.transactions.append({
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Date": date.today().isoformat(),
        "Shift": shift,
        "Drum ID": drum_id,
        "Transaction": transaction_type,
        "Quantity (kg)": round(float(quantity), 2),
        "Physical Stock After (kg)": round(float(physical_after), 2),
        "Notes": note
    })


def make_csv(dataframe):
    return dataframe.to_csv(index=False).encode("utf-8-sig")


def styled_chart(fig, height=320):
    fig.update_layout(
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter", color="#334155", size=12),
        margin=dict(l=15, r=15, t=45, b=15),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(showgrid=False, linecolor="#E2E8F0"),
        yaxis=dict(gridcolor="#E8EEF4", zeroline=False),
    )
    return fig


def get_stock_report():
    report = current_drums()
    report["Status"] = report["Remaining (kg)"].apply(
        lambda value: stock_status(value, st.session_state.threshold)
    )
    report["Stock Level (%)"] = (
        report["Remaining (kg)"]
        .div(report["Capacity (kg)"].replace(0, pd.NA))
        .mul(100)
        .fillna(0)
        .round(1)
    )
    return report


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("""
    <div style="padding: 8px 0 20px 0;">
        <div style="font-size: 34px;">🏭</div>
        <div style="font-size: 23px; font-weight: 800; letter-spacing: 1px;">
            SEALER IQ
        </div>
        <div style="font-size: 10px; letter-spacing: 1.8px; color: #A9D5E3;">
            INDUSTRIAL INVENTORY CONTROL
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("WORKSPACE")
    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Drum Inventory",
            "Consumption",
            "Transactions",
            "Reports"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.caption("MONITORING SETTINGS")

    st.session_state.threshold = st.slider(
        "Low-stock alert threshold (kg)",
        min_value=10,
        max_value=100,
        value=int(st.session_state.threshold),
        step=5
    )

    st.markdown("---")
    st.markdown(
        "<div style='background:#183F56; padding:13px; "
        "border-radius:10px;'>"
        "<div style='font-size:11px;color:#A9D5E3;'>SYSTEM MODE</div>"
        "<div style='font-weight:700;color:#FFFFFF;'>● SIMULATION</div>"
        "<div style='font-size:11px;color:#B8D0DE;margin-top:5px;'>"
        "No live sensor or SAP connection</div></div>",
        unsafe_allow_html=True
    )

    st.write("")
    st.caption("SEALER IQ • Prototype v2.0")

# =========================================================
# TOP HEADER
# =========================================================
st.markdown("""
<div class="brand">
    <div class="brand-title">DIGITAL SEALER MONITORING</div>
    <div class="brand-subtitle">
        BODY SHOP / AUTOMOTIVE MANUFACTURING / INVENTORY INTELLIGENCE
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(
    f'<div class="status-strip">● SYSTEM READY &nbsp; | &nbsp; '
    f'SIMULATION MODE &nbsp; | &nbsp; '
    f'LAST PAGE REFRESH: {datetime.now().strftime("%d %b %Y, %H:%M:%S")}'
    f'</div>',
    unsafe_allow_html=True
)

# =========================================================
# OVERVIEW DASHBOARD
# =========================================================
if page == "Overview":
    drums = current_drums()
    report = get_stock_report()

    physical_stock = float(drums["Remaining (kg)"].sum())
    capacity = float(drums["Capacity (kg)"].sum())
    active = int((drums["Remaining (kg)"] > 0).sum())
    low_count = int(
        (drums["Remaining (kg)"] <= st.session_state.threshold).sum()
    )
    utilization = physical_stock / capacity * 100 if capacity else 0

    st.markdown('<div class="section-label">Live Overview</div>',
                unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Physical Sealer Stock", f"{physical_stock:,.1f} kg")
    c2.metric("Storage Capacity", f"{capacity:,.0f} kg")
    c3.metric("Active Drums", f"{active} / {len(drums)}")
    c4.metric("Low-Stock Alerts", str(low_count))

    left, right = st.columns([1.45, 1])

    with left:
        st.subheader("📊 Inventory Levels")
        fig = go.Figure()

        colors = [
            "#DC5353" if value <= st.session_state.threshold * 0.5
            else "#E8A23A" if value <= st.session_state.threshold
            else "#0B9B8A"
            for value in drums["Remaining (kg)"]
        ]

        fig.add_trace(go.Bar(
            x=drums["Drum ID"],
            y=drums["Remaining (kg)"],
            marker_color=colors,
            text=[f"{v:.0f} kg" for v in drums["Remaining (kg)"]],
            textposition="outside",
            name="Remaining stock"
        ))

        fig.update_layout(
            title="Remaining Material per Drum",
            yaxis_title="Quantity (kg)",
            showlegend=False,
            yaxis_range=[0, max(220, float(drums["Capacity (kg)"].max()) + 25)]
        )
        st.plotly_chart(styled_chart(fig, 350), use_container_width=True)

    with right:
        st.subheader("🏭 Storage Utilization")

        fig = go.Figure(go.Pie(
            labels=["Used stock", "Available capacity"],
            values=[physical_stock, max(capacity - physical_stock, 0)],
            hole=0.72,
            marker_colors=["#087F8C", "#E7EDF3"],
            textinfo="percent",
            sort=False
        ))

        fig.add_annotation(
            text=f"<b>{utilization:.1f}%</b><br><span style='font-size:11px'>utilized</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=22, color="#173B56")
        )

        fig.update_layout(
            title="Total Capacity Usage",
            showlegend=True
        )
        st.plotly_chart(styled_chart(fig, 350), use_container_width=True)

    st.subheader("📍 Drum Storage Map")

    cols = st.columns(5)
    for i, (_, drum) in enumerate(report.iterrows()):
        remaining = float(drum["Remaining (kg)"])
        pct = float(drum["Stock Level (%)"])
        status = drum["Status"]

        if status == "Empty" or status == "Critical":
            color, bg = "#D64545", "#FCE8E8"
        elif status == "Low Stock":
            color, bg = "#C98214", "#FFF3D6"
        else:
            color, bg = "#07866F", "#E2F6F0"

        with cols[i % 5]:
            st.markdown(
                f"""
                <div style="background:white;border:1px solid #E1E8EF;
                    border-radius:13px;padding:14px 12px;
                    min-height:170px;">
                    <div style="font-size:11px;color:#64748B;">
                        LOCATION {drum['Location']}
                    </div>
                    <div style="font-size:17px;font-weight:800;
                        color:#173B56;margin-top:5px;">
                        {drum['Drum ID']}
                    </div>
                    <div style="background:#E9EEF4;height:9px;
                        border-radius:8px;margin:13px 0;overflow:hidden;">
                        <div style="width:{max(0,min(100,pct))}%;
                            background:{color};height:9px;border-radius:8px;">
                        </div>
                    </div>
                    <div style="font-size:19px;font-weight:800;color:#173B56;">
                        {remaining:.1f} kg
                    </div>
                    <div style="font-size:11px;color:#64748B;">
                        of {drum['Capacity (kg)']:.0f} kg
                    </div>
                    <div style="display:inline-block;margin-top:9px;
                        padding:4px 8px;border-radius:6px;
                        color:{color};background:{bg};
                        font-size:10px;font-weight:700;">
                        {status.upper()}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.subheader("⚠️ Reorder Alert Center")
    alerts = report[
        report["Remaining (kg)"] <= st.session_state.threshold
    ]

    if alerts.empty:
        st.success("All drums are above the configured alert threshold.")
    else:
        st.warning(f"{len(alerts)} drum(s) require stock review.")
        st.dataframe(
            alerts[[
                "Drum ID", "Sealer Type", "Location",
                "Remaining (kg)", "Status"
            ]],
            use_container_width=True,
            hide_index=True
        )

    st.subheader("📚 Physical vs SAP Book Stock")

    book_stock = float(st.session_state.book_stock)
    variance = physical_stock - book_stock

    a, b, c = st.columns(3)
    a.metric("Physical Stock", f"{physical_stock:.1f} kg")
    b.metric("SAP Book Stock (simulated)", f"{book_stock:.1f} kg")
    b_delta = None
    c.metric("Stock Variance", f"{variance:+.1f} kg")

    st.caption(
        "The SAP figure is a local demo value. It is not connected to a live ERP."
    )

# =========================================================
# DRUM INVENTORY
# =========================================================
elif page == "Drum Inventory":
    st.markdown('<div class="section-label">Inventory Operations</div>',
                unsafe_allow_html=True)
    st.title("🛢️ Drum Inventory")
    st.caption("View, receive, edit and monitor sealer drums.")

    report = get_stock_report()
    search = st.text_input(
        "🔎 Search by drum ID, type or location",
        placeholder="e.g. DR-001, Sealer A, A1"
    )

    if search.strip():
        mask = (
            report["Drum ID"].str.contains(search, case=False, na=False)
            | report["Sealer Type"].str.contains(search, case=False, na=False)
            | report["Location"].str.contains(search, case=False, na=False)
        )
        report = report[mask]

    st.dataframe(
        report,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Stock Level (%)": st.column_config.ProgressColumn(
                "Stock Level",
                min_value=0,
                max_value=100,
                format="%.1f%%"
            )
        }
    )

    st.divider()
    st.subheader("➕ Receive a New Drum")

    with st.form("receive_drum_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)

        with c1:
            new_type = st.selectbox(
                "Sealer Type", ["Sealer A", "Sealer B", "Sealer C"]
            )
            new_capacity = st.number_input(
                "Drum Capacity (kg)", min_value=1.0, value=200.0
            )

        with c2:
            tare = st.number_input(
                "Empty Drum Weight (kg)", min_value=0.0, value=10.0
            )
            initial = st.number_input(
                "Initial Sealer Quantity (kg)",
                min_value=0.0, value=200.0
            )

        with c3:
            location = st.text_input("Storage Location", value="A3")
            receipt_shift = st.selectbox(
                "Shift", ["A", "B", "C", "General"]
            )

        receive = st.form_submit_button(
            "＋ Add Drum to Inventory",
            type="primary",
            use_container_width=True
        )

        if receive:
            if tare >= new_capacity:
                st.error("Tare weight must be less than drum capacity.")
            elif initial > new_capacity:
                st.error("Initial quantity cannot exceed drum capacity.")
            elif not location.strip():
                st.error("Enter a storage location.")
            else:
                drum_id = f"DR-{st.session_state.next_id:03d}"
                st.session_state.next_id += 1

                new_row = pd.DataFrame([{
                    "Drum ID": drum_id,
                    "Sealer Type": new_type,
                    "Capacity (kg)": float(new_capacity),
                    "Tare Weight (kg)": float(tare),
                    "Remaining (kg)": float(initial),
                    "Location": location.strip()
                }])

                st.session_state.drums = pd.concat(
                    [st.session_state.drums, new_row],
                    ignore_index=True
                )
                st.session_state.book_stock += float(initial)

                add_transaction(
                    drum_id, "Drum Received", initial, initial,
                    receipt_shift, "New drum received"
                )

                st.success(f"{drum_id} has been added.")
                st.rerun()

    st.divider()
    st.subheader("✏️ Edit Drum Details")

    drums = current_drums()
    if not drums.empty:
        edit_id = st.selectbox(
            "Select drum to edit",
            drums["Drum ID"].tolist(),
            key="edit_drum_id"
        )
        selected = drums[drums["Drum ID"] == edit_id].iloc[0]

        with st.form("edit_drum_form"):
            e1, e2, e3 = st.columns(3)

            with e1:
                edit_type = st.selectbox(
                    "Sealer Type",
                    ["Sealer A", "Sealer B", "Sealer C"],
                    index=["Sealer A", "Sealer B", "Sealer C"].index(
                        selected["Sealer Type"]
                    )
                )
                edit_location = st.text_input(
                    "Location", value=str(selected["Location"])
                )

            with e2:
                edit_capacity = st.number_input(
                    "Capacity (kg)",
                    min_value=1.0,
                    value=float(selected["Capacity (kg)"])
                )
                edit_tare = st.number_input(
                    "Tare Weight (kg)",
                    min_value=0.0,
                    value=float(selected["Tare Weight (kg)"])
                )

            with e3:
                edit_remaining = st.number_input(
                    "Simulated Remaining Stock (kg)",
                    min_value=0.0,
                    value=float(selected["Remaining (kg)"])
                )
                edit_shift = st.selectbox(
                    "Adjustment Shift",
                    ["A", "B", "C", "General"]
                )

            save_edit = st.form_submit_button(
                "Save Drum Changes",
                type="primary"
            )

            if save_edit:
                if edit_tare >= edit_capacity:
                    st.error("Tare weight must be below capacity.")
                elif edit_remaining > edit_capacity:
                    st.error("Remaining stock cannot exceed capacity.")
                elif not edit_location.strip():
                    st.error("Location cannot be empty.")
                else:
                    idx = st.session_state.drums.index[
                        st.session_state.drums["Drum ID"] == edit_id
                    ][0]

                    old_remaining = float(
                        st.session_state.drums.at[idx, "Remaining (kg)"]
                    )
                    delta = float(edit_remaining) - old_remaining

                    st.session_state.drums.loc[idx, [
                        "Sealer Type", "Location", "Capacity (kg)",
                        "Tare Weight (kg)", "Remaining (kg)"
                    ]] = [
                        edit_type, edit_location.strip(),
                        float(edit_capacity), float(edit_tare),
                        float(edit_remaining)
                    ]

                    if delta != 0:
                        st.session_state.book_stock += delta
                        add_transaction(
                            edit_id, "Stock Adjustment", abs(delta),
                            edit_remaining, edit_shift,
                            f"Manual adjustment; change {delta:+.1f} kg"
                        )

                    st.success(f"{edit_id} updated successfully.")
                    st.rerun()

    st.divider()
    st.subheader("🗑️ Remove an Empty Drum")

    empty_ids = st.session_state.drums.loc[
        st.session_state.drums["Remaining (kg)"] <= 0, "Drum ID"
    ].tolist()

    if empty_ids:
        remove_id = st.selectbox(
            "Choose empty drum", empty_ids, key="remove_empty_drum"
        )
        if st.button("Remove Selected Drum"):
            st.session_state.drums = st.session_state.drums[
                st.session_state.drums["Drum ID"] != remove_id
            ].reset_index(drop=True)
            st.success(f"{remove_id} removed.")
            st.rerun()
    else:
        st.info("No empty drums are currently available for removal.")

# =========================================================
# CONSUMPTION
# =========================================================
elif page == "Consumption":
    st.markdown('<div class="section-label">Material Usage</div>',
                unsafe_allow_html=True)
    st.title("📉 Consumption Monitoring")
    st.caption("Record sealer usage and analyse consumption by drum and shift.")

    drums = current_drums()

    if drums.empty:
        st.info("Add a drum before recording consumption.")
    else:
        st.subheader("Record Consumption")

        with st.form("consumption_form"):
            c1, c2, c3 = st.columns(3)

            with c1:
                drum_id = st.selectbox(
                    "Select Drum", drums["Drum ID"].tolist()
                )
                shift = st.selectbox("Production Shift", ["A", "B", "C"])

            with c2:
                quick_amount = st.radio(
                    "Quick Quantity (kg)",
                    [1, 5, 10, 20],
                    horizontal=True
                )
                custom_amount = st.number_input(
                    "Or enter custom quantity (kg)",
                    min_value=0.0,
                    value=0.0,
                    step=0.5
                )

            with c3:
                consumption_note = st.text_input(
                    "Production / operator note",
                    placeholder="Optional note"
                )
                st.write("")
                st.caption("Consumption is simulated.")

            consume = st.form_submit_button(
                "− Record Consumption",
                type="primary",
                use_container_width=True
            )

            if consume:
                amount = (
                    float(custom_amount)
                    if custom_amount > 0
                    else float(quick_amount)
                )

                idx = st.session_state.drums.index[
                    st.session_state.drums["Drum ID"] == drum_id
                ][0]

                remaining = float(
                    st.session_state.drums.at[idx, "Remaining (kg)"]
                )

                if amount <= 0:
                    st.error("Consumption must be greater than zero.")
                elif amount > remaining:
                    st.error(
                        f"Insufficient material. Only {remaining:.1f} kg remains."
                    )
                else:
                    updated = round(remaining - amount, 2)
                    st.session_state.drums.at[
                        idx, "Remaining (kg)"
                    ] = updated

                    st.session_state.book_stock = max(
                        0.0,
                        st.session_state.book_stock - amount
                    )

                    add_transaction(
                        drum_id, "Consumption", amount, updated,
                        shift, consumption_note
                    )

                    st.success(
                        f"{amount:.1f} kg recorded against {drum_id}."
                    )
                    st.rerun()

    st.divider()
    tx = pd.DataFrame(st.session_state.transactions)

    if not tx.empty:
        usage = tx[tx["Transaction"] == "Consumption"].copy()

        if not usage.empty:
            usage["Date"] = pd.to_datetime(
                usage["Timestamp"], errors="coerce"
            ).dt.date

            total_usage = float(usage["Quantity (kg)"].sum())
            tx_count = len(usage)
            average_usage = total_usage / tx_count if tx_count else 0

            a, b, c = st.columns(3)
            a.metric("Total Recorded Consumption", f"{total_usage:.1f} kg")
            b.metric("Consumption Transactions", str(tx_count))
            c.metric("Average per Transaction", f"{average_usage:.1f} kg")

            left, right = st.columns(2)

            with left:
                st.subheader("Consumption by Drum")
                by_drum = usage.groupby("Drum ID", as_index=False)[
                    "Quantity (kg)"
                ].sum()

                fig = px.bar(
                    by_drum,
                    x="Drum ID",
                    y="Quantity (kg)",
                    color_discrete_sequence=["#087F8C"],
                    text_auto=".1f"
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(
                    styled_chart(fig), use_container_width=True
                )

            with right:
                st.subheader("Consumption by Shift")
                by_shift = usage.groupby("Shift", as_index=False)[
                    "Quantity (kg)"
                ].sum()

                fig = px.pie(
                    by_shift,
                    names="Shift",
                    values="Quantity (kg)",
                    hole=0.55,
                    color_discrete_sequence=[
                        "#087F8C", "#25B7A5", "#F0AE4E", "#6D8EA5"
                    ]
                )
                st.plotly_chart(
                    styled_chart(fig), use_container_width=True
                )

            st.subheader("Consumption Records")
            st.dataframe(
                usage.sort_values("Timestamp", ascending=False),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No consumption records yet. Record usage above.")
    else:
        st.info("No transaction data is available yet.")

    st.caption(
        "Reports use the transactions recorded in this app. "
        "Automatic production-cycle or sensor-based consumption is not connected."
    )

# =========================================================
# TRANSACTION HISTORY
# =========================================================
elif page == "Transactions":
    st.markdown('<div class="section-label">Audit Trail</div>',
                unsafe_allow_html=True)
    st.title("🧾 Transaction History")
    st.caption("Review stock receipts, consumption and inventory adjustments.")

    tx = pd.DataFrame(st.session_state.transactions)

    if tx.empty:
        st.info("No transactions have been recorded yet.")
    else:
        t1, t2, t3 = st.columns(3)

        t1.metric("Total Transactions", len(tx))
        t2.metric(
            "Material Received",
            f"{tx.loc[tx['Transaction'] == 'Drum Received', 'Quantity (kg)'].sum():.1f} kg"
        )
        t3.metric(
            "Material Consumed",
            f"{tx.loc[tx['Transaction'] == 'Consumption', 'Quantity (kg)'].sum():.1f} kg"
        )

        filter_type = st.selectbox(
            "Filter by transaction",
            ["All", "Drum Received", "Consumption", "Stock Adjustment"]
        )

        filtered = tx.copy()
        if filter_type != "All":
            filtered = filtered[
                filtered["Transaction"] == filter_type
            ]

        st.dataframe(
            filtered.sort_values("Timestamp", ascending=False),
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ Export Transactions CSV",
            data=make_csv(filtered),
            file_name="sealer_transactions.csv",
            mime="text/csv"
        )

# =========================================================
# REPORTS
# =========================================================
elif page == "Reports":
    st.markdown('<div class="section-label">Analytics & Exports</div>',
                unsafe_allow_html=True)
    st.title("📑 Inventory Reports")

    report = get_stock_report()
    physical = float(report["Remaining (kg)"].sum())
    book = float(st.session_state.book_stock)
    variance = physical - book

    a, b, c = st.columns(3)
    a.metric("Physical Inventory", f"{physical:.1f} kg")
    b.metric("Simulated Book Inventory", f"{book:.1f} kg")
    c.metric("Physical / Book Variance", f"{variance:+.1f} kg")

    st.subheader("Complete Inventory Report")
    st.dataframe(
        report,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Stock Level (%)": st.column_config.ProgressColumn(
                "Stock Level",
                min_value=0,
                max_value=100,
                format="%.1f%%"
            )
        }
    )

    st.download_button(
        "⬇️ Download Inventory CSV",
        data=make_csv(report),
        file_name="sealer_inventory_report.csv",
        mime="text/csv"
    )

    st.divider()
    st.subheader("📊 Inventory by Sealer Type")

    by_type = report.groupby("Sealer Type", as_index=False)[
        "Remaining (kg)"
    ].sum()

    fig = px.bar(
        by_type,
        x="Sealer Type",
        y="Remaining (kg)",
        color="Sealer Type",
        text_auto=".1f",
        color_discrete_sequence=["#087F8C", "#22A699", "#F0AE4E"]
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(styled_chart(fig), use_container_width=True)

    st.subheader("📆 Consumption Date Filter")

    tx = pd.DataFrame(st.session_state.transactions)

    if not tx.empty:
        tx["Parsed Date"] = pd.to_datetime(
            tx["Timestamp"], errors="coerce"
        ).dt.date

        consumption = tx[tx["Transaction"] == "Consumption"].copy()

        if not consumption.empty:
            min_date = min(consumption["Parsed Date"].dropna())
            max_date = max(consumption["Parsed Date"].dropna())

            start_date, end_date = st.date_input(
                "Select date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            ) if min_date != max_date else (
                st.date_input("Select date", value=max_date),
                max_date
            )

            filtered_usage = consumption[
                (consumption["Parsed Date"] >= start_date)
                & (consumption["Parsed Date"] <= end_date)
            ]

            total_period = float(
                filtered_usage["Quantity (kg)"].sum()
            )

            st.metric(
                "Consumption in Selected Period",
                f"{total_period:.1f} kg"
            )

            st.dataframe(
                filtered_usage.drop(columns=["Parsed Date"]),
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "⬇️ Download Period Consumption CSV",
                data=make_csv(
                    filtered_usage.drop(columns=["Parsed Date"])
                ),
                file_name="sealer_period_consumption.csv",
                mime="text/csv"
            )
        else:
            st.info("No consumption records are available for filtering.")
    else:
        st.info("Add inventory transactions to generate reports.")

# =========================================================
# FOOTER
# =========================================================
st.divider()

st.markdown(
    """
    <div style="text-align:center;padding:8px;color:#64748B;font-size:11px;">
        <b>SEALER IQ</b> &nbsp; | &nbsp;
        DIGITAL SEALER INVENTORY MONITORING SYSTEM<br>
        Automotive Body Shop Prototype • Simulation Mode • No live hardware/SAP
    </div>
    """,
    unsafe_allow_html=True
)

