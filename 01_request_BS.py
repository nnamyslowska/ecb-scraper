# ============================================================
# FILE: 01_request_BS.py
# STEP 1 of the ECB Web Scraping Project
#
# WHAT THIS FILE DOES:
# Downloads 5 ECB RSS feeds and collects all items
# (press releases, speeches, blog posts, working papers,
# publications) into one CSV file.
#
# WHY RSS FEEDS?
# The ECB main pages load content via JavaScript, which
# requests cannot access. RSS feeds are plain XML designed
# to be read by machines — no JavaScript needed.
#
# LIBRARIES USED:
# - requests: to download the RSS feed (HTTP GET request)
# - BeautifulSoup (bs4): to parse the XML and extract data
# - csv: to save results to a CSV file
# - os: to create the data/ folder if it doesn't exist
#
# SOURCE: https://www.ecb.europa.eu/home/html/rss.en.html
# ============================================================

import requests
from bs4 import BeautifulSoup
import csv
import os
from collections import Counter

# ============================================================
# LIST OF ALL 5 ECB RSS FEEDS
# Each feed covers a different type of ECB publication.
# The dictionary key is a short label, the value is the URL.
# ============================================================

RSS_FEEDS = {
    "press":          "https://www.ecb.europa.eu/rss/press.html",
    "blog":           "https://www.ecb.europa.eu/rss/blog.html",
    "statistical":    "https://www.ecb.europa.eu/rss/statpress.html",
    "publications":   "https://www.ecb.europa.eu/rss/pub.html",
    "working_papers": "https://www.ecb.europa.eu/rss/wppub.html",
}

# Create the data/ folder if it doesn't exist yet
os.makedirs("data", exist_ok=True)

# Output file path
OUTPUT_FILE = "data/ecb_all_feeds.csv"


def scrape_rss_feed(url, feed_type):
    """
    Downloads one RSS feed and extracts all items from it.

    Parameters:
        url (str): the URL of the RSS feed
        feed_type (str): a label like "press" or "blog"

    Returns:
        list of dicts: one dictionary per item with all fields
    """
    print(f"Scraping {feed_type} feed...")

    # --- Send HTTP GET request to download the RSS feed ---
    response = requests.get(url)

    # Check if the request was successful (status 200 = OK)
    if response.status_code != 200:
        print(f"  ERROR: Got status code {response.status_code}")
        return []  # return empty list if the request failed

    # --- Parse the XML content with BeautifulSoup ---
    # We use "xml" parser because RSS feeds are XML, not HTML
    soup = BeautifulSoup(response.text, "xml")

    # --- Find all <item> tags ---
    # In RSS XML, each article/document is wrapped in <item> tags
    items = soup.find_all("item")
    print(f"  Found {len(items)} items")

    # This list will hold one dictionary per item
    results = []

    # --- Loop through each item and extract data ---
    for item in items:

        # Extract the title (safely handle missing tags)
        title = item.find("title")
        title = title.get_text(strip=True) if title else ""

        # Extract the link to the full article
        link = item.find("link")
        link = link.get_text(strip=True) if link else ""

        # Extract the publication date
        pubdate = item.find("pubDate")
        pubdate = pubdate.get_text(strip=True) if pubdate else ""

        # Extract the short description/summary
        description = item.find("description")
        description = description.get_text(strip=True) if description else ""

        # --- Classify the document type based on the URL ---
        # ECB uses specific URL patterns for different content types
        if "/press/key/" in link:
            doc_type = "speech"
        elif "/press/pr/" in link:
            doc_type = "press_release"
        elif "/press/inter/" in link:
            doc_type = "interview"
        elif "/press/blog/" in link:
            doc_type = "blog_post"
        elif "/press/stats/" in link:
            doc_type = "statistical_release"
        elif "/pub/pdf/scpwps/" in link:
            doc_type = "working_paper"
        elif "/press/economic-bulletin/" in link:
            doc_type = "economic_bulletin"
        elif "/press/govcdec/" in link:
            doc_type = "governing_council_decision"
        else:
            # If no pattern matches, use the feed label as fallback
            doc_type = feed_type

        # Add this item to our results list
        results.append({
            "feed_type":   feed_type,
            "doc_type":    doc_type,
            "title":       title,
            "date":        pubdate,
            "link":        link,
            "description": description[:500]  # limit to 500 characters
        })

    return results


# ============================================================
# MAIN SCRIPT: Loop through all 5 feeds and collect items
# ============================================================

all_results = []

for feed_name, feed_url in RSS_FEEDS.items():
    items = scrape_rss_feed(feed_url, feed_name)
    all_results.extend(items)  # add this feed's items to the big list

# --- Print total count ---
print()
print(f"Total items collected: {len(all_results)}")

# ============================================================
# SAVE ALL RESULTS TO CSV
# ============================================================

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    fieldnames = ["feed_type", "doc_type", "title", "date", "link", "description"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()       # write the column names
    writer.writerows(all_results)  # write all data rows

print(f"Saved to {OUTPUT_FILE}")

# ============================================================
# SUMMARY: Count how many documents of each type we found
# ============================================================

type_counts = Counter(item["doc_type"] for item in all_results)
print("\n=== SUMMARY BY DOCUMENT TYPE ===")
for doc_type, count in sorted(type_counts.items()):
    print(f"  {doc_type}: {count}")