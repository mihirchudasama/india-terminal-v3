# pages/3_Prediction_Engine.py
import warnings; warnings.filterwarnings("ignore")
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
from utils import (inject_css,DC,DCM,XA,YA,YAN,rgba,
    get_ohlcv,get_bulk,get_beta,get_arima,get_rbi_model,
    NIFTY500,SECTOR_INDICES,SCENARIOS,PLAYBOOK,MACRO,CPI_HISTORY,
    BG,BG2,BG3,BORDER,TEXT,MUTED,ACCENT,UP,DOWN,BLUE,PURPLE)

st.set_page_config(page_title="Prediction Engine · India Terminal",
    page_icon="🤖",layout="wide",initial_sidebar_state="collapsed")
inject_css()
st_autorefresh(interval=120_000,key="pred")

st.markdown(f"""<div style="background:{BG2};border:1px solid {BORDER};
border-radius:8px;padding:8px 18px;margin-bottom:12px;display:flex;
align-items:center;gap:16px;">
<span style="font-size:17px;font-weight:700;color:{TEXT};">🤖 Prediction Engine</span>
<span style="font-size:11px;color:{MUTED};">Scenario simulator · Nifty shock · CPI forecast · RBI model</span>
</div>""",unsafe_allow_html=True)

# ── Scenario Simulator ────────────────────────────────────────
st.markdown(f'<div class="sh">Scenario Simulator — "What If?"</div>',
    unsafe_allow_html=True)
sc1,sc2=st.columns([1,2])
with sc1:
    scenario=st.radio("Select scenario",list(SCENARIOS.keys()),
        label_visibility="collapsed")
sc_data=SCENARIOS[scenario]
sc_sent=sc_data["sentiment"]
sc_icon=sc_data["icon"]
sent_col=UP if sc_sent>0 else DOWN
with sc2:
    st.markdown(f"""<div style="background:{sent_col}22;border:1px solid {sent_col}44;
border-radius:8px;padding:12px 16px;margin-bottom:12px;">
<div style="display:flex;align-items:center;gap:12px;">
<span style="font-size:28px;">{sc_icon}</span>
<div><div style="font-size:15px;font-weight:700;color:{TEXT};">{scenario}</div>
<div style="font-size:12px;color:{sent_col};margin-top:2px;">
{'Positive macro shock' if sc_sent>0 else 'Negative macro shock'} · Score: {sc_sent:+.1f}
</div></div></div></div>""",unsafe_allow_html=True)
    sec_df=pd.DataFrame([{"Sector":k,"Impact":v}
        for k,v in sc_data["sectors"].items()]).sort_values("Impact",ascending=True)
    fig_sc=go.Figure(go.Bar(y=sec_df["Sector"],x=sec_df["Impact"],
        orientation="h",
        marker=dict(color=sec_df["Impact"],
            colorscale=[[0,DOWN],[0.5,"#2a2a38"],[1,UP]],cmin=-4,cmax=4),
        text=[f"{v:+.1f}%" for v in sec_df["Impact"]],
        textposition="outside",textfont=dict(color=TEXT,size=11),
        hovertemplate="<b>%{y}</b>: %{x:+.1f}%<extra></extra>"))
    fig_sc.update_layout(**DC(l=4,r=60,t=32,b=4),height=280,showlegend=False,
        title=dict(text=f"Predicted sector impact",font_size=12),
        xaxis=dict(**XA,ticksuffix="%"),
        yaxis=dict(color=TEXT,showgrid=False))
    st.plotly_chart(fig_sc,use_container_width=True,config={"displayModeBar":False})
    winners=[k for k,v in sc_data["sectors"].items() if v>0.5]
    losers=[k for k,v in sc_data["sectors"].items() if v<-0.5]
    st.markdown(
        f'<span style="font-size:10px;color:{UP};font-weight:700;">OUTPERFORM: </span>'
        +"".join(f'<span class="pill" style="background:{UP}22;color:{UP};">{s}</span>'
                 for s in winners)
        +f'&nbsp;&nbsp;<span style="font-size:10px;color:{DOWN};font-weight:700;">UNDERPERFORM: </span>'
        +"".join(f'<span class="pill" style="background:{DOWN}22;color:{DOWN};">{s}</span>'
                 for s in losers),
        unsafe_allow_html=True)

# ── Nifty Shock Predictor ────────────────────────────────────
st.markdown(f'<div class="sh" style="margin-top:24px;">'
    f'Nifty Shock Predictor</div>',unsafe_allow_html=True)
sh1,sh2=st.columns([1.2,2.8])
with sh1:
    nifty_drop=st.slider("Nifty move (%)",-20,20,-5,1,format="%d%%")
    st.markdown(f"""<div style="text-align:center;padding:8px;background:{BG3};
border-radius:7px;border:1px solid {BORDER};">
<div style="font-size:11px;color:{MUTED};">If Nifty moves</div>
<div style="font-size:28px;font-weight:700;color:{'#ff3b5c' if nifty_drop<0 else '#00d084'};">
{nifty_drop:+d}%</div></div>""",unsafe_allow_html=True)
with sh2:
    all_q=get_bulk(tuple(NIFTY500.keys()))
    nifty_df=get_ohlcv("^NSEI","1y","1d")
    if not all_q.empty and not nifty_df.empty:
        beta_rows=[]
        for ticker,(name,sector) in list(NIFTY500.items())[:25]:
            df_s=get_ohlcv(ticker,"1y","1d")
            if not df_s.empty and len(df_s)>60:
                b=get_beta(df_s,nifty_df)
                beta_rows.append({"Symbol":ticker.replace(".NS",""),
                    "Sector":sector,"Beta":b,
                    "Predicted %":round(nifty_drop*b,2)})
        if beta_rows:
            beta_df=pd.DataFrame(beta_rows).sort_values("Predicted %")
            fig_b=go.Figure(go.Bar(x=beta_df["Symbol"],y=beta_df["Predicted %"],
                marker=dict(color=beta_df["Predicted %"],
                    colorscale=[[0,DOWN],[0.5,"#333"],[1,UP]],cmin=-20,cmax=20),
                text=[f"{v:+.1f}%" for v in beta_df["Predicted %"]],
                textposition="outside",textfont=dict(size=9,color=TEXT),
                hovertemplate="<b>%{x}</b><br>%{y:+.1f}%  β=%{customdata:.2f}<extra></extra>",
                customdata=beta_df["Beta"]))
            fig_b.update_layout(**DC(l=4,r=4,t=32,b=4),height=260,showlegend=False,
                title=dict(text=f"Predicted impact if Nifty {nifty_drop:+d}%",
                    font_size=12),
                xaxis=dict(showgrid=False,color=TEXT,tickangle=-35,tickfont_size=9),
                yaxis=dict(**YA,ticksuffix="%"))
            st.plotly_chart(fig_b,use_container_width=True,config={"displayModeBar":False})
            b1,b2=st.columns(2)
            with b1:
                st.markdown(f'<div style="font-size:10px;font-weight:700;color:{DOWN};'
                    f'margin-bottom:4px;">MOST SENSITIVE (High Beta)</div>',
                    unsafe_allow_html=True)
                for _,r in beta_df.tail(5).iterrows():
                    clr=UP if r["Predicted %"]>=0 else DOWN
                    st.markdown(f'<div class="trow">'
                        f'<span class="tsym">{r["Symbol"]}</span>'
                        f'<span style="color:{MUTED};font-size:11px;">β={r["Beta"]:.2f}</span>'
                        f'<span class="tch" style="color:{clr};">{r["Predicted %"]:+.1f}%</span>'
                        f'</div>',unsafe_allow_html=True)
            with b2:
                st.markdown(f'<div style="font-size:10px;font-weight:700;color:{UP};'
                    f'margin-bottom:4px;">MOST DEFENSIVE (Low Beta)</div>',
                    unsafe_allow_html=True)
                for _,r in beta_df.head(5).iterrows():
                    clr=UP if r["Predicted %"]>=0 else DOWN
                    st.markdown(f'<div class="trow">'
                        f'<span class="tsym">{r["Symbol"]}</span>'
                        f'<span style="color:{MUTED};font-size:11px;">β={r["Beta"]:.2f}</span>'
                        f'<span class="tch" style="color:{clr};">{r["Predicted %"]:+.1f}%</span>'
                        f'</div>',unsafe_allow_html=True)
    else:
        st.info("Loading beta data...")

# ── CPI Forecast + RBI Model ──────────────────────────────────
st.markdown(f'<div class="sh" style="margin-top:24px;">'
    f'CPI Forecast + RBI Decision Model</div>',unsafe_allow_html=True)
fc1,fc2=st.columns([2,1.2])
with fc1:
    fc_dates,fc_mean,fc_lo,fc_hi=get_arima()
    hist_dates=pd.date_range(end="2024-12-01",periods=len(CPI_HISTORY),freq="MS")
    hist_s=pd.Series(CPI_HISTORY,index=hist_dates)
    fig_cpi=go.Figure()
    fig_cpi.add_trace(go.Scatter(x=hist_s.index[-24:],y=hist_s.values[-24:],
        mode="lines",name="Actual CPI",line=dict(color=BLUE,width=2.5),
        hovertemplate="%{x|%b %Y}: <b>%{y:.2f}%</b><extra></extra>"))
    fig_cpi.add_trace(go.Scatter(x=fc_dates,y=fc_mean,
        mode="lines+markers",name="ARIMA Forecast",
        line=dict(color=ACCENT,width=2,dash="dash"),
        marker=dict(size=7,color=ACCENT),
        hovertemplate="%{x|%b %Y}: <b>%{y:.2f}%</b><extra></extra>"))
    fig_cpi.add_trace(go.Scatter(
        x=list(fc_dates)+list(reversed(fc_dates)),
        y=list(fc_hi)+list(reversed(fc_lo)),
        fill="toself",fillcolor=rgba(ACCENT,0.13),
        line=dict(color="rgba(0,0,0,0)"),
        name="80% band",hoverinfo="skip"))
    fig_cpi.add_hline(y=4.0,line_dash="dot",line_color=UP,line_width=1)
    fig_cpi.add_hline(y=6.0,line_dash="dot",line_color=DOWN,line_width=1)
    fig_cpi.add_annotation(x=str(fc_dates[0]),y=4.1,text="RBI target 4%",
        showarrow=False,font=dict(size=10,color=UP),xanchor="left")
    fig_cpi.add_annotation(x=str(fc_dates[0]),y=6.1,text="Upper limit 6%",
        showarrow=False,font=dict(size=10,color=DOWN),xanchor="left")
    trend="Rising ▲" if fc_mean[-1]>fc_mean[0] else "Falling ▼"
    tc=DOWN if "Rising" in trend else UP
    fig_cpi.update_layout(**DC(),height=300,
        title=dict(text=f"CPI Forecast (ARIMA)  <span style='color:{tc};'>{trend}</span>",
            font_size=12),
        xaxis=XA,yaxis=dict(**YA,ticksuffix="%"))
    st.plotly_chart(fig_cpi,use_container_width=True,config={"displayModeBar":False})
    fc_df=pd.DataFrame({"Month":[d.strftime("%b %Y") for d in fc_dates],
        "Forecast":[f"{v:.2f}%" for v in fc_mean],
        "Lower 80%":[f"{v:.2f}%" for v in fc_lo],
        "Upper 80%":[f"{v:.2f}%" for v in fc_hi]})
    st.dataframe(fc_df,use_container_width=True,hide_index=True,height=210)

with fc2:
    probs=get_rbi_model(); dec=max(probs,key=probs.get)
    dcol=UP if dec=="cut" else(DOWN if dec=="hike" else MUTED)
    st.markdown(f'<div class="card"><div class="card-title">RBI Rate Decision</div>',
        unsafe_allow_html=True)
    fig_rbi=go.Figure(go.Pie(
        labels=["CUT","HOLD","HIKE"],
        values=[probs.get("cut",0),probs.get("hold",0),probs.get("hike",0)],
        marker=dict(colors=[UP,MUTED,DOWN],
                    line=dict(color=BG2,width=2)),
        hole=0.6,textfont=dict(color=TEXT,size=11),
        hovertemplate="<b>%{label}</b>: %{value:.1f}%<extra></extra>"))
    fig_rbi.add_annotation(text=f"<b>{dec.upper()}</b>",
        font=dict(size=16,color=dcol),showarrow=False,x=0.5,y=0.5)
    fig_rbi.update_layout(**DC(4,4,32,4),height=220,showlegend=True)
    st.plotly_chart(fig_rbi,use_container_width=True,config={"displayModeBar":False})
    st.markdown(f'<div style="font-size:10px;color:{MUTED};font-weight:700;'
        f'margin:8px 0 6px;">SIGNAL DRIVERS</div>',unsafe_allow_html=True)
    drivers=[]
    if MACRO["cpi"]>6: drivers.append(("CPI above 6%","Favours HOLD/HIKE",DOWN))
    elif MACRO["cpi"]<4: drivers.append(("CPI below target","Favours CUT",UP))
    else: drivers.append(("CPI in band","Neutral",MUTED))
    if MACRO["real_rate"]<0: drivers.append(("Negative real rate","Watch for HOLD",ACCENT))
    elif MACRO["real_rate"]>1.5: drivers.append(("High real rate","Favours CUT",UP))
    if MACRO["gdp"]<5: drivers.append(("Weak GDP","Favours CUT",UP))
    elif MACRO["gdp"]>7: drivers.append(("Strong GDP","Allows HOLD",MUTED))
    for sig,imp,clr in drivers:
        st.markdown(f'<div style="padding:5px 0;border-bottom:1px solid {BORDER};">'
            f'<div style="font-size:11px;color:{TEXT};font-weight:600;">{sig}</div>'
            f'<div style="font-size:10px;color:{clr};">{imp}</div></div>',
            unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)

# ── Macro → Sector ────────────────────────────────────────────
st.markdown(f'<div class="sh" style="margin-top:24px;">Macro → Market Signal</div>',
    unsafe_allow_html=True)
pb=PLAYBOOK.get(MACRO["phase"],PLAYBOOK["Goldilocks"])
ms1,ms2,ms3=st.columns(3)
with ms1:
    st.markdown(f"""<div style="background:{pb['c']}22;border:1px solid {pb['c']}44;
border-radius:8px;padding:14px;text-align:center;">
<div style="font-size:10px;color:{pb['c']};font-weight:700;
text-transform:uppercase;letter-spacing:1px;">Current Phase</div>
<div style="font-size:22px;font-weight:700;color:{pb['c']};margin:6px 0;">{MACRO['phase']}</div>
<div style="font-size:11px;color:{MUTED};line-height:1.6;">
CPI {MACRO['cpi']}% · GDP {MACRO['gdp']}%<br>
Repo {MACRO['repo']}% · Real {MACRO['real_rate']:+.2f}%</div></div>""",
    unsafe_allow_html=True)
with ms2:
    st.markdown(f'<div style="font-size:11px;font-weight:700;color:{UP};'
        f'margin-bottom:6px;">▲ OVERWEIGHT</div>',unsafe_allow_html=True)
    for s in pb["over"]:
        st.markdown(f'<span class="pill" style="background:{UP}22;color:{UP};'
            f'border:1px solid {UP}33;">{s}</span>',unsafe_allow_html=True)
with ms3:
    st.markdown(f'<div style="font-size:11px;font-weight:700;color:{DOWN};'
        f'margin-bottom:6px;">▼ UNDERWEIGHT</div>',unsafe_allow_html=True)
    for s in pb["under"]:
        st.markdown(f'<span class="pill" style="background:{DOWN}22;color:{DOWN};'
            f'border:1px solid {DOWN}33;">{s}</span>',unsafe_allow_html=True)

# Historical CPI vs Repo
hist_dates2=pd.date_range(end="2024-12-01",periods=len(CPI_HISTORY),freq="MS")
repo_hist=np.array([
    6.50,6.50,6.25,6.25,6.25,6.00,6.00,6.00,6.00,6.00,6.00,6.00,
    6.00,6.00,6.00,6.25,6.50,6.50,6.50,6.50,6.50,6.25,6.00,5.75,
    5.40,5.15,5.15,5.15,4.40,4.00,4.00,4.00,4.00,4.00,4.00,4.00,
    4.00,4.00,4.00,4.00,4.00,4.00,4.40,4.90,4.90,5.40,5.90,6.25,
    6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,
    6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,
    6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,
    6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,
    6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,6.50,
])
n=min(len(CPI_HISTORY),len(repo_hist))
repo_hist=repo_hist[-n:]; cpi_hist=CPI_HISTORY[-n:]
hist_dates2=hist_dates2[-n:]
fig_mc=go.Figure()
fig_mc.add_trace(go.Scatter(x=hist_dates2,y=cpi_hist,mode="lines",
    name="CPI",line=dict(color=DOWN,width=2),
    fill="tozeroy",fillcolor=rgba(DOWN,0.12),
    hovertemplate="%{x|%b %Y} CPI: <b>%{y:.2f}%</b><extra></extra>"))
fig_mc.add_trace(go.Scatter(x=hist_dates2,y=repo_hist,mode="lines",
    name="Repo Rate",line=dict(color=BLUE,width=2),
    hovertemplate="%{x|%b %Y} Repo: <b>%{y:.2f}%</b><extra></extra>"))
fig_mc.add_hline(y=4.0,line_dash="dot",line_color=rgba(UP,0.5),line_width=1)
fig_mc.update_layout(**DC(),height=220,
    title=dict(text="CPI vs Repo Rate — 2017 to present",font_size=11),
    xaxis=XA,yaxis=dict(**YA,ticksuffix="%"))
st.plotly_chart(fig_mc,use_container_width=True,config={"displayModeBar":False})
