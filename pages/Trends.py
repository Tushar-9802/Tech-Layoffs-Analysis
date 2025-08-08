import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Layoff Trends", layout="wide")
st.title("Tech Layoff Trends")

@st.cache_data
def load_data():
    df = pd.read_csv("data/Cleaned_layoffs.csv")
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['quarter'] = df['date'].dt.to_period('Q').astype(str)
    df['year'] = df['date'].dt.year
    return df

df_full = load_data()

# ---- Sidebar filters ----
with st.sidebar:
    st.header("Filters")

    years = sorted(df_full['year'].dropna().unique().tolist())
    year_choice = st.selectbox("Select Year", options=["All years"] + years, index=0)

    # base df for the rest of the page
    df = df_full.copy() if year_choice == "All years" else df_full[df_full['year'] == year_choice]

    selected_country = st.multiselect(
        "Select Country",
        options=sorted(df['country'].dropna().unique()),
        default=None
    )
    selected_industry = st.multiselect(
        "Select Industry",
        options=sorted(df['industry'].dropna().unique()),
        default=None
    )

# apply country/industry filters
if selected_country:
    df = df[df['country'].isin(selected_country)]
if selected_industry:
    df = df[df['industry'].isin(selected_industry)]

# 1) Quarterly Layoff Trends
quarterly = df.groupby('quarter')['total_laid_off'].sum().reset_index()
quarterly = quarterly.sort_values('quarter')
st.subheader("1. Total Layoffs Over Time (Quarterly)")
fig_1 = px.line(quarterly, x='quarter', y='total_laid_off', markers=True, title="")
fig_1.update_layout(
    xaxis_title="Quarter",
    yaxis_title="Total Laid Off",
    template="plotly_white",
    xaxis=dict(title_font=dict(color="white"), side="left"),
    yaxis=dict(title_font=dict(color="white"))
)
st.plotly_chart(fig_1, use_container_width=True)
st.markdown("---")

# 2) Top Industries by Layoffs (for chosen year/scope)
df_valid = df[df['industry'].notna()]
top_industries = (
    df_valid.groupby('industry')['total_laid_off']
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)
st.subheader("2. Top 10 Industries by Total Layoffs")
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

# 3) Top 10 Countries by Layoffs (for chosen year/scope)
top_countries = (
    df.groupby('country')['total_laid_off']
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)
st.subheader("3. Top 10 Countries by Total Layoffs")
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

# 4) Layoff by Company Size
if 'company_size_category' in df.columns:
    size_order = ['Small (<500)', 'Mid (500–4999)', 'Large (5000+)', 'Unknown']
    size_totals = (
        df.groupby('company_size_category')['total_laid_off']
        .sum()
        .reindex(size_order)
        .reset_index()
    )
    st.subheader("4. Total Layoffs by Company Size")
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

# 5) Quarterly Layoffs by Company Size (with optional Unknown & reversed x)
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

# 6) Quarterly Layoffs by Top 6 Industries (for chosen year/scope)
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

# drop industries that are all-zero after filters (e.g., year/country/industry)
non_zero_industries = industry_time.groupby('industry')['total_laid_off'].sum()
industry_time = industry_time[industry_time['industry'].isin(non_zero_industries[non_zero_industries > 0].index)]

st.subheader("6. Quarterly Layoffs by Top 6 Industries")
fig_6 = px.line(industry_time, x='quarter', y='total_laid_off', color='industry', markers=True, title="")
fig_6.update_layout(
    xaxis_title="Quarter",
    yaxis_title="Total Laid Off",
    template="plotly_white",
    xaxis=dict(title_font=dict(color="white"), side="left"),
    yaxis=dict(title_font=dict(color="white"))
)
st.plotly_chart(fig_6, use_container_width=True)
st.markdown("---")

# 7) Boxplot of % laid-off by Company Size
st.subheader("7. Layoff Percentage by Company Size Category")
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
