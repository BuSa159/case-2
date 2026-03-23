import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time
from datetime import datetime

# ── 1. Configuratie ───────────────────────────────────────────────────────────
TICKERS = ['XOM', 'CVX', 'SHEL', 'TTE', 'COP', 'BP', 'ENB', 'EQNR']
kleurset = ["#2E86AB", "#E84855", "#F9C74F", "#6A994E", "#9B5DE5", "#F15BB5", "#00BBF9", "#00F5D4"]
kleur_map = {t: kleurset[i % len(kleurset)] for i, t in enumerate(TICKERS)}

# ── 2. Helper Functies ────────────────────────────────────────────────────────
def calculate_safety_score(payout, cagr, streak):
    """Berekent een score van 1 tot 10."""
    score = 0
    # Payout (Max 4 pnt)
    if payout:
        if payout < 50: score += 4
        elif payout < 75: score += 2
        elif payout < 90: score += 1
    
    # CAGR (Max 3 pnt)
    if cagr:
        if cagr > 8: score += 3
        elif cagr > 4: score += 2
        elif cagr > 0: score += 1
    
    # Streak (Max 3 pnt)
    if streak:
        if streak >= 20: score += 3
        elif streak >= 10: score += 2
        elif streak >= 5: score += 1
        
    return max(1, score)

@st.cache_data(ttl=3600)
def get_streak(ticker: str) -> int:
    try:
        stock = yf.Ticker(ticker)
        divs = stock.dividends
        if divs.empty: return 0
        annual = divs.resample('YE').sum().sort_index()
        streak, vals = 0, list(annual.values)
        for i in range(len(vals) - 1, 0, -1):
            if vals[i] >= vals[i - 1]: streak += 1
            else: break
        return streak
    except: return 0

@st.cache_data(ttl=3600)
def get_dividend_data(tickers: tuple) -> pd.DataFrame:
    rows = []
    current_year = datetime.now().year
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            divs = stock.dividends
            if divs.empty: continue
            
            divs.index = divs.index.tz_localize(None)
            annual_div = divs.resample('YE').sum()
            info = stock.info
            price = stock.fast_info.last_price
            eps = info.get('trailingEps')

            for year, amount in annual_div.items():
                y_int = year.year
                prev_ts = pd.Timestamp(year=y_int-1, month=12, day=31)
                growth = ((amount - annual_div[prev_ts]) / annual_div[prev_ts] * 100) if prev_ts in annual_div.index and annual_div[prev_ts] > 0 else None
                
                rows.append({
                    'Ticker': ticker, 'Jaar': y_int, 'Dividend ($)': round(amount, 2),
                    'Div. Rendement (%)': round(amount/price*100, 2) if price else None,
                    'Div. Stijging (%)': round(growth, 2) if growth else None,
                    'Payout Ratio (%)': round(amount/eps*100, 2) if eps and eps > 0 else None
                })
        except: continue
    return pd.DataFrame(rows)

# ── 3. UI & Logica ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Dividend Pro + Safety", layout="wide")
st.title("🛡️ Dividend Safety & Growth Dashboard")

with st.sidebar:
    st.header("Filters")
    sel_tickers = st.multiselect("Selecteer:", TICKERS, default=TICKERS)
    years = st.slider("Periode:", 2010, 2026, (2015, 2026))

df_all = get_dividend_data(tuple(sel_tickers))
curr_year = datetime.now().year

# --- Samenvatting Tabel met Safety Score ---
st.subheader("Dividend Kwaliteit Analyse")
summary_data = []
for t in sel_tickers:
    sub_full = df_all[(df_all['Ticker'] == t) & (df_all['Jaar'] < curr_year)].sort_values('Jaar')
    if sub_full.empty: continue
    
    latest = sub_full.iloc[-1]
    # CAGR 5j
    start_row = sub_full[sub_full['Jaar'] == (latest['Jaar'] - 5)]
    cagr5 = round((pow((latest['Dividend ($)'] / start_row['Dividend ($)'].values[0]), 1/5) - 1) * 100, 2) if not start_row.empty else None
    
    streak = get_streak(t)
    safety = calculate_safety_score(latest['Payout Ratio (%)'], cagr5, streak)
    
    summary_data.append({
        'Ticker': t, 'Safety Score': safety, 'Yield': f"{latest['Div. Rendement (%)']}%",
        '5j CAGR': f"{cagr5}%" if cagr5 else "N/A", 'Streak': f"{streak} jr", 'Status': "✅ Veilig" if safety > 7 else "⚠️ Oppassen" if safety > 4 else "🚨 Hoog Risico"
    })

st.table(pd.DataFrame(summary_data).set_index('Ticker'))

# ── 4. Visualisaties ──────────────────────────────────────────────────────────
st.divider()
df_f = df_all[(df_all['Ticker'].isin(sel_tickers)) & (df_all['Jaar'].between(years[0], years[1]))]
c1, c2 = st.columns(2)

with c1:
    fig = go.Figure()
    for t in sel_tickers:
        sub = df_f[df_f['Ticker'] == t].sort_values('Jaar')
        fig.add_trace(go.Bar(x=sub['Jaar'], y=sub['Dividend ($)'], name=t, marker_color=kleur_map.get(t)))
    fig.update_layout(title="Dividend per Jaar ($)", barmode='group', height=350, plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = go.Figure()
    for t in sel_tickers:
        sub = df_f[df_f['Ticker'] == t].sort_values('Jaar')
        fig.add_trace(go.Scatter(x=sub['Jaar'], y=sub['Div. Rendement (%)'], name=t, mode='lines+markers'))
    fig.update_layout(title="Yield (%)", height=350, plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

# ── 5. Detailtabel met Styling ────────────────────────────────────────────────
st.subheader("Historische Data")
df_display = df_f.sort_values(['Ticker', 'Jaar'], ascending=[True, False])

def style_df(v, col):
    if col == 'Div. Stijging (%)' and pd.notna(v):
        return 'color: #1D9E75; font-weight:bold' if v > 0 else 'color: #D85A30'
    if col == 'Payout Ratio (%)' and pd.notna(v):
        return 'color: #D85A30' if v > 80 else 'color: #1D9E75'
    return ''

st.dataframe(
    df_display.style.apply(lambda x: [style_df(v, x.name) for v in x], axis=0)
    .format({'Dividend ($)': '${:.2f}', 'Div. Rendement (%)': '{:.2f}%', 'Div. Stijging (%)': '{:.1f}%', 'Payout Ratio (%)': '{:.1f}%'}, na_rep='—'),
    use_container_width=True
)
