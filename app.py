import time
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sealer Drum Flow – Plant Simulation", page_icon="🛢️", layout="wide")

# ----------------------------- DATA -----------------------------
STEPS = [
    ("Arrival at Plant", "🚚", "Sealer drums arrive from supplier",
     ["GRN (Goods Receipt Note) created in SAP", "Delivery challan & PO checked"], "GRN created in SAP"),
    ("Unloading & Initial Check", "📦", "Forklift / pallet truck unloading",
     ["Visual inspection (damage, leakage, seal)", "Barcode scanned to capture Drum ID / Lot No."], "Barcode scanned – Drum ID & Lot captured"),
    ("Quality Check", "📋", "Verify lot, manufacture date & expiry",
     ["Check quantity as per PO", "Update GRN and quality status in SAP"], "Quality status = OK in SAP"),
    ("Move to Storage Area", "🏭", "Transport drums to sealer storage area",
     ["Use forklift / pallet truck", "Follow safety guidelines"], "Drums moved to storage area"),
    ("Storage & Tagging", "🏷️", "Place drums in rack / floor location",
     ["Update location in SAP", "Attach tag (Drum ID, Lot No, Expiry Date)"], "Location & tag updated"),
    ("Inventory Monitoring", "🖥️", "Real-time stock tracking",
     ["Monitor expiry date and quantity", "System alerts for low stock / near expiry"], "Stock live – no alerts"),
    ("FIFO / FEFO", "🔄", "Oldest / earliest-expiry drum goes first",
     ["Ensure correct drum is issued first", "Avoid expiry and quality risk"], "FEFO selects earliest-expiry drum"),
    ("Ready for Line Issue", "✅", "Drum brought from storage",
     ["Barcode scanned and weighed (load cell)", "Issue recorded in SAP / system"], "Issue posted in SAP"),
    ("Line Side Consumption", "📈", "Drum placed on weighing platform",
     ["Consumption = previous weight − current weight", "Data sent to PLC/IoT and shown on BI screen"], "Consumption streaming to BI"),
    ("Drum Empty / Return", "♻️", "Empty drum returned to storage",
     ["Marked as empty and scanned", "Records updated in SAP"], "Drum marked EMPTY in SAP"),
    ("Cycle Continues", "🔁", "Next drum issued as per FIFO/FEFO",
     ["Continuous monitoring", "No stock-out and no expiry"], "Cycle restarts with next drum"),
]
N = len(STEPS)
DRUM_L = 200
SUB_TICKS = 4  # consumption ticks during step 9


def init():
    ss = st.session_state
    ss.step = -1
    ss.sub = 0
    ss.playing = False
    ss.cur = 0
    ss.recv = 0
    ss.done = 0
    ss.log = []
    ss.inv = [
        {"Drum ID": "D001", "Lot No.": "L123", "Expiry Date": "12-2026", "Qty (L)": DRUM_L, "Status": "In Stock"},
        {"Drum ID": "D002", "Lot No.": "L124", "Expiry Date": "01-2027", "Qty (L)": DRUM_L, "Status": "In Stock"},
        {"Drum ID": "D003", "Lot No.": "L125", "Expiry Date": "03-2027", "Qty (L)": DRUM_L, "Status": "In Stock"},
    ]


if "step" not in st.session_state:
    init()
ss = st.session_state


def add_log(msg):
    ss.log.insert(0, f"[{datetime.now():%H:%M:%S}] {msg}")


def advance():
    """Move the simulation forward by one tick."""
    if ss.step == 8 and ss.sub < SUB_TICKS:  # consumption sub-ticks
        ss.sub += 1
        ss.inv[ss.cur]["Qty (L)"] = DRUM_L - ss.sub * (DRUM_L // SUB_TICKS)
        add_log(f"Load cell: {ss.inv[ss.cur]['Qty (L)']} L left on {ss.inv[ss.cur]['Drum ID']}")
        return
    ss.step = 0 if ss.step >= N - 1 else ss.step + 1
    ss.sub = 0
    s = ss.step
    if s == 0:
        ss.recv += 1
    elif s == 6:
        ss.inv[ss.cur]["Status"] = "FEFO – next"
    elif s == 7:
        ss.inv[ss.cur]["Status"] = "Issued"
    elif s == 8:
        ss.inv[ss.cur]["Status"] = "On line"
    elif s == 9:
        ss.inv[ss.cur].update({"Qty (L)": 0, "Status": "EMPTY"})
        ss.done += 1
    elif s == 10:
        nxt = next((k for k, d in enumerate(ss.inv) if d["Status"] != "EMPTY"), None)
        if nxt is None:
            n = len(ss.inv) + 1
            ss.inv.append({"Drum ID": f"D{n:03d}", "Lot No.": f"L{122 + n}", "Expiry Date": "06-2027",
                           "Qty (L)": DRUM_L, "Status": "In Stock"})
            nxt = len(ss.inv) - 1
        ss.cur = nxt
    add_log(STEPS[s][4])


# ----------------------------- STYLE -----------------------------
st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 20% 0,#14306b,#0b1630 55%);color:#e8eeff}
h1.t{text-align:center;font-size:2.6rem;background:linear-gradient(90deg,#6db3ff,#27d17f);
     -webkit-background-clip:text;color:transparent;margin-bottom:0}
p.sub{text-align:center;color:#9fb0dd;margin-bottom:10px}
.track{display:flex;gap:6px;overflow-x:auto;padding:8px 2px}
.nd{flex:1;min-width:84px;text-align:center;font-size:11px;color:#9fb0dd}
.nd b{display:grid;place-items:center;width:36px;height:36px;border-radius:50%;background:#233a75;
      margin:0 auto 6px;color:#fff;font-size:15px}
.nd.done b{background:#27d17f}.nd.on b{background:#2f8cff;transform:scale(1.3);box-shadow:0 0 0 6px #2f8cff44}
.nd.on{color:#fff;font-weight:600}
.card{background:#13224a;border:1px solid #25376b;border-radius:16px;padding:18px;box-shadow:0 8px 30px #0006}
.card h2{margin:0 0 6px 0;font-size:1.5rem;color:#fff}
.card li{color:#cfdbff;line-height:1.8}
.tag{background:#233a75;border-radius:20px;padding:3px 12px;font-size:12px;color:#9fb0dd}
.tank{width:90px;height:140px;border:3px solid #4c9bff;border-radius:12px;position:relative;overflow:hidden;background:#0a1938}
.lvl{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(#4c9bff,#1a4fb0);transition:height .5s}
.big{font-size:2.4rem;font-weight:700;color:#6db3ff}
.kpi{background:#0f1c40;border-radius:12px;padding:14px;text-align:center}
.kpi div{font-size:2rem;font-weight:700;color:#27d17f}.kpi small{color:#9fb0dd}
.res span{display:inline-block;background:#27d17f22;color:#7dffc0;padding:8px 16px;border-radius:20px;
          font-weight:600;margin:4px}
.logbox{height:190px;overflow:auto;font-family:Consolas,monospace;font-size:13px;color:#9fe0b8;
        background:#07102a;border-radius:10px;padding:10px}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="t">🛢️ Sealer Drum Flow – Live Plant Simulation</h1>'
            '<p class="sub">Supplier arrival → storage → FIFO/FEFO → line-side consumption · SAP · Barcode · Load Cell</p>',
            unsafe_allow_html=True)

# ----------------------------- CONTROLS -----------------------------
c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 2, 1])
if c1.button("⏸ Pause" if ss.playing else "▶ Start", use_container_width=True, type="primary"):
    ss.playing = not ss.playing
    if ss.playing and ss.step == -1:
        advance()
    st.rerun()
if c2.button("⏭ Next Step", use_container_width=True):
    ss.playing = False
    advance()
    st.rerun()
if c3.button("↺ Reset", use_container_width=True):
    init()
    st.rerun()
speed = c4.select_slider("Speed", options=["Slow", "Normal", "Fast"], value="Normal")
delay = {"Slow": 3.0, "Normal": 1.8, "Fast": 0.8}[speed]
jump = c5.selectbox("Jump to step", ["—"] + [f"{k + 1}. {s[0]}" for k, s in enumerate(STEPS)])
if jump != "—":
    target = int(jump.split(".")[0]) - 1
    if target != ss.step:
        ss.playing = False
        ss.step = target - 1
        advance()
        st.rerun()

# ----------------------------- TRACKER -----------------------------
nodes = "".join(
    f'<div class="nd {"done" if k < ss.step else "on" if k == ss.step else ""}"><b>{"✓" if k < ss.step else k + 1}</b>{s[0]}</div>'
    for k, s in enumerate(STEPS))
st.markdown(f'<div class="card"><div class="track">{nodes}</div></div>', unsafe_allow_html=True)
st.progress(max(ss.step, 0) / (N - 1))

# ----------------------------- STEP + INVENTORY -----------------------------
left, right = st.columns([1.2, 1])
with left:
    if ss.step < 0:
        st.markdown('<div class="card"><h2>👋 Press ▶ Start</h2><p style="color:#cfdbff">Watch a sealer drum travel '
                    'through all 11 stages – from supplier arrival to line-side consumption and the continuing cycle.</p></div>',
                    unsafe_allow_html=True)
    else:
        name, icon, desc, pts, _ = STEPS[ss.step]
        lis = "".join(f"<li>{p}</li>" for p in pts)
        st.markdown(f'<div class="card"><span class="tag">Step {ss.step + 1} of {N}</span>'
                    f'<h2 style="margin-top:10px">{icon} {name}</h2><p style="color:#cfdbff">{desc}</p><ul>{lis}</ul></div>',
                    unsafe_allow_html=True)
with right:
    st.markdown("##### 📊 Inventory Monitor (SAP)")
    df = pd.DataFrame(ss.inv)

    def hl(row):
        if row["Status"] == "EMPTY":
            return ["color:#667"] * len(row)
        if row["Status"] in ("FEFO – next", "Issued", "On line"):
            return ["background-color:#27d17f33"] * len(row)
        return [""] * len(row)

    st.dataframe(df.style.apply(hl, axis=1), hide_index=True, use_container_width=True)

# ----------------------------- WEIGHING + LOG -----------------------------
a, b = st.columns(2)
with a:
    st.markdown("##### ⚖️ Line-Side Weighing Platform (Load Cell)")
    on_scale = ss.step in (7, 8) or (ss.step == 10)
    qty = ss.inv[ss.cur]["Qty (L)"] if ss.step >= 7 else 0
    if ss.step == 10:
        qty = ss.inv[ss.cur]["Qty (L)"]
    consumed = DRUM_L - qty if ss.step in (8, 9) else 0
    status = "Streaming to PLC/IoT" if ss.step == 8 else "Idle"
    st.markdown(
        f'<div class="card" style="display:flex;gap:20px;align-items:center">'
        f'<div class="tank"><div class="lvl" style="height:{qty / DRUM_L * 100}%"></div></div>'
        f'<div><div class="big">{qty} L</div><div style="color:#9fb0dd">Consumed: <b style="color:#fff">{consumed} L</b></div>'
        f'<div style="color:#9fb0dd;margin-top:6px">Data → PLC/IoT → BI screen</div>'
        f'<span class="tag">{status}</span></div></div>', unsafe_allow_html=True)
with b:
    st.markdown("##### 🧾 System Log")
    logs = "".join(f"<div>{l}</div>" for l in ss.log[:30])
    st.markdown(f'<div class="logbox">{logs}</div>', unsafe_allow_html=True)

# ----------------------------- KPIs -----------------------------
total_cons = sum(DRUM_L - d["Qty (L)"] for d in ss.inv)
k = st.columns(4)
for col, (val, lab) in zip(k, [(ss.recv, "Drums Received"), (ss.done, "Drums Consumed"),
                               (f"{total_cons} L", "Total Consumption"), (0, "Expiry Losses")]):
    col.markdown(f'<div class="kpi"><div>{val}</div><small>{lab}</small></div>', unsafe_allow_html=True)

st.markdown('<br><div class="card res" style="text-align:center"><h2>✅ Result / Conclusion</h2>'
            '<span>Accurate tracking</span><span>Real-time visibility</span><span>FIFO / FEFO</span>'
            '<span>Reduced expiry & waste</span><span>Safe handling</span><span>Efficient consumption</span></div>',
            unsafe_allow_html=True)

# ----------------------------- AUTOPLAY LOOP -----------------------------
if ss.playing:
    time.sleep(delay)
    advance()
    st.rerun()
