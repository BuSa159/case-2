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
