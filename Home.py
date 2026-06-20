import streamlit as st
from src.db import init_db

# We need a small hack to only run Home content when we're actually on the Home page,
# because when using st.navigation, this file becomes the router and runs for every page.
if "page" not in st.session_state:
    st.session_state.page = "Home"

pages = {
    "Navigation": [
        st.Page("pages/0_Home_Content.py", title="Home", icon="🏠", default=True),
        st.Page("pages/1_Trade.py", title="Trade", icon="📝"),
        st.Page("pages/2_Journal.py", title="Journal", icon="📓"),
        st.Page("pages/3_Dashboard.py", title="Dashboard", icon="📊"),
    ],
    "Hidden": [
        st.Page("pages/4_Close Trade.py", title="Close Trade", icon="✖")
    ]
}

pg = st.navigation(pages)
pg.run()

