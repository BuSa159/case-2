import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

tickers = ["XOM", "SHEL", "CVX", "TTE"]

# --- API Keys ---
FINNHUB_KEY = "d6okk81r01qnu98if63gd6okk81r01qnu98if640"
FMP_KEY = "43a39GW86qFEdUpYJ3crtC8CCpa88yrz"
ALPHA_VANTAGE_KEY = "046SOW0RCBGPECLG"

# --- DATA FUNCTIES ---

@st.cache_data
def load_alpha_vantage_daily(ticker, api_key):
    try:
        url = (
            f"https://www.alphavantage.co/query"
            f"?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={api_key}"
        )
        r = requests.get(url, timeout=10)
        data = r.json()
        ts = data.get("Time Series (Daily)", {})
        if ts:
            records = [
                {"date": pd.to_datetime(date), "close_price": float(values["4. close"]), "ticker": ticker}
                for date, values in ts.items()
            ]
            df = pd.DataFrame(records)
            df = df.sort_values("date").reset_index(drop=True)
            return df
        else:
            st.error(f"Geen Alpha Vantage data voor {ticker}: {data.get('Note', data.get('Information', 'Onbekende fout'))}")
    except Exception as e:
        st.error(f"Fout bij laden Alpha Vantage data voor {ticker}: {e}")
    return pd.DataFrame()


@st.cache_data
def load_fmp_overview(ticker, api_key):
    # Tijdelijk uitgeschakeld om API call limiet te voorkomen
    return pd.DataFrame()

    # try:
    #     url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"
    #     r = requests.get(url, timeout=10)
    #     data = r.json()
    #     if isinstance(data, list) and len(data) > 0:
    #         df = pd.DataFrame(data)
    #         df["ticker"] = ticker
    #         cols_to_rename = {
    #             "companyName": "Name",
    #             "mktCap": "MarketCapitalization",
    #             "sector": "Sector",
    #             "sharesOutstanding": "SharesOutstanding"
    #         }
    #         df = df.rename(columns=cols_to_rename)
    #         return df
    # except Exception as e:
    #     st.error(f"Fout bij laden overzicht voor {ticker}: {e}")
    # return pd.DataFrame()


@st.cache_data
def load_fmp_earnings(ticker, api_key):
    try:
        url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?period=quarter&apikey={api_key}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            df["ticker"] = ticker
            df["reportedDate"] = pd.to_datetime(df["date"])
            eps_col = "eps" if "eps" in df.columns else "epsdiluted"
            df["reportedEPS"] = pd.to_numeric(df[eps_col], errors="coerce")
            return df[["reportedDate", "reportedEPS", "ticker"]]
    except Exception as e:
        st.error(f"Fout bij laden FMP earnings voor {ticker}: {e}")
    return pd.DataFrame()


@st.cache_data
def load_finnhub_profile(ticker, api_key):
    try:
        url = f"https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={api_key}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if data and "name" in data:
            df = pd.DataFrame([data])
            df["ticker"] = ticker
            return df
    except Exception as e:
        st.error(f"Fout bij laden Finnhub profiel voor {ticker}: {e}")
    return pd.DataFrame()


# =====================
# LOGIC & STATE
# =====================

for t in tickers:
    if f"daily_{t}" not in st.session_state:
        st.session_state[f"daily_{t}"] = load_alpha_vantage_daily(t, ALPHA_VANTAGE_KEY)
    if f"overview_{t}" not in st.session_state:
        st.session_state[f"overview_{t}"] = load_fmp_overview(t, FMP_KEY)
    if f"earnings_{t}" not in st.session_state:
        st.session_state[f"earnings_{t}"] = load_fmp_earnings(t, FMP_KEY)
    if f"finnhub_{t}" not in st.session_state:
        st.session_state[f"finnhub_{t}"] = load_finnhub_profile(t, FINNHUB_KEY)

all_daily = pd.concat([st.session_state[f"daily_{t}"] for t in tickers], ignore_index=True)
all_overviews = pd.concat([st.session_state[f"overview_{t}"] for t in tickers], ignore_index=True)
all_earnings = pd.concat([st.session_state[f"earnings_{t}"] for t in tickers], ignore_index=True)

# =====================
# DASHBOARD LAYOUT
# =====================

_, center_col, _ = st.columns([1, 2, 1])
with center_col:
    st.markdown("<h1 style='text-align: center;'>💹 Multi-Stock Analysis Dashboard</h1>", unsafe_allow_html=True)
    st.image("wjack money.png", caption="Wasted time")

with st.sidebar:
    st.header("Instellingen")
    selected_ticker = st.selectbox("Selecteer ticker voor metrics:", tickers)
    if st.button("🔄 Cache herladen"):
        st.cache_data.clear()
        st.rerun()

st.divider()

# --- BOVENSTE RIJ: Dynamische Metric kaarten ---
if not all_overviews.empty:
    ticker_data = all_overviews[all_overviews['ticker'] == selected_ticker]

    if not ticker_data.empty:
        profile = ticker_data.iloc[0]
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Bedrijf", profile.get("Name", "—"))
        with m2:
            mcap = float(profile.get("MarketCapitalization", 0))
            st.metric("Market Cap", f"${mcap / 1e9:.1f}B")
        with m3:
            st.metric("Sector", profile.get("Sector", "—"))
        with m4:
            shares = float(profile.get("SharesOutstanding", 0))
            st.metric("Aandelen (M)", f"{shares / 1e6:.1f}M")
    else:
        st.warning(f"Geen detaildata voor {selected_ticker}")

st.divider()

# --- GRAFIEK RIJ 1 ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Koers informatie")
    if not all_daily.empty:
        periode = st.select_slider(
            "Tijdsperiode",
            options=["Alles", "Laatste 24 maanden", "Laatste 3 maanden"],
            value="Alles"
        )

        df_filtered = all_daily.copy()
        today = pd.Timestamp.today()

        if periode == "Laatste 24 maanden":
            df_filtered = df_filtered[df_filtered["date"] >= today - pd.DateOffset(months=24)]
        elif periode == "Laatste 3 maanden":
            df_filtered = df_filtered[df_filtered["date"] >= today - pd.DateOffset(months=3)]

        fig, ax = plt.subplots(figsize=(8, 5))
        sns.lineplot(data=df_filtered, x="date", y="close_price", hue="ticker", ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.info("Geen koersdata beschikbaar.")

with col_right:
    st.subheader("Marktkapitalisatie Vergelijking")
    if not all_overviews.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=all_overviews, x="ticker", y="MarketCapitalization", ax=ax, palette="viridis")
        ax.set_ylabel("USD ($)")
        st.pyplot(fig)

# --- GRAFIEK RIJ 2 ---
st.divider()
st.subheader("Quarterly EPS per ticker")
if not all_earnings.empty:
    fig, ax = plt.subplots(figsize=(15, 5))
    sns.lineplot(data=all_earnings, x="reportedDate", y="reportedEPS", hue="ticker", marker="o", ax=ax)
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.info("Geen winst data beschikbaar.")

# Debugging
# st.divider()
# st.write(all_earnings.columns.tolist())
# st.write(all_daily.columns.tolist())