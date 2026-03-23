import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time
import random
from datetime import datetime

# ── 1. Configuratie ───────────────────────────────────────────────────────────
TICKERS = {
    'XOM': 'ExxonMobil', 'CVX': 'Chevron', 'SHEL': 'Shell', 
    'TTE': 'TotalEnergies', 'COP': 'ConocoPhillips', 'BP': 'BP', 
    'ENB': 'Enbridge', 'EQNR': 'Equinor'
}
kleurset = ["#2E86AB", "#E84855", "#F9C74F", "#6A994E",
            "#9B5DE5", "#F15BB5", "#00BBF9", "#00F5D4"]
kleur_map = {t: kleurset[i % len(kleurset)] for i, t in enumerate(TICKERS)}

# ── 2. Data Functies ──────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_dividend_data(tickers: tuple) -> pd.DataFrame:
    rows = []
    
    # Gebruik een status container om de gebruiker op de hoogte te houden van de delays
    with st.status("Dividendgegevens ophalen (met API-beveiliging)...", expanded=True) as status:
        for ticker in tickers:
            status.write(f"Bezig met {ticker}...")
            
            # De cruciale delay: tussen 1.5 en 3 seconden pauze per ticker
            time.sleep(random.uniform(1.5, 3.0))
            
            try:
                stock = yf.Ticker(ticker)
                
                # Dividenden ophalen
                dividends = stock.dividends
                if dividends.empty:
                    status.write(f"⚠️ Geen dividendhistorie voor {ticker}")
                    continue
                
                # Opschonen van data
                dividends.index = dividends.index.tz_localize(None)
                annual_div = dividends.resample('YE').sum()

                # Fundamentele data (Prijs & EPS)
                info = stock.info
                current_price = info.get('currentPrice') or info.get('previousClose')
                eps = info.get('trailingEps')

                for year, div_amount in annual_div.items():
                    year_int = year.year
                    # Alleen data tot en met vorig jaar of huidig jaar
                    if year_int > datetime.now().year: continue

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
                        'Dividend ($)': float(div_amount),
                        'Div. Rendement (%)': float(div_yield) if div_yield else None,
                        'Div. Stijging (%)': float(div_growth) if div_growth else None,
                        'Payout Ratio (%)': float(payout) if payout else None,
                    })
            except Exception as e:
                status.write(f"❌ Fout bij {ticker}: {e}")
                
        status.update(label="Data succesvol opgehaald!", state="complete", expanded=False)
        
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
                    # CAGR formule: ((End/Start)^(1/n) - 1) * 100
                    cagr = (pow((end_val / start_val), 1/period) - 1) * 100
                    res[f'{period}j CAGR'] = round(float(cagr), 2)
                else: res[f'{period}j CAGR'] = None
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
    sel_tickers = st.multiselect("Selecteer Tickers:", TICKERS, default=['XOM', 'CVX', 'SHEL'])
    # Verbreed de slider tot het huidige jaar
    years = st.slider("Periode in grafiek:", 2005, datetime.now().year, (2015, datetime.now().year))

if not sel_tickers: 
    st.warning("Selecteer tenminste één ticker in de sidebar.")
    st.stop()

# Data ophalen
df_all = get_dividend_data(tuple(sel_tickers))

if df_all.empty:
    st.error("Geen data beschikbaar voor de geselecteerde tickers.")
    st.stop()

# ── 5. CAGR Sectie ────────────────────────────────────────────────────────────
st.subheader("Structurele Groei (CAGR)")
df_cagr = calculate_cagr(df_all, sel_tickers)

if not df_cagr.empty:
    # Toon metrics voor de eerste 5 geselecteerde tickers
    cols = st.columns(min(len(df_cagr), 5))
    for i, row in df_cagr.head(5).iterrows():
        with cols[i]:
            val = row['5j CAGR']
            st.metric(row['Ticker'], f"{val}%" if val else "N/A", "5j CAGR")
    
    st.dataframe(df_cagr.set_index('Ticker'), use_container_width=True)

st.divider()

# ── 6. Grafieken ──────────────────────────────────────────────────────────────
df_f = df_all[(df_all['Ticker'].isin(sel_tickers)) & (df_all['Jaar'].between(years[0], years[1]))]
col_l, col_r = st.columns(2)

with col_l:
    fig_bar = go.Figure()
    for t in sel_tickers:
        sub = df_f[df_f['Ticker'] == t].sort_values('Jaar')
        fig_bar.add_trace(go.Bar(
            x=sub['Jaar'], y=sub['Dividend ($)'], 
            name=t, marker_color=kleur_map.get(t)
        ))
    fig_bar.update_layout(
        title="Dividend per Jaar ($)", 
        barmode='group', 
        template="plotly_dark",
        height=400,
        xaxis=dict(tickmode='linear')
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_r:
    fig_line = go.Figure()
    for t in sel_tickers:
        sub = df_f[df_f['Ticker'] == t].sort_values('Jaar')
        fig_line.add_trace(go.Scatter(
            x=sub['Jaar'], y=sub['Div. Rendement (%)'], 
            name=t, mode='lines+markers',
            line=dict(width=3)
        ))
    fig_line.update_layout(
        title="Dividendrendement (%)", 
        template="plotly_dark",
        height=400,
        yaxis_ticksuffix="%"
    )
    st.plotly_chart(fig_line, use_container_width=True)

# ── 7. De Gestylede Detailtabel ───────────────────────────────────────────────
st.subheader("Gedetailleerde Historie")
df_display = df_f.sort_values(['Ticker', 'Jaar'], ascending=[True, False])

# Gebruik .map() in plaats van .applymap() (Pandas 2.x compatibel)
styled_df = (
    df_display.style
    .map(kleur_groei, subset=['Div. Stijging (%)'])
    .map(kleur_payout, subset=['Payout Ratio (%)'])
    .format({
        'Dividend ($)': '${:.2f}',
        'Div. Rendement (%)': '{:.2f}%',
        'Div. Stijging (%)': lambda v: f'+{v:.1f}%' if pd.notna(v) and v > 0 else (f'{v:.1f}%' if pd.notna(v) else '—'),
        'Payout Ratio (%)': '{:.1f}%'
    }, na_rep='—')
)

st.dataframe(styled_df, use_container_width=True, height=500)

# Download knop
st.download_button(
    label="Download Data als CSV",
    data=df_display.to_csv(index=False),
    file_name="energy_dividenden.csv",
    mime="text/csv"
)
