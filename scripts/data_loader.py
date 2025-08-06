import pandas as pd

def clean_layoff_data(df):
    #---Data Cleaning---#

    # Convert Date Columns to datetime type
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['date_added'] = pd.to_datetime(df['date_added'], errors='coerce')

    # Clean and convert 'percentage_laid_off' from string with '%' to float
    df['percentage_laid_off'] = (
    df['percentage_laid_off']
    .astype(str)
    .str.replace('%', '')
    .replace({'nan': None, 'None': None, '': None})
    .astype(float)
    )

    # Function to Convert Funds into Numerical values
    def parse_funding(value):
        if pd.isna(value):
            return None
        value = str(value).replace('$', '').replace(',', '').upper()
        if 'M' in value:
            return float(value.replace('M', '')) * 1_000_000
        elif 'B' in value:
            return float(value.replace('B', '')) * 1_000_000_000
        else:
            try:
                return float(value)
            except:
                return None

    # Apply function to clean Funds-Raised
    df['funds_raised_clean'] = df['funds_raised'].apply(parse_funding)

    # Date extraction
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['quarter'] = df['date'].dt.to_period('Q')

    # Company Size based on Layoffs
    def estimate_size(row):
        try:
            if pd.notna(row['total_laid_off']) and pd.notna(row['percentage_laid_off']) and row['percentage_laid_off'] > 0:
                return int(row['total_laid_off'] / (row['percentage_laid_off'] / 100))
        except:
            return None
        return None

    df['estimated_company_size'] = df.apply(estimate_size, axis=1)

    # Categorize Company into Small, Mid, Large 
    def categorize_size(size):
        if pd.isna(size):
            return 'Unknown'
        elif size < 500:
            return 'Small (<500)'
        elif size < 5000:
            return 'Mid (500–4999)'
        else:
            return 'Large (5000+)'

    df['company_size_category'] = df['estimated_company_size'].apply(categorize_size)

    # Handle missing locations
    df['country'] = df['country'].fillna('Unknown')
    df['location'] = df['location'].fillna('Unknown')

    return df
