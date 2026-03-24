import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from datetime import datetime, timedelta
import time
import random

# ── 1. CONFIGURATIE ───────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Price vs Oil Return + Intrinsieke Waarde", layout="wide")

TICKERS = {
    'XOM': 'ExxonMobil', 'CVX': 'Chevron', 'SHEL': 'Shell',
    'TTE': 'TotalEnergies', 'COP': 'ConocoPhillips', 'BP': 'BP',
    'ENB': 'Enbridge', 'EQNR': 'Equinor'
}

# ── 2. DATA FUNCTIES ──────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_full_data(stock_ticker):
    """Haalt aandeeldata en Brent Crude op met delay."""
    time.sleep(random.uniform(1.5, 2.5))
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 10)

    s_data = yf.download(stock_ticker, start=start_date, end=end_date, auto_adjust=True)
    o_data = yf.download("BZ=F", start=start_date, end=end_date, auto_adjust=True)

    if s_data.empty or o_data.empty:
        return None

    for d in [s_data, o_data]:
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)

    df = s_data[['Close']].rename(columns={'Close': 'Stock_Close'})
    df['Oil_Close'] = o_data['Close']
    return df.dropna()


# ── 3. DE TWEE MODELLEN ───────────────────────────────────────────────────────
def run_price_model(df):
    """Het 'oude' model: Voorspelt de PRIJS ($)"""
    df = df.copy()
    df['SMA_10'] = df['Stock_Close'].rolling(window=10).mean()
    df['Target'] = df['Stock_Close'].shift(-1)
    df = df.dropna()

    X = df[['Stock_Close', 'SMA_10']]
    y = df['Target']
    split = int(len(X) * 0.8)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X[:split], y[:split])

    preds = model.predict(X[split:])
    tomorrow = model.predict(X.tail(1))[0]
    return y[split:], preds, tomorrow, r2_score(y[split:], preds)


def run_return_model(df):
    """Het 'nieuwe' model: Voorspelt de RETURN (%) met Olie"""
    df = df.copy()
    df['Stock_Ret'] = df['Stock_Close'].pct_change()
    df['Oil_Ret'] = df['Oil_Close'].pct_change()
    df['Target_Ret'] = df['Stock_Ret'].shift(-1)
    df = df.dropna()

    X = df[['Stock_Ret', 'Oil_Ret']]
    y = df['Target_Ret']
    split = int(len(X) * 0.8)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X[:split], y[:split])

    preds = model.predict(X[split:])
    tomorrow_ret = model.predict(X.tail(1))[0]
    return y[split:], preds, tomorrow_ret, r2_score(y[split:], preds)


# ── 4. STREAMLIT UI ───────────────────────────────────────────────────────────
st.title("🌲 Dual Random Forest: Price vs. Oil Correlation")

selected_symbol = st.sidebar.selectbox(
    "Kies een aandeel:",
    list(TICKERS.keys()),
    format_func=lambda x: f"{x} ({TICKERS[x]})"
)

# ── Cache reset knop (NIEUW) ──────────────────────────────────────────────────
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Cache wissen & herladen"):
    st.cache_data.clear()
    st.rerun()

if selected_symbol:
    data = get_full_data(selected_symbol)

    if data is not None:
        y_p_test, p_preds, p_tomorrow, p_r2 = run_price_model(data)
        y_r_test, r_preds, r_tomorrow, r_r2 = run_return_model(data)

        st.subheader("Voorspelling voor Morgen")
        c1, c2, c3 = st.columns(3)
        last_price = data['Stock_Close'].iloc[-1]

        c1.metric("Huidige Koers", f"${last_price:.2f}")
        c2.metric("Prijs Model (Oud)", f"${p_tomorrow:.2f}", f"{((p_tomorrow - last_price) / last_price) * 100:.2f}%")
        c3.metric("Olie-Return Model (Nieuw)", f"{r_tomorrow * 100:.2f}%", "Daily Return")

        st.divider()

        tab1, tab2 = st.tabs(["📈 Prijs Voorspeller (Oud)", "📊 Olie Correlatie (Nieuw)"])

        with tab1:
            st.write(f"**Model Score (R²): {p_r2:.4f}** (Let op: Hoge score door lag-effect)")
            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(x=y_p_test.index, y=y_p_test, name="Echt", line=dict(color="#2E86AB")))
            fig_p.add_trace(go.Scatter(x=y_p_test.index, y=p_preds, name="AI Voorspelling", line=dict(color="#E84855", dash='dot')))
            fig_p.update_layout(template="plotly_dark", height=450, title="Prijsvoorspelling (Lag-effect zichtbaar)")
            st.plotly_chart(fig_p, use_container_width=True)

        with tab2:
            st.write(f"**Model Score (R²): {r_r2:.4f}** (Lage score, maar realistischer voor trading)")
            fig_r = go.Figure()
            fig_r.add_trace(go.Scatter(x=y_r_test.index, y=y_r_test, name="Echte Return", line=dict(color="#6A994E")))
            fig_r.add_trace(go.Scatter(x=y_r_test.index, y=r_preds, name="AI Return Voorspelling", line=dict(color="#F9C74F")))
            fig_r.update_layout(template="plotly_dark", height=450, title="Dagelijkse Rendementen (Focus op volatiliteit)")
            st.plotly_chart(fig_r, use_container_width=True)

        st.info(f"Huidige Brent Crude prijs gebruikt in model: **${data['Oil_Close'].iloc[-1]:.2f}**")


# ═══════════════════════════════════════════════════════════════════════════════
# ── 5. INTRINSIEKE WAARDE TABEL (DCF-model) ───────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

st.divider()
st.title("📊 Intrinsieke Waarde Analyse")
st.caption(
    "Kolom 6–8: DCF-waardering (normaal / best / worst). "
    "Kolom 9: gewogen gemiddelde (elk 33%). "
    "Pay-out ratio = meest recente waarde van yfinance."
)

# ── Parameters sidebar ────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.header("DCF Parameters")

discount_rate = st.sidebar.number_input("Discontovoet (%)", value=10.0, step=0.5) / 100

# Scenario 1 – Normaal
st.sidebar.subheader("Scenario 1 – Normaal")
g1_y1_5  = st.sidebar.number_input("Groei jaar 1–5 (%)",  value=7.0,  step=0.5, key="g1a") / 100
g1_y6_10 = st.sidebar.number_input("Groei jaar 6–10 (%)", value=5.0,  step=0.5, key="g1b") / 100
mult1    = st.sidebar.number_input("Terminal multiple",    value=15.0, step=1.0, key="m1")

# Scenario 2 – Best
st.sidebar.subheader("Scenario 2 – Best")
g2_y1_5  = st.sidebar.number_input("Groei jaar 1–5 (%)",  value=12.0, step=0.5, key="g2a") / 100
g2_y6_10 = st.sidebar.number_input("Groei jaar 6–10 (%)", value=8.0,  step=0.5, key="g2b") / 100
mult2    = st.sidebar.number_input("Terminal multiple",    value=20.0, step=1.0, key="m2")

# Scenario 3 – Worst
st.sidebar.subheader("Scenario 3 – Worst")
g3_y1_5  = st.sidebar.number_input("Groei jaar 1–5 (%)",  value=2.0,  step=0.5, key="g3a") / 100
g3_y6_10 = st.sidebar.number_input("Groei jaar 6–10 (%)", value=0.0,  step=0.5, key="g3b") / 100
mult3    = st.sidebar.number_input("Terminal multiple",    value=10.0, step=1.0, key="m3")


# ── DCF hulpfunctie ───────────────────────────────────────────────────────────
def dcf_intrinsic_value(eps_base, payout_ratio, g_y1_5, g_y6_10, terminal_mult, disc_rate):
    """
    DCF op basis van EPS * payout_ratio (= dividend).
    Jaar 1–5 groeien met g_y1_5, jaar 6–10 met g_y6_10.
    Terminal value = cashflow jaar 10 * terminal_mult.
    Alles verdisconteert met disc_rate.
    """
    if eps_base is None or np.isnan(eps_base):
        return np.nan

    # Gebruik absolute waarde zodat tijdelijk negatieve EPS geen None geeft
    eps_base = abs(eps_base)
    if eps_base == 0:
        return np.nan

    cf0 = eps_base * payout_ratio if payout_ratio and payout_ratio > 0 else eps_base

    pv_total = 0.0
    cf = cf0
    for yr in range(1, 11):
        g = g_y1_5 if yr <= 5 else g_y6_10
        cf = cf * (1 + g)
        pv_total += cf / (1 + disc_rate) ** yr

    terminal_value = cf * terminal_mult
    pv_total += terminal_value / (1 + disc_rate) ** 10
    return pv_total


# ── FIX: Verbeterde get_fundamentals met retry-logica ────────────────────────
@st.cache_data(ttl=1800)
def get_fundamentals(ticker_symbol):
    """
    Haalt fundamentele data op via yfinance.
    - 3 pogingen met toenemende vertraging
    - Betere fallbacks voor payout_ratio, dividendYield en PE
    - Accepteert ook negatieve EPS (abs() in DCF)
    """
    for attempt in range(3):
        try:
            time.sleep(random.uniform(0.8 + attempt, 1.8 + attempt))
            t    = yf.Ticker(ticker_symbol)
            info = t.info

            # Prijs ophalen met meerdere fallbacks
            price = (
                info.get('currentPrice')
                or info.get('regularMarketPrice')
                or info.get('previousClose')
            )

            # EPS ophalen
            eps = info.get('trailingEps')

            # Als zowel prijs als EPS None zijn: data is leeg, opnieuw proberen
            if price is None and eps is None:
                if attempt < 2:
                    time.sleep(3)
                    continue
                else:
                    return None

            # P/E – bereken zelf als niet beschikbaar
            pe = info.get('trailingPE')
            if pe is None and eps and eps != 0 and price:
                pe = price / eps

            # Dividendrendement
            div_yield_raw = info.get('dividendYield') or 0
            if div_yield_raw == 0:
                div_rate = info.get('dividendRate') or info.get('lastDividendValue') or 0
                if div_rate and price and price > 0:
                    div_yield_raw = div_rate / price
            # yfinance geeft soms decimaal (0.035), soms al % (3.5)
            div_yield_pct = div_yield_raw if div_yield_raw > 0.5 else div_yield_raw * 100

            # Pay-out ratio met meerdere fallbacks
            payout_ratio = info.get('payoutRatio') or 0
            if payout_ratio == 0 and eps and eps != 0:
                div_rate = info.get('dividendRate') or info.get('lastDividendValue') or 0
                if div_rate:
                    payout_ratio = abs(div_rate / eps)  # abs() bij negatieve EPS
            # Fallback: als nog steeds 0, gebruik 50% als conservatieve schatting
            if payout_ratio == 0 or payout_ratio is None:
                payout_ratio = 0.5

            # Cap payout ratio op 1.5 (150%) om extreme waarden te vermijden
            payout_ratio = min(payout_ratio, 1.5)

            return {
                'price':        price,
                'pe':           pe,
                'div_yield':    div_yield_pct,
                'payout_ratio': payout_ratio,
                'eps':          eps,
            }

        except Exception as e:
            if attempt < 2:
                time.sleep(3)
                continue
            return None

    return None


# ── Data ophalen voor alle tickers ────────────────────────────────────────────
rows = []

progress = st.progress(0, text="Fundamentele data ophalen…")
for i, (ticker, name) in enumerate(TICKERS.items()):
    progress.progress((i + 1) / len(TICKERS), text=f"Laden: {ticker}")

    fund = get_fundamentals(ticker)
    if fund is None:
        rows.append({
            'Ticker': ticker, 'Naam': name,
            'K/W': None, 'Div. Rendement (%)': None,
            'Business Return (%)': None,
            'Waardering Normaal ($)': None,
            'Waardering Best ($)': None,
            'Waardering Worst ($)': None,
            'Gewogen Gem. ($)': None,
            'Huidige Koers ($)': None,
        })
        continue

    pe        = fund['pe']
    div_yield = fund['div_yield']
    payout    = fund['payout_ratio']
    eps       = fund['eps']

    # Business return = earnings yield + dividend yield
    business_return = (100 / pe + div_yield) if pe and pe > 0 else None

    # DCF scenario's
    val_norm  = dcf_intrinsic_value(eps, payout, g1_y1_5, g1_y6_10, mult1, discount_rate)
    val_best  = dcf_intrinsic_value(eps, payout, g2_y1_5, g2_y6_10, mult2, discount_rate)
    val_worst = dcf_intrinsic_value(eps, payout, g3_y1_5, g3_y6_10, mult3, discount_rate)

    # Gewogen gemiddelde (elk 1/3)
    vals = [v for v in [val_norm, val_best, val_worst] if v is not None and not np.isnan(v)]
    weighted_avg = np.mean(vals) if vals else None

    rows.append({
        'Ticker':                 ticker,
        'Naam':                   name,
        'K/W':                    round(pe, 1) if pe else None,
        'Div. Rendement (%)':     round(div_yield, 2),
        'Business Return (%)':    round(business_return, 2) if business_return else None,
        'Waardering Normaal ($)': round(val_norm,  2) if val_norm  and not np.isnan(val_norm)  else None,
        'Waardering Best ($)':    round(val_best,  2) if val_best  and not np.isnan(val_best)  else None,
        'Waardering Worst ($)':   round(val_worst, 2) if val_worst and not np.isnan(val_worst) else None,
        'Gewogen Gem. ($)':       round(weighted_avg, 2) if weighted_avg else None,
        'Huidige Koers ($)':      round(fund['price'], 2) if fund['price'] else None,
    })

progress.empty()

df_result = pd.DataFrame(rows)


# ── Styling: kleur op basis van upside/downside t.o.v. huidige prijs ─────────
def color_value(val, price):
    if val is None or price is None:
        return ''
    if val > price * 1.10:
        return 'background-color: #d4edda; color: #155724'   # groen = ondergewaardeerd
    elif val < price * 0.90:
        return 'background-color: #f8d7da; color: #721c24'   # rood = overgewaardeerd
    return ''


def style_row(row):
    price = row['Huidige Koers ($)']
    styles = [''] * len(row)
    val_cols = ['Waardering Normaal ($)', 'Waardering Best ($)', 'Waardering Worst ($)', 'Gewogen Gem. ($)']
    for col in val_cols:
        if col in row.index:
            idx = row.index.get_loc(col)
            styles[idx] = color_value(row[col], price)
    return styles


# ── Debug expander: toon ruwe yfinance data ───────────────────────────────────
with st.expander("🔍 Debug – ruwe yfinance data per ticker"):
    debug_rows = []
    for tkr in TICKERS:
        try:
            raw = yf.Ticker(tkr).info
            debug_rows.append({
                'Ticker':        tkr,
                'currentPrice':  raw.get('currentPrice'),
                'trailingPE':    raw.get('trailingPE'),
                'trailingEps':   raw.get('trailingEps'),
                'dividendYield': raw.get('dividendYield'),
                'dividendRate':  raw.get('dividendRate'),
                'payoutRatio':   raw.get('payoutRatio'),
                'Keys (#)':      len(raw),
            })
        except Exception as ex:
            debug_rows.append({'Ticker': tkr, 'Fout': str(ex)})
    st.dataframe(pd.DataFrame(debug_rows), use_container_width=True)

st.subheader("Overzichtstabel – Intrinsieke Waarde (DCF)")

styled = (
    df_result.style
    .apply(style_row, axis=1)
    .format({
        'K/W':                    '{:.1f}',
        'Div. Rendement (%)':     '{:.2f}%',
        'Business Return (%)':    '{:.2f}%',
        'Waardering Normaal ($)': '${:.2f}',
        'Waardering Best ($)':    '${:.2f}',
        'Waardering Worst ($)':   '${:.2f}',
        'Gewogen Gem. ($)':       '${:.2f}',
        'Huidige Koers ($)':      '${:.2f}',
    }, na_rep='n.b.')
)

st.dataframe(styled, use_container_width=True, height=380)

# ── Legenda ───────────────────────────────────────────────────────────────────
st.caption(
    "🟢 Groen = intrinsieke waarde >10% boven huidige koers (mogelijk ondergewaardeerd)  |  "
    "🔴 Rood = intrinsieke waarde >10% onder huidige koers (mogelijk overgewaardeerd)  |  "
    "Pay-out ratio = meest recente waarde van yfinance (fallback: 50%)  |  "
    "DCF op basis van Trailing EPS × Pay-out ratio als startcashflow"
)

# ── Detail per aandeel ────────────────────────────────────────────────────────
st.subheader("🔍 Detail – Cashflow per scenario")
detail_ticker = st.selectbox(
    "Selecteer aandeel voor detail:", list(TICKERS.keys()),
    format_func=lambda x: f"{x} ({TICKERS[x]})", key="detail"
)

fund_detail = get_fundamentals(detail_ticker)
if fund_detail and fund_detail['eps']:
    eps_d    = fund_detail['eps']
    payout_d = fund_detail['payout_ratio']
    cf0_d    = abs(eps_d) * payout_d if payout_d and payout_d > 0 else abs(eps_d)
    years    = list(range(1, 11))

    scenarios = {
        'Normaal': (g1_y1_5, g1_y6_10, mult1),
        'Best':    (g2_y1_5, g2_y6_10, mult2),
        'Worst':   (g3_y1_5, g3_y6_10, mult3),
    }

    fig_cf = go.Figure()
    colors = {'Normaal': '#2E86AB', 'Best': '#6A994E', 'Worst': '#E84855'}

    for sc_name, (gy15, gy610, _) in scenarios.items():
        cfs = []
        cf = cf0_d
        for yr in years:
            g = gy15 if yr <= 5 else gy610
            cf = cf * (1 + g)
            cfs.append(round(cf, 2))
        fig_cf.add_trace(go.Bar(name=sc_name, x=years, y=cfs, marker_color=colors[sc_name]))

    fig_cf.update_layout(
        barmode='group', template='plotly_dark', height=350,
        title=f"Geschatte cashflow per jaar – {detail_ticker} ({TICKERS[detail_ticker]})",
        xaxis_title="Jaar", yaxis_title="Cashflow ($)"
    )
    st.plotly_chart(fig_cf, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("EPS (trailing)", f"${eps_d:.2f}")
    col2.metric("Pay-out ratio",  f"{payout_d * 100:.1f}%" if payout_d else "n.b.")
    col3.metric("Start cashflow", f"${cf0_d:.2f}")
else:
    st.info("Geen EPS-data beschikbaar voor dit aandeel.")
