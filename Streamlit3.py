import streamlit as st

st.set_page_config(layout="wide", page_title="Stock Dashboard")

dashboard = st.Page("dashboard.py", title="Startpagina",           icon=":material/dashboard:")
page_1    = st.Page("page_1.py",   title="Dividend analyse",       icon=":material/article:")
page_2    = st.Page("page_2.py",   title="Bedrijfsinfo",           icon=":material/article:")
page_3    = st.Page("page_3.py",   title="Aandelen voorspeller",   icon=":material/article:")

pg = st.navigation([dashboard, page_1, page_2, page_3])
pg.run()
