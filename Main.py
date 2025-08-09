import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Tech Layoffs Dashboard",
    page_icon="📉",
    layout="wide",
)

# Title and description
st.title("📉 Tech Layoffs Dashboard (2020–2025)")
st.markdown("""
Welcome to the **Tech Layoffs Dashboard** — an interactive tool to explore layoffs across the tech sector from 2020 to 2025.

Use the **sidebar** to:
- Navigate between sections
- Filter by country, industry, or company size
- Analyze custom metrics
""")
