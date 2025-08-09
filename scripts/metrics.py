import pandas as pd
import numpy as np

def calculate_layoff_efficiency(df):
    df_eff = df[
        df['total_laid_off'].notna() &
        df['percentage_laid_off'].notna() &
        df['funds_raised_clean'].notna() &
        (df['percentage_laid_off'] > 0) &
        (df['funds_raised_clean'] > 0)
    ].copy()

    df_eff['layoffs_per_million'] = df_eff['total_laid_off'] / (df_eff['funds_raised_clean'] / 1_000_000)
    df_eff['layoff_efficiency_score'] = df_eff['layoffs_per_million'] / df_eff['percentage_laid_off']

    inefficient = (
        df_eff.groupby('company')
        .agg({
            'total_laid_off': 'sum',
            'percentage_laid_off': 'mean',
            'funds_raised_clean': 'sum',
            'layoffs_per_million': 'mean',
            'layoff_efficiency_score': 'mean'
        })
        .sort_values(by='layoff_efficiency_score', ascending=False)
        .reset_index()
    )
    return inefficient


def calculate_layoff_instability(df):
    df['quarter'] = pd.to_datetime(df['date'], errors='coerce').dt.to_period('Q')
    instability = (
        df.dropna(subset=['company', 'quarter'])[['company', 'quarter']]
        .drop_duplicates()
        .groupby('company')
        .size()
        .reset_index(name='layoff_instability_score')
        .sort_values('layoff_instability_score', ascending=False)
    )
    return instability


def calculate_layoff_severity(df):
    df_filtered = df[
        df['percentage_laid_off'].notnull() &
        df['total_laid_off'].notnull()
    ].copy()

    df_filtered['layoff_severity_index'] = df_filtered['percentage_laid_off'] * np.log(df_filtered['total_laid_off'] + 1)

    lsi_by_company = (
        df_filtered.groupby('company')['layoff_severity_index']
        .mean()
        .reset_index()
        .sort_values('layoff_severity_index', ascending=False)
    )
    return lsi_by_company


def calculate_fragility_index(df):
    fragility_df = (
        df[['location', 'company', 'percentage_laid_off']]
        .dropna()
        .groupby(['location', 'company'])
        .mean()  # avg % per company per location
        .reset_index()
        .groupby('location')
        .agg(
            num_companies=('company', 'nunique'),
            avg_pct=('percentage_laid_off', 'mean')
        )
    )

    fragility_df['fragility_index'] = fragility_df['num_companies'] * fragility_df['avg_pct']
    fragility_df = fragility_df.sort_values('fragility_index', ascending=False).reset_index()
    return fragility_df
