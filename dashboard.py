import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf

tickers = ["XOM", "SHEL", "CVX", "TTE", "COP", "BP", "ENB", "EQNR"]

# --- API Keys ---

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
def load_cashflow(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.quarterly_cashflow.T
        if "Free Cash Flow" in df.columns:
            df = df[["Free Cash Flow"]].reset_index()
            df.columns = ["reportedDate", "freeCashFlow"]
        else:
            st.warning(f"Geen Free Cash Flow kolom gevonden voor {ticker}")
            return pd.DataFrame()
        df["reportedDate"] = pd.to_datetime(df["reportedDate"])
        df["freeCashFlow"] = pd.to_numeric(df["freeCashFlow"], errors="coerce") / 1e9
        df["ticker"] = ticker
        return df[["reportedDate", "freeCashFlow", "ticker"]].dropna()
    except Exception as e:
        st.error(f"Fout bij laden cashflow voor {ticker}: {e}")
    return pd.DataFrame()

# =====================
# LOGIC & STATE
# =====================

for t in tickers:
    if f"daily_{t}" not in st.session_state:
        st.session_state[f"daily_{t}"] = load_daily(t)
    if f"cashflow_{t}" not in st.session_state:
        st.session_state[f"cashflow_{t}"] = load_cashflow(t)

all_daily = pd.concat([st.session_state[f"daily_{t}"] for t in tickers], ignore_index=True)
all_cashflow = pd.concat([st.session_state[f"cashflow_{t}"] for t in tickers], ignore_index=True)

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

_, center_col1, _ = st.columns([0.5, 3, 0.5])
with center_col1:
    st.markdown("""
        <h2 style='text-align: center;'>🎈🎈🎈 Hallo en welkom bij het financieel energie dashboard 🎈🎈🎈</h2>
        <p style='text-align: center; font-size: 18px; line-height: 2.5;'>
            In deze Streamlit omgeving worden 8 verschillende energie bedrijven bestudeerd.<br>
            Op de meerdere pagina's wordt er gekeken naar verschillende aspecten van de energie bedrijven.<br>
            Waaronder wat meer bedrijfsinformatie, een analyse van het dividend en een voorspeller voor aandelen.<br>
            Op de startpagina kan je wat algemene informatie vinden van de energie bedrijven,<br>
            en ook aangeven wat jouw financiële gevoel is 😉
        </p>
    """, unsafe_allow_html=True)

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
            df_mcap_filtered = df_mcap_filtered.sort_values("MarketCap_B", ascending=False)

            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(
                data=df_mcap_filtered,
                x="ticker",
                y="MarketCap_B",
                ax=ax,
                palette={t: kleur_map[t] for t in df_mcap_filtered["ticker"]},
                order=df_mcap_filtered["ticker"].tolist()
            )
            ax.set_xlabel("Bedrijf")
            ax.set_ylabel("Marktkapitalisatie (miljarden USD)")
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("Selecteer minimaal één bedrijf.")
    else:
        st.info("Laad eerst pagina Bedrijfsinfo om marktkapitalisatie data in te laden.")

# --- GRAFIEK RIJ 2 ---
st.divider()
st.subheader("Quarterly Free Cash Flow")
if not all_cashflow.empty:
    import plotly.graph_objects as go

    selected_cf_tickers = st.multiselect(
        "Selecteer bedrijven:",
        options=tickers,
        default=tickers,
        key="cf_multiselect"
    )

    fig_cf = go.Figure()

    for t in selected_cf_tickers:
        df_t = all_cashflow[all_cashflow["ticker"] == t]
        if df_t.empty:
            continue
        fig_cf.add_trace(go.Scatter(
            x=df_t["reportedDate"],
            y=df_t["freeCashFlow"],
            mode="lines+markers",
            name=t,
            line=dict(color=kleur_map[t], width=2),
            marker=dict(size=7, color=kleur_map[t]),
            hovertemplate=(
                f"<b>{t}</b><br>"
                "Datum: %{x|%Y-%m-%d}<br>"
                "Free Cash Flow: $%{y:.2f}B<br>"
                "<extra></extra>"
            )
        ))

    fig_cf.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)

    fig_cf.update_layout(
        xaxis_title="Datum",
        yaxis_title="Free Cash Flow (miljarden USD)",
        legend=dict(title="Ticker"),
        height=500,
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified"
    )
    fig_cf.update_xaxes(showgrid=True, gridcolor="#EEEEEE")
    fig_cf.update_yaxes(showgrid=True, gridcolor="#EEEEEE")

    st.plotly_chart(fig_cf, use_container_width=True)
else:
    st.info("Geen cashflow data beschikbaar.")

# --- FINANCIEEL GEVOEL ---
st.divider()
gevoel = st.radio("Hoe voel je je financieel?", options=["Goed", "Slecht"])

_, center_col2, _ = st.columns([1, 2, 1])
with center_col2:
    if gevoel == "Goed":
        st.image("stonks_up.webp", caption="Alles is goed")
    else:
        st.image("stonks_down.webp", caption="Alles is fout")
