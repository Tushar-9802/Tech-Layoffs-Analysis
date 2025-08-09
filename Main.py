import streamlit as st
import pandas as pd

st.set_page_config(page_title="Tech Layoffs Dashboard", layout="wide")
st.title("📊 Tech Layoffs Analysis Dashboard")

# --- Load Data ---
@st.cache_data
def load_data():
    df = pd.read_csv("data/Cleaned_layoffs.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = df["date"].dt.year
    return df

df = load_data()

# --- KPI Cards ---
total_layoffs = int(df["total_laid_off"].sum())
total_companies = df["company"].nunique()
total_industries = df["industry"].nunique()
total_countries = df["country"].nunique()
years_covered = f"{df['year'].min()} — {df['year'].max()}"

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Layoffs", f"{total_layoffs:,}")
k2.metric("Companies Covered", f"{total_companies:,}")
k3.metric("Industries", f"{total_industries:,}")
k4.metric("Countries", f"{total_countries:,}")
k5.metric("Years Covered", years_covered)

st.markdown("---")

# --- Intro Section ---
st.markdown("""
## Welcome to the Tech Layoffs Dashboard

This dashboard explores **global tech layoffs** using curated public datasets.  
Our goal: uncover **patterns**, provide **company-level insights**, and measure the **impact** of layoffs 
through **custom metrics**.

---
### 📌 About the Dataset
- **Source:** Aggregated public records & verified layoff trackers
- **Timeframe:** 2020 — Present
- **Scope:** Tech sector — hardware, software, fintech, startups, etc.
- **Coverage:** Layoff counts, percentage workforce laid off, industry, country, funding stage, company size

While the dataset captures a broad spectrum of events, some entries may be incomplete.  
Analyses reflect only the available data.

---
## 📂 Dashboard Pages Overview

### 1️⃣ **Trends**
Macro view of layoffs:
- Quarterly totals, YoY & QoQ changes
- Country and industry rankings
- Layoffs by company size
- Outlier events
- Optional normalization per active company

### 2️⃣ **Company**
Industry & company drilldown:
- Top companies in an industry
- Industry share donut chart
- Compare focus company vs top peers
- Event history table

### 3️⃣ **Custom Metrics**
Advanced quantitative analysis:
- **Layoff Efficiency** – % of workforce cut
- **Layoff Instability** – volatility in layoffs over time
- **Layoff Severity** – extremity relative to company history
- Includes formulas & interpretations

---
💡 **How to Use**:
- Use **sidebar filters** to refine scope (year, country, industry, company).
- Hover on charts for tooltips.
- Download tables from the **Company** page for your own analysis.

---
""")

st.markdown("""
---
**Built for data-driven insight into the evolving tech landscape.**
""")
