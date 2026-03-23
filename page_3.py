import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from datetime import datetime, timedelta

# ── 1. Configuratie ───────────────────────────────────────────────────────────
TICKERS = {
    'XOM': 'ExxonMobil', 'CVX': 'Chevron', 'SHEL': 'Shell', 
    'TTE': 'TotalEnergies', 'COP': 'ConocoPhillips', 'BP': 'BP', 
    'ENB': 'Enbridge', 'EQNR': 'Equinor', 'SO': 'Southern Company', 'E': 'Eni'
}

# ── 2. Functies ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_clean_data(ticker):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*10)
    # auto_adjust=True voorkomt vage kolomnamen
    df = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)
    
    # yfinance geeft soms MultiIndex koloms (bijv. ['Close', 'XOM']). 
    # Dit vlakt ze af naar simpele namen.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    return df

def train_random_forest(df):
    df = df.copy()
    
    # Features maken
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['Returns'] = df['Close'].pct_change()
    df['Volatility'] = df['Close'].rolling(window=10).std()
    
    # Target: De prijs van morgen
    df['Target'] = df['Close'].shift(-1)
    df = df.dropna()
    
    features = ['Close', 'SMA_10', 'SMA_50', 'Returns', 'Volatility']
    X = df[features]
    y = df['Target']
    
    # Split (80% train, 20% test) - Geen shuffle voor tijdreeksen!
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    # Model trainen
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Voorspellingen
    test_preds = model.predict(X_test)
    
    # Voorspelling voor morgen op basis van de ALLERLAATSTE data rij
    last_row = X.tail(1)
    tomorrow_pred = model.predict(last_row)[0]
    
    # Dwing alles naar floats om formatting errors te voorkomen
    return {
        'model': model,
        'y_test': y_test,
        'preds': test_preds,
        'tomorrow': float(tomorrow_pred),
        'last_close': float(df['Close'].iloc[-1])
    }

# ── 3. Streamlit Interface ────────────────────────────────────────────────────
st.title("🛢️ AI Energy Predictor")
st.markdown("Voorspelling op basis van 10 jaar koershistorie.")

selected_ticker = st.selectbox("Selecteer een aandeel:", list(TICKERS.keys()), 
                               format_func=lambda x: f"{x} ({TICKERS[x]})")

if selected_ticker:
    with st.spinner('Model wordt getraind...'):
        df_raw = get_clean_data(selected_ticker)
        
        if not df_raw.empty:
            res = train_random_forest(df_raw)
            
            # Berekeningen voor metrics
            diff = res['tomorrow'] - res['last_close']
            pct = (diff / res['last_close']) * 100
            r2 = r2_score(res['y_test'], res['preds'])

            # DISPLAY METRICS
            col1, col2, col3 = st.columns(3)
            col1.metric("Huidige Koers", f"${res['last_close']:.2f}")
            col2.metric("AI Voorspelling (Morgen)", f"${res['tomorrow']:.2f}", f"{pct:.2f}%")
            col3.metric("Model Score (R²)", f"{r2:.2f}")

            # GRAFIEK
            st.subheader("Voorspelling vs Werkelijkheid (Test Periode)")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=res['y_test'].index, y=res['y_test'].values, name="Echt", line=dict(color="#2E86AB")))
            fig.add_trace(go.Scatter(x=res['y_test'].index, y=res['preds'], name="AI", line=dict(color="#E84855", dash='dot')))
            fig.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
            
            # FEATURE IMPORTANCE
            st.subheader("Belangrijkste indicatoren")
            feat_df = pd.DataFrame({
                'Indicator': ['Prijs', 'SMA 10', 'SMA 50', 'Returns', 'Volatiliteit'],
                'Impact': res['model'].feature_importances_
            }).sort_values('Impact', ascending=False)
            st.bar_chart(feat_df.set_index('Indicator'))

        else:
            st.error("Geen data gevonden voor dit aandeel.")
