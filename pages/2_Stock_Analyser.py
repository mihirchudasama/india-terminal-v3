# pages/2_Stock_Analyser.py
import warnings; warnings.filterwarnings("ignore")
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
from utils import (inject_css,DC,DCM,XA,YA,YAN,rgba,
    get_quote,get_ohlcv,get_bulk,get_indicators,get_beta,
    NIFTY500,INDICES,SECTOR_INDICES,
    BG,BG2,BG3,BORDER,TEXT,MUTED,ACCENT,UP,DOWN,BLUE,PURPLE)

st.set_page_config(page_title="Stock Analyser · India Terminal",
    page_icon="📈",layout="wide",initial_sidebar_state="collapsed")
inject_css()
st_autorefresh(interval=60_000,key="stock")

st.markdown(f"""<div style="background:{BG2};border:1px solid {BORDER};
border-radius:8px;padding:8px 18px;margin-bottom:12px;display:flex;
align-items:center;gap:16px;">
<span style="font-size:17px;font-weight:700;color:{TEXT};">📈 Stock Analyser</span>
<span style="font-size:11px;color:{MUTED};">Deep dive · Technicals · Momentum · Correlations</span>
</div>""",unsafe_allow_html=True)

ci,cp=st.columns([3,2])
with ci:
    raw=st.text_input("NSE ticker",value="RELIANCE",
        placeholder="RELIANCE, TCS, HDFCBANK ...",
        label_visibility="collapsed").upper().strip()
    ticker=f"{raw}.NS"
with cp:
    p_map={"1M":"1mo","3M":"3mo","6M":"6mo","1Y":"1y","3Y":"3y","5Y":"5y"}
    p_sel=st.radio("Period",list(p_map),horizontal=True,index=3,
        label_visibility="collapsed")
    pk=p_map[p_sel]

df=get_ohlcv(ticker,pk,"1d")
dq=get_quote(ticker)
nifty_df=get_ohlcv("^NSEI",pk,"1d")

if df.empty or not dq["p"]:
    st.warning(f"No data for **{raw}**. Check ticker (e.g. RELIANCE not RELIANCE.NS)")
    st.stop()

ind=get_indicators(df)
b=get_beta(df,nifty_df) if not nifty_df.empty else 1.0
price=dq["p"]; pct=dq["pct"]
name=NIFTY500.get(ticker,(raw,"—"))[0]
p_clr=UP if pct>=0 else DOWN
arr="▲" if pct>=0 else "▼"
hi20=float(df["High"].tail(20).max())
lo20=float(df["Low"].tail(20).min())
pivot=(hi20+lo20+price)/3
r1=round(2*pivot-lo20,2)
s1=round(2*pivot-hi20,2)

# Metric row
m1,m2,m3,m4,m5,m6,m7=st.columns(7)
mets=[
    (name[:16],f"₹{price:,.2f}",f"{arr} {pct:+.2f}%",p_clr),
    ("Beta",f"{b:.2f}","High risk" if b>1.3 else"Low risk" if b<0.7 else"Market",
     DOWN if b>1.3 else UP if b<0.7 else MUTED),
    ("RSI",f"{ind['rsi']}",
     "Overbought" if ind["rsi"]>70 else"Oversold" if ind["rsi"]<30 else"Neutral",
     DOWN if ind["rsi"]>70 else UP if ind["rsi"]<30 else MUTED),
    ("MACD",f"{ind['macd']:+.2f}",
     "Bullish" if ind["macd"]>ind["macd_sig"] else"Bearish",
     UP if ind["macd"]>ind["macd_sig"] else DOWN),
    ("MA20",f"₹{ind['ma20']:,.0f}",
     "Above" if price>ind["ma20"] else"Below",
     UP if price>ind["ma20"] else DOWN),
    ("Support",f"₹{s1:,.0f}","20-day pivot",BLUE),
    ("Resist.",f"₹{r1:,.0f}","20-day pivot",ACCENT),
]
for col,(lbl,val,sub,clr) in zip([m1,m2,m3,m4,m5,m6,m7],mets):
    with col:
        st.markdown(f"""<div class="badge">
<div class="badge-lbl">{lbl}</div>
<div class="badge-val" style="color:{clr};">{val}</div>
<div class="badge-sub">{sub}</div></div>""",unsafe_allow_html=True)

# Chart + signals
ca,cb=st.columns([2.8,1.2])

with ca:
    st.markdown(f'<div class="card"><div class="card-title">{name} — Technicals</div>',
        unsafe_allow_html=True)
    show_bb=st.checkbox("Bollinger Bands",value=True)
    show_ma=st.checkbox("Moving Averages (20/50)",value=True)

    fig=make_subplots(rows=3,cols=1,shared_xaxes=True,
        row_heights=[0.58,0.22,0.20],vertical_spacing=0.02,
        subplot_titles=["","RSI","MACD"])
    fig.add_trace(go.Candlestick(
        x=df.index,open=df["Open"],high=df["High"],
        low=df["Low"],close=df["Close"],
        increasing_line_color=UP,increasing_fillcolor=rgba(UP,0.33),
        decreasing_line_color=DOWN,decreasing_fillcolor=rgba(DOWN,0.33),
        name=raw),row=1,col=1)
    if show_bb:
        fig.add_trace(go.Scatter(x=df.index,y=ind["bb_up_s"],
            line=dict(color=PURPLE,width=0.8,dash="dot"),
            name="BB Upper",showlegend=False),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=ind["bb_lo_s"],
            fill="tonexty",fillcolor=rgba(PURPLE,0.07),
            line=dict(color=PURPLE,width=0.8,dash="dot"),
            name="BB Lower",showlegend=False),row=1,col=1)
    if show_ma:
        fig.add_trace(go.Scatter(x=df.index,y=ind["ma20_s"],
            line=dict(color=ACCENT,width=1.2),name="MA20"),row=1,col=1)
        if ind["ma50"] and not ind["ma50_s"].isna().all():
            fig.add_trace(go.Scatter(x=df.index,y=ind["ma50_s"],
                line=dict(color=BLUE,width=1.2),name="MA50"),row=1,col=1)
    fig.add_hline(y=s1,line_dash="dot",line_color=UP,line_width=1,
        annotation_text=f"S1 {s1:,.0f}",
        annotation_font_color=UP,annotation_font_size=9,row=1,col=1)
    fig.add_hline(y=r1,line_dash="dot",line_color=DOWN,line_width=1,
        annotation_text=f"R1 {r1:,.0f}",
        annotation_font_color=DOWN,annotation_font_size=9,row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=ind["rsi_s"],
        line=dict(color=ACCENT,width=1.5),
        name="RSI",showlegend=False),row=2,col=1)
    fig.add_hline(y=70,line_dash="dot",line_color=rgba(DOWN,0.5),
        line_width=1,row=2,col=1)
    fig.add_hline(y=30,line_dash="dot",line_color=rgba(UP,0.5),
        line_width=1,row=2,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=ind["macd_s"],
        line=dict(color=BLUE,width=1.5),
        name="MACD",showlegend=False),row=3,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=ind["sig_s"],
        line=dict(color=ACCENT,width=1,dash="dot"),
        name="Signal",showlegend=False),row=3,col=1)
    fig.add_trace(go.Bar(x=df.index,y=ind["hist_s"],
        marker_color=[UP if v>=0 else DOWN for v in ind["hist_s"]],
        opacity=0.7,showlegend=False),row=3,col=1)
    fig.update_layout(**DC(),height=500,
        title=dict(text=f"{name}  <span style='color:{p_clr};'>"
            f"₹{price:,.2f}  {arr} {pct:+.2f}%</span>",font_size=13),
        xaxis_rangeslider_visible=False,showlegend=True,
        xaxis=XA,xaxis2=XA,xaxis3=XA,
        yaxis=dict(**YA,tickformat=",.0f"),
        yaxis2=dict(**YA,range=[0,100]),
        yaxis3=YA)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown("</div>",unsafe_allow_html=True)

with cb:
    st.markdown(f'<div class="card"><div class="card-title">AI Signal</div>',
        unsafe_allow_html=True)
    sigs=[]
    sigs.append(("RSI Overbought","Caution",DOWN) if ind["rsi"]>65
        else ("RSI Oversold","Bounce zone",UP) if ind["rsi"]<35
        else ("RSI Neutral","No extreme",MUTED))
    sigs.append(("MACD Bullish","Upward momentum",UP)
        if ind["macd"]>ind["macd_sig"] and ind["macd"]>0
        else ("MACD Bearish","Downward momentum",DOWN)
        if ind["macd"]<ind["macd_sig"] and ind["macd"]<0
        else ("MACD Crossover","Watch direction",ACCENT))
    sigs.append(("Above MA20","Short-term bullish",UP)
        if price>ind["ma20"] else ("Below MA20","Short-term bearish",DOWN))
    if ind["ma50"]:
        sigs.append(("Above MA50","Medium bullish",UP)
            if price>ind["ma50"] else ("Below MA50","Medium bearish",DOWN))
    sigs.append(("BB Breakout","Strong upside",UP)
        if price>ind["bb_up"] else ("BB Breakdown","Oversold bounce",ACCENT)
        if price<ind["bb_lo"] else ("Inside BB","Normal range",MUTED))
    bull=sum(1 for _,_,c in sigs if c==UP)
    bear=sum(1 for _,_,c in sigs if c==DOWN)
    ov="BUY" if bull>=3 else("SELL" if bear>=3 else "HOLD")
    oc=UP if ov=="BUY" else(DOWN if ov=="SELL" else MUTED)
    st.markdown(f"""<div style="background:{oc}22;border:1px solid {oc}55;
border-radius:8px;padding:10px;text-align:center;margin-bottom:12px;">
<div style="font-size:10px;color:{oc};font-weight:700;text-transform:uppercase;">Overall Signal</div>
<div style="font-size:26px;font-weight:700;color:{oc};">{ov}</div>
<div style="font-size:11px;color:{MUTED};">{bull} bullish · {bear} bearish</div>
</div>""",unsafe_allow_html=True)
    for title,detail,clr in sigs:
        st.markdown(f'<div style="padding:6px 0;border-bottom:1px solid {BORDER};">'
            f'<div style="font-size:12px;color:{clr};font-weight:600;">{title}</div>'
            f'<div style="font-size:11px;color:{MUTED};">{detail}</div></div>',
            unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)
    st.markdown(f'<div class="card"><div class="card-title">Returns</div>',
        unsafe_allow_html=True)
    for lbl,days in [("1W",5),("1M",21),("3M",63),("6M",126),("1Y",252)]:
        if len(df)>days:
            r=(float(df["Close"].iloc[-1])/float(df["Close"].iloc[-days])-1)*100
            clr=UP if r>=0 else DOWN; a2="▲" if r>=0 else "▼"
            st.markdown(f'<div class="trow"><span style="color:{MUTED};">{lbl}</span>'
                f'<span style="color:{clr};font-weight:600;">{a2} {r:+.2f}%</span></div>',
                unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)

# Momentum screener
st.markdown(f'<div class="sh">Momentum Screener</div>',unsafe_allow_html=True)
all_q=get_bulk(tuple(NIFTY500.keys()))
if not all_q.empty:
    cf1,cf2=st.columns([2,2])
    with cf1:
        secs=["All"]+sorted(all_q["Sector"].unique().tolist())
        sel=st.selectbox("Sector",secs,label_visibility="collapsed")
    with cf2:
        srt=st.selectbox("Sort by",["Chg %","Price"],label_visibility="collapsed")
    filt=all_q.copy()
    if sel!="All": filt=filt[filt["Sector"]==sel]
    filt=filt.sort_values("Pct" if srt=="Chg %" else "Price",
        ascending=False).reset_index(drop=True)
    filt.index+=1
    top15=filt.head(15)
    fig_m=go.Figure(go.Bar(x=top15["Symbol"],y=top15["Pct"],
        marker=dict(color=top15["Pct"],
            colorscale=[[0,DOWN],[0.5,"#333"],[1,UP]],cmin=-5,cmax=5),
        text=[f"{v:+.2f}%" for v in top15["Pct"]],
        textposition="outside",textfont=dict(color=TEXT,size=10),
        hovertemplate="<b>%{x}</b><br>₹%{customdata:,.1f}<extra></extra>",
        customdata=top15["Price"]))
    fig_m.update_layout(**DC(l=4,r=4,t=32,b=4),height=240,showlegend=False,
        title=dict(text="Top 15 by momentum",font_size=11),
        xaxis=dict(showgrid=False,color=TEXT),
        yaxis=dict(**YA,ticksuffix="%"))
    st.plotly_chart(fig_m,use_container_width=True,config={"displayModeBar":False})
    def colour_cell(val):
        if isinstance(val,float):
            if val>0: return f"color:{UP};font-weight:600"
            if val<0: return f"color:{DOWN};font-weight:600"
        return ""
    st.dataframe(
        filt[["Symbol","Name","Sector","Price","Pct","Chg"]]
        .rename(columns={"Pct":"Chg %","Chg":"Chg ₹"})
        .style.applymap(colour_cell,subset=["Chg %","Chg ₹"])
        .format({"Price":"₹{:,.2f}","Chg %":"{:+.2f}%","Chg ₹":"₹{:+.2f}"}),
        use_container_width=True,height=280)

# Correlation explorer
st.markdown(f'<div class="sh">Correlation Explorer</div>',unsafe_allow_html=True)
all_inst=list(NIFTY500.keys())+list(INDICES.values())
all_lbl=([f"{v[0]} ({k.replace('.NS','')})" for k,v in NIFTY500.items()]
         +[f"Index: {k}" for k in INDICES.keys()])
lbl_to_t=dict(zip(all_lbl,all_inst))
cc1,cc2,cc3=st.columns([2,2,1])
with cc1:
    sel_a=st.selectbox("Instrument A",all_lbl,index=0,label_visibility="collapsed")
with cc2:
    sel_b=st.selectbox("Instrument B",all_lbl,index=2,label_visibility="collapsed")
with cc3:
    win=st.select_slider("Window",[30,60,90,180,252],value=60,
        label_visibility="collapsed")
ta,tb=lbl_to_t[sel_a],lbl_to_t[sel_b]
dfa=get_ohlcv(ta,"2y","1d"); dfb=get_ohlcv(tb,"2y","1d")
if not dfa.empty and not dfb.empty:
    ra=dfa["Close"].pct_change().rename("A")
    rb=dfb["Close"].pct_change().rename("B")
    both=pd.concat([ra,rb],axis=1).dropna()
    roll=both["A"].rolling(win).corr(both["B"])
    oc=round(float(both.corr().iloc[0,1]),3)
    cc_col=UP if oc>0.3 else(DOWN if oc<-0.3 else MUTED)
    cca,ccb=st.columns([2.5,1.5])
    with cca:
        fig_c=make_subplots(rows=2,cols=1,shared_xaxes=True,
            row_heights=[0.55,0.45],vertical_spacing=0.04)
        na=dfa["Close"]/float(dfa["Close"].iloc[0])*100
        nb=dfb["Close"]/float(dfb["Close"].iloc[0])*100
        fig_c.add_trace(go.Scatter(x=dfa.index,y=na,mode="lines",
            line=dict(color=BLUE,width=1.5),name=sel_a[:25]),row=1,col=1)
        fig_c.add_trace(go.Scatter(x=dfb.index,y=nb,mode="lines",
            line=dict(color=ACCENT,width=1.5),name=sel_b[:25]),row=1,col=1)
        fig_c.add_trace(go.Scatter(x=roll.index,y=roll,mode="lines",
            line=dict(color=PURPLE,width=1.5),
            fill="tozeroy",fillcolor=rgba(PURPLE,0.13),
            name=f"{win}d corr"),row=2,col=1)
        fig_c.add_hline(y=0,line_color=MUTED,line_width=0.8,row=2,col=1)
        fig_c.add_hline(y=0.7,line_dash="dot",line_color=rgba(UP,0.4),
            line_width=1,row=2,col=1)
        fig_c.add_hline(y=-0.7,line_dash="dot",line_color=rgba(DOWN,0.4),
            line_width=1,row=2,col=1)
        fig_c.update_layout(**DC(),height=320,
            title=dict(text=f"Correlation: <span style='color:{cc_col};'>{oc:+.3f}</span>",
                font_size=12),
            xaxis2=XA,yaxis=YA,
            yaxis2=dict(**YA,range=[-1.1,1.1]))
        st.plotly_chart(fig_c,use_container_width=True,config={"displayModeBar":False})
    with ccb:
        st.markdown(f'<div class="card"><div class="card-title">Analysis</div>',
            unsafe_allow_html=True)
        st.markdown(f"""<div style="text-align:center;padding:12px;
background:{cc_col}22;border-radius:8px;border:1px solid {cc_col}44;margin-bottom:12px;">
<div style="font-size:11px;color:{MUTED};">Overall correlation</div>
<div style="font-size:30px;font-weight:700;color:{cc_col};">{oc:+.3f}</div>
<div style="font-size:11px;color:{cc_col};">
{'Strong positive' if oc>0.7 else 'Moderate positive' if oc>0.3
 else 'Strong negative' if oc<-0.7 else 'Moderate negative' if oc<-0.3
 else 'Weak / no link'}</div></div>""",unsafe_allow_html=True)
        fig_sc=go.Figure(go.Scatter(x=both["A"],y=both["B"],
            mode="markers",marker=dict(color=BLUE,size=3,opacity=0.5),
            hovertemplate="A:%{x:.2%}<br>B:%{y:.2%}<extra></extra>"))
        fig_sc.update_layout(**DC(4,4,28,4),height=200,
            title=dict(text="Return scatter",font_size=10),showlegend=False,
            xaxis=dict(**XA,tickformat=".1%"),
            yaxis=dict(**YA,tickformat=".1%"))
        st.plotly_chart(fig_sc,use_container_width=True,config={"displayModeBar":False})
        st.markdown("</div>",unsafe_allow_html=True)
else:
    st.info("Loading correlation data...")
