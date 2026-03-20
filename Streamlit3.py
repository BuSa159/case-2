
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from dotenv import load_dotenv


st.set_page_config(layout="wide")

# --- API Keys ---
ALPHA_KEY = "046SOW0RCBGPECLG"
FINNHUB_KEY = "d6okk81r01qnu98if63gd6okk81r01qnu98if640"

# --- Tickers ---
tickers = ["XOM"]
# Voor toekomst: ["XOM", "CVX", "SHEL", "TTE", "COP", "BP", "ENB", "EQNR", "SO", "E"]


# --- Functies voor Alpha Vantage ---
@st.cache_data
def load_alpha_daily(ticker, api_key):
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={api_key}"
        r = requests.get(url)
        data = r.json()
        if "Time Series (Daily)" in data:
            df = pd.DataFrame(data["Time Series (Daily)"]).T.astype(float)
            df.index = pd.to_datetime(df.index)
            df.reset_index(inplace=True)
            df.rename(columns={"index": "date"}, inplace=True)
            df["ticker"] = ticker
            return df
    except Exception as e:
        st.error(f"Fout bij laden dagdata voor {ticker}: {e}")
    return pd.DataFrame()


@st.cache_data
def load_alpha_overview(ticker, api_key):
    try:
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
        r = requests.get(url)
        data = r.json()
        if data:
            df = pd.DataFrame([data])
            df["ticker"] = ticker
            return df
    except Exception as e:
        st.error(f"Fout bij laden overzicht voor {ticker}: {e}")
    return pd.DataFrame()


@st.cache_data
def load_alpha_shares(ticker, api_key):
    try:
        url = f"https://www.alphavantage.co/query?function=SHARES_OUTSTANDING&symbol={ticker}&apikey={api_key}"
        r = requests.get(url)
        data = r.json()
        if "SharesOutstanding" in data:
            return pd.DataFrame([{"SharesOutstanding": float(data["SharesOutstanding"]), "ticker": ticker}])
    except Exception as e:
        st.error(f"Fout bij laden aandelen voor {ticker}: {e}")
    return pd.DataFrame()


@st.cache_data
def load_alpha_earnings(ticker, api_key):
    try:
        url = f"https://www.alphavantage.co/query?function=EARNINGS&symbol={ticker}&apikey={api_key}"
        r = requests.get(url)
        data = r.json()
        if "quarterlyEarnings" in data:
            df = pd.DataFrame(data["quarterlyEarnings"])
            df["ticker"] = ticker
            df["reportedDate"] = pd.to_datetime(df["reportedDate"])
            return df
    except Exception as e:
        st.error(f"Fout bij laden winst voor {ticker}: {e}")
    return pd.DataFrame()


# --- Functie voor Finnhub ---
@st.cache_data
def load_finnhub_profile(ticker, api_key):
    try:
        url = f"https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={api_key}"
        r = requests.get(url)
        data = r.json()
        if data:
            df = pd.DataFrame([data])
            df["ticker"] = ticker
            return df
    except Exception as e:
        st.error(f"Fout bij laden Finnhub profiel voor {ticker}: {e}")
    return pd.DataFrame()


# --- Laden in session_state ---
if "daily_data" not in st.session_state:
    st.session_state.daily_data = {t: load_alpha_daily(t, ALPHA_KEY) for t in tickers}

if "overview_data" not in st.session_state:
    st.session_state.overview_data = {t: load_alpha_overview(t, ALPHA_KEY) for t in tickers}

if "shares_data" not in st.session_state:
    st.session_state.shares_data = {t: load_alpha_shares(t, ALPHA_KEY) for t in tickers}

if "earnings_data" not in st.session_state:
    st.session_state.earnings_data = {t: load_alpha_earnings(t, ALPHA_KEY) for t in tickers}

if "finnhub_profile" not in st.session_state:
    st.session_state.finnhub_profile = {t: load_finnhub_profile(t, FINNHUB_KEY) for t in tickers}


# --- Samenvoegen dataframes ---
dfs_overview = [df for df in st.session_state.overview_data.values() if not df.empty]
dfs_shares = [df for df in st.session_state.shares_data.values() if not df.empty]
dfs_finnhub = [df for df in st.session_state.finnhub_profile.values() if not df.empty]

if dfs_overview and dfs_shares and dfs_finnhub:
    df_overview_merged = pd.concat(dfs_overview, ignore_index=True)
    df_shares_merged = pd.concat(dfs_shares, ignore_index=True)
    df_finnhub_merged = pd.concat(dfs_finnhub, ignore_index=True)
    st.session_state.merged_profile = (
        df_overview_merged
        .merge(df_shares_merged, on="ticker")
        .merge(df_finnhub_merged, on="ticker")
    )

dfs_daily = [df for df in st.session_state.daily_data.values() if not df.empty]
if dfs_daily:
    st.session_state.daily_merged = pd.concat(dfs_daily, ignore_index=True)

dfs_earnings = [df for df in st.session_state.earnings_data.values() if not df.empty]
if dfs_earnings:
    st.session_state.earnings_merged = pd.concat(dfs_earnings, ignore_index=True)

# --- Visualisaties Testen ---

# --- Visualisaties ---
st.title("💹 Stock & Company Dashboard")

# Slotkoers per ticker
if "daily_merged" in st.session_state and not st.session_state.daily_merged.empty:
    st.subheader("Slotkoers per ticker")
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.lineplot(data=st.session_state.daily_merged, x="date", y="4. close", hue="ticker", ax=ax)
    plt.xticks(rotation=45)
    st.pyplot(fig)

# Marktkapitalisatie
if "merged_profile" in st.session_state and not st.session_state.merged_profile.empty:
    st.subheader("Marktkapitalisatie per ticker")
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(data=st.session_state.merged_profile, x="ticker", y="MarketCapitalization", ax=ax)
    st.pyplot(fig)

# Quarterly Earnings
if "earnings_merged" in st.session_state and not st.session_state.earnings_merged.empty:
    st.subheader("Quarterly EPS per ticker")
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.lineplot(data=st.session_state.earnings_merged, x="reportedDate", y="reportedEPS", hue="ticker", ax=ax)
    st.pyplot(fig)
