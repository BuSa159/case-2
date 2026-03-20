# streamlit_app.py
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide")

# --- API Keys ---
ALPHA_KEY = "JE_ALPHA_KEY_HIER"
FINNHUB_KEY = "JE_FINNHUB_KEY_HIER"

# --- Jouw tickers ---
tickers = ["XOM"]

#voor toekomst
#, "CVX", "SHEL", "TTE", "COP", "BP", "ENB", "EQNR", "SO", "E"]


# --- Functies voor Alpha Vantage ---
def load_alpha_daily(ticker, api_key):
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
    return pd.DataFrame()


def load_alpha_overview(ticker, api_key):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
    r = requests.get(url)
    data = r.json()
    if data:
        df = pd.DataFrame([data])
        df["ticker"] = ticker
        return df
    return pd.DataFrame()


def load_alpha_shares(ticker, api_key):
    url = f"https://www.alphavantage.co/query?function=SHARES_OUTSTANDING&symbol={ticker}&apikey={api_key}"
    r = requests.get(url)
    data = r.json()
    if "SharesOutstanding" in data:
        return pd.DataFrame([{"SharesOutstanding": float(data["SharesOutstanding"]), "ticker": ticker}])
    return pd.DataFrame()


def load_alpha_earnings(ticker, api_key):
    url = f"https://www.alphavantage.co/query?function=EARNINGS&symbol={ticker}&apikey={api_key}"
    r = requests.get(url)
    data = r.json()
    if "quarterlyEarnings" in data:
        df = pd.DataFrame(data["quarterlyEarnings"])
        df["ticker"] = ticker
        df["reportedDate"] = pd.to_datetime(df["reportedDate"])
        return df
    return pd.DataFrame()


# --- Functie voor Finnhub Company Profile ---
def load_finnhub_profile(ticker, api_key):
    url = f"https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={api_key}"
    r = requests.get(url)
    data = r.json()
    if data:
        df = pd.DataFrame([data])
        df["ticker"] = ticker
        return df
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

# OVERVIEW + SHARES + Finnhub profile
dfs_overview = [df for df in st.session_state.overview_data.values() if not df.empty]
dfs_shares = [df for df in st.session_state.shares_data.values() if not df.empty]
dfs_finnhub = [df for df in st.session_state.finnhub_profile.values() if not df.empty]

if dfs_overview and dfs_shares and dfs_finnhub:
    df_overview_merged = pd.concat(dfs_overview, ignore_index=True)
    df_shares_merged = pd.concat(dfs_shares, ignore_index=True)
    df_finnhub_merged = pd.concat(dfs_finnhub, ignore_index=True)

    st.session_state.merged_profile = df_overview_merged.merge(df_shares_merged, on="ticker").merge(df_finnhub_merged,
                                                                                                    on="ticker")

# Daily time series
dfs_daily = [df for df in st.session_state.daily_data.values() if not df.empty]
if dfs_daily:
    st.session_state.daily_merged = pd.concat(dfs_daily, ignore_index=True)

# Earnings
dfs_earnings = [df for df in st.session_state.earnings_data.values() if not df.empty]
if dfs_earnings:
    st.session_state.earnings_merged = pd.concat(dfs_earnings, ignore_index=True)

            #toegevoegd
# --- Visualisaties ---
case-2/
    main_page.py      #eerste pagina
    pages/
        01_grafieken.py #tweede pagina
        02_overzichten.py  # derde pagina

main_page.py
st.title("💹 Stock & Company Dashboard")

# Slotkoers per ticker
if "daily_merged" in st.session_state and not st.session_state.daily_merged.empty:
    st.subheader("Slotkoers per ticker")
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=st.session_state.daily_merged, x="date", y="4. close", hue="ticker")
    plt.xticks(rotation=45)
    st.pyplot(plt)

# Marktkapitalisatie + Shares
if "merged_profile" in st.session_state and not st.session_state.merged_profile.empty:
    st.subheader("Marktkapitalisatie per ticker")
    plt.figure(figsize=(10, 5))
    sns.barplot(data=st.session_state.merged_profile, x="ticker", y="MarketCapitalization")
    st.pyplot(plt)

# Quarterly Earnings
if "earnings_merged" in st.session_state and not st.session_state.earnings_merged.empty:
    st.subheader("Quarterly EPS per ticker")
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=st.session_state.earnings_merged, x="reportedDate", y="reportedEPS", hue="ticker")
    st.pyplot(plt)

        #toegevoegd
01_grafieken.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# data set voor grafieken
# Eerste grafiek voor slotkoers over tijd
fig, ax = plt.subplots()
ax.plot(____.index, ____['close'])
ax.set_xlabel('Tijd')
ax.set_ylabel('Slotkoers')
ax[0].set_title('Slotkoers over tijd')

            # toegevoegd
02_grafieken.py
import streamlit as st
import yfinance as yf
import pandas as pd

# Pagina configuratie
st.set_page_config(page_title="Investment Valuator", layout="wide")

st.title("📈 Aandelen Waarderings Model")
st.sidebar.header("Variabelen")

# 1. Ticker Input
ticker_symbol = st.sidebar.text_input("Voer Ticker in (bijv. ASML.AS, AAPL, MSFT):", value="AAPL")

# Ophalen van basisdata
@st.cache_data
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    # Pak de meest recente winst per aandeel (EPS)
    eps = info.get('trailingEps', 0)
    price = info.get('currentPrice', 0)
    name = info.get('longName', 'Onbekend')
    return eps, price, name

eps, current_price, company_name = get_stock_data(ticker_symbol)

# 2. Sliders voor de variabelen
st.sidebar.subheader("Model Parameters")
payout_ratio = st.sidebar.slider("Payout Ratio (%)", 0, 100, 30) / 100
growth_rate = st.sidebar.slider("Groei Verwachting (%) - Eerste 5 jaar", 0, 50, 10) / 100
discount_rate = st.sidebar.slider("Discount Value / WACC (%)", 5, 20, 10) / 100
terminal_multiple = st.sidebar.slider("Terminal Multiple (P/E)", 5, 50, 15)

# --- BEREKENING ---
def calculate_valuation(eps, growth, discount, payout, terminal_mult):
    years = list(range(1, 6))
    projections = []
    current_eps = eps
    
    # Projectie voor de komende 5 jaar
    for year in years:
        current_eps *= (1 + growth)
        dividend = current_eps * payout
        # Present Value van het dividend
        pv_dividend = dividend / ((1 + discount) ** year)
        projections.append(pv_dividend)
    
    # Terminal Value berekening aan het einde van jaar 5
    terminal_value = (current_eps * terminal_mult)
    pv_terminal_value = terminal_value / ((1 + discount) ** 5)
    
    intrinsic_value = sum(projections) + pv_terminal_value
    return intrinsic_value

intrinsic_value = calculate_valuation(eps, growth_rate, discount_rate, payout_ratio, terminal_multiple)

# --- VISUALISATIE ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Bedrijf", company_name)
with col2:
    st.metric("Huidige Koers", f"${current_price:.2f}")
with col3:
    delta = ((intrinsic_value - current_price) / current_price) * 100
    st.metric("Intrinsieke Waarde", f"${intrinsic_value:.2f}", f"{delta:.2f}%")

# Toelichting
st.divider()
st.subheader("Analyse")
if intrinsic_value > current_price:
    st.success(f"Op basis van jouw parameters is {company_name} momenteel **ondergewaardeerd**.")
else:
    st.error(f"Op basis van jouw parameters is {company_name} momenteel **overgewaardeerd**.")

st.info(f"**Berekening:** Dit model gebruikt een 5-jaars groeimodel met een Terminal Multiple van {terminal_multiple}x de winst in jaar 5, verdisconteerd tegen {discount_rate*100}%.")




