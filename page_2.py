import streamlit as st
import pandas as pd
import yfinance as yf

tickers = ["XOM", "SHEL", "CVX", "TTE"]

@st.cache_data
def load_info(ticker):
    info = yf.Ticker(ticker).info
    return {
        "Name": info.get("longName", "—"),
        "MarketCapitalization": info.get("marketCap", 0),
        "Sector": info.get("sector", "—"),
        "SharesOutstanding": info.get("sharesOutstanding", 0),
    }

for t in tickers:
    if f"info_{t}" not in st.session_state:
        st.session_state[f"info_{t}"] = load_info(t)

st.title("Bedrijfsinfo Dashboard")

st.divider()

# Metrics
info = st.session_state[f"info_{tickers[0]}"]
m1, m2, m3, m4 = st.columns(4)
m1.metric("Bedrijf", info["Name"])
m2.metric("Market Cap", f"${info['MarketCapitalization']/1e9:.1f}B")
m3.metric("Sector", info["Sector"])
m4.metric("Aandelen (M)", f"{info['SharesOutstanding']/1e6:.1f}M")