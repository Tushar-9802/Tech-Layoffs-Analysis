import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from io import BytesIO  # NEW: for downloads

st.set_page_config(page_title="Company Explorer", layout="wide")
st.title("Company Landscape Explorer")

@st.cache_data
def load_data():
    df = pd.read_csv("data/Cleaned_layoffs.csv")
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['quarter'] = df['date'].dt.to_period('Q').astype(str)  # stored as str "2023Q1"
    df['year'] = df['date'].dt.year                           # <-- add year
    return df

df = load_data()

# ---------- Sidebar Filters ----------
st.sidebar.header("Filters")

# Multi-year selection (safe and defaults to all years)
years_avail = sorted(df['year'].dropna().unique().tolist())
selected_years = st.sidebar.multiselect(
    "Select Year(s)",
    options=years_avail,
    default=years_avail
)

# Apply year filter
if selected_years:
    df = df[df['year'].isin(selected_years)]

industries = sorted(df['industry'].dropna().unique())
if not industries:
    st.warning("No industries found in data.")
    st.stop()

selected_industry = st.sidebar.selectbox("Select Industry", industries)
df_industry = df[df['industry'] == selected_industry].copy()

companies_in_industry = sorted(df_industry['company'].dropna().unique())
if not companies_in_industry:
    st.warning(f"No companies found for industry: {selected_industry}")
    st.stop()

highlight_company = st.sidebar.selectbox("Compare Against", companies_in_industry)

# Optional smoothing toggle for trend chart
smooth_toggle = st.sidebar.checkbox("Smooth trend (2-quarter rolling mean)", value=True)

years_label = ", ".join(map(str, selected_years)) if selected_years else "All"
st.markdown(f"### Industry: **{selected_industry}**  |  Years: **{years_label}**  |  Focus: **{highlight_company}**")
st.markdown("---")

# ---------- NEW: KPI Header (Context) ----------
try:
    industry_total = int(df_industry['total_laid_off'].sum())
    companies_affected = int(df_industry['company'].nunique())

    comp_total = int(df_industry.loc[df_industry['company'] == highlight_company, 'total_laid_off'].sum())
    share_pct = (comp_total / industry_total * 100.0) if industry_total > 0 else np.nan

    ranks = (
        df_industry.groupby('company')['total_laid_off']
        .sum().sort_values(ascending=False)
    )
    rank_pos = (ranks.index.get_loc(highlight_company) + 1) if highlight_company in ranks.index else None

    comp_q = (
        df_industry[df_industry['company'] == highlight_company]
        .groupby('quarter')['total_laid_off'].sum().reset_index()
    )
    peak_row = comp_q.loc[comp_q['total_laid_off'].idxmax()] if not comp_q.empty else None
    peak_q_label = str(peak_row['quarter']) if peak_row is not None else "—"
    peak_q_val = int(peak_row['total_laid_off']) if peak_row is not None else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Industry Layoffs (scope)", f"{industry_total:,}")
    k2.metric("Companies Affected", f"{companies_affected:,}")
    k3.metric("Focus Rank / Share", f"{(rank_pos if rank_pos else '—')} / {share_pct:.1f}%" if not np.isnan(share_pct) else "—")
    k4.metric("Focus Peak Quarter", f"{peak_q_label}", delta=f"{peak_q_val:,} laid off" if peak_q_val else None)
except Exception:
    # Soft-fail if any edge case occurs
    pass

st.markdown("---")

# ---------- 1) Top Companies by Total Layoffs ----------
top_companies_raw = (
    df_industry.groupby('company')['total_laid_off']
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

# Ensure the highlight company is included even if not in the top 10 (or has 0)
top_companies = top_companies_raw.copy()
if highlight_company not in top_companies.index:
    highlight_val = df_industry.loc[df_industry['company'] == highlight_company, 'total_laid_off'].sum()
    top_companies.loc[highlight_company] = highlight_val

top_companies = top_companies.sort_values(ascending=False).reset_index()

st.subheader("1. Top Companies by Total Layoffs")
fig_top = px.bar(
    top_companies,
    x='total_laid_off',
    y='company',
    orientation='h',
    color=top_companies['company'].apply(lambda x: "Selected" if x == highlight_company else "Other"),
    color_discrete_map={"Selected": "#EF553B", "Other": "#636EFA"}
)
fig_top.update_layout(
    xaxis_title="Total Laid Off",
    yaxis_title="Company",
    template="plotly_white",
    showlegend=False
)
st.plotly_chart(fig_top, use_container_width=True)

st.markdown("---")

# ---------- 2) Layoff Share Within Industry (Donut) ----------
st.subheader("2. Layoff Share Within Industry")
industry_share = df_industry.groupby('company')['total_laid_off'].sum().reset_index()

# Ensure zero-layoff companies appear in pie (gives them 0 weight)
missing_zero = set(companies_in_industry) - set(industry_share['company'])
if missing_zero:
    industry_share = pd.concat([
        industry_share,
        pd.DataFrame({"company": list(missing_zero), "total_laid_off": 0})
    ], ignore_index=True)

fig_pie = px.pie(
    industry_share,
    names='company',
    values='total_laid_off',
    hole=0.7
)
fig_pie.update_traces(
    textinfo='none',  # no long labels on slices
    pull=[0.05 if c == highlight_company else 0 for c in industry_share['company']],
    hovertemplate='%{label}: %{percent:.1%}<extra></extra>',  # % on hover
    marker=dict(line=dict(color='rgba(0,0,0,0)', width=0))  # no white leader lines
)
fig_pie.update_layout(
    template="plotly_white",
    height=720,  # bigger donut
    legend_title_text='Company',
    showlegend=True,
    margin=dict(t=20, b=20, l=80, r=80)
)
st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

#3> Layoffs by Stage (NEW) ----------
st.subheader("3. Layoffs by Funding Stage (Industry Scope)")
stage_counts = (
    df_industry.assign(stage=df_industry['stage'].fillna("Unknown"))
    .groupby('stage')['total_laid_off'].sum()
    .sort_values(ascending=False).reset_index()
)
fig_stage = px.bar(stage_counts, x='total_laid_off', y='stage', orientation='h', title="")
fig_stage.update_layout(
    xaxis_title="Total Laid Off",
    yaxis_title="Stage",
    template="plotly_white"
)
st.plotly_chart(fig_stage, use_container_width=True)

st.markdown("---")

#4> Quarterly Layoffs: Highlight vs Top 4 ----------
st.subheader("4. Quarterly Layoffs: Highlight vs Top 4")

top_4 = (
    df_industry.groupby('company')['total_laid_off']
    .sum().sort_values(ascending=False)
    .head(4).index.tolist()
)
compare_companies = sorted(set(top_4 + [highlight_company]))

df_compare = df_industry[df_industry['company'].isin(compare_companies)].copy()

# Build a complete grid of quarters × companies using PeriodIndex (robust to str quarters)
if df_compare.empty:
    st.info("No quarterly data available for this selection.")
else:
    # Convert to PeriodIndex to compute a full range
    quarters_pi = pd.PeriodIndex(df_compare['quarter'], freq='Q')
    q_min, q_max = quarters_pi.min(), quarters_pi.max()
    # In rare cases with a single quarter, guard for None
    if pd.isna(q_min) or pd.isna(q_max):
        all_quarters = sorted(df_compare['quarter'].unique())
    else:
        all_quarters = pd.period_range(q_min, q_max, freq='Q').astype(str).tolist()

    full_index = pd.MultiIndex.from_product([all_quarters, compare_companies], names=['quarter', 'company'])

    trend = (
        df_compare.groupby(['quarter', 'company'])['total_laid_off']
        .sum().reindex(full_index, fill_value=0).reset_index()
    )

    # Optional smoothing
    if smooth_toggle:
        trend['y_value'] = (
            trend.groupby('company')['total_laid_off']
            .transform(lambda x: x.rolling(window=2, min_periods=1).mean())
        )
        y_label = "Total Laid Off (Smoothed)"
    else:
        trend['y_value'] = trend['total_laid_off']
        y_label = "Total Laid Off"

    fig_line = px.line(
        trend,
        x='quarter',
        y='y_value',
        color='company',
        markers=True
    )
    fig_line.update_layout(
        xaxis_title="Quarter",
        yaxis_title=y_label,
        template="plotly_white"
    )
    st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")

#5> Highlight vs Industry Average per Active Company (NEW) ----------
st.subheader("5. Focus vs Industry Avg per Active Company")

# Per-quarter totals for industry
ind_q = df_industry.groupby('quarter')['total_laid_off'].sum().reset_index()
# Active companies per quarter (industry)
ind_active = df_industry.groupby('quarter')['company'].nunique().reset_index(name='active_companies')
ind_join = ind_q.merge(ind_active, on='quarter', how='left')
ind_join['industry_avg'] = ind_join['total_laid_off'] / ind_join['active_companies'].replace(0, np.nan)

# Per-quarter totals for the focus company
comp_q = (
    df_industry[df_industry['company'] == highlight_company]
    .groupby('quarter')['total_laid_off'].sum().reset_index()
    .rename(columns={'total_laid_off': 'company_total'})
)

# Build full quarter range union of both series
q_all = pd.PeriodIndex(pd.Index(ind_join['quarter']).astype(str), freq='Q')
if not comp_q.empty:
    q_all = q_all.union(pd.PeriodIndex(pd.Index(comp_q['quarter']).astype(str), freq='Q'))
q_min, q_max = (q_all.min(), q_all.max()) if len(q_all) else (None, None)
if q_min is None or q_max is None:
    comp_vs_avg = ind_join.merge(comp_q, on='quarter', how='left')
else:
    full_quarters = pd.period_range(q_min, q_max, freq='Q').astype(str)
    comp_vs_avg = pd.DataFrame({'quarter': full_quarters}).merge(ind_join, on='quarter', how='left').merge(comp_q, on='quarter', how='left')

comp_vs_avg['company_total'] = comp_vs_avg['company_total'].fillna(0)

# Optional smoothing using the same toggle
if smooth_toggle:
    comp_vs_avg['industry_avg_s'] = comp_vs_avg['industry_avg'].rolling(2, min_periods=1).mean()
    comp_vs_avg['company_total_s'] = comp_vs_avg['company_total'].rolling(2, min_periods=1).mean()
    y_cols = ['company_total_s', 'industry_avg_s']
    y_names = {'company_total_s': highlight_company, 'industry_avg_s': 'Industry Avg / Active Co'}
else:
    y_cols = ['company_total', 'industry_avg']
    y_names = {'company_total': highlight_company, 'industry_avg': 'Industry Avg / Active Co'}

plot_df = comp_vs_avg[['quarter'] + y_cols].melt(id_vars='quarter', value_vars=y_cols, var_name='series', value_name='value')
plot_df['series'] = plot_df['series'].map(y_names)

fig_cmp = px.line(plot_df, x='quarter', y='value', color='series', markers=True)
fig_cmp.update_layout(
    xaxis_title="Quarter",
    yaxis_title="Layoffs",
    template="plotly_white",
    legend_title_text=""
)
st.plotly_chart(fig_cmp, use_container_width=True)

st.markdown("---")

#6> Layoff Events Table for Focus Company ----------
st.subheader(f"6. Layoff Events for {highlight_company}")
selected_df = df_industry[df_industry['company'] == highlight_company].copy()
display_cols = ['date', 'location', 'total_laid_off', 'percentage_laid_off']
if selected_df.empty:
    st.info("No layoff events found for the selected company in this industry.")
else:
    st.dataframe(selected_df[display_cols].sort_values('date'), use_container_width=True)

st.markdown("---")

