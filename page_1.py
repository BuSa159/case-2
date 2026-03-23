import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time

# ── Configuratie ──────────────────────────────────────────────────────────────
TICKERS  = ['XOM', 'CVX', 'SHEL', 'TTE', 'COP', 'BP', 'ENB', 'EQNR']
kleurset = ["#2E86AB", "#E84855", "#F9C74F", "#6A994E",
            "#9B5DE5", "#F15BB5", "#00BBF9", "#00F5D4"]
kleur_map = {t: kleurset[i % len(kleurset)] for i, t in enumerate(TICKERS)}


# ── Data ophalen (gecached) ───────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_dividend_data(tickers: tuple) -> pd.DataFrame:
    rows = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)

            dividends = stock.dividends
            if dividends.empty:
                continue
            dividends.index = dividends.index.tz_localize(None)
            annual_div = dividends.resample('YE').sum()

            info          = stock.fast_info
            current_price = info.last_price
            eps_row       = stock.info.get('trailingEps')

            time.sleep(1)

            for year, div_amount in annual_div.items():
                year_int  = year.year
                div_yield = (div_amount / current_price * 100) if current_price else None

                prev = [y for y in annual_div.index if y.year == year_int - 1]
                div_growth = None
                if prev:
                    prev_div   = annual_div[prev[0]]
                    div_growth = ((div_amount - prev_div) / prev_div * 100) if prev_div else None

                payout = (div_amount / eps_row * 100) if eps_row and eps_row > 0 else None

                rows.append({
                    'Ticker':             ticker,
                    'Jaar':               year_int,
                    'Dividend ($)':       round(div_amount, 2),
                    'Div. Rendement (%)': round(div_yield, 2)  if div_yield  else None,
                    'Div. Stijging (%)':  round(div_growth, 2) if div_growth else None,
                    'Payout Ratio (%)':   round(payout, 2)     if payout     else None,
                })
        except Exception as e:
            st.warning(f"Fout bij ophalen data voor {ticker}: {e}")
            continue

    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_streak(ticker: str) -> int:
    """Bereken aantal opeenvolgende jaren met gelijk of hoger dividend."""
    try:
        stock     = yf.Ticker(ticker)
        dividends = stock.dividends
        if dividends.empty:
            return 0
        dividends.index = dividends.index.tz_localize(None)
        annual = dividends.resample('YE').sum().sort_index()
        streak = 0
        vals   = list(annual.values)
        for i in range(len(vals) - 1, 0, -1):
            if vals[i] >= vals[i - 1]:
                streak += 1
            else:
                break
        return streak
    except Exception:
        return 0


# ── Pagina opbouw ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Dividend Dashboard", layout="wide")

st.title("Dividend overzicht — energie sector")
st.caption("XOM · CVX · SHEL · TTE · COP · BP · ENB · EQNR")

st.divider()

# ── Sidebar filter ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    selected_tickers = st.multiselect(
        "Selecteer aandelen:",
        options=TICKERS,
        default=TICKERS,
    )
    min_year, max_year = st.slider(
        "Periode:",
        min_value=2010,
        max_value=2024,
        value=(2015, 2024),
    )

if not selected_tickers:
    st.warning("Selecteer minimaal één aandeel in de sidebar.")
    st.stop()

# ── Data laden ────────────────────────────────────────────────────────────────
with st.spinner("Data ophalen van Yahoo Finance…"):
    df_all = get_dividend_data(tuple(selected_tickers))

if df_all.empty:
    st.error("Geen dividenddata beschikbaar.")
    st.stop()

df = df_all[
    (df_all['Ticker'].isin(selected_tickers)) &
    (df_all['Jaar'] >= min_year) &
    (df_all['Jaar'] <= max_year)
].sort_values(['Ticker', 'Jaar'], ascending=[True, False]).reset_index(drop=True)

# ── KPI kaarten ───────────────────────────────────────────────────────────────
latest = (
    df.sort_values('Jaar')
      .groupby('Ticker')
      .last()
      .reset_index()
)

avg_yield  = latest['Div. Rendement (%)'].mean()
avg_growth = latest['Div. Stijging (%)'].mean()
avg_payout = latest['Payout Ratio (%)'].mean()

streaks    = {t: get_streak(t) for t in selected_tickers}
max_streak = max(streaks.values()) if streaks else 0
max_ticker = max(streaks, key=streaks.get) if streaks else "—"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Gem. dividendrendement",   f"{avg_yield:.1f}%"  if pd.notna(avg_yield)  else "—", "vs. S&P500 ~1.3%")
col2.metric("Gem. dividendgroei (YoY)", f"{avg_growth:.1f}%" if pd.notna(avg_growth) else "—")
col3.metric("Gem. payout ratio",        f"{avg_payout:.0f}%" if pd.notna(avg_payout) else "—")
col4.metric("Langste dividend streak",  f"{max_streak} jr",  max_ticker)

st.divider()

# ── Grafieken ─────────────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)

# Staafgrafiek — dividend per jaar
with col_l:
    st.subheader("Dividend per jaar ($)")
    fig_bar = go.Figure()
    for ticker in selected_tickers:
        sub = df[df['Ticker'] == ticker].sort_values('Jaar')
        fig_bar.add_trace(go.Bar(
            x=sub['Jaar'],
            y=sub['Dividend ($)'],
            name=ticker,
            marker_color=kleur_map.get(ticker, '#888'),
            marker_line_width=0,
        ))
    fig_bar.update_layout(
        barmode='group',
        height=320,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation='h', y=-0.2),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor='rgba(128,128,128,0.1)'),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Lijndiagram — rendement over tijd
with col_r:
    st.subheader("Dividendrendement (%)")
    fig_line = go.Figure()
    for ticker in selected_tickers:
        sub = df[df['Ticker'] == ticker].sort_values('Jaar')
        fig_line.add_trace(go.Scatter(
            x=sub['Jaar'],
            y=sub['Div. Rendement (%)'],
            name=ticker,
            mode='lines+markers',
            line=dict(color=kleur_map.get(ticker, '#888'), width=2),
            marker=dict(size=5),
        ))
    fig_line.update_layout(
        height=320,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation='h', y=-0.2),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor='rgba(128,128,128,0.1)', ticksuffix='%'),
    )
    st.plotly_chart(fig_line, use_container_width=True)

st.divider()

# ── Detailtabel ───────────────────────────────────────────────────────────────
st.subheader("Detail per aandeel")


def kleur_groei(val):
    if pd.isna(val):
        return ''
    return 'color: #1D9E75; font-weight:500' if val > 0 else 'color: #D85A30; font-weight:500'


def kleur_payout(val):
    if pd.isna(val):
        return ''
    if val > 80:
        return 'color: #D85A30'
    if val > 60:
        return 'color: #EF9F27'
    return 'color: #1D9E75'


styled = (
    df.style
    .applymap(kleur_groei,  subset=['Div. Stijging (%)'])
    .applymap(kleur_payout, subset=['Payout Ratio (%)'])
    .format({
        'Dividend ($)':       '{:.2f}',
        'Div. Rendement (%)': '{:.2f}%',
        'Div. Stijging (%)':  lambda v: f'+{v:.1f}%' if pd.notna(v) and v > 0 else (f'{v:.1f}%' if pd.notna(v) else '—'),
        'Payout Ratio (%)':   lambda v: f'{v:.0f}%'  if pd.notna(v) else '—',
    }, na_rep='—')
)

st.dataframe(styled, use_container_width=True, height=420)

# ── Download knop ─────────────────────────────────────────────────────────────
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download als CSV",
    data=csv,
    file_name='dividend_overzicht.csv',
    mime='text/csv',
)


# ── CAGR Berekening Functie ──────────────────────────────────────────────────
def calculate_cagr_metrics(df_all, tickers):
    cagr_results = []
    
    for ticker in tickers:
        # Filter data voor dit aandeel en sorteer op jaar
        sub = df_all[df_all['Ticker'] == ticker].sort_values('Jaar')
        if sub.empty:
            continue
            
        latest_div = sub['Dividend ($)'].iloc[-1]
        latest_year = sub['Jaar'].iloc[-1]
        
        res = {'Ticker': ticker}
        
        for period in [3, 5, 10]:
            target_year = latest_year - period
            # Zoek de dividend waarde van n jaar geleden
            start_div_row = sub[sub['Jaar'] == target_year]
            
            if not start_div_row.empty:
                start_div = start_div_row['Dividend ($)'].values[0]
                if start_div > 0:
                    # Formule: (Eindwaarde / Beginwaarde)^(1/n) - 1
                    cagr = (latest_div / start_div) ** (1 / period) - 1
                    res[f'{period}j CAGR'] = round(cagr * 100, 2)
                else:
                    res[f'{period}j CAGR'] = None
            else:
                res[f'{period}j CAGR'] = None
                
        cagr_results.append(res)
        
    return pd.DataFrame(cagr_results)

# ── In de hoofdsectie (onder de grafieken of tabel) ───────────────────────────
st.divider()
st.subheader("Dividend Groei Analyse (CAGR)")
st.markdown("De *Compound Annual Growth Rate* laat het gemiddelde groeipercentage per jaar zien over een specifieke periode.")

df_cagr = calculate_cagr_metrics(df_all, selected_tickers)

if not df_cagr.empty:
    # Styling voor de CAGR tabel
    def style_cagr(val):
        if pd.isna(val): return ''
        return 'color: #1D9E75; font-weight: bold' if val >= 5 else '' # Accent bij >5% groei

    styled_cagr = (
        df_cagr.style
        .applymap(style_cagr, subset=['3j CAGR', '5j CAGR', '10j CAGR'])
        .format({
            '3j CAGR': '{:.2f}%',
            '5j CAGR': '{:.2f}%',
            '10j CAGR': '{:.2f}%',
        }, na_rep='N/A')
    )
    
    st.dataframe(styled_cagr, use_container_width=True)
else:
    st.info("Onvoldoende historische data om CAGR te berekenen.")

