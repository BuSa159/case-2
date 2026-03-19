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

# KEYS toekomstig
API_KEY_ALP
API_KEY_FINN

# Session_state voor data
if "df_alpha" not in st.session_state:
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": "IBM",
        "apikey": "JOUW_KEY"
    }

    r = requests.get(url, params=params)
    data = r.json()

    df = pd.DataFrame(data["Time Series (Daily)"]).T
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    df.reset_index(inplace=True)
    df.rename(columns={"index": "date"}, inplace=True)

    st.session_state.df_alpha = df

#moet nog worden toegevoegd
if "df_finn" not in st.session_state:
    # voorbeeld (vervang met echte API call)
    df = pd.DataFrame({
        "date": pd.date_range(start="2024-01-01", periods=5),
        "sentiment": [0.1, 0.2, -0.1, 0.3, 0.5]
    })

    st.session_state.df_finn = df

#mergen van de api data
if "merged_df" not in st.session_state:
    df1 = st.session_state.df_alpha
    df2 = st.session_state.df_finn

    merged = pd.merge(df1, df2, on="date", how="inner")
    st.session_state.merged_df = merged

#de df
st.write(st.session_state.merged_df)

#Reload knop
if st.button("Reload data"):
    st.session_state.clear()
    st.rerun()
#Figuren


#Indeling