import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf

tickers = ["XOM", "SHEL", "CVX", "TTE", "COP", "BP", "ENB", "EQNR"]

# --- API Keys ---
FINNHUB_KEY = "d6okk81r01qnu98if63gd6okk81r01qnu98if640"

# --- DATA FUNCTIES ---

@st.cache_data
def load_daily(ticker):
    try:
        df = yf.download(ticker, period="1y", auto_adjust=True, progress=False)
        df = df[["Close"]].reset_index()
        df.columns = ["date", "close_price"]
        df["ticker"] = ticker
        return df
    except Exception as e:
        st.error(f"Fout bij laden koersdata voor {ticker}: {e}")
    return pd.DataFrame()


@st.cache_data
def load_earnings(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.quarterly_income_stmt.T
        if "Basic EPS" in df.columns:
            df = df[["Basic EPS"]].reset_index()
            df.columns = ["reportedDate", "reportedEPS"]
        elif "Diluted EPS" in df.columns:
            df = df[["Diluted EPS"]].reset_index()
            df.columns = ["reportedDate", "reportedEPS"]
        else:
            st.warning(f"Geen EPS kolom gevonden voor {ticker}")
            return pd.DataFrame()
        df["reportedDate"] = pd.to_datetime(df["reportedDate"])
        df["reportedEPS"] = pd.to_numeric(df["reportedEPS"], errors="coerce")
        df["ticker"] = ticker
        return df[["reportedDate", "reportedEPS", "ticker"]].dropna()
    except Exception as e:
        st.error(f"Fout bij laden earnings voor {ticker}: {e}")
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
        st.session_state[f"daily_{t}"] = load_daily(t)
    if f"earnings_{t}" not in st.session_state:
        st.session_state[f"earnings_{t}"] = load_earnings(t)
    if f"finnhub_{t}" not in st.session_state:
        st.session_state[f"finnhub_{t}"] = load_finnhub_profile(t, FINNHUB_KEY)

all_daily = pd.concat([st.session_state[f"daily_{t}"] for t in tickers], ignore_index=True)
all_earnings = pd.concat([st.session_state[f"earnings_{t}"] for t in tickers], ignore_index=True)

# Marktkapitalisatie ophalen uit session_state (ingeladen door pagina 2)
market_cap_data = []
for t in tickers:
    info = st.session_state.get(f"info_{t}")
    if info:
        market_cap_data.append({
            "ticker": t,
            "MarketCapitalization": info.get("MarketCapitalization", 0)
        })
df_market_cap = pd.DataFrame(market_cap_data)

# Centrale kleurmap — elke ticker krijgt een vaste kleur
kleurset = ["#2E86AB", "#E84855", "#F9C74F", "#6A994E",
            "#9B5DE5", "#F15BB5", "#00BBF9", "#00F5D4"]
kleur_map = {t: kleurset[i % len(kleurset)] for i, t in enumerate(tickers)}

# =====================
# DASHBOARD LAYOUT
# =====================

_, center_col, _ = st.columns([1, 2, 1])
with center_col:
    st.markdown("<h1 style='text-align: center;'>Financieel Energie Dashboard</h1>", unsafe_allow_html=True)
st.divider()

# --- GRAFIEK RIJ 1 ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Sluitende Beurskoers")
    if not all_daily.empty:
        today = pd.Timestamp.today()

        periode = st.select_slider(
            "Tijdsperiode",
            options=["Alles", "Laatste 3 maanden", "Laatste maand"],
            value="Alles"
        )

        df_filtered = all_daily.copy()
        if periode == "Laatste 3 maanden":
            df_filtered = df_filtered[df_filtered["date"] >= today - pd.DateOffset(months=3)]
        elif periode == "Laatste maand":
            df_filtered = df_filtered[df_filtered["date"] >= today - pd.DateOffset(months=1)]

        fig, ax = plt.subplots(figsize=(8, 5))
        sns.lineplot(data=df_filtered, x="date", y="close_price", hue="ticker",
                     palette=kleur_map, ax=ax)
        ax.set_xlabel("Datum")
        ax.set_ylabel("Slotkoers (USD)")
        ax.legend(title="Ticker", bbox_to_anchor=(1.01, 1), loc="upper left", borderaxespad=0)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("Geen koersdata beschikbaar.")

with col_right:
    st.subheader("Marktkapitalisatie Vergelijking")
    if not df_market_cap.empty:
        selected_tickers = st.multiselect(
            "Selecteer bedrijven:",
            options=tickers,
            default=tickers
        )

        df_mcap_filtered = df_market_cap[df_market_cap["ticker"].isin(selected_tickers)].copy()

        if not df_mcap_filtered.empty:
            df_mcap_filtered["MarketCap_B"] = df_mcap_filtered["MarketCapitalization"] / 1e9
            # Sorteren van hoog naar laag
            df_mcap_filtered = df_mcap_filtered.sort_values("MarketCap_B", ascending=False)

            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(
                data=df_mcap_filtered,
                x="ticker",
                y="MarketCap_B",
                ax=ax,
                palette={t: kleur_map[t] for t in df_mcap_filtered["ticker"]}
            )
            ax.set_xlabel("Bedrijf")
            ax.set_ylabel("Marktkapitalisatie (miljarden USD)")
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("Selecteer minimaal één bedrijf.")
    else:
        st.info("Laad eerst pagina 2 om marktkapitalisatie data in te laden.")

# --- GRAFIEK RIJ 2 ---
st.divider()
st.subheader("Quarterly EPS")
if not all_earnings.empty:
    fig, ax = plt.subplots(figsize=(15, 5))
    sns.lineplot(data=all_earnings, x="reportedDate", y="reportedEPS", hue="ticker",
                 marker="o", palette=kleur_map, ax=ax)
    ax.set_xlabel("Datum")
    ax.set_ylabel("EPS (USD)")
    ax.legend(title="Ticker", bbox_to_anchor=(1.01, 1), loc="upper left", borderaxespad=0)
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
else:
    st.info("Geen winst data beschikbaar.")

# --- Stupiede foto ---
st.divider()
_, center_col2, _ = st.columns([1, 2, 1])
with center_col2:
    st.image("wjack money.png", caption="Wasted time")


# --- FINANCIEEL GEVOEL ---
st.divider()
gevoel = st.radio("Hoe voel je je financieel?", options=["Goed", "Slecht"])

_, center_col2, _ = st.columns([1, 2, 1])
with center_col2:
    if gevoel == "Goed":
        st.image("stonks_up.webp", caption="Alles is goed")
    else:
        st.image("stonks_down.webp", caption="Alles is fout")
