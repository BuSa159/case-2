import streamlit as st

st.set_page_config(layout="wide", page_title="Stock Dashboard")

dashboard = st.Page("dashboard.py", title="Dashboard", icon=":material/dashboard:")
page_1    = st.Page("page_1.py",   title="Page 1",      icon=":material/article:")
page_2    = st.Page("page_2.py",   title="Page 2",      icon=":material/article:")

pg = st.navigation([dashboard, page_1, page_2])
pg.run()