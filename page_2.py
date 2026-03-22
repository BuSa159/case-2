import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf

tickers = ["XOM"]

@st.cache_data
def load_daily(ticker):
    df = yf.download(ticker, period="5y", auto_adjust=True)
    df = df[["Close"]].reset_index()
    df.columns = ["date", "close_price"]
    df["ticker"] = ticker
    return df

@st.cache_data
def load_info(ticker):
    info = yf.Ticker(ticker).info
    return {
        "Name": info.get("longName", "—"),
        "MarketCapitalization": info.get("marketCap", 0),
        "Sector": info.get("sector", "—"),
        "SharesOutstanding": info.get("sharesOutstanding", 0),
    }

@st.cache_data
def load_earnings(ticker):
    t = yf.Ticker(ticker)
    df = t.quarterly_financials.T
    if "Net Income" in df.columns and "Basic EPS" in df.columns:
        df = df[["Basic EPS"]].reset_index()
        df.columns = ["reportedDate", "reportedEPS"]
    else:
        df = t.quarterly_earnings.reset_index()
        df = df.rename(columns={"Earnings": "reportedEPS", "index": "reportedDate"})
    df["ticker"] = ticker
    return df

for t in tickers:
    if f"daily_{t}" not in st.session_state:
        st.session_state[f"daily_{t}"] = load_daily(t)
    if f"info_{t}" not in st.session_state:
        st.session_state[f"info_{t}"] = load_info(t)
    if f"earnings_{t}" not in st.session_state:
        st.session_state[f"earnings_{t}"] = load_earnings(t)

all_daily = pd.concat([st.session_state[f"daily_{t}"] for t in tickers], ignore_index=True)
all_earnings = pd.concat([st.session_state[f"earnings_{t}"] for t in tickers], ignore_index=True)

st.title("💹 Stock Dashboard")

st.title("Page 2")
st.write("Content for page 2 goes here.")
st.divider()

# Metrics
info = st.session_state[f"info_{tickers[0]}"]
m1, m2, m3, m4 = st.columns(4)
m1.metric("Bedrijf", info["Name"])
m2.metric("Market Cap", f"${info['MarketCapitalization']/1e9:.1f}B")
m3.metric("Sector", info["Sector"])
m4.metric("Aandelen (M)", f"{info['SharesOutstanding']/1e6:.1f}M")

st.divider()

# Slotkoers
st.subheader("Slotkoers over tijd")
fig, ax = plt.subplots(figsize=(10, 4))
sns.lineplot(data=all_daily, x="date", y="close_price", hue="ticker", ax=ax)
plt.xticks(rotation=45)
st.pyplot(fig)

st.divider()

# EPS
st.subheader("Quarterly EPS")
if not all_earnings.empty:
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    sns.lineplot(data=all_earnings, x="reportedDate", y="reportedEPS", hue="ticker", marker="o", ax=ax2)
    plt.xticks(rotation=45)
    st.pyplot(fig2)
