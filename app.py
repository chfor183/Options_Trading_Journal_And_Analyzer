import streamlit as st
from src.db import init_db

st.set_page_config(
    page_title="Options Trading Journal",
    page_icon="📈",
    layout="wide",
)

st.title("Options Trading Journal & Analyzer")

st.markdown("""
Welcome to your local trading journal! 

Navigate using the sidebar to:
- **Trade**: Enter new trades and analyze their payoffs.
- **Journal**: View and edit your past trades.
- **Dashboard**: Review your performance metrics.
""")

# Initialize database on startup
try:
    init_db()
    st.success("Database connected and initialized.")
except Exception as e:
    st.error(f"Failed to connect to the database. Ensure PostgreSQL is running. Error: {e}")

