import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from datetime import datetime, timedelta
import time
import random

# ── 1. CONFIGURATIE ───────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Price vs Oil Return", layout="wide")

TICKERS = {
    'XOM': 'ExxonMobil', 'CVX': 'Chevron', 'SHEL': 'Shell', 
    'TTE': 'TotalEnergies', 'COP': 'ConocoPhillips', 'BP': 'BP', 
    'ENB': 'Enbridge', 'EQNR': 'Equinor'
}

# ── 2. DATA FUNCTIES ──────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_full_data(stock_ticker):
    """Haalt aandeeldata en Brent Crude op met delay."""
    time.sleep(random.uniform(1.5, 2.5))
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*10)
    
    s_data = yf.download(stock_ticker, start=start_date, end=end_date, auto_adjust=True)
    o_data = yf.download("BZ=F", start=start_date, end=end_date, auto_adjust=True)
    
    if s_data.empty or o_data.empty: return None

    # MultiIndex fix
    for d in [s_data, o_data]:
        if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)

    df = s_data[['Close']].rename(columns={'Close': 'Stock_Close'})
    df['Oil_Close'] = o_data['Close']
    return df.dropna()

# ── 3. DE TWEE MODELLEN ───────────────────────────────────────────────────────

def run_price_model(df):
    """Het 'oude' model: Voorspelt de PRIJS ($)"""
    df = df.copy()
    df['SMA_10'] = df['Stock_Close'].rolling(window=10).mean()
    df['Target'] = df['Stock_Close'].shift(-1)
    df = df.dropna()
    
    X = df[['Stock_Close', 'SMA_10']]
    y = df['Target']
    split = int(len(X) * 0.8)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X[:split], y[:split])
    
    preds = model.predict(X[split:])
    tomorrow = model.predict(X.tail(1))[0]
    return y[split:], preds, tomorrow, r2_score(y[split:], preds)

def run_return_model(df):
    """Het 'nieuwe' model: Voorspelt de RETURN (%) met Olie"""
    df = df.copy()
    df['Stock_Ret'] = df['Stock_Close'].pct_change()
    df['Oil_Ret'] = df['Oil_Close'].pct_change()
    df['Target_Ret'] = df['Stock_Ret'].shift(-1)
    df = df.dropna()
    
    X = df[['Stock_Ret', 'Oil_Ret']]
    y = df['Target_Ret']
    split = int(len(X) * 0.8)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X[:split], y[:split])
    
    preds = model.predict(X[split:])
    tomorrow_ret = model.predict(X.tail(1))[0]
    return y[split:], preds, tomorrow_ret, r2_score(y[split:], preds)

# ── 4. STREAMLIT UI ───────────────────────────────────────────────────────────
st.title("🌲 Dual Random Forest: Price vs. Oil Correlation")

selected_symbol = st.sidebar.selectbox("Kies een aandeel:", list(TICKERS.keys()), format_func=lambda x: f"{x} ({TICKERS[x]})")

if selected_symbol:
    data = get_full_data(selected_symbol)
    
    if data is not None:
        # Draai beide modellen
        y_p_test, p_preds, p_tomorrow, p_r2 = run_price_model(data)
        y_r_test, r_preds, r_tomorrow, r_r2 = run_return_model(data)
        
        # --- BOVENSTE RIJ: METRICS ---
        st.subheader("Voorspelling voor Morgen")
        c1, c2, c3 = st.columns(3)
        last_price = data['Stock_Close'].iloc[-1]
        
        c1.metric("Huidige Koers", f"${last_price:.2f}")
        c2.metric("Prijs Model (Oud)", f"${p_tomorrow:.2f}", f"{((p_tomorrow-last_price)/last_price)*100:.2f}%")
        c3.metric("Olie-Return Model (Nieuw)", f"{r_tomorrow*100:.2f}%", "Daily Return")

        st.divider()

        # --- TABS VOOR DE TWEE ANALYSES ---
        tab1, tab2 = st.tabs(["📈 Prijs Voorspeller (Oud)", "📊 Olie Correlatie (Nieuw)"])

        with tab1:
            st.write(f"**Model Score (R²): {p_r2:.4f}** (Let op: Hoge score door lag-effect)")
            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(x=y_p_test.index, y=y_p_test, name="Echt", line=dict(color="#2E86AB")))
            fig_p.add_trace(go.Scatter(x=y_p_test.index, y=p_preds, name="AI Voorspelling", line=dict(color="#E84855", dash='dot')))
            fig_p.update_layout(template="plotly_dark", height=450, title="Prijsvoorspelling (Lag-effect zichtbaar)")
            st.plotly_chart(fig_p, use_container_width=True)

        with tab2:
            st.write(f"**Model Score (R²): {r_r2:.4f}** (Lage score, maar realistischer voor trading)")
            fig_r = go.Figure()
            fig_r.add_trace(go.Scatter(x=y_r_test.index, y=y_r_test, name="Echte Return", line=dict(color="#6A994E")))
            fig_r.add_trace(go.Scatter(x=y_r_test.index, y=r_preds, name="AI Return Voorspelling", line=dict(color="#F9C74F")))
            fig_r.update_layout(template="plotly_dark", height=450, title="Dagelijkse Rendementen (Focus op volatiliteit)")
            st.plotly_chart(fig_r, use_container_width=True)

        # --- Olie Prijs Check ---
        st.info(f"Huidige Brent Crude prijs gebruikt in model: **${data['Oil_Close'].iloc[-1]:.2f}**")
