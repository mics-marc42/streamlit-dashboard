import pandas as pd

# Read the CSV file
df = pd.read_csv("C:/Users/micho/Downloads/bq-results-20260208-074557-1770536771719.csv")

# Define filter condition
# Example: Filter rows where 'accepted_collabs' column equals a specific value
# You can modify this condition based on your needs
column_name = "accepted_collabs"  # Column to filter on
filter_value = 0  # Value to filter for (change this to your desired value)

# Apply filter condition
# Option 1: Filter by exact value
filtered_df = df[df[column_name] > filter_value]

filtered_df = filtered_df[filtered_df['amazon_id'].astype(str).str.len() > 5]

# Option 2: Filter by multiple values (uncomment to use)
# filtered_df = df[df[column_name].isin(["value1", "value2"])]

# Option 3: Filter by condition (e.g., greater than, contains, etc.)
# filtered_df = df[df[column_name] > 100]  # For numeric comparison
# filtered_df = df[df[column_name].str.contains("text", na=False)]  # For string contains

# Save filtered data to new CSV
output_filename = "filtered_output.csv"
filtered_df.to_csv(output_filename, index=False)

print(f"Filtered {len(filtered_df)} rows out of {len(df)} total rows")
print(f"Saved to {output_filename}")

