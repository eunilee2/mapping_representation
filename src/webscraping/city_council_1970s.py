import pandas as pd

# Load your previously created CSV file
df = pd.read_csv("pittsburgh_past_council_members.csv")

# Convert the year columns to numeric (in case there are any issues)
df["year elected"] = pd.to_numeric(df["year elected"], errors="coerce")
df["year terminated"] = pd.to_numeric(df["year terminated"], errors="coerce")

# Filter for members active during 1970–1979
df_1970s = df[(df["year terminated"] >= 1970) & (df["year elected"] <= 1979)]

# Save to new CSV
df_1970s.to_csv("council_members_1970s.csv", index=False)

print("Filtered file saved as council_members_1970s.csv")
