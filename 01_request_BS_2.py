# ============================================================
# FILE: 01_request_BS.py
# STEP 1 of the ECB Web Scraping Project
#
# WHAT THIS FILE DOES:
# Collects ALL ECB article URLs from 2019 to 2026 using two
# methods:
#   A) The ECB "index_include" pages — hidden HTML fragments
#      that the ECB website's JavaScript normally loads. We
#      discovered these by exploring the ECB site structure.
#      They give us FULL article listings by year.
#   B) RSS feeds — for the most recent articles (last ~15
#      per feed). These complement the index_include data.
#
# WHY TWO METHODS?
# - index_include pages give us historical data (2019-2026)
# - RSS feeds give us the very latest articles
# - Together, they give us comprehensive coverage
#
# LIBRARIES USED:
# - requests: sends HTTP GET requests to download pages
# - BeautifulSoup (bs4): parses HTML/XML to extract data
# - csv: saves results to a CSV file
# - os: creates folders
# - time: adds delays between requests (polite scraping)
# - re: used for cleaning text (regex)
#
# OUTPUT: data/ecb_articles.csv
# ============================================================

import requests
from bs4 import BeautifulSoup
import csv
import os
import time
import re
from collections import Counter

# ============================================================
# CONFIGURATION
# ============================================================

# Base URL for all ECB pages
BASE_URL = "https://www.ecb.europa.eu"

# Years to scrape (2019 through 2026)
YEARS = list(range(2019, 2027))

# Content types and their URL path segments
# These are the sections of the ECB website we want to scrape.
# The "path" is used to build the index_include URL.
# The "link_pattern" helps us identify article links on the page.
CONTENT_TYPES = {
    "speech": {
        "path": "press/key",
        "link_pattern": "/press/key/",
    },
    "press_release": {
        "path": "press/pr",
        "link_pattern": "/press/pr/",
    },
    "interview": {
        "path": "press/inter",
        "link_pattern": "/press/inter/",
    },
    "blog_post": {
        "path": "press/blog",
        "link_pattern": "/press/blog/",
    },
    "governing_council_decision": {
        "path": "press/govcdec",
        "link_pattern": "/press/govcdec/",
    },
}

# RSS feed URLs (for the most recent articles)
RSS_FEEDS = {
    "press":          "https://www.ecb.europa.eu/rss/press.html",
    "blog":           "https://www.ecb.europa.eu/rss/blog.html",
    "statistical":    "https://www.ecb.europa.eu/rss/statpress.html",
    "publications":   "https://www.ecb.europa.eu/rss/pub.html",
    "working_papers": "https://www.ecb.europa.eu/rss/wppub.html",
}

# Polite scraping: wait between requests (ECB robots.txt says 5 seconds)
DELAY_SECONDS = 5

# Create the output folder
os.makedirs("data", exist_ok=True)
OUTPUT_FILE = "data/ecb_articles.csv"


# ============================================================
# PART A: SCRAPE INDEX_INCLUDE PAGES (historical articles)
# ============================================================

def scrape_index_include(content_type, path, link_pattern, year):
    """
    Downloads one index_include page and extracts all article
    links from it.

    The index_include pages are HTML fragments that the ECB
    website loads via JavaScript. They contain a <dl> list
    with <dt> (date) and <dd> (article details) elements.

    Parameters:
        content_type (str): label like "speech" or "interview"
        path (str): URL path segment like "press/key"
        link_pattern (str): pattern to match in article URLs
        year (int): the year to scrape

    Returns:
        list of dicts: one dictionary per article
    """
    # Build the URL for this content type and year
    url = f"{BASE_URL}/{path}/date/{year}/html/index_include.en.html"
    print(f"  Fetching {content_type} for {year}...")

    try:
        response = requests.get(url, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"    ERROR: Request failed — {e}")
        return []

    # If the page doesn't exist, skip it (404 = Not Found)
    if response.status_code != 200:
        print(f"    Skipped (status {response.status_code})")
        return []

    # If the response is very short, there's probably no content
    if len(response.text) < 100:
        print(f"    Skipped (empty page)")
        return []

    # Parse the HTML fragment with BeautifulSoup
    # We use "html.parser" because these are HTML fragments, not XML
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    seen_links = set()  # to avoid duplicate articles

    # --------------------------------------------------------
    # Strategy: find all <a> tags and filter for article links
    # --------------------------------------------------------
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        title = a_tag.get_text(strip=True)

        # --- FILTER 1: Only keep English HTML pages ---
        # Skip PDFs, anchors, and non-English pages
        if not href.endswith(".en.html"):
            continue

        # --- FILTER 2: Only keep links matching our content type ---
        if link_pattern not in href:
            continue

        # --- FILTER 3: Skip very short text (language selectors) ---
        # Language buttons like "English" or "Deutsch" are short
        if len(title) < 10:
            continue

        # --- FILTER 4: Skip duplicates ---
        if href in seen_links:
            continue
        seen_links.add(href)

        # --- BUILD FULL URL ---
        if href.startswith("/"):
            full_url = BASE_URL + href
        else:
            full_url = href

        # --- EXTRACT DATE ---
        # Walk up the HTML tree to find the nearest <dt> with a date
        date = ""
        parent_dd = a_tag.find_parent("dd")
        if parent_dd:
            prev_dt = parent_dd.find_previous_sibling("dt")
            if prev_dt:
                # The isoDate attribute contains the date (e.g. "2024-08-30")
                # BeautifulSoup lowercases attributes, so it's "isodate"
                date = prev_dt.get("isodate", "")

        # --- EXTRACT SUBTITLE (description) ---
        subtitle = ""
        if parent_dd:
            sub_div = parent_dd.find("div", class_="subtitle")
            if sub_div:
                subtitle = sub_div.get_text(strip=True)

        # Clean up the title (remove extra whitespace and &nbsp;)
        title = re.sub(r'\s+', ' ', title).strip()
        subtitle = re.sub(r'\s+', ' ', subtitle).strip()

        results.append({
            "source":      "index_include",
            "doc_type":    content_type,
            "title":       title,
            "date":        date,
            "year":        year,
            "link":        full_url,
            "description": subtitle[:500],
        })

    print(f"    Found {len(results)} articles")
    return results


# ============================================================
# PART B: SCRAPE RSS FEEDS (most recent articles)
# ============================================================

def scrape_rss_feed(feed_name, feed_url):
    """
    Downloads one RSS feed (XML) and extracts all items.
    RSS feeds give us the ~15 most recent articles per feed.

    Parameters:
        feed_name (str): label like "press" or "blog"
        feed_url (str): URL of the RSS feed

    Returns:
        list of dicts: one dictionary per item
    """
    print(f"  Fetching RSS: {feed_name}...")

    try:
        response = requests.get(feed_url, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"    ERROR: {e}")
        return []

    if response.status_code != 200:
        print(f"    ERROR: Status {response.status_code}")
        return []

    # RSS is XML, so we use the "xml" parser
    soup = BeautifulSoup(response.text, "xml")
    items = soup.find_all("item")
    print(f"    Found {len(items)} items")

    results = []

    for item in items:
        # Extract fields safely (handle missing tags)
        title = item.find("title")
        title = title.get_text(strip=True) if title else ""

        link = item.find("link")
        link = link.get_text(strip=True) if link else ""

        pubdate = item.find("pubDate")
        pubdate = pubdate.get_text(strip=True) if pubdate else ""

        description = item.find("description")
        description = description.get_text(strip=True) if description else ""

        # Classify the document type based on the URL
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
            doc_type = feed_name

        # Try to extract year from the date string
        year_match = re.search(r'(\d{4})', pubdate)
        year = int(year_match.group(1)) if year_match else 0

        # Convert RSS date to ISO format (YYYY-MM-DD)
        # RSS dates look like: "Wed, 12 Mar 2025 12:00:00 GMT"
        date_iso = ""
        try:
            from datetime import datetime
            dt = datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S %Z")
            date_iso = dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            date_iso = pubdate  # keep original if parsing fails

        results.append({
            "source":      "rss",
            "doc_type":    doc_type,
            "title":       title,
            "date":        date_iso,
            "year":        year,
            "link":        link,
            "description": description[:500],
        })

    return results


# ============================================================
# MAIN SCRIPT
# ============================================================

print("=" * 60)
print("ECB ARTICLE COLLECTOR")
print("Scraping article URLs from 2019 to 2026")
print("=" * 60)

all_results = []

# --- PART A: Scrape index_include pages ---
print("\n--- PART A: Index_include pages (historical data) ---\n")

for content_type, config in CONTENT_TYPES.items():
    for year in YEARS:
        articles = scrape_index_include(
            content_type=content_type,
            path=config["path"],
            link_pattern=config["link_pattern"],
            year=year,
        )
        all_results.extend(articles)

        # Polite delay between requests
        time.sleep(DELAY_SECONDS)

print(f"\nArticles from index_include: {len(all_results)}")

# --- PART B: Scrape RSS feeds ---
print("\n--- PART B: RSS feeds (recent articles) ---\n")

rss_count_before = len(all_results)

for feed_name, feed_url in RSS_FEEDS.items():
    items = scrape_rss_feed(feed_name, feed_url)
    all_results.extend(items)
    time.sleep(DELAY_SECONDS)

rss_count = len(all_results) - rss_count_before
print(f"\nArticles from RSS feeds: {rss_count}")

# --- DEDUPLICATE by link ---
# Some articles may appear in both index_include and RSS
print("\n--- Deduplicating ---")
seen = set()
unique_results = []
for item in all_results:
    if item["link"] not in seen:
        seen.add(item["link"])
        unique_results.append(item)

duplicates_removed = len(all_results) - len(unique_results)
print(f"Removed {duplicates_removed} duplicate articles")
print(f"Total unique articles: {len(unique_results)}")

# --- SAVE TO CSV ---
print(f"\nSaving to {OUTPUT_FILE}...")

fieldnames = ["source", "doc_type", "title", "date", "year", "link", "description"]

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(unique_results)

print(f"Saved {len(unique_results)} articles to {OUTPUT_FILE}")

# --- PRINT SUMMARY ---
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

# Count by document type
print("\nBy document type:")
type_counts = Counter(item["doc_type"] for item in unique_results)
for doc_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {doc_type}: {count}")

# Count by year
print("\nBy year:")
year_counts = Counter(item["year"] for item in unique_results)
for year, count in sorted(year_counts.items()):
    print(f"  {year}: {count}")

# Count by source
print("\nBy source:")
source_counts = Counter(item["source"] for item in unique_results)
for source, count in sorted(source_counts.items()):
    print(f"  {source}: {count}")

print("\nStep 1 complete! Next: run 02_selenium.py to get full article text.")
