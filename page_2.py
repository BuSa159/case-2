import streamlit as st
import pandas as pd
import yfinance as yf

tickers = ["XOM", "SHEL", "CVX", "TTE", "COP", "BP", "ENB", "EQNR"]

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

# Sorteeroptie
sorteer_op = st.selectbox(
    "Sorteer op:",
    options=["Marktkapitalisatie (hoog → laag)", "Marktkapitalisatie (laag → hoog)", "Aandelen (hoog → laag)", "Aandelen (laag → hoog)"]
)

# Bouw dataframe van alle tickers
rows = []
for t in tickers:
    info = st.session_state.get(f"info_{t}", {})
    rows.append({
        "ticker": t,
        "Name": info.get("Name", "—"),
        "MarketCapitalization": info.get("MarketCapitalization", 0),
        "Sector": info.get("Sector", "—"),
        "SharesOutstanding": info.get("SharesOutstanding", 0),
    })

df = pd.DataFrame(rows)

# Sorteren
if sorteer_op == "Marktkapitalisatie (hoog → laag)":
    df = df.sort_values("MarketCapitalization", ascending=False)
elif sorteer_op == "Marktkapitalisatie (laag → hoog)":
    df = df.sort_values("MarketCapitalization", ascending=True)
elif sorteer_op == "Aandelen (hoog → laag)":
    df = df.sort_values("SharesOutstanding", ascending=False)
elif sorteer_op == "Aandelen (laag → hoog)":
    df = df.sort_values("SharesOutstanding", ascending=True)

st.divider()

# Toon elke ticker als een rij met metrics
for _, row in df.iterrows():
    st.markdown(f"#### {row['ticker']} — {row['Name']}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Bedrijf", row["Name"])
    m2.metric("Market Cap", f"${row['MarketCapitalization'] / 1e9:.1f}B")
    m3.metric("Sector", row["Sector"])
    m4.metric("Aandelen (M)", f"{row['SharesOutstanding'] / 1e6:.1f}M")
    st.divider()