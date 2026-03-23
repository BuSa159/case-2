import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time
from datetime import datetime

# ── 1. Configuratie ───────────────────────────────────────────────────────────
TICKERS = ['XOM', 'CVX', 'SHEL', 'TTE', 'COP', 'BP', 'ENB', 'EQNR']
kleurset = ["#2E86AB", "#E84855", "#F9C74F", "#6A994E",
            "#9B5DE5", "#F15BB5", "#00BBF9", "#00F5D4"]
kleur_map = {t: kleurset[i % len(kleurset)] for i, t in enumerate(TICKERS)}

# ── 2. Data Functies ──────────────────────────────────────────────────────────
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
            annual_div = dividends.resample('YE').sum()

            info = stock.info
            try:
                current_price = stock.fast_info.last_price
            except:
                current_price = info.get('previousClose')
            
            eps = info.get('trailingEps')

            for year, div_amount in annual_div.items():
                year_int = year.year
                div_yield = (div_amount / current_price * 100) if current_price else None

                # Groei berekening t.o.v. vorig jaar
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
            time.sleep(0.5)
        except Exception as e:
            st.warning(f"Fout bij {ticker}: {e}")
    return pd.DataFrame(rows)

def calculate_cagr(df_all, tickers):
    current_year = datetime.now().year
    cagr_list = []
    for ticker in tickers:
        sub = df_all[(df_all['Ticker'] == ticker) & (df_all['Jaar'] < current_year)].sort_values('Jaar')
        if sub.empty: continue
        
        last_full = sub.iloc[-1]
        end_val, end_year = last_full['Dividend ($)'], last_full['Jaar']
        res = {'Ticker': ticker}
        for period in [3, 5, 10]:
            start_row = sub[sub['Jaar'] == (end_year - period)]
            if not start_row.empty:
                start_val = start_row['Dividend ($)'].values[0]
                if start_val > 0:
                    res[f'{period}j CAGR'] = round((pow((end_val / start_val), 1/period) - 1) * 100, 2)
            else: res[f'{period}j CAGR'] = None
        cagr_list.append(res)
    return pd.DataFrame(cagr_list)

# ── 3. Styling Functies ───────────────────────────────────────────────────────
def kleur_groei(val):
    if pd.isna(val): return ''
    return 'color: #1D9E75; font-weight:bold' if val > 0 else 'color: #D85A30'

def kleur_payout(val):
    if pd.isna(val): return ''
    if val > 75: return 'color: #D85A30' # Risicovol
    if val > 50: return 'color: #EF9F27' # Aandachtspunt
    return 'color: #1D9E75' # Gezond

# ── 4. Pagina Opbouw ──────────────────────────────────────────────────────────
st.set_page_config(page_title="Dividend Pro", layout="wide")
st.title("Energy Sector Dividend Intelligence")

with st.sidebar:
    st.header("Instellingen")
    sel_tickers = st.multiselect("Tickers:", TICKERS, default=TICKERS)
    years = st.slider("Periode:", 2010, 2026, (2015, 2026))

if not sel_tickers: st.stop()

df_all = get_dividend_data(tuple(sel_tickers))

# ── 5. CAGR Sectie ────────────────────────────────────────────────────────────
st.subheader("Structurele Groei (CAGR)")
df_cagr = calculate_cagr(df_all, sel_tickers)
if not df_cagr.empty:
    cols = st.columns(len(df_cagr))
    for i, row in df_cagr.iterrows():
        with cols[i]:
            st.metric(row['Ticker'], f"{row['5j CAGR']}%" if row['5j CAGR'] else "N/A", "5j CAGR")
    st.dataframe(df_cagr.set_index('Ticker'), use_container_width=True)

st.divider()

# ── 6. Grafieken ──────────────────────────────────────────────────────────────
df_f = df_all[(df_all['Ticker'].isin(sel_tickers)) & (df_all['Jaar'].between(years[0], years[1]))]
col_l, col_r = st.columns(2)

with col_l:
    fig_bar = go.Figure()
    for t in sel_tickers:
        sub = df_f[df_f['Ticker'] == t].sort_values('Jaar')
        fig_bar.add_trace(go.Bar(x=sub['Jaar'], y=sub['Dividend ($)'], name=t, marker_color=kleur_map.get(t)))
    fig_bar.update_layout(title="Dividend per Jaar ($)", barmode='group', height=350)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_r:
    fig_line = go.Figure()
    for t in sel_tickers:
        sub = df_f[df_f['Ticker'] == t].sort_values('Jaar')
        fig_line.add_trace(go.Scatter(x=sub['Jaar'], y=sub['Div. Rendement (%)'], name=t, mode='lines+markers'))
    fig_line.update_layout(title="Dividendrendement (%)", height=350)
    st.plotly_chart(fig_line, use_container_width=True)

# ── 7. De Gestylede Detailtabel ───────────────────────────────────────────────
st.subheader("Gedetailleerde Historie")
df_display = df_f.sort_values(['Ticker', 'Jaar'], ascending=[True, False])

styled_df = (
    df_display.style
    .applymap(kleur_groei, subset=['Div. Stijging (%)'])
    .applymap(kleur_payout, subset=['Payout Ratio (%)'])
    .format({
        'Dividend ($)': '${:.2f}',
        'Div. Rendement (%)': '{:.2f}%',
        'Div. Stijging (%)': lambda v: f'+{v:.1f}%' if pd.notna(v) and v > 0 else (f'{v:.1f}%' if pd.notna(v) else '—'),
        'Payout Ratio (%)': '{:.1f}%'
    }, na_rep='—')
)

st.dataframe(styled_df, use_container_width=True, height=500)

# Download knop
st.download_button("Download CSV", df_display.to_csv(index=False), "dividenden.csv", "text/csv")
