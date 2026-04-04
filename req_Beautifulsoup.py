import requests
from bs4 import BeautifulSoup

# Step 1: Download the page
response = requests.get("https://www.ecb.europa.eu/press/pr/html/index.en.html")

# Step 2: Parse the HTML
soup = BeautifulSoup(response.text, "lxml")

# Step 3: Find all the date elements
dates = soup.select("dl dt")

# Step 4: Print them
for date in dates:
    print(date.get_text())