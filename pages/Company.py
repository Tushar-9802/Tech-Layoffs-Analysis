import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Company Explorer", layout="wide")
st.title("Company Landscape Explorer")

@st.cache_data
def load_data():
    df = pd.read_csv("data/Cleaned_layoffs.csv")
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['quarter'] = df['date'].dt.to_period('Q').astype(str)
    return df

df = load_data()

# Sidebar Filters
st.sidebar.header("Filters")
industries = sorted(df['industry'].dropna().unique())
selected_industry = st.sidebar.selectbox("Select Industry", industries)
df_industry = df[df['industry'] == selected_industry]

highlight_company = st.sidebar.selectbox("Compare Against", sorted(df_industry['company'].dropna().unique()))

st.markdown(f"### Industry: {selected_industry} | Focus: {highlight_company}")
st.markdown("---")

# 1> Top 10 Companies in Industry
top_companies_raw = (
    df_industry.groupby('company')['total_laid_off']
    .sum()
    .sort_values(ascending=False)
    .head(10)
)
top_companies = top_companies_raw.copy()
if highlight_company not in top_companies:
    highlight_val = df_industry[df_industry['company'] == highlight_company]['total_laid_off'].sum()
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
    xaxis=dict(title_font=dict(color="white")),
    yaxis=dict(title_font=dict(color="white")),
    showlegend=False
)
st.plotly_chart(fig_top, use_container_width=True)

st.markdown("---")

# 2> Industry Share Donut Chart.
st.subheader("2. Layoff Share Within Industry")
industry_share = df_industry.groupby('company')['total_laid_off'].sum().reset_index()
fig_pie = px.pie(
    industry_share,
    names='company',
    values='total_laid_off',
    hole=0.7  # Increase donut size
)
fig_pie.update_traces(
    textinfo='none',  # Remove static text on chart
    pull=[0.05 if c == highlight_company else 0 for c in industry_share['company']],  # Optional: highlight selected
    hovertemplate='%{label}: %{percent}',  # Show percentage on hover
    marker=dict(line=dict(color='rgba(0,0,0,0)', width=0))  # Remove white lines to labels
)
fig_pie.update_layout(
    template="plotly_white",
    height=700,
    legend_title_text='Company',
    showlegend=True,
    margin=dict(t=20, b=20, l=100, r=100)
)
st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# 3> Quarterly Trend Comparison.
st.subheader("3. Quarterly Layoffs: Highlight vs Top 4")

# Get top 4 companies by total layoffs in the selected industry
top_4 = (
    df_industry.groupby('company')['total_laid_off']
    .sum()
    .sort_values(ascending=False)
    .head(4)
    .index.tolist()
)
compare_companies = list(set(top_4 + [highlight_company]))

# Filter data for comparison companies
df_compare = df_industry[df_industry['company'].isin(compare_companies)]

# Create a complete grid of quarters and companies to avoid missing data points
all_quarters = pd.period_range(df_compare['quarter'].min(), df_compare['quarter'].max(), freq='Q').astype(str)
all_companies = sorted(compare_companies)
full_index = pd.MultiIndex.from_product([all_quarters, all_companies], names=['quarter', 'company'])

trend = (
    df_compare.groupby(['quarter', 'company'])['total_laid_off']
    .sum()
    .reindex(full_index, fill_value=0)
    .reset_index()
)

# Optional: Smooth the data using rolling average to reduce noise
trend['smoothed_laid_off'] = (
    trend.groupby('company')['total_laid_off']
    .transform(lambda x: x.rolling(window=2, min_periods=1).mean())
)

fig_line = px.line(
    trend,
    x='quarter',
    y='smoothed_laid_off',
    color='company',
    markers=True
)
fig_line.update_layout(
    xaxis_title="Quarter",
    yaxis_title="Total Laid Off (Smoothed)",
    template="plotly_white"
)
st.plotly_chart(fig_line, use_container_width=True)
st.markdown("---")

# 4> Optional Table.
st.subheader(f"4. Layoff Events for {highlight_company}")
selected_df = df_industry[df_industry['company'] == highlight_company]
display_cols = ['date', 'location', 'total_laid_off', 'percentage_laid_off']
st.dataframe(selected_df[display_cols].sort_values('date'), use_container_width=True)