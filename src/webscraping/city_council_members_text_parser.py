import requests
from bs4 import BeautifulSoup
import csv
import re

url = "https://en.wikipedia.org/wiki/Pittsburgh_City_Council"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# Find "Past members" section
past_members_section = soup.find(id="Past_members")
members_list = past_members_section.find_next("ul")

# CSV setup
rows = [("name", "year elected", "year terminated")]

# Regex for name and years
pattern = re.compile(r"^(.*?)\s+\((\d{4})–(\d{4})\)")

# Parse each list item
for li in members_list.find_all("li"):
    text = li.get_text(strip=True)
    match = pattern.match(text)
    if match:
        name, start, end = match.groups()
        rows.append((name, start, end))

# Write to CSV
with open("pittsburgh_past_council_members.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(rows)

print("CSV file saved as pittsburgh_past_council_members.csv")
