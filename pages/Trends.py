import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Layoff Trends", layout="wide")
st.title("📊 Tech Layoff Trends")
def pct_change_safe(curr, prev):
    if prev == 0 or pd.isna(prev):
        return np.nan
    return (curr - prev) / prev * 100.0

def add_outlier_annotations(fig, quarterly_df, top_n=3):
    # Annotate top N quarters by total_laid_off (within current filters)
    q = quarterly_df.sort_values("total_laid_off", ascending=False).head(top_n)
    for _, r in q.iterrows():
        fig.add_scatter(
            x=[r["quarter"]], y=[r["total_laid_off"]],
            mode="markers+text",
            text=[f"⬆ {int(r['total_laid_off']):,}"],
            textposition="top center",
            marker=dict(size=10, color="#EF553B", line=dict(color="black", width=1)),
            showlegend=False
        )
    return fig

@st.cache_data
def load_data():
    df = pd.read_csv("data/Cleaned_layoffs.csv")
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['quarter'] = df['date'].dt.to_period('Q').astype(str)
    df['year'] = df['date'].dt.year
    return df

df_full = load_data()

#Filters
with st.sidebar:
    st.header("Filters")

    years = st.multiselect(
        "Select Year",
        options=sorted(df_full['year'].dropna().unique()),
        default=None
    )

    selected_country = st.multiselect(
        "Select Country",
        options=sorted(df_full['country'].dropna().unique()),
        default=None
    )
    selected_industry = st.multiselect(
        "Select Industry",
        options=sorted(df_full['industry'].dropna().unique()),
        default=None
    )

    normalize_toggle = st.checkbox("Normalize: show average layoffs per active company", value=False)

# Start with full data, apply filters
df = df_full.copy()
if years:
    df = df[df['year'].isin(years)]
if selected_country:
    df = df[df['country'].isin(selected_country)]
if selected_industry:
    df = df[df['industry'].isin(selected_industry)]

#KPI
# Quarter totals (within filter scope)
quarterly_all = (
    df.groupby('quarter')['total_laid_off']
    .sum()
    .reset_index()
    .sort_values('quarter')
)

# Current year vs last year totals (within scope)
yearly = (
    df.groupby('year')['total_laid_off']
    .sum()
    .reset_index()
    .sort_values('year')
)

# compute QoQ
q_curr = quarterly_all['total_laid_off'].iloc[-1] if len(quarterly_all) else np.nan
q_prev = quarterly_all['total_laid_off'].iloc[-2] if len(quarterly_all) > 1 else np.nan
q_qoq = pct_change_safe(q_curr, q_prev)

# compute YoY
if len(yearly) >= 1:
    y_curr = yearly['total_laid_off'].iloc[-1]
else:
    y_curr = np.nan
y_prev = yearly['total_laid_off'].iloc[-2] if len(yearly) > 1 else np.nan
y_yoy = pct_change_safe(y_curr, y_prev)

# other KPIs
num_companies = df['company'].nunique()
num_countries = df['country'].nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Layoffs (scope)", f"{int(df['total_laid_off'].sum()):,}")
k2.metric("QoQ change", f"{q_qoq:+.1f}%" if not pd.isna(q_qoq) else "–")
k3.metric("YoY change", f"{y_yoy:+.1f}%" if not pd.isna(y_yoy) else "–")
k4.metric("Companies / Countries", f"{num_companies:,} / {num_countries:,}")

st.markdown("---")

#1> Total Layoffs Over Time (Quarterly)
quarterly = df.groupby('quarter')['total_laid_off'].sum().reset_index()
quarterly = quarterly.sort_values('quarter')

# Normalized: average per active company per quarter
active_counts = (
    df.groupby(['quarter'])['company']
    .nunique()
    .reset_index(name='active_companies')
    .sort_values('quarter')
)
quarterly_norm = quarterly.merge(active_counts, on='quarter', how='left')
quarterly_norm['avg_laid_off_per_company'] = (
    quarterly_norm['total_laid_off'] / quarterly_norm['active_companies'].replace(0, np.nan)
)

st.subheader("1. Total Layoffs Over Time (Quarterly)")
st.caption(
    "Quarter-by-quarter totals in the current filter scope. "
    "If **Normalize** is enabled, we plot the average per active company: "
    "`avg_laid_off_per_company = total_laid_off / #active_companies_in_quarter`."
)
if not normalize_toggle:
    fig_1 = px.line(quarterly, x='quarter', y='total_laid_off', markers=True, title="")
    fig_1.update_layout(
        xaxis_title="Quarter", yaxis_title="Total Laid Off",
        template="plotly_white",
        xaxis=dict(title_font=dict(color="white"), side="left"),
        yaxis=dict(title_font=dict(color="white"))
    )
    fig_1 = add_outlier_annotations(fig_1, quarterly, top_n=3)
else:
    fig_1 = px.line(
        quarterly_norm,
        x='quarter', y='avg_laid_off_per_company',
        markers=True, title=""
    )
    fig_1.update_layout(
        xaxis_title="Quarter", yaxis_title="Avg Laid Off per Active Company",
        template="plotly_white",
        xaxis=dict(title_font=dict(color="white"), side="left"),
        yaxis=dict(title_font=dict(color="white"))
    )
    # annotate top 3 normalized quarters
    topn = quarterly_norm.nlargest(3, 'avg_laid_off_per_company')
    for _, r in topn.iterrows():
        fig_1.add_scatter(
            x=[r["quarter"]], y=[r["avg_laid_off_per_company"]],
            mode="markers+text",
            text=[f"⬆ {r['avg_laid_off_per_company']:.1f}"],
            textposition="top center",
            marker=dict(size=10, color="#EF553B", line=dict(color="black", width=1)),
            showlegend=False
        )
st.plotly_chart(fig_1, use_container_width=True)
st.markdown("---")

#2> Quarterly Layoffs by Country (Top 10)
df_valid = df[df['industry'].notna()]
top_industries = (
    df_valid.groupby('industry')['total_laid_off']
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)
st.subheader("2. Top 10 Industries by Total Layoffs")
st.caption(
    "Industries with the highest total layoffs in the current scope. "
    "Computed as `sum(total_laid_off)` per industry."
)
fig_2 = px.bar(top_industries, x='total_laid_off', y='industry', orientation='h')
fig_2.update_layout(
    xaxis_title="Employees Laid Off",
    yaxis_title="Quarter",
    template="plotly_white",
    xaxis=dict(title_font=dict(color="white"), side="top"),
    yaxis=dict(title_font=dict(color="white"))
)
st.plotly_chart(fig_2, use_container_width=True)
st.markdown("---")

#3> Top 10 Countries by Total Layoffs
top_countries = (
    df.groupby('country')['total_laid_off']
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)
st.subheader("3. Top 10 Countries by Total Layoffs")
st.caption(
    "Countries with the highest total layoffs in the current scope. "
    "Computed as `sum(total_laid_off)` per country."
)
fig_3 = px.bar(top_countries, x='total_laid_off', y='country', orientation='h')
fig_3.update_layout(
    xaxis_title="Employees Laid Off",
    yaxis_title="Country",
    template="plotly_white",
    xaxis=dict(title_font=dict(color="white"), side="left"),
    yaxis=dict(title_font=dict(color="white"))
)
st.plotly_chart(fig_3, use_container_width=True)
st.markdown("---")

#4> Total Layoffs by Company Size
if 'company_size_category' in df.columns:
    size_order = ['Small (<500)', 'Mid (500–4999)', 'Large (5000+)', 'Unknown']
    size_totals = (
        df.groupby('company_size_category')['total_laid_off']
        .sum()
        .reindex(size_order)
        .reset_index()
    )
    st.subheader("4. Total Layoffs by Company Size")
    st.caption(
        "Total layoffs aggregated by company size category in the current scope. "
        "Computed as `sum(total_laid_off)` per `company_size_category`."
    )
    fig_4 = px.bar(size_totals, x='company_size_category', y='total_laid_off', title="")
    fig_4.update_layout(
        xaxis_title="Company Size",
        yaxis_title="Total Laid Off",
        template="plotly_white",
        xaxis=dict(title_font=dict(color="white"), side="left"),
        yaxis=dict(title_font=dict(color="white"))
    )
    st.plotly_chart(fig_4, use_container_width=True)
st.markdown("---")

#5> Quarterly Layoffs by Company Size
if 'company_size_category' in df.columns:
    show_unknown = st.sidebar.checkbox("Include 'Unknown' in Company Size Trends", value=False)

    filtered_df = df.copy()
    if not show_unknown:
        filtered_df = filtered_df[filtered_df['company_size_category'] != 'Unknown']

    all_quarters = pd.Series(filtered_df['quarter'].unique(), name='quarter')
    all_sizes = pd.Series(filtered_df['company_size_category'].unique(), name='company_size_category')
    full_index = pd.MultiIndex.from_product([all_quarters, all_sizes], names=['quarter', 'company_size_category'])

    grouped = (
        filtered_df.groupby(['quarter', 'company_size_category'])['total_laid_off']
        .sum()
        .reindex(full_index, fill_value=0)
        .reset_index()
    )

    if show_unknown and 'Unknown' in df['company_size_category'].values:
        unknown_df = df[df['company_size_category'] == 'Unknown'].copy()
        unknown_df['quarter_dt'] = pd.PeriodIndex(unknown_df['quarter'], freq='Q').to_timestamp()
        unknown_grouped = unknown_df.groupby('quarter_dt')['total_laid_off'].sum().rolling(2, min_periods=1).mean()
        unknown_grouped = unknown_grouped.reset_index()
        unknown_grouped['quarter'] = unknown_grouped['quarter_dt'].dt.to_period('Q').astype(str)
        unknown_grouped['company_size_category'] = 'Unknown (Smoothed)'
        unknown_grouped = unknown_grouped[['quarter', 'company_size_category', 'total_laid_off']]
        grouped = pd.concat([grouped, unknown_grouped], ignore_index=True)

    grouped['quarter'] = pd.Categorical(
        grouped['quarter'],
        categories=sorted(grouped['quarter'].unique(), reverse=True),
        ordered=True
    )

    st.subheader("5. Quarterly Layoffs by Company Size")
    st.caption(
        "Trend of layoffs per quarter split by company size. "
        "We build a full `quarter × size` grid so lines don’t break, and optionally smooth the **Unknown** series."
    )
    fig_5 = px.line(grouped, x='quarter', y='total_laid_off', color='company_size_category', markers=True, title="")
    fig_5.update_layout(
        xaxis_title="Quarter",
        yaxis_title="Total Laid Off",
        template="plotly_white",
        xaxis=dict(title_font=dict(color="white"), side="left", autorange="reversed"),
        yaxis=dict(title_font=dict(color="white"))
    )
    st.plotly_chart(fig_5, use_container_width=True)
st.markdown("---")

#6> Quarterly Layoffs by Top 6 Industries
all_quarters = df['quarter'].unique()
top_6_industries = (
    df.groupby('industry')['total_laid_off']
    .sum()
    .sort_values(ascending=False)
    .head(6)
    .index
)

full_index = pd.MultiIndex.from_product([all_quarters, top_6_industries], names=['quarter', 'industry'])

industry_time = (
    df[df['industry'].isin(top_6_industries)]
    .groupby(['quarter', 'industry'])['total_laid_off']
    .sum()
    .reindex(full_index, fill_value=0)
    .reset_index()
)

non_zero_industries = industry_time.groupby('industry')['total_laid_off'].sum()
industry_time = industry_time[industry_time['industry'].isin(non_zero_industries[non_zero_industries > 0].index)]

st.subheader("6. Quarterly Layoffs by Top 6 Industries")
st.caption(
    "Quarterly trend lines for the **top 6 industries** by total layoffs in the current scope. "
    "We complete the `quarter × industry` grid and fill missing with 0 to keep lines continuous."
)
fig_6 = px.line(industry_time, x='quarter', y='total_laid_off', color='industry', markers=True, title="")
fig_6.update_layout(
    xaxis_title="Quarter",
    yaxis_title="Total Laid Off",
    template="plotly_white",
    xaxis=dict(title_font=dict(color="white"), side="left", autorange="reversed"),
    yaxis=dict(title_font=dict(color="white"))
)
st.plotly_chart(fig_6, use_container_width=True)
st.markdown("---")

#7> Percentage Laid Off by Company Size Category
st.subheader("7. Layoff Percentage by Company Size Category")
st.caption(
    "Distribution of the **% of workforce laid off** per event, grouped by company size category. "
    "Each point is an event; the box shows median and IQR. Uses `percentage_laid_off` from the dataset."
)
fig_7 = px.box(df, x='company_size_category', y='percentage_laid_off', title="")
fig_7.update_layout(
    xaxis_title="Company Size",
    yaxis_title="Percentage of Workforce Laid Off",
    template="plotly_white",
    xaxis=dict(title_font=dict(color="white")),
    yaxis=dict(title_font=dict(color="white"))
)
fig_7.update_traces(marker=dict(line=dict(color='white', width=2)))
st.plotly_chart(fig_7, use_container_width=True)
st.markdown("---")
