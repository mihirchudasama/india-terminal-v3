# pages/4_Portfolio_Alerts.py  —  India Terminal v3
import warnings; warnings.filterwarnings("ignore")
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from utils import (inject_css, DC, XA, YA, rgba,
    get_quote, get_ohlcv, STOCKS,
    BG, BG2, BG3, BORDER, TEXT, MUTED,
    ACCENT, UP, DOWN, BLUE, PURPLE)

st.set_page_config(page_title="Portfolio · India Terminal",
    page_icon="💼", layout="wide",
    initial_sidebar_state="expanded")
inject_css()
count = st_autorefresh(interval=30_000, key="port_v3")

st.markdown(f"""
<div style="background:{BG2};border:1px solid {BORDER};border-radius:8px;
padding:8px 18px;margin-bottom:12px;display:flex;align-items:center;
justify-content:space-between;">
<div style="display:flex;align-items:center;gap:16px;">
<span style="font-size:17px;font-weight:700;color:{TEXT};">💼 Portfolio & Alerts</span>
<span style="font-size:11px;color:{MUTED};">
Live P&amp;L · Risk · Price alerts · Auto-refresh #{count}
</span>
</div>
<div>
<span style="font-size:10px;color:{UP};background:{UP}33;
padding:3px 10px;border-radius:4px;font-weight:700;">● LIVE — updates every 30s</span>
</div>
</div>""", unsafe_allow_html=True)

# ── Quick-add from stock universe ─────────────────────────────
st.markdown(f'<div class="sh">Quick Add from Stock Universe</div>',
    unsafe_allow_html=True)
qa1, qa2, qa3, qa4, qa5 = st.columns([2,1,1,1,1])
with qa1:
    all_options = [f"{v[0]} ({k.replace('.NS','').replace('.BO','')} · {v[2]})"
                   for k,v in STOCKS.items()]
    option_to_ticker = {f"{v[0]} ({k.replace('.NS','').replace('.BO','')} · {v[2]})": k
                        for k,v in STOCKS.items()}
    quick_sel = st.selectbox("Search stock", all_options,
        label_visibility="collapsed")
    quick_ticker = option_to_ticker[quick_sel]
with qa2:
    quick_qty  = st.number_input("Qty", min_value=1, value=10,
        label_visibility="collapsed")
with qa3:
    live_q = get_quote(quick_ticker)
    live_px = live_q["p"] or 1000.0
    quick_cost = st.number_input("Avg Cost ₹", value=live_px,
        label_visibility="collapsed")
with qa4:
    quick_tgt = st.number_input("Target ₹", value=round(live_px*1.15,1),
        label_visibility="collapsed")
with qa5:
    quick_sl  = st.number_input("Stop Loss ₹", value=round(live_px*0.92,1),
        label_visibility="collapsed")

# Session state portfolio
if "portfolio" not in st.session_state:
    st.session_state["portfolio"] = [
        {"Ticker":"RELIANCE.NS","Symbol":"RELIANCE","Qty":10,
         "Avg Cost":2750.0,"Target":3200.0,"Stop Loss":2400.0},
        {"Ticker":"TCS.NS","Symbol":"TCS","Qty":5,
         "Avg Cost":3800.0,"Target":4200.0,"Stop Loss":3400.0},
        {"Ticker":"HDFCBANK.NS","Symbol":"HDFCBANK","Qty":15,
         "Avg Cost":1580.0,"Target":1900.0,"Stop Loss":1400.0},
        {"Ticker":"INFY.NS","Symbol":"INFY","Qty":20,
         "Avg Cost":1420.0,"Target":1650.0,"Stop Loss":1200.0},
        {"Ticker":"BAJFINANCE.NS","Symbol":"BAJFINANCE","Qty":8,
         "Avg Cost":6800.0,"Target":8000.0,"Stop Loss":5800.0},
    ]

add_col, _ = st.columns([1, 4])
with add_col:
    if st.button("➕ Add to Portfolio", type="primary"):
        sym = quick_ticker.replace(".NS","").replace(".BO","")
        # Update if exists, else add
        exists = False
        for h in st.session_state["portfolio"]:
            if h["Ticker"] == quick_ticker:
                h["Qty"]      = quick_qty
                h["Avg Cost"] = quick_cost
                h["Target"]   = quick_tgt
                h["Stop Loss"]= quick_sl
                exists = True
                break
        if not exists:
            st.session_state["portfolio"].append({
                "Ticker": quick_ticker, "Symbol": sym,
                "Qty": quick_qty, "Avg Cost": quick_cost,
                "Target": quick_tgt, "Stop Loss": quick_sl,
            })
        st.success(f"✅ {sym} added / updated!")
        st.rerun()

# ── Live portfolio table ──────────────────────────────────────
st.markdown(f'<div class="sh">Live Portfolio — ₹ P&L Updating Every 30s</div>',
    unsafe_allow_html=True)

portfolio = st.session_state["portfolio"]

# Fetch all live quotes
all_quotes = {h["Ticker"]: get_quote(h["Ticker"]) for h in portfolio}

# Build enriched rows
rows = []
for h in portfolio:
    dq      = all_quotes.get(h["Ticker"], {})
    lp      = dq.get("p") or h["Avg Cost"]
    qty     = h["Qty"]
    cost    = h["Avg Cost"]
    tgt     = h["Target"]
    sl      = h["Stop Loss"]
    cur_val = qty * lp
    cost_val= qty * cost
    pnl     = cur_val - cost_val
    pnl_pct = (lp/cost - 1)*100 if cost > 0 else 0
    day_chg = dq.get("pct", 0)
    day_pnl = qty * (lp - (lp/(1+day_chg/100))) if day_chg else 0
    tgt_upside = (tgt/lp - 1)*100 if lp > 0 else 0
    sl_risk    = (sl/lp  - 1)*100 if lp > 0 else 0
    rr_ratio   = abs(tgt_upside/sl_risk) if sl_risk != 0 else 0
    hit_tgt    = lp >= tgt and tgt > 0
    hit_sl     = lp <= sl and sl > 0

    rows.append({
        "Symbol":    h["Symbol"],
        "Exchange":  STOCKS.get(h["Ticker"],("","","NSE"))[2],
        "Qty":       int(qty),
        "Buy ₹":     round(cost, 2),
        "CMP ₹":     round(lp, 2),
        "Value ₹":   round(cur_val, 0),
        "P&L ₹":     round(pnl, 0),
        "P&L %":     round(pnl_pct, 2),
        "Day P&L ₹": round(day_pnl, 0),
        "Day %":     round(day_chg, 2),
        "Upside %":  round(tgt_upside, 1),
        "Risk %":    round(sl_risk, 1),
        "R:R":       round(rr_ratio, 2),
        "Alert":     ("🎯 TARGET" if hit_tgt else "🛑 STOP" if hit_sl else ""),
        "_ticker":   h["Ticker"],
    })

pf_df = pd.DataFrame(rows)

# ── Triggered alerts ──────────────────────────────────────────
alerts_df = pf_df[pf_df["Alert"] != ""]
if not alerts_df.empty:
    for _, r in alerts_df.iterrows():
        clr = UP if "TARGET" in r["Alert"] else DOWN
        st.markdown(f"""
<div style="background:{clr}22;border:2px solid {clr}66;border-radius:8px;
padding:10px 18px;margin:6px 0;display:flex;align-items:center;gap:14px;">
<span style="font-size:22px;">{'🎯' if 'TARGET' in r['Alert'] else '🛑'}</span>
<div>
<span style="font-size:15px;font-weight:700;color:{clr};">{r['Alert']} — {r['Symbol']}</span>
&nbsp;&nbsp;
<span style="color:{TEXT};font-size:13px;">
CMP ₹{r['CMP ₹']:,.2f} · P&L {r['P&L %']:+.2f}%</span>
</div>
<div style="margin-left:auto;">
<span style="color:{MUTED};font-size:12px;">Unrealised: </span>
<span style="color:{clr};font-weight:700;font-size:14px;">
₹{r['P&L ₹']:+,.0f}</span>
</div>
</div>""", unsafe_allow_html=True)

# ── Portfolio summary ─────────────────────────────────────────
if not pf_df.empty:
    tot_val   = pf_df["Value ₹"].sum()
    tot_cost  = sum(h["Qty"]*h["Avg Cost"] for h in portfolio)
    tot_pnl   = tot_val - tot_cost
    tot_pct   = (tot_val/tot_cost - 1)*100 if tot_cost > 0 else 0
    day_pnl   = pf_df["Day P&L ₹"].sum()
    profitable= (pf_df["P&L %"] > 0).sum()
    pnl_col   = UP if tot_pnl >= 0 else DOWN
    day_col   = UP if day_pnl >= 0 else DOWN

    sm1,sm2,sm3,sm4,sm5 = st.columns(5)
    for col,(lbl,val,sub,clr) in zip([sm1,sm2,sm3,sm4,sm5],[
        ("Portfolio Value",  f"₹{tot_val:,.0f}", f"Cost: ₹{tot_cost:,.0f}", TEXT),
        ("Total P&L",        f"₹{tot_pnl:+,.0f}", f"{tot_pct:+.2f}% overall", pnl_col),
        ("Today's P&L",      f"₹{day_pnl:+,.0f}", "Live day change", day_col),
        ("Profitable",       f"{profitable}/{len(pf_df)}", "Holdings in green", UP),
        ("Alerts",           str(len(alerts_df)), "Active signals", ACCENT),
    ]):
        with col:
            st.markdown(f"""<div class="badge">
<div class="badge-lbl">{lbl}</div>
<div class="badge-val" style="color:{clr};">{val}</div>
<div class="badge-sub">{sub}</div>
</div>""", unsafe_allow_html=True)

    # ── Interactive table ─────────────────────────────────────
    st.markdown(f'<div style="margin:12px 0 6px;"></div>', unsafe_allow_html=True)

    display_df = pf_df[[
        "Symbol","Exchange","Qty","Buy ₹","CMP ₹",
        "Value ₹","P&L ₹","P&L %","Day %","Upside %","Risk %","R:R","Alert"
    ]].copy()

    def colour_v(val):
        if isinstance(val, (int,float)):
            if val > 0: return f"color:{UP};font-weight:600"
            if val < 0: return f"color:{DOWN};font-weight:600"
        return ""

    st.dataframe(
        display_df.style
        .applymap(colour_v, subset=["P&L ₹","P&L %","Day %","Upside %","Risk %"])
        .format({
            "Buy ₹":    "₹{:,.2f}",
            "CMP ₹":    "₹{:,.2f}",
            "Value ₹":  "₹{:,.0f}",
            "P&L ₹":    "₹{:+,.0f}",
            "P&L %":    "{:+.2f}%",
            "Day %":    "{:+.2f}%",
            "Upside %": "{:+.1f}%",
            "Risk %":   "{:+.1f}%",
            "R:R":      "{:.2f}x",
        }),
        use_container_width=True, height=250)

    # Delete holding
    del_col, _ = st.columns([2,4])
    with del_col:
        del_sym = st.selectbox("Remove holding",
            ["— select —"] + [r["Symbol"] for r in portfolio],
            label_visibility="collapsed")
        if del_sym != "— select —":
            if st.button(f"🗑️ Remove {del_sym}"):
                st.session_state["portfolio"] = [
                    h for h in portfolio if h["Symbol"] != del_sym]
                st.rerun()

    # ── Charts ────────────────────────────────────────────────
    ch1, ch2, ch3 = st.columns(3)

    with ch1:
        fig_pnl = go.Figure(go.Bar(
            x=pf_df["Symbol"], y=pf_df["P&L %"],
            marker=dict(color=pf_df["P&L %"],
                colorscale=[[0,DOWN],[0.5,"#2a2a38"],[1,UP]],
                cmin=-20, cmax=20),
            text=[f"{v:+.1f}%" for v in pf_df["P&L %"]],
            textposition="outside", textfont=dict(color=TEXT,size=10),
            hovertemplate="<b>%{x}</b><br>P&L: %{y:+.2f}%<extra></extra>"))
        fig_pnl.update_layout(**DC(l=4,r=4,t=32,b=4), height=260,
            showlegend=False,
            title=dict(text="Unrealised P&L %", font_size=11),
            xaxis=dict(showgrid=False, color=TEXT),
            yaxis=dict(**YA, ticksuffix="%"))
        st.plotly_chart(fig_pnl, use_container_width=True,
            config={"displayModeBar":False})

    with ch2:
        fig_alloc = go.Figure(go.Pie(
            labels=pf_df["Symbol"], values=pf_df["Value ₹"],
            hole=0.5, marker=dict(line=dict(color=BG2,width=2)),
            textfont=dict(color=TEXT,size=10),
            hovertemplate="<b>%{label}</b><br>₹%{value:,.0f} (%{percent})<extra></extra>"))
        fig_alloc.update_layout(**DC(l=4,r=4,t=32,b=4), height=260,
            showlegend=True,
            title=dict(text="Portfolio allocation", font_size=11),
            legend=dict(font_color=TEXT, bgcolor=BG2,
                        font_size=9, orientation="h", y=-0.12))
        st.plotly_chart(fig_alloc, use_container_width=True,
            config={"displayModeBar":False})

    with ch3:
        st.markdown(f'<div style="background:{BG3};border:1px solid {BORDER};'
            f'border-radius:8px;padding:12px 14px;">',
            unsafe_allow_html=True)
        st.markdown(f'<div class="sh" style="margin:0 0 8px;">Price vs Target vs SL</div>',
            unsafe_allow_html=True)
        for h in portfolio:
            dq   = all_quotes.get(h["Ticker"],{})
            lp   = dq.get("p") or h["Avg Cost"]
            tgt  = h["Target"]; sl = h["Stop Loss"]
            if tgt > 0 and sl > 0:
                rng  = tgt - sl
                if rng <= 0: continue
                pos  = min(100, max(0, (lp-sl)/rng*100))
                bc   = UP if lp>=h["Avg Cost"] else (ACCENT if pos>50 else DOWN)
                st.markdown(f"""
<div style="margin:5px 0;">
<div style="display:flex;justify-content:space-between;
font-size:10px;color:{MUTED};margin-bottom:2px;">
<span style="color:{TEXT};font-weight:600;">{h['Symbol']}</span>
<span style="color:{bc};">₹{lp:,.1f}</span>
</div>
<div style="background:{BORDER};border-radius:4px;height:7px;">
<div style="background:{bc};width:{pos:.0f}%;height:100%;border-radius:4px;"></div>
</div>
<div style="display:flex;justify-content:space-between;
font-size:9px;color:{MUTED};margin-top:1px;">
<span>SL ₹{sl:,.0f}</span>
<span style="color:{UP};">Tgt ₹{tgt:,.0f}</span>
</div>
</div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ── Custom Price Alerts ───────────────────────────────────────
st.markdown(f'<div class="sh" style="margin-top:24px;">Custom Price Alerts</div>',
    unsafe_allow_html=True)
st.markdown(
    f'<div style="font-size:11px;color:{MUTED};margin-bottom:8px;">'
    f'Set alerts on any NSE/BSE stock. Triggers highlighted when price '
    f'crosses your level. Updates every 30 seconds.</div>',
    unsafe_allow_html=True)

if "alerts" not in st.session_state:
    st.session_state["alerts"] = [
        {"Ticker":"RELIANCE.NS","Symbol":"RELIANCE",
         "Condition":"above","Level":3000.0,"Note":"Breakout level"},
        {"Ticker":"TCS.NS","Symbol":"TCS",
         "Condition":"below","Level":3500.0,"Note":"Pullback buy"},
        {"Ticker":"HDFCBANK.NS","Symbol":"HDFCBANK",
         "Condition":"above","Level":1800.0,"Note":"52W high breakout"},
    ]

# Alert adder
ac1,ac2,ac3,ac4,ac5 = st.columns([2,1,1,2,1])
with ac1:
    a_sel    = st.selectbox("Alert stock", all_options,
        key="alert_stock_sel", label_visibility="collapsed")
    a_ticker = option_to_ticker[a_sel]
    a_sym    = a_ticker.replace(".NS","").replace(".BO","")
with ac2:
    a_cond = st.selectbox("When", ["above","below"],
        label_visibility="collapsed")
with ac3:
    a_live = get_quote(a_ticker)
    a_lv   = st.number_input("Level ₹",
        value=a_live["p"] or 1000.0, label_visibility="collapsed")
with ac4:
    a_note = st.text_input("Note", value="", placeholder="Breakout, support, etc.",
        label_visibility="collapsed")
with ac5:
    if st.button("➕ Add Alert", type="secondary"):
        st.session_state["alerts"].append({
            "Ticker":a_ticker,"Symbol":a_sym,
            "Condition":a_cond,"Level":a_lv,"Note":a_note})
        st.rerun()

# Render alerts
st.markdown(f'<div style="margin-top:8px;"></div>', unsafe_allow_html=True)
to_delete = None
for idx, alert in enumerate(st.session_state["alerts"]):
    dq     = get_quote(alert["Ticker"])
    lp     = dq["p"]
    if not lp:
        continue
    cond   = alert["Condition"]
    level  = alert["Level"]
    fired  = (lp > level if cond=="above" else lp < level)
    flr    = UP if fired else MUTED
    dist   = ((lp/level - 1)*100) if level > 0 else 0
    dist_s = f"{'▲' if dist>=0 else '▼'} {abs(dist):.2f}% away"

    al1, al2 = st.columns([5, 1])
    with al1:
        st.markdown(f"""
<div style="background:{flr}18;border:1px solid {flr}{'66' if fired else '33'};
border-radius:7px;padding:8px 14px;display:flex;align-items:center;gap:16px;">
<span style="font-size:16px;">{'🔔' if fired else '⏳'}</span>
<div>
<span style="font-weight:700;color:{flr};font-size:13px;">
{'TRIGGERED' if fired else 'Waiting'}
</span>&nbsp;&nbsp;
<span style="color:{TEXT};font-size:12px;">
{alert['Symbol']} {cond} ₹{level:,.2f}
</span>&nbsp;&nbsp;
<span style="color:{MUTED};font-size:11px;">{alert.get('Note','')}</span>
</div>
<div style="margin-left:auto;text-align:right;">
<span style="color:{TEXT};font-size:12px;">CMP ₹{lp:,.2f}</span>&nbsp;
<span style="color:{MUTED};font-size:11px;">{dist_s}</span>
</div>
</div>""", unsafe_allow_html=True)
    with al2:
        if st.button("✕", key=f"del_alert_{idx}"):
            to_delete = idx

if to_delete is not None:
    st.session_state["alerts"].pop(to_delete)
    st.rerun()
