import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time
from datetime import datetime  # CRUCIALE FIX: Importeer de class direct

# ── Configuratie ──────────────────────────────────────────────────────────────
TICKERS = ['XOM', 'CVX', 'SHEL', 'TTE', 'COP', 'BP', 'ENB', 'EQNR']
kleurset = ["#2E86AB", "#E84855", "#F9C74F", "#6A994E",
            "#9B5DE5", "#F15BB5", "#00BBF9", "#00F5D4"]
kleur_map = {t: kleurset[i % len(kleurset)] for i, t in enumerate(TICKERS)}

# ── Data ophalen (gecached) ───────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_dividend_data(tickers: tuple) -> pd.DataFrame:
    rows = []
    current_year = datetime.now().year
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            dividends = stock.dividends
            if dividends.empty:
                continue
            
            dividends.index = dividends.index.tz_localize(None)
            # Resample naar jaar-einde (YE)
            annual_div = dividends.resample('YE').sum()

            # Gebruik fast_info voor prijs, info voor EPS
            info = stock.info
            try:
                current_price = stock.fast_info.last_price
            except:
                current_price = info.get('previousClose')
            
            eps = info.get('trailingEps')

            time.sleep(0.5) # Voorkom rate-limiting

            for year, div_amount in annual_div.items():
                year_int = year.year
                div_yield = (div_amount / current_price * 100) if current_price else None

                # Groei berekening
                prev_year_ts = pd.Timestamp(year=year_int-1, month=12, day=31)
                div_growth = None
                if prev_year_ts in annual_div.index:
                    prev_div = annual_div[prev_year_ts]
                    div_growth = ((div_amount - prev_div) / prev_div * 100) if prev_div and prev_div > 0 else None

                payout = (div_amount / eps * 100) if eps and eps > 0 else None

                rows.append({
                    'Ticker': ticker,
                    'Jaar': year_int,
                    'Dividend ($)': round(div_amount, 2),
                    'Div. Rendement (%)': round(div_yield, 2) if div_yield else None,
                    'Div. Stijging (%)': round(div_growth, 2) if div_growth else None,
                    'Payout Ratio (%)': round(payout, 2) if payout else None,
                })
        except Exception as e:
            st.warning(f"Fout bij ophalen data voor {ticker}: {e}")
            continue

    return pd.DataFrame(rows)

def calculate_cagr(df_all, tickers):
    """Berekent CAGR op basis van het laatste VOLLEDIGE jaar."""
    current_year = datetime.now().year
    cagr_list = []

    for ticker in tickers:
        # Filter op ticker en negeer het huidige jaar voor de CAGR groei
        sub = df_all[(df_all['Ticker'] == ticker) & (df_all['Jaar'] < current_year)].sort_values('Jaar')
        if sub.empty: 
            continue

        last_full_year_row = sub.iloc[-1]
        end_val = last_full_year_row['Dividend ($)']
        end_year = last_full_year_row['Jaar']

        res = {'Ticker': ticker}
        for period in [3, 5, 10]:
            start_year = end_year - period
            start_row = sub[sub['Jaar'] == start_year]
            
            if not start_row.empty:
                start_val = start_row['Dividend ($)'].values[0]
                if start_val > 0:
                    val = (pow((end_val / start_val), 1/period) - 1) * 100
                    res[f'{period}j CAGR'] = round(val, 2)
                else: res[f'{period}j CAGR'] = None
            else: res[f'{period}j CAGR'] = None
        cagr_list.append(res)
    return pd.DataFrame(cagr_list)

# ── Pagina opbouw ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Dividend Pro Dashboard", layout="wide")
st.title("Dividend Analyse — Energie Sector")

# ── Sidebar filter ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    selected_tickers = st.multiselect("Selecteer aandelen:", options=TICKERS, default=TICKERS)
    min_year, max_year = st.slider("Periode voor tabel/grafiek:", 2010, 2026, (2015, 2026))

if not selected_tickers:
    st.warning("Selecteer minimaal één aandeel.")
    st.stop()

# ── Data laden ────────────────────────────────────────────────────────────────
with st.spinner("Data ophalen van Yahoo Finance..."):
    df_all = get_dividend_data(tuple(selected_tickers))

if df_all.empty:
    st.error("Geen data gevonden.")
    st.stop()

# ── CAGR Sectie ───────────────────────────────────────────────────────────────
st.subheader("Structurele Groei (CAGR)")
st.caption("Gemiddelde groei per jaar over de laatste volledige kalenderjaren.")
df_cagr = calculate_cagr(df_all, selected_tickers)

if not df_cagr.empty:
    # Toon metrics voor 5-jaars groei
    m_cols = st.columns(len(df_cagr))
    for idx, row in df_cagr.iterrows():
        with m_cols[idx]:
            val = row['5j CAGR']
            st.metric(row['Ticker'], f"{val}%" if val else "N/A", "5j CAGR")
    
    st.table(df_cagr.set_index('Ticker'))

st.divider()

# ── Grafieken en Tabel ────────────────────────────────────────────────────────
# Filter de data voor de weergave
df_filtered = df_all[
    (df_all['Ticker'].isin(selected_tickers)) & 
    (df_all['Jaar'] >= min_year) & 
    (df_all['Jaar'] <= max_year)
].sort_values(['Ticker', 'Jaar'], ascending=[True, False])

col_l, col_r = st.columns(2)

with col_l:
    st.subheader("Dividend Historie ($)")
    fig_bar = go.Figure()
    for t in selected_tickers:
        sub = df_filtered[df_filtered['Ticker'] == t].sort_values('Jaar')
        fig_bar.add_trace(go.Bar(x=sub['Jaar'], y=sub['Dividend ($)'], name=t, marker_color=kleur_map.get(t)))
    fig_bar.update_layout(barmode='group', height=350)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_r:
    st.subheader("Dividendrendement (%)")
    fig_line = go.Figure()
    for t in selected_tickers:
        sub = df_filtered[df_filtered['Ticker'] == t].sort_values('Jaar')
        fig_line.add_trace(go.Scatter(x=sub['Jaar'], y=sub['Div. Rendement (%)'], name=t, mode='lines+markers'))
    fig_line.update_layout(height=350)
    st.plotly_chart(fig_line, use_container_width=True)

st.subheader("Details per jaar")
st.dataframe(df_filtered, use_container_width=True)
