import streamlit as st
import matplotlib.pyplot as plt

st.title("Page 1")
st.write("Content for page 1 goes here.")

# Probeersel vanuit co pilot  
#  Tweede grafiek voor volume over tijd van verschillende aandelen
fig, ax = plt.subplots(5, 2)
for i, ticker in enumerate(['XOM', 'CVX', 'SHEL', 'TTE']):
    ax[i//2, i%2].plot(df[df['ticker'] == ticker].index, df[df['ticker'] == ticker]['volume'])
    ax[i//2, i%2].set_title(f'Volume over tijd voor {ticker}')
    ax[i//2, i%2].set_xlabel('Tijd')
    ax[i//2, i%2].set_ylabel('Volume')

plt.tight_layout()
plt.show()
