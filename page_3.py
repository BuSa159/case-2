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

# ── 1. CONFIGURATIE & STYLING ────────────────────────────────────────────────
st.set_page_config(page_title="AI Energy Predictor", layout="wide")

TICKERS = {
    'XOM': 'ExxonMobil', 'CVX': 'Chevron', 'SHEL': 'Shell', 
    'TTE': 'TotalEnergies', 'COP': 'ConocoPhillips', 'BP': 'BP', 
    'ENB': 'Enbridge', 'EQNR': 'Equinor', 'SO': 'Southern Company', 'E': 'Eni'
}

# ── 2. DATA FUNCTIES ──────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_clean_data(ticker):
    """Haalt 10 jaar data op met een ingebouwde delay tegen API-blocks."""
    # Delay om de Yahoo Finance API te ontzien
    time.sleep(random.uniform(1.5, 3.0)) 
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*10)
    
    try:
        # auto_adjust=True zorgt voor opschoning van dividend/splitsingen
        df = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)
        
        if df.empty:
            return None

        # Fix voor yfinance MultiIndex kolommen
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        return df
    except Exception as e:
        st.error(f"Fout bij ophalen data voor {ticker}: {e}")
        return None

def train_ai_model(df):
    """Berekent features en traint het Random Forest model."""
    df = df.copy()
    
    # Feature Engineering
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['Returns'] = df['Close'].pct_change()
    df['Volatility'] = df['Close'].rolling(window=10).std()
    
    # Target: De prijs van morgen (shift -1)
    df['Target'] = df['Close'].shift(-1)
    df = df.dropna()
    
    features = ['Close', 'SMA_10', 'SMA_50', 'Returns', 'Volatility']
    X = df[features]
    y = df['Target']
    
    # Time-series split (laatste 20% is test-data)
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    # Model Training
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # Voorspellingen voor de test-set
    test_preds = model.predict(X_test)
    
    # Voorspelling voor de koers van morgen
    last_row = X.tail(1)
    tomorrow_pred = model.predict(last_row)[0]
    
    return {
        'model': model,
        'y_test': y_test,
        'preds': test_preds,
        'tomorrow': float(tomorrow_pred),
        'last_close': float(df['Close'].iloc[-1]),
        'feature_names': features
    }

# ── 3. STREAMLIT UI ───────────────────────────────────────────────────────────
st.title("🛢️ Energy Giants AI Predictor")
st.markdown("""
Dit dashboard gebruikt een **Random Forest Regressor** om trends te voorspellen in de energiesector. 
Het model kijkt naar de koershistorie van de afgelopen 10 jaar.
""")

# Sidebar selectie
selected_symbol = st.sidebar.selectbox(
    "Kies een aandeel:", 
    list(TICKERS.keys()), 
    format_func=lambda x: f"{x} ({TICKERS[x]})"
)

# Uitvoering
if selected_symbol:
    with st.spinner(f"Gegevens ophalen en model trainen voor {TICKERS[selected_symbol]}..."):
        raw_data = get_clean_data(selected_symbol)
        
        if raw_data is not None:
            # Model draaien
            res = train_ai_model(raw_data)
            
            # Berekeningen voor Metrics
            diff = res['tomorrow'] - res['last_close']
            pct = (diff / res['last_close']) * 100
            score = r2_score(res['y_test'], res['preds'])

            # --- RIJ 1: METRICS ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Huidige Koers", f"${res['last_close']:.2f}")
            col2.metric("Voorspelling Morgen", f"${res['tomorrow']:.2f}", f"{pct:.2f}%")
            col3.metric("Model Betrouwbaarheid (R²)", f"{score:.2f}")

            st.divider()

            # --- RIJ 2: GRAFIEK ---
            st.subheader(f"Voorspelling vs Werkelijkheid: {TICKERS[selected_symbol]}")
            fig = go.Figure()
            # Werkelijke koers
            fig.add_trace(go.Scatter(
                x=res['y_test'].index, y=res['y_test'].values, 
                name="Werkelijke Koers", line=dict(color="#2E86AB", width=2)
            ))
            # Voorspelde koers
            fig.add_trace(go.Scatter(
                x=res['y_test'].index, y=res['preds'], 
                name="AI Voorspelling", line=dict(color="#E84855", width=2, dash='dot')
            ))
            
            fig.update_layout(
                template="plotly_dark",
                hovermode="x unified",
                margin=dict(l=0, r=0, t=30, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- RIJ 3: FEATURE IMPORTANCE ---
            st.subheader("Wat drijft de voorspelling?")
            importance_df = pd.DataFrame({
                'Indicator': res['feature_names'],
                'Belangrijkheid': res['model'].feature_importances_
            }).sort_values('Belangrijkheid', ascending=True)

            # Horizontale bar chart voor impact
            import plotly.express as px
            fig_imp = px.bar(
                importance_df, x='Belangrijkheid', y='Indicator', 
                orientation='h', template="plotly_dark",
                color_discrete_sequence=['#F9C74F']
            )
            fig_imp.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_imp, use_container_width=True)

        else:
            st.error("Kon geen verbinding maken met de data-bron. Probeer het over een minuutje weer.")

st.sidebar.info("Tip: De R² score geeft aan hoe goed het model de test-data volgde. Een score dicht bij 1.00 is ideaal.")
