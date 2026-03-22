import streamlit as st

st.title("Page 1")
st.write("Content for page 1 goes here.")

@st.cache_data
def load_fmp_daily(ticker, api_key):
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={api_key}"
        r = requests.get(url, timeout=10)
        st.write("Daily API response:", r.json())  # ← tijdelijk toevoegen
        ...
```

**2. Netwerk/timeout probleem in Streamlit Cloud**
Als je dit draait op Streamlit Cloud, kan het zijn dat externe API calls geblokkeerd worden.

**3. Snelste diagnose — test de URL direct in je browser:**
Plak dit in je browser en kijk wat je terugkrijgt:
```
https://financialmodelingprep.com/api/v3/historical-price-full/XOM?apikey=43a39GW86qFEdUpYJ3crtC8CCpa88yrz
```

En dit:
```
https://financialmodelingprep.com/api/v3/income-statement/XOM?period=quarter&apikey=43a39GW86qFEdUpYJ3crtC8CCpa88yrz
