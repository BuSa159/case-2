import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from datetime import datetime, timedelta

# ── 1. Configuratie ───────────────────────────────────────────────────────────
st.set_page_config(page_title="Energy Giants AI Predictor", layout="wide")

TICKERS = {
    'XOM': 'ExxonMobil',
    'CVX': 'Chevron',
    'SHEL': 'Shell',
    'TTE': 'TotalEnergies',
    'COP': 'ConocoPhillips',
    'BP': 'BP',
    'ENB': 'Enbridge',
    'EQNR': 'Equinor',
    'SO': 'Southern Company',
    'E': 'Eni'
}

# ── 2. Data & Model Functies ──────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_data(ticker):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*10)
    df = yf.download(ticker, start=start_date, end=end_date)
    return df

def prepare_and_train(df):
    # Feature Engineering
    df = df.copy()
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['Returns'] = df['Close'].pct_change()
    df['Volatility'] = df['Close'].rolling(window=10).std()
    
    # Target: De prijs van morgen
    df['Target'] = df['Close'].shift(-1)
    df.dropna(inplace=True)
    
    features = ['Close', 'SMA_10', 'SMA_50', 'Returns', 'Volatility']
    X = df[features]
    y = df['Target']
    
    # Time-series split (laatste 20% voor test)
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    # Model Training
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Voorspellingen
    test_preds = model.predict(X_test)
    
    # Voorspelling voor morgen
    last_row = X.tail(1)
    tomorrow_pred = model.predict(last_row)[0]
    
    return model, X_test, y_test, test_preds, tomorrow_pred, df['Close'].iloc[-1]

# ── 3. Streamlit UI ───────────────────────────────────────────────────────────
st.title("🛢️ Energy Giants: Random Forest Price Predictor")
st.markdown("Dit model gebruikt 10 jaar historische data om de koers van morgen te voorspellen.")

# Sidebar voor selectie
selected_ticker = st.sidebar.selectbox("Kies een aandeel:", list(TICKERS.keys()), format_func=lambda x: f"{x} ({TICKERS[x]})")

with st.spinner(f"Data ophalen en model trainen voor {selected_ticker}..."):
    # Data ophalen
    data = get_data(selected_ticker)
    
    if not data.empty:
        # Model draaien
        model, X_test, y_real, y_pred, tomorrow, last_price = prepare_and_train(data)
        
        # Statistieken tonen
        diff = tomorrow - last_price
        pct_change = (diff / last_price) * 100
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Laatste Slotkoers", f"${last_price:.2f}")
        col2.metric("Voorspelling Morgen", f"${tomorrow:.2f}", f"{pct_change:.2f}%")
        col3.metric("Model Betrouwbaarheid (R²)", f"{r2_score(y_real, y_pred):.2f}")

        # Grafiek: Werkelijkheid vs Voorspelling (Test Set)
        st.subheader("Model Prestaties: Werkelijkheid vs AI Voorspelling (Laatste periode)")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=y_real.index, y=y_real.values, name="Werkelijke Prijs", line=dict(color="#2E86AB")))
        fig.add_trace(go.Scatter(x=y_real.index, y=y_pred, name="AI Voorspelling", line=dict(color="#E84855", dash='dot')))
        
        fig.update_layout(template="plotly_dark", height=500, xaxis_title="Datum", yaxis_title="Prijs ($)")
        st.plotly_chart(fig, use_container_width=True)

        # Feature Importance
        st.subheader("Welke factoren bepalen de voorspelling?")
        importances = pd.DataFrame({
            'Feature': ['Prijs', 'SMA 10', 'SMA 50', 'Returns', 'Volatiliteit'],
            'Belangrijkheid': model.feature_importances_
        }).sort_values(by='Belangrijkheid', ascending=False)
        
        st.bar_chart(importances.set_index('Feature'))

    else:
        st.error("Kon geen data ophalen voor dit aandeel.")

st.info("**Let op:** Dit model is gebaseerd op historische data en biedt geen garantie voor de toekomst. Beleggen brengt risico's met zich mee.")
