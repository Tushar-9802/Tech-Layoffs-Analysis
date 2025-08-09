# pages/customs.py — Custom Derived Metrics (Plotly version, notebook formulas preserved)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Custom Metrics", layout="wide")
st.title("🧮 Custom Derived Metrics")

# --- Larger descriptions under each heading ---
st.markdown(
    """
    <style>
      .desc { font-size: 0.98rem; color: #5a5a5a; line-height: 1.35rem; margin-top: -0.3rem; margin-bottom: 0.65rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def load_data():
    df = pd.read_csv("data/Cleaned_layoffs.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["quarter"] = df["date"].dt.to_period("Q").astype(str)
    df["year"] = df["date"].dt.year
    return df

df_full = load_data()

# ---------------- Sidebar (align with Trends/Company) ----------------
with st.sidebar:
    st.header("Filters")

    # Years (default=None => acts as "All years" until user picks)
    years_all = sorted(df_full["year"].dropna().unique().tolist())
    sel_years = st.multiselect("Select Year(s)", options=years_all, default=None)

    # Base slice by years
    base = df_full.copy()
    if sel_years:
        base = base[base["year"].isin(sel_years)]

    # Optional Industry filter
    industries_all = sorted(base["industry"].dropna().unique().tolist())
    sel_industries = st.multiselect("Industry", options=industries_all, default=None)
    if sel_industries:
        base = base[base["industry"].isin(sel_industries)]

    # Optional Country filter
    countries_all = sorted(base["country"].dropna().unique().tolist())
    sel_countries = st.multiselect("Country", options=countries_all, default=None)
    if sel_countries:
        base = base[base["country"].isin(sel_countries)]

    # Company multiselect — default to ALL in current scope
    # Build options after applying Year/Industry/Country filters
    companies_all = sorted(base["company"].dropna().unique().tolist())

# Leave default empty -> visually clean; logically means "all companies"
    selected_companies = st.multiselect(
        "Companies (optional)",
        options=companies_all,
        default=None,                      # <-- empty by default
        help="Leave empty to include all companies in the selected scope."
    )

# After you compute companies_all (new scope)
if "companies_sel" in st.session_state:
    st.session_state.companies_sel = [
        c for c in st.session_state.companies_sel if c in companies_all
    ]

selected_companies = st.multiselect(
    "Companies (optional)",
    options=companies_all,
    default=None,
    key="companies_sel",
    help="Leave empty to include all companies in the selected scope."
)
df = base if not selected_companies else base[base["company"].isin(selected_companies)]


# Scope label
scope_years = "All years" if not sel_years else ", ".join(map(str, sel_years))
scope_inds = "All industries" if not sel_industries else ", ".join(sel_industries)
scope_ctrs = "All countries" if not sel_countries else ", ".join(sel_countries)
st.caption(f"Scope → Years: **{scope_years}** · Industries: **{scope_inds}** · Countries: **{scope_ctrs}**")

# Guard
if df.empty:
    st.info("No data in the current selection. Try broadening your filters.")
    st.stop()

#1> Layoff Efficiency (Notebook formula, Plotly)
st.subheader("1. Layoff Efficiency")
st.markdown(
    """
    <div class="desc">
      <b>What it captures:</b> Layoffs scaled by capital and normalized by the share of staff cut.<br/>
      <b>Notebook formula:</b><br/>
      <code>layoffs_per_million = total_laid_off / (funds_raised_clean / 1,000,000)</code><br/>
      <code>layoff_efficiency_score = layoffs_per_million / percentage_laid_off</code><br/>
      Higher values suggest more layoffs per $ raised per % workforce cut (i.e., less efficient capital‑to‑outcome).
    </div>
    """,
    unsafe_allow_html=True,
)

req_cols_eff = {"total_laid_off", "percentage_laid_off", "funds_raised_clean", "company"}
if not req_cols_eff.issubset(df.columns):
    st.warning("Efficiency inputs missing. Required columns: total_laid_off, percentage_laid_off, funds_raised_clean, company.")
else:
    eff = df[
        df["total_laid_off"].notna()
        & df["percentage_laid_off"].notna()
        & df["funds_raised_clean"].notna()
        & (df["percentage_laid_off"] > 0)
        & (df["funds_raised_clean"] > 0)
    ].copy()

    if eff.empty:
        st.info("No rows available for efficiency metric after filtering.")
    else:
        eff["layoffs_per_million"] = eff["total_laid_off"] / (eff["funds_raised_clean"] / 1_000_000)
        eff["layoff_efficiency_score"] = eff["layoffs_per_million"] / eff["percentage_laid_off"]

        inefficient = (
            eff.groupby("company")
            .agg({
                "total_laid_off": "sum",
                "percentage_laid_off": "mean",
                "funds_raised_clean": "sum",
                "layoffs_per_million": "mean",
                "layoff_efficiency_score": "mean",
            })
            .reset_index()
        )
        top_eff = inefficient.sort_values("layoff_efficiency_score", ascending=False).head(15)

        fig_eff = px.bar(
            top_eff,
            x="layoff_efficiency_score",
            y="company",
            orientation="h",
            title="Top Companies by Layoff Inefficiency Score",
            template="plotly_white",
        )
        fig_eff.update_layout(xaxis_title="Layoff Efficiency Score (Layoffs per $1M ÷ % staff cut)", yaxis_title="Company")
        st.plotly_chart(fig_eff, use_container_width=True)

st.markdown("---")

#2> Layoff Instability (Notebook formula, Plotly)
st.subheader("2. Layoff Instability")
st.markdown(
    """
    <div class="desc">
      <b>What it captures:</b> Volatility of layoff activity over time.<br/>
      <b>Notebook formula:</b> Count of <i>distinct layoff‑active quarters</i> per company.<br/>
      Higher = layoffs occur in more quarters → more unstable.
    </div>
    """,
    unsafe_allow_html=True,
)

inst = df.copy()
inst["quarter"] = pd.to_datetime(inst["date"], errors="coerce").dt.to_period("Q")
instability = (
    inst.dropna(subset=["company", "quarter"])[["company", "quarter"]]
    .drop_duplicates()
    .groupby("company")
    .size()
    .reset_index(name="layoff_instability_score")
    .sort_values("layoff_instability_score", ascending=False)
)

if instability.empty:
    st.info("No rows available for instability metric after filtering.")
else:
    top_inst = instability.head(15)
    fig_inst = px.bar(
        top_inst,
        x="layoff_instability_score",
        y="company",
        orientation="h",
        title="Top 15 Companies by Layoff Instability Score",
        template="plotly_white",
    )
    fig_inst.update_layout(xaxis_title="Layoff‑active quarters", yaxis_title="Company")
    st.plotly_chart(fig_inst, use_container_width=True)

st.markdown("---")

# 3> Layoff Severity (Notebook formula, Plotly)
st.subheader("3. Layoff Severity")
st.markdown(
    """
    <div class="desc">
      <b>What it captures:</b> Intensity of each event, combining % workforce cut and absolute scale.<br/>
      <b>Notebook formula:</b><br/>
      <code>layoff_severity_index = percentage_laid_off × ln(total_laid_off + 1)</code><br/>
      Then averaged across events per company and ranked by mean LSI.
    </div>
    """,
    unsafe_allow_html=True,
)

req_cols_sev = {"percentage_laid_off", "total_laid_off", "company"}
if not req_cols_sev.issubset(df.columns):
    st.warning("Severity inputs missing. Required columns: percentage_laid_off, total_laid_off, company.")
else:
    sev = df[(df["percentage_laid_off"].notnull()) & (df["total_laid_off"].notnull())].copy()
    if sev.empty:
        st.info("No rows available for severity metric after filtering.")
    else:
        sev["layoff_severity_index"] = sev["percentage_laid_off"] * np.log(sev["total_laid_off"] + 1)
        lsi_by_company = (
            sev.groupby("company")["layoff_severity_index"]
            .mean()
            .reset_index()
            .sort_values("layoff_severity_index", ascending=False)
        )
        top_sev = lsi_by_company.head(15)

        fig_sev = px.bar(
            top_sev,
            x="layoff_severity_index",
            y="company",
            orientation="h",
            title="Top 15 Companies by Layoff Severity Index (LSI)",
            template="plotly_white",
        )
        fig_sev.update_layout(xaxis_title="Average LSI", yaxis_title="Company")
        st.plotly_chart(fig_sev, use_container_width=True)
