from Clean import clean_layoff_data
import pandas as pd

def main():
    df = pd.read_csv("layoffs.csv")
    df_clean = clean_layoff_data(df)
    df_clean.to_csv("Cleaned_layoffs.csv", index=False)
    print("✅ Data cleaned and saved.")
    
    print(df['estimated_company_size'].describe())
    print(df['company_size_category'].value_counts(dropna=False))

if __name__ == "__main__":
    main()
