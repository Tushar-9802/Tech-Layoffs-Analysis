# pages/Company_Profiles.py  (or whatever your file is named for the per-company deep dive)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Company Profiles", layout="wide")
st.title("🏢 Company Layoff Profiles")

@st.cache_data
def load_data():
    df = pd.read_csv("data/Cleaned_layoffs.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["quarter"] = df["date"].dt.to_period("Q").astype(str)
    df["year"] = df["date"].dt.year
    return df

df_full = load_data()

# ---------------- Sidebar (match Trends behavior) ----------------
with st.sidebar:
    st.header("Filters")

    # Year(s) selection
    years_avail = sorted(df_full["year"].dropna().unique().tolist())
    selected_years = st.multiselect(
        "Select Year(s)",
        options=years_avail,
        default=None
    )

    # Apply year filter first
    df_base = df_full.copy()
    if selected_years:
        df_base = df_base[df_base["year"].isin(selected_years)]

    # Industry selection
    industries = sorted(df_base["industry"].dropna().unique())
    selected_industry = st.selectbox("Select Industry", industries)

    # Apply industry filter
    df_base = df_base[df_base["industry"] == selected_industry]

    # Company selection (filtered by both)
    companies = sorted(df_base["company"].dropna().unique())
    company_options = ["All Companies"] + companies
    selected_company = st.selectbox("Select a Company", company_options, index=0)

    smooth_toggle = st.checkbox("Smooth timelines (2-quarter rolling mean)", value=True)

# Build the slice for THIS company or all companies
if selected_company == "All Companies":
    df_company_all = df_full[df_full["industry"] == selected_industry].copy()
    if selected_years:
        df_company_all = df_company_all[df_company_all["year"].isin(selected_years)]
    df_company = df_company_all.copy()
else:
    df_company_all = df_full[df_full["company"] == selected_company].copy()
    df_company = df_company_all.copy()
    if selected_years:
        df_company = df_company[df_company["year"].isin(selected_years)]

years_label = "All years" if not selected_years else ", ".join(map(str, selected_years))
scope_label = f"**{selected_company}**" if selected_company != "All Companies" else "**All Companies**"
st.caption(f"Scope: {scope_label} — Years: **{years_label}**")

# Guard
if df_company.empty:
    st.info("No layoff records for this selection in the selected years.")
    st.stop()

st.markdown("---")

# ---------------- KPI Header ----------------
total_laid_off = int(df_company["total_laid_off"].sum())
rounds = int(df_company["date"].nunique())
peak_q = (
    df_company.groupby("quarter")["total_laid_off"]
    .sum().reset_index()
    .sort_values("total_laid_off", ascending=False).head(1)
)
peak_q_label = peak_q["quarter"].iloc[0] if not peak_q.empty else "—"
peak_q_val = int(peak_q["total_laid_off"].iloc[0]) if not peak_q.empty else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Layoffs (scope)", f"{total_laid_off:,}")
k2.metric("Layoff Rounds", f"{rounds:,}")
k3.metric("Peak Quarter", f"{peak_q_label}", delta=f"{peak_q_val:,} laid off" if peak_q_val else None)
k4.metric("Unique Locations", f"{df_company['location'].nunique():,}")

st.markdown("---")

#1> Quarterly Layoff Timeline ----------------
st.subheader(f"1. Layoff Timeline — {selected_company}")
ts = (
    df_company.groupby("quarter")["total_laid_off"]
    .sum().reset_index().sort_values("quarter")
)
if smooth_toggle:
    ts["y"] = ts["total_laid_off"].rolling(2, min_periods=1).mean()
    ylab = "Total Laid Off (Smoothed)"
else:
    ts["y"] = ts["total_laid_off"]
    ylab = "Total Laid Off"

fig_ts = px.line(ts, x="quarter", y="y", markers=True)
fig_ts.update_layout(
    xaxis_title="Quarter",
    yaxis_title=ylab,
    template="plotly_white"
)
st.plotly_chart(fig_ts, use_container_width=True)

#2> Cumulative Layoffs (selected years) ----------------
st.subheader("2. Cumulative Layoffs (Selected Years)")
ts_cum = ts.copy()
ts_cum["cumulative"] = ts_cum["total_laid_off"].cumsum()
fig_cum = px.area(ts_cum, x="quarter", y="cumulative")
fig_cum.update_layout(
    xaxis_title="Quarter",
    yaxis_title="Cumulative Laid Off",
    template="plotly_white"
)
st.plotly_chart(fig_cum, use_container_width=True)

#3> % Laid Off per Event (distribution) ----------------
st.subheader("3. Percentage Laid Off per Event")
if "percentage_laid_off" in df_company.columns and df_company["percentage_laid_off"].notna().any():
    fig_pct = px.box(df_company, y="percentage_laid_off", points="all")
    fig_pct.update_layout(
        yaxis_title="Percentage of Workforce Laid Off",
        template="plotly_white"
    )
    st.plotly_chart(fig_pct, use_container_width=True)
else:
    st.info("No percentage data available for this company in the selected years.")

#4> Layoff Rounds per Year ----------------
st.subheader("4. Layoff Rounds per Year")
rounds_year = (
    df_company.dropna(subset=["date"])
    .groupby("year")["date"].nunique()
    .reset_index(name="layoff_rounds")
    .sort_values("year")
)
fig_rounds = px.bar(rounds_year, x="year", y="layoff_rounds")
fig_rounds.update_layout(
    xaxis_title="Year",
    yaxis_title="Layoff Rounds",
    template="plotly_white"
)
st.plotly_chart(fig_rounds, use_container_width=True)

#5> Top Locations ----------------
st.subheader("5. Top Locations by Total Layoffs")
if "location" in df_company.columns and df_company["location"].notna().any():
    top_loc = (
        df_company.groupby("location")["total_laid_off"]
        .sum().sort_values(ascending=False).head(10).reset_index()
    )
    fig_loc = px.bar(top_loc, x="total_laid_off", y="location", orientation="h")
    fig_loc.update_layout(
        xaxis_title="Total Laid Off",
        yaxis_title="Location",
        template="plotly_white"
    )
    st.plotly_chart(fig_loc, use_container_width=True)
else:
    st.info("No location data available for this company in the selected years.")

st.markdown("---")

# ---------------- Events Table + CSV Download ----------------
st.subheader("6. Layoff Events (Filtered)")
display_cols = [
    "date", "quarter", "location", "country", "industry", "stage",
    "company_size_category", "total_laid_off", "percentage_laid_off"
]
table_df = df_company[display_cols].sort_values("date")
st.dataframe(table_df, use_container_width=True)

def df_to_csv_bytes(d: pd.DataFrame) -> bytes:
    return d.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇️ Download events (CSV)",
    data=df_to_csv_bytes(table_df),
    file_name=f"{selected_company}_events_{years_label.replace(', ', '-')}.csv",
    mime="text/csv",
    key="download_company_events_csv"
)
