import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

tickers = ["XOM", "SHEL", "CVX", "TTE", "COP", "BP", "ENB", "EQNR"]

# Centrale kleurmap — elke ticker krijgt een vaste kleur
kleurset = ["#2E86AB", "#E84855", "#F9C74F", "#6A994E",
            "#9B5DE5", "#F15BB5", "#00BBF9", "#00F5D4"]
kleur_map = {t: kleurset[i % len(kleurset)] for i, t in enumerate(tickers)}


@st.cache_data
def load_info(ticker):
    info = yf.Ticker(ticker).info
    return {
        "Name": info.get("longName", "—"),
        "MarketCapitalization": info.get("marketCap", 0),
        "Sector": info.get("sector", "—"),
        "SharesOutstanding": info.get("sharesOutstanding", 0),
    }


for t in tickers:
    if f"info_{t}" not in st.session_state:
        st.session_state[f"info_{t}"] = load_info(t)

st.title("Bedrijfsinfo Dashboard")

st.divider()

# Sorteeroptie
sorteer_op = st.selectbox(
    "Sorteer op:",
    options=["Marktkapitalisatie (hoog → laag)", "Marktkapitalisatie (laag → hoog)",
             "Aandelen (hoog → laag)", "Aandelen (laag → hoog)"]
)

# Bouw dataframe van alle tickers
rows = []
for t in tickers:
    info = st.session_state.get(f"info_{t}", {})
    rows.append({
        "ticker": t,
        "Name": info.get("Name", "—"),
        "MarketCapitalization": info.get("MarketCapitalization", 0),
        "Sector": info.get("Sector", "—"),
        "SharesOutstanding": info.get("SharesOutstanding", 0),
    })

df = pd.DataFrame(rows)

# Sorteren
if sorteer_op == "Marktkapitalisatie (hoog → laag)":
    df = df.sort_values("MarketCapitalization", ascending=False)
elif sorteer_op == "Marktkapitalisatie (laag → hoog)":
    df = df.sort_values("MarketCapitalization", ascending=True)
elif sorteer_op == "Aandelen (hoog → laag)":
    df = df.sort_values("SharesOutstanding", ascending=False)
elif sorteer_op == "Aandelen (laag → hoog)":
    df = df.sort_values("SharesOutstanding", ascending=True)

st.divider()

# Toon elke ticker als een rij met metrics
for _, row in df.iterrows():
    st.markdown(f"#### {row['ticker']} — {row['Name']}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Bedrijf", row["Name"])
    m2.metric("Market Cap", f"${row['MarketCapitalization'] / 1e9:.1f}B")
    m3.metric("Sector", row["Sector"])
    m4.metric("Aandelen (M)", f"{row['SharesOutstanding'] / 1e6:.1f}M")
    st.divider()

# --- BUBBLE CHART: Marktkapitalisatie vs Aandelen ---
st.subheader("Marktkapitalisatie vs Aandelen Uitstaand")

geselecteerde_tickers = st.multiselect(
    "Selecteer bedrijven:",
    options=tickers,
    default=tickers
)

df_bubble = df[df["ticker"].isin(geselecteerde_tickers)]

fig = go.Figure()

for _, row in df_bubble.iterrows():
    t = row["ticker"]
    fig.add_trace(go.Scatter(
        x=[row["SharesOutstanding"] / 1e6],           # X-as: aandelen in miljoenen
        y=[row["MarketCapitalization"] / 1e9],         # Y-as: marktcap in miljarden
        mode="markers+text",
        name=t,
        text=[t],
        textposition="top center",
        marker=dict(
            size=row["SharesOutstanding"] / 1e7,       # Grootte op basis van aandelen
            sizemode="area",
            sizeref=2,
            sizemin=10,
            color=kleur_map[t],
            opacity=0.85,
            line=dict(width=1, color="white")
        ),
        hovertemplate=(
            f"<b>{t}</b><br>"
            f"Naam: {row['Name']}<br>"
            f"Marktcap: ${row['MarketCapitalization'] / 1e9:.1f}B<br>"
            f"Aandelen: {row['SharesOutstanding'] / 1e6:.0f}M<br>"
            "<extra></extra>"
        )
    ))

fig.update_layout(
    xaxis_title="Aandelen Uitstaand (miljoen)",
    yaxis_title="Marktkapitalisatie (miljarden USD)",
    showlegend=True,
    legend=dict(title="Ticker"),
    height=550,
    plot_bgcolor="white",
    paper_bgcolor="white",
)

fig.update_xaxes(showgrid=True, gridcolor="#EEEEEE")
fig.update_yaxes(showgrid=True, gridcolor="#EEEEEE")

if not df_bubble.empty:
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Selecteer minimaal één bedrijf.")