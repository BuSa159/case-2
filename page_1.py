import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

st.title("Page 1")
st.write("Content for page 1 goes here.")

tickers = ['XOM', 'CVX', 'SHEL', 'TTE']
data = yf.download(tickers, period="1y", group_by='ticker', auto_adjust=True)

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=[f'Volume over tijd voor {t}' for t in tickers]
)

for i, ticker in enumerate(tickers):
    row, col = i // 2 + 1, i % 2 + 1
    volume = data[ticker]['Volume']

    fig.add_trace(
        go.Scatter(
            x=volume.index,
            y=volume,
            name=ticker,
            mode='lines'
        ),
        row=row, col=col
    )

fig.update_layout(
    height=700,
    title_text="Volume over tijd",
    showlegend=False
)

fig.update_xaxes(title_text="Tijd")
fig.update_yaxes(title_text="Volume")

st.plotly_chart(fig, use_container_width=True)

st.divider

import streamlit as st
import yfinance as yf
import pandas as pd

tickers = ['XOM', 'CVX', 'SHEL', 'TTE']

rows = []

for ticker in tickers:
    stock = yf.Ticker(ticker)
    
    # Dividenden ophalen
    dividends = stock.dividends
    if dividends.empty:
        continue
    
    # Jaarlijks dividenden optellen
    dividends.index = dividends.index.tz_localize(None)
    annual_div = dividends.resample('YE').sum()
    
    # Info ophalen
    info = stock.info
    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
    eps = info.get('trailingEps')
    
    for year, div_amount in annual_div.items():
        year_str = year.year
        
        # Dividend rendement (alleen voor huidig jaar zinvol, anders benadering)
        div_yield = (div_amount / current_price * 100) if current_price else None
        
        # Dividend stijging t.o.v. vorig jaar
        prev_years = [y for y in annual_div.index if y.year == year_str - 1]
        if prev_years:
            prev_div = annual_div[prev_years[0]]
            div_growth = ((div_amount - prev_div) / prev_div * 100) if prev_div else None
        else:
            div_growth = None
        
        # Payout ratio (EPS alleen beschikbaar als huidig getal)
        payout = (div_amount / eps * 100) if eps and eps > 0 else None
        
        rows.append({
            'Ticker': ticker,
            'Jaar': year_str,
            'Dividend ($)': round(div_amount, 2),
            'Div. Rendement (%)': round(div_yield, 2) if div_yield else None,
            'Div. Stijging (%)': round(div_growth, 2) if div_growth else None,
            'Payout Ratio (%)': round(payout, 2) if payout else None,
        })

df = pd.DataFrame(rows)

# Sorteren op ticker en jaar
df = df.sort_values(['Ticker', 'Jaar'], ascending=[True, False]).reset_index(drop=True)

st.title("Dividend Overzicht")
st.dataframe(
    df.style.format({
        'Dividend ($)': '{:.2f}',
        'Div. Rendement (%)': '{:.2f}%',
        'Div. Stijging (%)': '{:.2f}%',
        'Payout Ratio (%)': '{:.2f}%',
    }, na_rep='-'),
    use_container_width=True
)
