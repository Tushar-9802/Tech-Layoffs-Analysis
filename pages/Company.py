import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Company Explorer", layout="wide")
st.title("🏢 Company Landscape Explorer")

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

st.markdown(f"### 🎯 Industry: {selected_industry} | 🔍 Focus: {highlight_company}")
st.markdown("---")

#1> Top 10 Companies in Industry
st.subheader("🏆 Top 10 Companies by Total Layoffs")
top_companies = (
    df_industry.groupby('company')['total_laid_off']
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)
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

#2> Industry Share Donut Chart.
st.subheader("🍩 Layoff Share Within Industry")
industry_share = df_industry.groupby('company')['total_laid_off'].sum().reset_index()
fig_pie = px.pie(
industry_share,
names='company',
values='total_laid_off',
hole=0.5
)
fig_pie.update_traces(textinfo='percent+label')
fig_pie.update_layout(template="plotly_white")
st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

#3> Quarterly Trend Comparison.
st.subheader("📈 Quarterly Layoffs: Highlight vs Top 5")
top_5 = top_companies['company'].tolist()
compare_companies = list(set(top_5 + [highlight_company]))

df_compare = df_industry[df_industry['company'].isin(compare_companies)]
trend = df_compare.groupby(['quarter', 'company'])['total_laid_off'].sum().reset_index()
fig_line = px.line(
trend,
x='quarter',
y='total_laid_off',
color='company',
markers=True
)
fig_line.update_layout(
xaxis_title="Quarter",
yaxis_title="Total Laid Off",
template="plotly_white",
xaxis=dict(title_font=dict(color="white")),
yaxis=dict(title_font=dict(color="white"))
)
st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")

#4> Optional Table.
st.subheader(f"📆 Layoff Events for {highlight_company}")
selected_df = df_industry[df_industry['company'] == highlight_company]
display_cols = ['date', 'location', 'total_laid_off', 'percentage_laid_off']
st.dataframe(selected_df[display_cols].sort_values('date'), use_container_width=True)