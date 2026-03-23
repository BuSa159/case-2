import streamlit as st
import matplotlib.pyplot as plt
import yfinance as yf

st.title("Page 1")
st.write("Content for page 1 goes here.")


tickers = ['XOM', 'CVX', 'SHEL', 'TTE']
data = yf.download(tickers, period="1y", group_by='ticker', auto_adjust=True)

fig, ax = plt.subplots(2, 2, figsize=(12, 8))

for i, ticker in enumerate(tickers):
    row, col = i // 2, i % 2
    volume = data[ticker]['Volume']
    ax[row, col].plot(volume.index, volume)
    ax[row, col].set_title(f'Volume over tijd voor {ticker}')
    ax[row, col].set_xlabel('Tijd')
    ax[row, col].set_ylabel('Volume')

plt.tight_layout()
st.pyplot(fig)
