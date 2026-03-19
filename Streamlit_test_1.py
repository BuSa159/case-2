import streamlit as st
import requests
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

#KEYS en URL
API_KEY_1 = "046SOW0RCBGPECLG"
API_URL = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey={API_KEY_1}'


#Standaard Cache
@st.cache_data(ttl=600)  # 10 minuten cache
def fetch_data(url, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


# Cache data defineren
data = fetch_data(API_URL, API_KEY_1)

# Zet om naar DataFrame en gebruik .T om datums naar de rijen te verplaatsen
# We gebruiken .from_dict() voor meer controle
IBM = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')

# Optioneel: zet de index om naar echte datums en de cijfers naar floats
IBM.index = pd.to_datetime(IBM.index)
IBM = IBM.astype(float)
#fig1 = sns.lineplot(data=IBM, x='index', y='4.close')
st.write(IBM)
#st.pyplot(fig1)