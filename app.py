
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Digital Sealer Inventory Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown(
    """
    <style>
    /* Main application */
    .stApp {
        background-color: #f4f7fb;
    }

    /* Sidebar background */
    [data-testid="stSidebar"] {
        background-color: #14243b;
    }

    /* Sidebar labels and headings */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #ffffff;
    }

    /* Number and text input fields in sidebar */
    [data-testid="stSidebar"] input {
        color: #14243b !important;
        background-color: #ffffff !important;
        -webkit-text-fill-color: #14243b !important;
    }

    /* Input buttons */
    [data-testid="stSidebar"] button {
        color: #14243b;
    }

    /* Dashboard metric cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e1e7ef;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04);
    }

    /* Headings */
    h1, h2, h3 {
        color: #14243b;
    }

    /* Data tables */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# INITIAL SAMPLE INVENTORY
# --------------------------------------------------

INITIAL_DRUMS = [
    {
        "Drum ID": "DR-001",
        "Sealer Type": "PVC Sealer",
        "Location": "Line 1",
        "Initial Stock (kg)": 200.0,
        "Current Stock (kg)": 125.0,
        "Unit Cost (₹/kg)": 180.0,
    },
    {
        "Drum ID": "DR-002",
        "Sealer Type": "PU Sealer",
        "Location": "Line 1",
        "Initial Stock (kg)": 200.0,
        "Current Stock (kg)": 42.0,
        "Unit Cost (₹/kg)": 220.0,
    },
    {
        "Drum ID": "DR-003",
        "Sealer Type": "PVC Sealer",
        "Location": "Line 2",
        "Initial Stock (kg)": 180.0,
        "Current Stock (kg)": 90.0,
        "Unit Cost (₹/kg)": 180.0,
    },
    {
        "Drum ID": "DR-004",
        "Sealer Type": "MS Polymer",
        "Location": "Line 2",
        "Initial Stock (kg)": 150.0,
        "Current Stock (kg)": 28.0,
        "Unit Cost (₹/kg)": 250.0,
    },
    {
        "Drum ID": "DR-005",
        "Sealer Type": "PU Sealer",
        "Location": "Line 3",
        "Initial Stock (kg)": 200.0,
        "Current Stock (kg)": 155.0,
        "Unit Cost (₹/kg)": 220.0,
    },
    {
        "Drum ID": "DR-006",
        "Sealer Type": "PVC Sealer",
        "Location": "Warehouse",
        "Initial Stock (kg)": 250.0,
        "Current Stock (kg)": 210.0,
        "Unit Cost (₹/kg)": 180.0,
    },
]


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "drums" not in st.session_state:
    st.session_state.drums = pd.DataFrame(INITIAL_DRUMS)

if "transactions" not in st.session_state:
    st.session_state.transactions = pd.DataFrame(
        columns=[
            "Timestamp",
            "Transaction Type",
            "Drum ID",
            "Sealer Type",
            "Quantity (kg)",
            "Location",
            "Remarks",
        ]
    )


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def record_transaction(
    transaction_type,
    drum_id,
    sealer_type,
    quantity,
    location,
    remarks,
):
    """Add a transaction to the transaction history."""

    new_transaction = pd.DataFrame(
        [
            {
                "Timestamp": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "Transaction Type": transaction_type,
                "Drum ID": drum_id,
                "Sealer Type": sealer_type,
                "Quantity (kg)": float(quantity),
                "Location": location,
                "Remarks": remarks,
            }
        ]
    )

    st.session_state.transactions = pd.concat(
        [
            new_transaction,
            st.session_state.transactions,
        ],
        ignore_index=True,
    )


def format_kg(value):
    """Format a quantity in kilograms."""
    return f"{value:,.2f} kg"


def style_stock_status(value, threshold):
    """Return the stock status for a drum."""
    if value <= 0:
        return "Out of Stock"
    elif value <= threshold:
        return "Low Stock"
    return "In Stock"


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.title("🏭 Sealer Monitor")
    st.caption("Digital Inventory Management")

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Drum Inventory",
            "Consumption",
            "Transaction History",
        ],
    )

    st.divider()

    st.subheader("Inventory Settings")

    low_stock_threshold = st.number_input(
        "Low stock threshold (kg)",
        min_value=0.0,
        max_value=10000.0,
        value=50.0,
        step=5.0,
        format="%.2f",
        key="low_stock_threshold",
    )

    st.divider()

    st.caption("Demo version")
    st.caption("Sample data only")


# --------------------------------------------------
# COMMON CALCULATIONS
# --------------------------------------------------

drums = st.session_state.drums.copy()

drums["Stock Status"] = drums["Current Stock (kg)"].apply(
    lambda quantity: style_stock_status(
        quantity,
        low_stock_threshold,
    )
)

total_stock = drums["Current Stock (kg)"].sum()

total_stock_value = (
    drums["Current Stock (kg)"]
    * drums["Unit Cost (₹/kg)"]
).sum()

total_drums = len(drums)

low_stock_count = (
    drums["Current Stock (kg)"] <= low_stock_threshold
).sum()

out_of_stock_count = (
    drums["Current Stock (kg)"] <= 0
).sum()

total_consumed = (
    drums["Initial Stock (kg)"].sum()
    - drums["Current Stock (kg)"].sum()
)

# --------------------------------------------------
# PAGE 1: OVERVIEW
# --------------------------------------------------

if page == "Overview":

    st.title("Digital Sealer Inventory Dashboard")

    st.write(
        "Monitor sealer drum stock, material consumption, "
        "inventory value, and low-stock conditions."
    )

    st.caption(
        f"Last page refresh: {datetime.now().strftime('%d %b %Y, %H:%M:%S')}"
    )

    st.divider()

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Stock",
        format_kg(total_stock),
    )

    col2.metric(
        "Total Drums",
        total_drums,
    )

    col3.metric(
        "Low Stock Drums",
        int(low_stock_count),
    )

    col4.metric(
        "Inventory Value",
        f"₹{total_stock_value:,.0f}",
    )

    st.divider()

    left_col, right_col = st.columns(2)

    # Stock by sealer type
    with left_col:
        st.subheader("Stock by Sealer Type")

        stock_by_type = (
            drums.groupby("Sealer Type", as_index=False)
            ["Current Stock (kg)"]
            .sum()
        )

        stock_chart = (
            alt.Chart(stock_by_type)
            .mark_bar(
                cornerRadiusEnd=5,
            )
            .encode(
                x=alt.X(
                    "Sealer Type:N",
                    title="Sealer Type",
                    sort="-y",
                    axis=alt.Axis(labelAngle=-25),
                ),
                y=alt.Y(
                    "Current Stock (kg):Q",
                    title="Current Stock (kg)",
                ),
                tooltip=[
                    "Sealer Type",
                    alt.Tooltip(
                        "Current Stock (kg):Q",
                        format=".2f",
                    ),
                ],
            )
            .properties(height=320)
        )

        st.altair_chart(
            stock_chart,
            use_container_width=True,
        )

    # Stock by location
    with right_col:
        st.subheader("Stock by Location")

        stock_by_location = (
            drums.groupby("Location", as_index=False)
            ["Current Stock (kg)"]
            .sum()
        )

        location_chart = (
            alt.Chart(stock_by_location)
            .mark_arc(innerRadius=65)
            .encode(
                theta=alt.Theta(
                    "Current Stock (kg):Q",
                    stack=True,
                ),
                color=alt.Color(
                    "Location:N",
                    title="Location",
                ),
                tooltip=[
                    "Location",
                    alt.Tooltip(
                        "Current Stock (kg):Q",
                        format=".2f",
                    ),
                ],
            )
            .properties(height=320)
        )

        st.altair_chart(
            location_chart,
            use_container_width=True,
        )

    st.divider()

    st.subheader("Low Stock Alerts")

    low_stock_drums = drums[
        drums["Current Stock (kg)"] <= low_stock_threshold
    ].copy()

    if low_stock_drums.empty:
        st.success(
            "All drums are above the configured low-stock threshold."
        )
    else:
        st.warning(
            f"{len(low_stock_drums)} drum(s) are at or below "
            f"{low_stock_threshold:.2f} kg."
        )

        st.dataframe(
            low_stock_drums[
                [
                    "Drum ID",
                    "Sealer Type",
                    "Location",
                    "Current Stock (kg)",
                    "Stock Status",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("Current Drum Summary")

    st.dataframe(
        drums[
            [
                "Drum ID",
                "Sealer Type",
                "Location",
                "Current Stock (kg)",
                "Stock Status",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# PAGE 2: DRUM INVENTORY
# --------------------------------------------------

elif page == "Drum Inventory":

    st.title("Drum Inventory")

    st.write(
        "View the current stock level, location, and value of each drum."
    )

    # Filters
    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        sealer_options = [
            "All",
            *sorted(
                st.session_state.drums["Sealer Type"]
                .dropna()
                .unique()
                .tolist()
            ),
        ]

        selected_sealer = st.selectbox(
            "Filter by sealer type",
            sealer_options,
        )

    with filter_col2:
        location_options = [
            "All",
            *sorted(
                st.session_state.drums["Location"]
                .dropna()
                .unique()
                .tolist()
            ),
        ]

        selected_location = st.selectbox(
            "Filter by location",
            location_options,
        )

    filtered_drums = drums.copy()

    if selected_sealer != "All":
        filtered_drums = filtered_drums[
            filtered_drums["Sealer Type"] == selected_sealer
        ]

    if selected_location != "All":
        filtered_drums = filtered_drums[
            filtered_drums["Location"] == selected_location
        ]

    filtered_drums["Stock Value (₹)"] = (
        filtered_drums["Current Stock (kg)"]
        * filtered_drums["Unit Cost (₹/kg)"]
    )

    st.dataframe(
        filtered_drums[
            [
                "Drum ID",
                "Sealer Type",
                "Location",
                "Initial Stock (kg)",
                "Current Stock (kg)",
                "Unit Cost (₹/kg)",
                "Stock Value (₹)",
                "Stock Status",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    csv_inventory = filtered_drums.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download Inventory CSV",
        data=csv_inventory,
        file_name="sealer_inventory.csv",
        mime="text/csv",
    )

    st.divider()

    st.subheader("Add a New Drum")

    with st.form("add_drum_form", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:
            new_drum_id = st.text_input(
                "Drum ID",
                placeholder="Example: DR-007",
            )

            new_sealer_type = st.selectbox(
                "Sealer Type",
                [
                    "PVC Sealer",
                    "PU Sealer",
                    "MS Polymer",
                    "Other",
                ],
            )

            new_location = st.selectbox(
                "Location",
                [
                    "Line 1",
                    "Line 2",
                    "Line 3",
                    "Warehouse",
                ],
            )

        with col2:
            new_initial_stock = st.number_input(
                "Initial Stock (kg)",
                min_value=0.0,
                value=200.0,
                step=5.0,
            )

            new_current_stock = st.number_input(
                "Current Stock (kg)",
                min_value=0.0,
                value=200.0,
                step=5.0,
            )

            new_unit_cost = st.number_input(
                "Unit Cost (₹/kg)",
                min_value=0.0,
                value=180.0,
                step=10.0,
            )

        add_drum = st.form_submit_button(
            "Add Drum",
            use_container_width=True,
        )

        if add_drum:
            existing_ids = (
                st.session_state.drums["Drum ID"]
                .astype(str)
                .str.strip()
                .str.upper()
                .tolist()
            )

            normalized_id = new_drum_id.strip().upper()

            if not normalized_id:
                st.error("Please enter a Drum ID.")

            elif normalized_id in existing_ids:
                st.error("That Drum ID already exists.")

            elif new_current_stock > new_initial_stock:
                st.error(
                    "Current stock cannot exceed initial stock."
                )

            else:
                new_row = pd.DataFrame(
                    [
                        {
                            "Drum ID": normalized_id,
                            "Sealer Type": new_sealer_type,
                            "Location": new_location,
                            "Initial Stock (kg)": new_initial_stock,
                            "Current Stock (kg)": new_current_stock,
                            "Unit Cost (₹/kg)": new_unit_cost,
                        }
                    ]
                )

                st.session_state.drums = pd.concat(
                    [
                        st.session_state.drums,
                        new_row,
                    ],
                    ignore_index=True,
                )

                record_transaction(
                    "Drum Added",
                    normalized_id,
                    new_sealer_type,
                    new_current_stock,
                    new_location,
                    "New drum added to inventory",
                )

                st.success(
                    f"Drum {normalized_id} added successfully."
                )

                st.rerun()


# --------------------------------------------------
# PAGE 3: CONSUMPTION
# --------------------------------------------------

elif page == "Consumption":

    st.title("Sealer Consumption")

    st.write(
        "Record material consumption or add stock received for a drum."
    )

    drum_ids = (
        st.session_state.drums["Drum ID"]
        .astype(str)
        .tolist()
    )

    if not drum_ids:
        st.info("Add a drum before recording transactions.")

    else:
        selected_drum_id = st.selectbox(
            "Select Drum",
            drum_ids,
        )

        selected_index = st.session_state.drums.index[
            st.session_state.drums["Drum ID"]
            == selected_drum_id
        ][0]

        selected_drum = st.session_state.drums.loc[
            selected_index
        ]

        info1, info2, info3 = st.columns(3)

        info1.metric(
            "Sealer Type",
            selected_drum["Sealer Type"],
        )

        info2.metric(
            "Location",
            selected_drum["Location"],
        )

        info3.metric(
            "Current Stock",
            format_kg(selected_drum["Current Stock (kg)"]),
        )

        st.divider()

        transaction_type = st.radio(
            "Transaction Type",
            [
                "Consumption",
                "Stock Receipt",
            ],
            horizontal=True,
        )

        with st.form("transaction_form", clear_on_submit=True):

            quantity = st.number_input(
                "Quantity (kg)",
                min_value=0.01,
                value=5.0,
                step=1.0,
            )

            remarks = st.text_input(
                "Remarks",
                placeholder="Example: Production line usage",
            )

            submit_transaction = st.form_submit_button(
                "Submit Transaction",
                use_container_width=True,
            )

            if submit_transaction:

                current_stock = float(
                    st.session_state.drums.at[
                        selected_index,
                        "Current Stock (kg)",
                    ]
                )

                if transaction_type == "Consumption":

                    if quantity > current_stock:
                        st.error(
                            "Insufficient stock. "
                            f"Available: {current_stock:.2f} kg."
                        )

                    else:
                        st.session_state.drums.at[
                            selected_index,
                            "Current Stock (kg)",
                        ] = current_stock - quantity

                        record_transaction(
                            "Consumption",
                            selected_drum_id,
                            selected_drum["Sealer Type"],
                            quantity,
                            selected_drum["Location"],
                            remarks or "Material consumed",
                        )

                        st.success(
                            f"{quantity:.2f} kg consumed from "
                            f"{selected_drum_id}."
                        )

                        st.rerun()

                else:
                    updated_stock = current_stock + quantity

                    st.session_state.drums.at[
                        selected_index,
                        "Current Stock (kg)",
                    ] = updated_stock

                    st.session_state.drums.at[
                        selected_index,
                        "Initial Stock (kg)",
                    ] = (
                        float(
                            st.session_state.drums.at[
                                selected_index,
                                "Initial Stock (kg)",
                            ]
                        )
                        + quantity
                    )

                    record_transaction(
                        "Stock Receipt",
                        selected_drum_id,
                        selected_drum["Sealer Type"],
                        quantity,
                        selected_drum["Location"],
                        remarks or "Stock received",
                    )

                    st.success(
                        f"{quantity:.2f} kg added to "
                        f"{selected_drum_id}."
                    )

                    st.rerun()

    st.divider()

    st.subheader("Current Stock by Drum")

    current_stock_chart = (
        alt.Chart(drums)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X(
                "Drum ID:N",
                title="Drum ID",
                sort=None,
            ),
            y=alt.Y(
                "Current Stock (kg):Q",
                title="Current Stock (kg)",
            ),
            color=alt.Color(
                "Stock Status:N",
                scale=alt.Scale(
                    domain=[
                        "In Stock",
                        "Low Stock",
                        "Out of Stock",
                    ],
                    range=[
                        "#2e8b57",
                        "#f0ad4e",
                        "#d9534f",
                    ],
                ),
            ),
            tooltip=[
                "Drum ID",
                "Sealer Type",
                "Location",
                alt.Tooltip(
                    "Current Stock (kg):Q",
                    format=".2f",
                ),
                "Stock Status",
            ],
        )
        .properties(height=350)
    )

    st.altair_chart(
        current_stock_chart,
        use_container_width=True,
    )


# --------------------------------------------------
# PAGE 4: TRANSACTION HISTORY
# --------------------------------------------------

elif page == "Transaction History":

    st.title("Transaction History")

    st.write(
        "Review recorded consumption, stock receipts, and new drums."
    )

    transactions = st.session_state.transactions.copy()

    if transactions.empty:
        st.info(
            "No transactions recorded yet. "
            "Use the Consumption page to record a transaction."
        )

    else:
        transactions["Quantity (kg)"] = pd.to_numeric(
            transactions["Quantity (kg)"],
            errors="coerce",
        )

        col1, col2 = st.columns(2)

        with col1:
            transaction_types = [
                "All",
                *sorted(
                    transactions["Transaction Type"]
                    .dropna()
                    .unique()
                    .tolist()
                ),
            ]

            selected_transaction_type = st.selectbox(
                "Filter by transaction type",
                transaction_types,
            )

        with col2:
            transaction_drum_ids = [
                "All",
                *sorted(
                    transactions["Drum ID"]
                    .dropna()
                    .unique()
                    .tolist()
                ),
            ]

            selected_transaction_drum = st.selectbox(
                "Filter by drum",
                transaction_drum_ids,
            )

        filtered_transactions = transactions.copy()

        if selected_transaction_type != "All":
            filtered_transactions = filtered_transactions[
                filtered_transactions["Transaction Type"]
                == selected_transaction_type
            ]

        if selected_transaction_drum != "All":
            filtered_transactions = filtered_transactions[
                filtered_transactions["Drum ID"]
                == selected_transaction_drum
            ]

        st.dataframe(
            filtered_transactions,
            use_container_width=True,
            hide_index=True,
        )

        csv_transactions = (
            filtered_transactions.to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "⬇️ Download Transaction History CSV",
            data=csv_transactions,
            file_name="sealer_transaction_history.csv",
            mime="text/csv",
        )

        st.divider()

        st.subheader("Transaction Quantities")

        chart_data = (
            filtered_transactions[
                filtered_transactions["Transaction Type"].isin(
                    ["Consumption", "Stock Receipt"]
                )
            ]
            .groupby(
                "Transaction Type",
                as_index=False,
            )["Quantity (kg)"]
            .sum()
        )

        if chart_data.empty:
            st.info(
                "No consumption or stock receipt transactions "
                "match the selected filters."
            )

        else:
            transaction_chart = (
                alt.Chart(chart_data)
                .mark_bar(cornerRadiusEnd=5)
                .encode(
                    x=alt.X(
                        "Transaction Type:N",
                        title="Transaction Type",
                    ),
                    y=alt.Y(
                        "Quantity (kg):Q",
                        title="Total Quantity (kg)",
                    ),
                    color=alt.Color(
                        "Transaction Type:N",
                        legend=None,
                    ),
                    tooltip=[
                        "Transaction Type",
                        alt.Tooltip(
                            "Quantity (kg):Q",
                            format=".2f",
                        ),
                    ],
                )
                .properties(height=320)
            )

            st.altair_chart(
                transaction_chart,
                use_container_width=True,
            )

    st.divider()

    if st.button(
        "Reset Demo Data",
        type="secondary",
    ):
        st.session_state.drums = pd.DataFrame(INITIAL_DRUMS)

        st.session_state.transactions = pd.DataFrame(
            columns=[
                "Timestamp",
                "Transaction Type",
                "Drum ID",
                "Sealer Type",
                "Quantity (kg)",
                "Location",
                "Remarks",
            ]
        )

        st.success("Demo inventory and transaction history reset.")

        st.rerun()


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Digital Sealer Inventory Monitoring System | "
    "Streamlit Demo | Sample data stored in session memory"
)

