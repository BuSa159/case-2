import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide", page_title="Stock Dashboard")

# --- API Keys ---
FINNHUB_KEY = "d6okk81r01qnu98if63gd6okk81r01qnu98if640"
FMP_KEY = "43a39GW86qFEdUpYJ3crtC8CCpa88yrz"

# --- Tickers ---
tickers = ["XOM", "BP"]
# Voor toekomst: ["XOM", "CVX", "SHEL", "TTE", "COP", "BP", "ENB", "EQNR", "SO", "E"]


# --- Functies voor FMP ---
@st.cache_data
def load_fmp_daily(ticker, api_key):
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={api_key}"
        r = requests.get(url)
        data = r.json()
        if "historical" in data:
            df = pd.DataFrame(data["historical"])
            df["date"] = pd.to_datetime(df["date"])
            df = df.rename(columns={"close": "4. close"})
            df["ticker"] = ticker
            return df[["date", "4. close", "ticker"]]
    except Exception as e:
        st.error(f"Fout bij laden dagdata voor {ticker}: {e}")
    return pd.DataFrame()


@st.cache_data
def load_fmp_overview(ticker, api_key):
    try:
        url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"
        r = requests.get(url)
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            df["ticker"] = ticker
            df = df.rename(columns={
                "companyName": "Name",
                "mktCap": "MarketCapitalization",
                "sector": "Sector",
                "sharesOutstanding": "SharesOutstanding"
            })
            return df
    except Exception as e:
        st.error(f"Fout bij laden overzicht voor {ticker}: {e}")
    return pd.DataFrame()


@st.cache_data
def load_fmp_earnings(ticker, api_key):
    try:
        url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?period=quarter&apikey={api_key}"
        r = requests.get(url)
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            df["ticker"] = ticker
            df["reportedDate"] = pd.to_datetime(df["date"])
            df["reportedEPS"] = pd.to_numeric(df["eps"], errors="coerce")
            return df[["reportedDate", "reportedEPS", "ticker"]]
    except Exception as e:
        st.error(f"Fout bij laden FMP earnings voor {ticker}: {e}")
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
    st.session_state.daily_data = {t: load_fmp_daily(t, FMP_KEY) for t in tickers}

if "overview_data" not in st.session_state:
    st.session_state.overview_data = {t: load_fmp_overview(t, FMP_KEY) for t in tickers}

if "earnings_data" not in st.session_state:
    st.session_state.earnings_data = {t: load_fmp_earnings(t, FMP_KEY) for t in tickers}

if "finnhub_profile" not in st.session_state:
    st.session_state.finnhub_profile = {t: load_finnhub_profile(t, FINNHUB_KEY) for t in tickers}


# --- Samenvoegen dataframes ---
dfs_overview = [df for df in st.session_state.overview_data.values() if not df.empty]
dfs_finnhub = [df for df in st.session_state.finnhub_profile.values() if not df.empty]

if dfs_overview and dfs_finnhub:
    df_overview_merged = pd.concat(dfs_overview, ignore_index=True)
    df_finnhub_merged = pd.concat(dfs_finnhub, ignore_index=True)
    st.session_state.merged_profile = (
        df_overview_merged
        .merge(df_finnhub_merged, on="ticker")
    )

dfs_daily = [df for df in st.session_state.daily_data.values() if not df.empty]
if dfs_daily:
    st.session_state.daily_merged = pd.concat(dfs_daily, ignore_index=True)

dfs_earnings = [df for df in st.session_state.earnings_data.values() if not df.empty]
if dfs_earnings:
    st.session_state.earnings_merged = pd.concat(dfs_earnings, ignore_index=True)


# =====================
# DASHBOARD LAYOUT
# =====================

st.title("💹 Stock & Company Dashboard")
if st.button("🔄 Cache wissen & herladen"):
    st.cache_data.clear()
    for key in ["daily_data", "overview_data", "earnings_data", "finnhub_profile", "merged_profile", "daily_merged", "earnings_merged"]:
        st.session_state.pop(key, None)
    st.rerun()
st.divider()

# --- BOVENSTE RIJ: Metric kaarten ---
if "merged_profile" in st.session_state and not st.session_state.merged_profile.empty:
    profile = st.session_state.merged_profile.iloc[0]

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Bedrijf", profile.get("Name", "—"))
    with m2:
        market_cap = float(profile.get("MarketCapitalization", 0))
        st.metric("Marktkapitalisatie", f"${market_cap / 1e9:.1f}B")
    with m3:
        st.metric("Sector", profile.get("Sector", "—"))
    with m4:
        shares = float(profile.get("SharesOutstanding", 0))
        st.metric("Aandelen uitstaand", f"{shares / 1e6:.0f}M")

    st.divider()

# --- GRAFIEK RIJ 1: Slotkoers + Marktkapitalisatie naast elkaar ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Slotkoers over tijd")
    if "daily_merged" in st.session_state and not st.session_state.daily_merged.empty:
        fig, ax = plt.subplots(figsize=(7, 4))
        sns.lineplot(data=st.session_state.daily_merged, x="date", y="4. close", hue="ticker", ax=ax)
        ax.set_xlabel("Datum")
        ax.set_ylabel("Koers ($)")
        ax.tick_params(axis='x', rotation=45)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("Geen koersdata beschikbaar.")

with col_right:
    st.subheader("Marktkapitalisatie per ticker")
    if "merged_profile" in st.session_state and not st.session_state.merged_profile.empty:
        fig, ax = plt.subplots(figsize=(7, 4))
        sns.barplot(data=st.session_state.merged_profile, x="ticker", y="MarketCapitalization", ax=ax)
        ax.set_xlabel("Ticker")
        ax.set_ylabel("Marktkapitalisatie ($)")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("Geen profieldata beschikbaar.")

st.divider()

# --- GRAFIEK RIJ 2: Quarterly EPS breed over de volle breedte ---
st.subheader("Quarterly EPS per ticker")
if "earnings_merged" in st.session_state and not st.session_state.earnings_merged.empty:
    fig, ax = plt.subplots(figsize=(14, 4))
    sns.lineplot(data=st.session_state.earnings_merged, x="reportedDate", y="reportedEPS", hue="ticker", ax=ax)
    ax.set_xlabel("Datum")
    ax.set_ylabel("EPS ($)")
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
else:
    st.info("Geen winst data beschikbaar.")
