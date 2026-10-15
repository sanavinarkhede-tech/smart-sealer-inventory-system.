import random
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sealer Drum Digital Twin", page_icon="🛢️", layout="wide")

DRUM, TICK_H = 200, 4          # litres per drum, simulated hours per tick
START = datetime(2026, 10, 15, 8, 0)

# ============================ SIMULATION ENGINE ============================
def new_drum(S, loc, exp=None):
    S["n"] += 1
    day = S["t"] / 24
    return dict(id=f"D{S['n']:03d}", lot=f"L{100 + S['n']}", loc=loc, q=DRUM,
                exp=exp if exp is not None else day + S["rng"].randint(8, 30))

def new_state(seed=7):
    S = dict(t=0, n=0, rng=random.Random(seed), drums=[], line=None, log=[], hist=[],
             consumed_l=0, drums_done=0, wasted_l=0, wasted_n=0, stockouts=0, received=0)
    for _ in range(8):
        S["drums"].append(new_drum(S, "Storage"))
    return S

def log(S, msg, kind="ok"):
    S["log"].insert(0, (START + timedelta(hours=S["t"]), kind, msg))

def step(S, policy, rate, every, batch):
    S["t"] += TICK_H
    day = S["t"] / 24
    # 1) Receiving -> QC -> Storage pipeline
    for d in S["drums"]:
        if d["loc"] == "QC":
            d["loc"] = "Storage"; log(S, f"{d['id']} tagged & stored in SAP (Lot {d['lot']})")
        elif d["loc"] == "Receiving":
            d["loc"] = "QC"; log(S, f"{d['id']} barcode scanned, quality check started", "info")
    # 2) Truck arrival
    if S["t"] % (every * 24) == 0:
        for _ in range(batch):
            S["drums"].append(new_drum(S, "Receiving")); S["received"] += 1
        log(S, f"🚚 Truck arrived: {batch} drums, GRN created in SAP", "info")
    # 3) Expiry
    for d in list(S["drums"]):
        if d["loc"] == "Storage" and d["exp"] < day:
            S["drums"].remove(d); S["wasted_l"] += d["q"]; S["wasted_n"] += 1
            log(S, f"❌ {d['id']} EXPIRED in storage – {d['q']} L wasted", "bad")
    # 4) Line issue + load-cell consumption
    if S["line"] is None:
        stock = [d for d in S["drums"] if d["loc"] == "Storage"]
        if stock:
            d = min(stock, key=lambda x: x["exp"]) if policy == "FEFO" else S["rng"].choice(stock)
            d["loc"] = "Line"; S["line"] = d
            log(S, f"✅ {d['id']} issued to line ({policy}) – exp in {d['exp'] - day:.0f} d")
        else:
            S["stockouts"] += 1; log(S, "⚠️ STOCK-OUT – line waiting for drum", "bad")
    d = S["line"]
    if d:
        use = min(d["q"], rate * TICK_H); d["q"] -= use; S["consumed_l"] += use
        if d["q"] <= 0:
            S["drums"].remove(d); S["drums_done"] += 1; S["line"] = None
            log(S, f"♻️ {d['id']} empty – scanned & returned, SAP updated", "info")
    S["hist"].append(dict(t=START + timedelta(hours=S["t"]),
                          Stock=sum(x["loc"] == "Storage" for x in S["drums"]),
                          LineWeight=S["line"]["q"] if S["line"] else 0,
                          Consumed=S["consumed_l"], Wasted=S["wasted_l"]))

def compare(rate, every, batch, days=60):
    out = []
    for pol in ("FEFO", "Random (no system)"):
        S = new_state()
        for _ in range(days * 24 // TICK_H):
            step(S, "FEFO" if pol == "FEFO" else "Random", rate, every, batch)
        out.append(dict(Policy=pol, **{"Waste (L)": S["wasted_l"], "Expired drums": S["wasted_n"],
                                       "Stock-outs": S["stockouts"], "Consumed (L)": round(S["consumed_l"])}))
    return pd.DataFrame(out)

# ============================ STATE + SIDEBAR ============================
if "S" not in st.session_state:
    st.session_state.S, st.session_state.play = new_state(), False
ss = st.session_state

with st.sidebar:
    st.markdown("## ⚙️ Control Room")
    policy = st.radio("Issue policy", ["FEFO", "Random"], help="FEFO = First Expiry First Out (SAP-driven)")
    rate = st.slider("Line consumption (L/hour)", 5, 25, 10)
    every = st.slider("Truck arrives every (days)", 1, 7, 3)
    batch = st.slider("Drums per truck", 1, 10, 4)
    speed = st.slider("Refresh (sec / tick)", 0.3, 2.0, 0.8)
    a, b = st.columns(2)
    if a.button("⏸ Pause" if ss.play else "▶ Start", type="primary", use_container_width=True):
        ss.play = not ss.play; st.rerun()
    if b.button("↺ Reset", use_container_width=True):
        ss.S, ss.play = new_state(), False; st.rerun()
    if st.button("⏭ One tick (+4 h)", use_container_width=True):
        step(ss.S, policy, rate, every, batch); st.rerun()
    st.caption("1 tick = 4 simulated hours")

# ============================ STYLE ============================
st.markdown("""<style>
.stApp{background:radial-gradient(circle at 15% 0,#16367a,#0a1330 55%);}
.hero{background:linear-gradient(90deg,#0f3d91,#1565c0 50%,#0b8f6a);border-radius:18px;padding:22px 28px;
      box-shadow:0 10px 40px #0008;margin-bottom:14px}
.hero h1{margin:0;font-size:2.1rem;color:#fff}.hero p{margin:4px 0 0;color:#cfe3ff}
.live{float:right;background:#ff3b4e;color:#fff;border-radius:20px;padding:4px 14px;font-weight:700;font-size:13px;
      animation:bl 1.2s infinite}.paused{background:#6b7a99;animation:none}
@keyframes bl{50%{opacity:.4}}
[data-testid=stMetric]{background:#13224a;border:1px solid #25376b;border-radius:14px;padding:12px 16px}
.plant{display:grid;grid-template-columns:1fr 36px 1fr 36px 1.6fr 36px 1.1fr;gap:6px;align-items:stretch}
.zone{background:linear-gradient(160deg,#15296a,#0e1c47);border:1px solid #2c4590;border-radius:16px;padding:14px;min-height:230px}
.zone h4{margin:0 0 4px;color:#fff;font-size:15px}.zone small{color:#9fb0dd}
.arr{display:grid;place-items:center;color:#4c9bff;font-size:26px;animation:mv 1s infinite}
@keyframes mv{50%{transform:translateX(5px)}}
.rack{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.dr{width:30px;height:38px;border-radius:6px/8px;border:2px solid #0d2b66;background:linear-gradient(90deg,#1a4fb0,#4c9bff 45%,#1a4fb0)}
.g{box-shadow:0 0 8px #27d17f;border-color:#27d17f}.y{box-shadow:0 0 8px #ffb020;border-color:#ffb020}
.r{box-shadow:0 0 10px #ff5c6c;border-color:#ff5c6c;animation:bl 1s infinite}
.pulse{animation:pl 1s infinite}@keyframes pl{50%{transform:scale(1.15)}}
.tank{width:70px;height:120px;border:3px solid #4c9bff;border-radius:12px;position:relative;overflow:hidden;background:#091536}
.lvl{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(#5aa8ff,#1a4fb0);transition:height .6s}
.big{font-size:2rem;font-weight:800;color:#7cc0ff}
.badge{display:inline-block;border-radius:12px;padding:2px 10px;font-size:12px;font-weight:700;margin:2px 0}
.b-ok{background:#27d17f33;color:#7dffc0}.b-bad{background:#ff5c6c33;color:#ff9aa5}.b-info{background:#2f8cff33;color:#9bc8ff}
.logbox{height:260px;overflow:auto;background:#070f2a;border-radius:12px;padding:10px;font:13px Consolas,monospace}
.logbox .ok{color:#8ff0b8}.logbox .bad{color:#ff8a98}.logbox .info{color:#8fc3ff}.logbox span{color:#6f82b3}
.flow{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}
.fc{background:#13224a;border:1px solid #2c4590;border-radius:14px;padding:14px}
.fc b{display:inline-grid;place-items:center;width:28px;height:28px;border-radius:50%;background:#2f8cff;color:#fff;margin-right:8px}
.fc p{color:#b9c8ee;font-size:13px;margin:6px 0 0}
</style>""", unsafe_allow_html=True)

live_badge = '<span class="live">● LIVE</span>' if ss.play else '<span class="live paused">❚❚ PAUSED</span>'
st.markdown(f'<div class="hero">{live_badge}<h1>🛢️ Sealer Drum Digital Twin</h1>'
            '<p>Real-time plant simulation · SAP · Barcode · Load Cell · FIFO/FEFO · Expiry-risk analytics</p></div>',
            unsafe_allow_html=True)

# ============================ LIVE DASHBOARD ============================
def drums_html(ds, cls_fn=lambda d: ""):
    return "".join(f'<div class="dr {cls_fn(d)}" title="{d["id"]} | {d["lot"]}"></div>' for d in ds) or "<small>— empty —</small>"

@st.fragment(run_every=speed if ss.play else None)
def dashboard():
    S = ss.S
    if ss.play:
        step(S, policy, rate, every, batch)
    day = S["t"] / 24
    now = START + timedelta(hours=S["t"])
    storage = sorted([d for d in S["drums"] if d["loc"] == "Storage"], key=lambda d: d["exp"])
    recv = [d for d in S["drums"] if d["loc"] == "Receiving"]
    qc = [d for d in S["drums"] if d["loc"] == "QC"]
    near = [d for d in storage if d["exp"] - day < 5]
    cls = lambda d: "r" if d["exp"] - day < 5 else "y" if d["exp"] - day < 12 else "g"

    st.caption(f"🕒 Plant clock: **{now:%d %b %Y, %H:%M}**  ·  Day {day:.1f}")
    k = st.columns(6)
    k[0].metric("Drums in storage", len(storage), "LOW STOCK" if len(storage) < 3 else None, delta_color="inverse")
    k[1].metric("Drums consumed", S["drums_done"])
    k[2].metric("Consumption", f"{S['consumed_l']:,.0f} L")
    k[3].metric("Near-expiry alerts", len(near), delta_color="inverse")
    k[4].metric("Expiry waste", f"{S['wasted_l']:,.0f} L", f"{S['wasted_n']} drums" if S["wasted_n"] else None, delta_color="inverse")
    k[5].metric("Stock-outs", S["stockouts"], delta_color="inverse")

    t1, t2, t3, t4 = st.tabs(["🏭 Live Plant Floor", "📈 Analytics", "📦 Inventory (SAP)", "🧭 Process Flow"])

    with t1:
        ln = S["line"]
        q = ln["q"] if ln else 0
        st.markdown(f"""<div class="plant">
        <div class="zone"><h4>🚚 1-2 Receiving</h4><small>GRN · unload · barcode</small><div class="rack">{drums_html(recv)}</div></div>
        <div class="arr">➜</div>
        <div class="zone"><h4>📋 3 Quality Check</h4><small>Lot · expiry · qty</small><div class="rack">{drums_html(qc)}</div></div>
        <div class="arr">➜</div>
        <div class="zone"><h4>🏷️ 4-7 Sealer Storage</h4><small>FEFO order → <span class="badge b-ok">&gt;12d</span><span class="badge" style="background:#ffb02033;color:#ffd27a">5-12d</span><span class="badge b-bad">&lt;5d</span></small>
          <div class="rack">{drums_html(storage, cls)}</div></div>
        <div class="arr">➜</div>
        <div class="zone"><h4>⚖️ 8-9 Line Side</h4><small>Load cell → PLC/IoT → BI</small>
          <div style="display:flex;gap:14px;align-items:center;margin-top:10px">
            <div class="tank"><div class="lvl" style="height:{q / DRUM * 100}%"></div></div>
            <div><div class="big">{q:.0f} L</div><small>{ln['id'] + ' · ' + ln['lot'] if ln else 'waiting for drum'}</small><br>
            <span class="badge {'b-ok' if ln else 'b-bad'}">{'STREAMING' if ln else 'STOCK-OUT'}</span></div></div></div>
        </div>""", unsafe_allow_html=True)
        st.markdown("##### 🧾 Live SAP / System Events")
        rows = "".join(f'<div class="{kind}"><span>{ts:%d-%b %H:%M}</span> {m}</div>' for ts, kind, m in S["log"][:40])
        st.markdown(f'<div class="logbox">{rows}</div>', unsafe_allow_html=True)

    with t2:
        if S["hist"]:
            h = pd.DataFrame(S["hist"]).set_index("t")
            c1, c2 = st.columns(2)
            c1.markdown("##### 📦 Storage stock level (drums)"); c1.area_chart(h["Stock"], color="#2f8cff")
            c2.markdown("##### ⚖️ Line-side drum weight (L)"); c2.line_chart(h["LineWeight"], color="#27d17f")
            c3, c4 = st.columns(2)
            c3.markdown("##### 🧪 Cumulative consumption (L)"); c3.line_chart(h["Consumed"], color="#6db3ff")
            c4.markdown("##### 🗑️ Cumulative expiry waste (L)"); c4.line_chart(h["Wasted"], color="#ff5c6c")
        else:
            st.info("Press ▶ Start in the sidebar to stream live data.")
        st.markdown("---")
        st.markdown("### 💰 Business impact: FEFO system vs. no system (60-day run, same demand)")
        if st.button("Run 60-day comparison", type="primary"):
            res = compare(rate, every, batch)
            r1, r2 = st.columns([1, 1])
            r1.dataframe(res, hide_index=True, use_container_width=True)
            r2.bar_chart(res.set_index("Policy")["Waste (L)"], color="#ff5c6c")
            saved = res.loc[1, "Waste (L)"] - res.loc[0, "Waste (L)"]
            st.success(f"✅ FEFO with SAP + barcode tracking saves **{saved:,.0f} L** of sealer over 60 days.")

    with t3:
        df = pd.DataFrame([dict(**{"Drum ID": d["id"], "Lot No.": d["lot"], "Location": d["loc"],
                                   "Days to expiry": round(d["exp"] - day, 1), "Qty (L)": d["q"]})
                           for d in sorted(S["drums"], key=lambda x: x["exp"])])
        if df.empty:
            st.info("No drums in plant.")
        else:
            st.dataframe(df, hide_index=True, use_container_width=True, column_config={
                "Qty (L)": st.column_config.ProgressColumn("Qty (L)", min_value=0, max_value=DRUM, format="%d L"),
                "Days to expiry": st.column_config.NumberColumn(format="%.1f d")})

    with t4:
        flow = [("🚚", "Arrival", "GRN in SAP"), ("📦", "Unloading", "Visual check + barcode"), ("📋", "Quality Check", "Lot, expiry, qty"),
                ("🏭", "Move to Storage", "Forklift, safety"), ("🏷️", "Storage & Tagging", "Location + tag"),
                ("🖥️", "Inventory Monitoring", "Real-time stock & alerts"), ("🔄", "FIFO / FEFO", "Oldest / earliest expiry first"),
                ("✅", "Ready for Line Issue", "Scan + weigh + SAP issue"), ("📈", "Line Consumption", "Load cell → PLC/IoT → BI"),
                ("♻️", "Drum Empty / Return", "Scan, mark empty"), ("🔁", "Cycle Continues", "No stock-out, no expiry")]
        st.markdown('<div class="flow">' + "".join(f'<div class="fc"><b>{i + 1}</b>{ic} <strong>{t}</strong><p>{p}</p></div>'
                    for i, (ic, t, p) in enumerate(flow)) + "</div>", unsafe_allow_html=True)
        st.markdown("**Result:** Accurate tracking · Real-time visibility · FIFO/FEFO · Reduced expiry & waste · Safe handling · Efficient consumption")

dashboard()
