import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

tickers = ["XOM"]

FINNHUB_KEY = "d6okk81r01qnu98if63gd6okk81r01qnu98if640"
FMP_KEY = "43a39GW86qFEdUpYJ3crtC8CCpa88yrz"

@st.cache_data
def load_fmp_daily(ticker, api_key):
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={api_key}"
        r = requests.get(url, timeout=10)
        data = r.json()
        st.write("Daily API response:", data)  # tijdelijk voor debugging
        if "historical" in data:
            df = pd.DataFrame(data["historical"])
            df["date"] = pd.to_datetime(df["date"])
            df = df.rename(columns={"close": "close_price"})
            df["ticker"] = ticker
            return df[["date", "close_price", "ticker"]]
    except Exception as e:
        st.error(f"Fout bij laden dagdata voor {ticker}: {e}")
    return pd.DataFrame()

@st.cache_data
def load_fmp_earnings(ticker, api_key):
    try:
        url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?period=quarter&apikey={api_key}"
        r = requests.get(url, timeout=10)
        data = r.json()
        st.write("Earnings API response:", data)  # tijdelijk voor debugging
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            df["ticker"] = ticker
            df["reportedDate"] = pd.to_datetime(df["date"])
            eps_col = "eps" if "eps" in df.columns else "epsdiluted"
            df["reportedEPS"] = pd.to_numeric(df[eps_col], errors="coerce")
            return df[["reportedDate", "reportedEPS", "ticker"]]
    except Exception as e:
        st.error(f"Fout bij laden earnings voor {ticker}: {e}")
    return pd.DataFrame()

for t in tickers:
    if f"daily_{t}" not in st.session_state:
        st.session_state[f"daily_{t}"] = load_fmp_daily(t, FMP_KEY)
    if f"earnings_{t}" not in st.session_state:
        st.session_state[f"earnings_{t}"] = load_fmp_earnings(t, FMP_KEY)

all_daily = pd.concat([st.session_state[f"daily_{t}"] for t in tickers], ignore_index=True)
all_earnings = pd.concat([st.session_state[f"earnings_{t}"] for t in tickers], ignore_index=True)

st.write("Kolommen daily:", all_daily.columns.tolist())
st.write("Kolommen earnings:", all_earnings.columns.tolist())
