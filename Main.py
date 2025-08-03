import pandas as pd
from Clean import clean_layoff_data

#---Load CSV as DataFrame---#
df = pd.read_csv("layoffs.csv")

#---Clean the DataFrame using the external cleaning function---#
df1 = clean_layoff_data(df)

#---Example: Display first 5 rows of the cleaned percentage laid off column---#
print(df1['percentage_laid_off'].head())

# Continue with your analysis or visualization here
