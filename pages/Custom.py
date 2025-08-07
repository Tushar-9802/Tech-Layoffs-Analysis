import streamlit as st
import pandas as pd
import plotly.express as px
from scripts.metrics import (
    calculate_layoff_efficiency,
    calculate_layoff_instability,
    calculate_layoff_severity,
)

st.set_page_config(page_title="Company Profiles", layout="wide")
st.title("🏢 Company Layoff Profiles")

@st.cache_data

def load_data():
    df = pd.read_csv("data/Cleaned_layoffs.csv")
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['quarter'] = df['date'].dt.to_period('Q').astype(str)
    return df

df = load_data()

# Company Selector
companies = sorted(df['company'].dropna().unique())
selected_company = st.selectbox("Select a Company", companies)
company_df = df[df['company'] == selected_company]

st.subheader(f"📉 Layoff Timeline for {selected_company}")
time_series = (
    company_df.groupby('quarter')['total_laid_off']
    .sum()
    .reset_index()
)
fig_ts = px.line(time_series, x='quarter', y='total_laid_off', markers=True)
fig_ts.update_layout(
    xaxis_title="Quarter",
    yaxis_title="Total Laid Off",
    template="plotly_white"
)
st.plotly_chart(fig_ts, use_container_width=True)

# Scorecards
st.subheader(f"📊 Key Metrics for {selected_company}")
eff_df = calculate_layoff_efficiency(df)
inst_df = calculate_layoff_instability(df)
sev_df = calculate_layoff_severity(df)

col1, col2, col3 = st.columns(3)

with col1:
    eff_score = eff_df[eff_df['company'] == selected_company]['layoff_efficiency_score'].mean()
    st.metric("Layoff Efficiency Score", f"{eff_score:.2f}" if pd.notna(eff_score) else "N/A")

with col2:
    inst_score = inst_df[inst_df['company'] == selected_company]['layoff_instability_score'].sum()
    st.metric("Instability Score", f"{inst_score}" if pd.notna(inst_score) else "N/A")

with col3:
    sev_score = sev_df[sev_df['company'] == selected_company]['layoff_severity_index'].mean()
    st.metric("Severity Index", f"{sev_score:.2f}" if pd.notna(sev_score) else "N/A")

st.markdown("---")

# Repeat Layoffs
st.subheader(f"🔁 Number of Layoff Rounds for {selected_company}")
num_rounds = company_df['date'].nunique()
st.write(f"{selected_company} has had **{num_rounds}** documented layoff rounds.")

# Top 10 Layoff Companies (reference-style, optional)
st.subheader("🏆 Top 10 Companies by Total Layoffs")
top_companies = df.groupby('company')['total_laid_off'].sum().sort_values(ascending=False).head(10).reset_index()
fig_top = px.bar(top_companies, x='total_laid_off', y='company', orientation='h')
fig_top.update_layout(
    xaxis_title="Total Laid Off",
    yaxis_title="Company",
    template="plotly_white"
)
st.plotly_chart(fig_top, use_container_width=True)
