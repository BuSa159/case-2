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



