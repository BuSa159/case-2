import streamlit as st
import requests
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

#KEYS en URL (tijdelijk)
API_KEY_ALP = "046SOW0RCBGPECLG"
API_KEY_FINN = "d6okk81r01qnu98if63gd6okk81r01qnu98if640"
API_URL_ALP = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey={API_KEY_1}'
API_URL_FINN = f'...'

# --- API Keys ---
API_KEY_ALP = "046SOW0RCBGPECLG"
API_KEY_FINN = "d6okk81r01qnu98if63gd6okk81r01qnu98if640"

# --- Tickers die we willen ophalen ---
tickers = {
    "XOM": "ExxonMobil",
    "CVX": "Chevron",
    "SHEL": "Shell",
    "TTE": "TotalEnergies",
    "COP": "ConocoPhillips",
    "BP": "BP",
    "ENB": "Enbridge",
    "EQNR": "Equinor",
    "SO": "Southern Company",
    "E": "Eni"
}

# --- Functie om Alpha Vantage data op te halen per ticker ---
def load_alpha_ticker(ticker, api_key):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "apikey": api_key
    }
    r = requests.get(url, params=params)
    data = r.json()

    if "Time Series (Daily)" in data:
        df = pd.DataFrame(data["Time Series (Daily)"]).T
        df = df.astype(float)
        df.index = pd.to_datetime(df.index)
        df.reset_index(inplace=True)
        df.rename(columns={"index": "date"}, inplace=True)
        df["ticker"] = ticker  # Voeg ticker kolom toe voor merge
        return df
    else:
        st.warning(f"Alpha Vantage error voor {ticker}: {data}")
        return pd.DataFrame()  # lege df bij error

# --- Laden van Alpha Vantage data in session_state ---
if "alpha_data" not in st.session_state:
    st.session_state.alpha_data = {}
    for ticker in tickers:
        st.session_state.alpha_data[ticker] = load_alpha_ticker(ticker, API_KEY_ALP)

# --- Alle tickers samenvoegen in één DataFrame ---
if "df_alpha_merged" not in st.session_state:
    dfs = [df for df in st.session_state.alpha_data.values() if not df.empty]
    if dfs:
        st.session_state.df_alpha_merged = pd.concat(dfs, ignore_index=True)
    else:
        st.session_state.df_alpha_merged = pd.DataFrame()

# --- Finnhub dummy-data (vervangen door echte API call) ---
if "df_finn" not in st.session_state:
    df = pd.DataFrame({
        "date": pd.date_range(start="2024-01-01", periods=5),
        "sentiment": [0.1, 0.2, -0.1, 0.3, 0.5]
    })
    df["date"] = pd.to_datetime(df["date"])
    st.session_state.df_finn = df

# --- Merge Alpha Vantage + Finnhub data ---
if "merged_df" not in st.session_state:
    df1 = st.session_state.df_alpha_merged
    df2 = st.session_state.df_finn
    # Zorg dat beide date kolommen datetime zijn
    df1["date"] = pd.to_datetime(df1["date"])
    df2["date"] = pd.to_datetime(df2["date"])
    st.session_state.merged_df = pd.merge(df1, df2, on="date", how="inner")

# --- Weergeven merged data ---
st.write(st.session_state.merged_df)

# --- Reload knop ---
if st.button("Reload data"):
    st.session_state.clear()
    st.rerun()

#Figuren(voorbeeld)
if not st.session_state.merged_df.empty:
    plt.figure(figsize=(10,5))
    sns.lineplot(data=st.session_state.merged_df, x="date", y="4. close", hue="ticker")
    plt.title("Slotkoers per ticker")
    plt.xlabel("Datum")
    plt.ylabel("Slotkoers")
    plt.xticks(rotation=45)
    st.pyplot(plt)


#Indeling