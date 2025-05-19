import pandas as pd
import re
name ='Counter_Strike'
# Load your CSV
df = pd.read_csv(f'{name}_reviews.csv')

# Clean 'Hours Played' (remove commas, convert to float)
df['Hours Played'] = df['Hours Played'].astype(str).str.replace(',', '', regex=False).astype(float)

# Clean 'Helpful Votes' (extract only the first numeric value)
def extract_first_number(text):
    match = re.search(r'[\d,]+', str(text))
    if match:
        number = match.group(0).replace(',', '')
        return int(number)
    return 0

df['Helpful Votes'] = df['Helpful Votes'].apply(extract_first_number)

# Save cleaned data
df.to_csv(f'{name}_cleaned_reviews.csv', index=False)
