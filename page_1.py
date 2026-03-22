import streamlit as st
import requests

try:
    r = requests.get("https://financialmodelingprep.com/api/v3/historical-price-full/XOM?apikey=43a39GW86qFEdUpYJ3crtC8CCpa88yrz", timeout=10)
    st.write("Status code:", r.status_code)
    st.write("Response:", r.json())
except Exception as e:
    st.error(f"Fout: {e}")
st.write("Kolommen earnings:", all_earnings.columns.tolist())
