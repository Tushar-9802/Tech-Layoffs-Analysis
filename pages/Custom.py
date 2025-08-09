import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

from scripts.metrics import (
    calculate_layoff_efficiency,
    calculate_layoff_instability,
    calculate_layoff_severity,
)

st.set_page_config(page_title="Custom Metrics", layout="wide")
st.title("🧮 Custom Layoff Metrics")

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

    years_avail = sorted(df_full["year"].dropna().unique().tolist())
    selected_years = st.multiselect(
        "Select Year(s)",
        options=years_avail,
        default=None  # match Trends: nothing selected -> All years
    )

    # Base slice for rest of the page
    base = df_full.copy()
    if selected_years:
        base = base[base["year"].isin(selected_years)]

    # Company selection defaults to top 10 (by total layoffs) in the base slice
    top10 = (
        base.groupby("company")["total_laid_off"]
        .sum().sort_values(ascending=False).head(10).index.tolist()
    )
    all_companies = sorted(base["company"].dropna().unique())
    selected_companies = st.multiselect(
        "Companies",
        options=all_companies,
        default=[c for c in all_companies if c in top10] or all_companies[:10],
    )

st.caption(
    "Metrics are computed from the current scope (years you pick above). "
    "If a metric dataframe includes dates, it is filtered to the selected years."
)

# ---------------- Helpers ----------------
def filter_metric_df_by_year(metric_df: pd.DataFrame) -> pd.DataFrame:
    if metric_df is None or metric_df.empty:
        return metric_df
    metric_df = metric_df.copy()
    if "date" in metric_df.columns and selected_years:
        metric_df["date"] = pd.to_datetime(metric_df["date"], errors="coerce")
        metric_df["year"] = metric_df["date"].dt.year
        metric_df = metric_df[metric_df["year"].isin(selected_years)]
    return metric_df

def restrict_to_companies(metric_df: pd.DataFrame) -> pd.DataFrame:
    if metric_df is None or metric_df.empty:
        return metric_df
    if "company" in metric_df.columns and selected_companies:
        return metric_df[metric_df["company"].isin(selected_companies)].copy()
    return metric_df

# Compute once
eff_df = restrict_to_companies(filter_metric_df_by_year(calculate_layoff_efficiency(df_full)))
inst_df = restrict_to_companies(filter_metric_df_by_year(calculate_layoff_instability(df_full)))
sev_df = restrict_to_companies(filter_metric_df_by_year(calculate_layoff_severity(df_full)))

st.markdown("---")

# ==============================
# 1) Layoff Efficiency
# ==============================
st.subheader("⚙️ Layoff Efficiency")
st.caption(
    "Measures the **fraction of workforce reduced** relative to company size for each layoff event or period. "
    "Higher values mean a larger share of the workforce was laid off.\n\n"
    "**Formula (event‑level):**  \n"
    "`Efficiency Score = total_laid_off / estimated_company_size`  \n"
    "where *estimated_company_size* is taken from size category or headcount fields."
)
if eff_df is None or eff_df.empty:
    st.info("No efficiency data available for the current filters.")
else:
    eff_col = next((c for c in eff_df.columns if "efficiency" in c), None)
    if eff_col is None:
        st.dataframe(eff_df, use_container_width=True)
    else:
        eff_summary = (
            eff_df.groupby("company")[eff_col]
            .mean().reset_index()
            .sort_values(eff_col, ascending=False)
        )
        c1, c2 = st.columns([2, 1])
        with c1:
            fig_eff = px.bar(eff_summary, x=eff_col, y="company", orientation="h",
                             title="Average Efficiency Score (Selected Years)")
            fig_eff.update_layout(template="plotly_white", xaxis_title="Avg Efficiency", yaxis_title="Company")
            st.plotly_chart(fig_eff, use_container_width=True)
        with c2:
            st.dataframe(eff_summary, use_container_width=True)

st.markdown("---")

# ==============================
# 2) Layoff Instability
# ==============================
st.subheader("📉 Layoff Instability")
st.caption(
    "Captures **volatility** in a company’s layoff activity over time. "
    "Higher values indicate irregular, bursty layoffs rather than steady patterns.\n\n"
    "**One formulation (period‑level):**  \n"
    "`Instability Score = (# of layoff‑active quarters) × stdev(layoffs per quarter)`  \n"
    "The implementation from `scripts.metrics.calculate_layoff_instability` is used as the source of truth."
)
if inst_df is None or inst_df.empty:
    st.info("No instability data available for the current filters.")
else:
    inst_col = next((c for c in inst_df.columns if "instability" in c), None)
    if inst_col is None:
        st.dataframe(inst_df, use_container_width=True)
    else:
        inst_summary = (
            inst_df.groupby("company")[inst_col]
            .sum().reset_index()
            .sort_values(inst_col, ascending=False)
        )
        c1, c2 = st.columns([2, 1])
        with c1:
            fig_inst = px.bar(inst_summary, x=inst_col, y="company", orientation="h",
                              title="Instability Score (Selected Years)")
            fig_inst.update_layout(template="plotly_white", xaxis_title="Instability", yaxis_title="Company")
            st.plotly_chart(fig_inst, use_container_width=True)
        with c2:
            st.dataframe(inst_summary, use_container_width=True)

st.markdown("---")

# ==============================
# 3) Layoff Severity
# ==============================
st.subheader("🚨 Layoff Severity")
st.caption(
    "Quantifies the **intensity** of layoffs relative to the company’s own scale or history. "
    "Useful to compare how severe an event is for that specific company.\n\n"
    "**One formulation (event‑normalized):**  \n"
    "`Severity Index = total_laid_off_in_event / max(total_laid_off_in_any_event_for_company)`  \n"
    "Then aggregated (e.g., mean) across events for a company. "
    "We use your `scripts.metrics.calculate_layoff_severity` implementation."
)
if sev_df is None or sev_df.empty:
    st.info("No severity data available for the current filters.")
else:
    sev_col = next((c for c in sev_df.columns if "severity" in c), None)
    if sev_col is None:
        st.dataframe(sev_df, use_container_width=True)
    else:
        sev_summary = (
            sev_df.groupby("company")[sev_col]
            .mean().reset_index()
            .sort_values(sev_col, ascending=False)
        )
        c1, c2 = st.columns([2, 1])
        with c1:
            fig_sev = px.bar(sev_summary, x=sev_col, y="company", orientation="h",
                             title="Average Severity Index (Selected Years)")
            fig_sev.update_layout(template="plotly_white", xaxis_title="Avg Severity", yaxis_title="Company")
            st.plotly_chart(fig_sev, use_container_width=True)
        with c2:
            st.dataframe(sev_summary, use_container_width=True)

st.markdown("---")

# Optional: raw rows for selected companies
st.subheader("🔎 Per‑Company Raw Rows (Optional)")
st.caption("Toggle to inspect raw layoff rows feeding the metrics for your selected companies.")
if selected_companies:
    show_raw = st.checkbox("Show raw rows", value=False)
    if show_raw:
        raw = base[base["company"].isin(selected_companies)].copy()
        cols = ["date", "quarter", "company", "industry", "country", "stage",
                "company_size_category", "total_laid_off", "percentage_laid_off"]
        st.dataframe(raw[cols].sort_values(["company", "date"]), use_container_width=True)
