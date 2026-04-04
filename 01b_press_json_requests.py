# ============================================================
# FILE: 01c_press_json_requests.py
# PURPOSE:
# Collect ECB press releases from the JSON dataset used by
# the "All news & publications" page.
#
# SAME APPROACH AS 01_speech_json_requests.py BUT:
# - Filters for type = 1 (ECB Press release)
#   instead of type = 19 (ECB Speech)
#
# WHAT IT DOES:
# 1. Downloads metadata.json
# 2. Downloads all main data chunks
# 3. Rebuilds rows using the header structure
# 4. Keeps only press releases (type = 1)
# 5. Keeps only years 2019-2026
# 6. Saves results to CSV
#
# OUTPUT:
# data/ecb_press_releases_json.csv
# ============================================================

import requests
import csv
import os
import math
from datetime import datetime, UTC
from collections import Counter

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

BASE_DATASET = "https://www.ecb.europa.eu/foedb/dbs/foedb/publications.en/1775134838/wr3YWp5G"
METADATA_URL = BASE_DATASET + "/metadata.json"

OUTPUT_FILE = "data/ecb_press_releases_json.csv"

# Type 1 = "ECB Press release" (found via discover_types.py)
PRESS_RELEASE_TYPE_ID = 1

START_YEAR = 2019
END_YEAR = 2026

os.makedirs("data", exist_ok=True)

# ------------------------------------------------------------
# HELPER FUNCTIONS
# (Same as in 01_speech_json_requests.py)
# ------------------------------------------------------------

def unix_to_date_string(timestamp_value):
    """
    Converts Unix timestamp to YYYY-MM-DD.
    """
    if timestamp_value is None:
        return ""
    try:
        timestamp_value = int(timestamp_value)
        return datetime.fromtimestamp(timestamp_value, UTC).strftime("%Y-%m-%d")
    except Exception:
        return ""


def get_best_link(document_types):
    """
    Returns the best available link for a record.
    Preference: English HTML > English PDF > Any PDF
    """
    if not document_types:
        return ""

    # First choice: English HTML
    for item in document_types:
        if isinstance(item, str) and item.endswith(".en.html"):
            if item.startswith("http"):
                return item
            return "https://www.ecb.europa.eu" + item

    # Second choice: English PDF
    for item in document_types:
        if isinstance(item, str) and item.endswith(".en.pdf"):
            if item.startswith("http"):
                return item
            return "https://www.ecb.europa.eu" + item

    # Third choice: any PDF
    for item in document_types:
        if isinstance(item, str) and item.endswith(".pdf"):
            if item.startswith("http"):
                return item
            return "https://www.ecb.europa.eu" + item

    return ""


def get_title(properties):
    """Extract title from publicationProperties."""
    if not isinstance(properties, dict):
        return ""
    value = properties.get("Title", "")
    if isinstance(value, list):
        return value[0] if value else ""
    return value


def get_subtitle(properties):
    """Extract subtitle from publicationProperties."""
    if not isinstance(properties, dict):
        return ""
    value = properties.get("Subtitle", "")
    if isinstance(value, list):
        return value[0] if value else ""
    return value


def get_link_type(link):
    """Determine if the link points to HTML or PDF."""
    if link.endswith(".html"):
        return "html"
    elif link.endswith(".pdf"):
        return "pdf"
    return ""


# ------------------------------------------------------------
# STEP 1: DOWNLOAD METADATA
# ------------------------------------------------------------

print("=" * 60)
print("ECB PRESS RELEASE SCRAPER - JSON VERSION")
print("=" * 60)

print("\nDownloading metadata...")
meta_response = requests.get(METADATA_URL, timeout=30)
print("Metadata status:", meta_response.status_code)

if meta_response.status_code != 200:
    print("ERROR: Could not download metadata.")
    raise SystemExit

metadata = meta_response.json()

header = metadata["header"]
total_records = metadata["total_records"]
chunk_size = metadata["chunk_size"]

print("Fields in header:", len(header))
print("Total records in dataset:", total_records)
print("Chunk size:", chunk_size)

num_chunks = math.ceil(total_records / chunk_size)
print("Number of chunks to download:", num_chunks)

# ------------------------------------------------------------
# STEP 2: DOWNLOAD ALL MAIN DATA CHUNKS
# ------------------------------------------------------------

all_rows = []

for chunk_number in range(num_chunks):
    chunk_url = f"{BASE_DATASET}/data/0/chunk_{chunk_number}.json"

    print(f"\nDownloading chunk {chunk_number + 1}/{num_chunks}")
    print("URL:", chunk_url)

    response = requests.get(chunk_url, timeout=60)

    if response.status_code != 200:
        print("  Skipped - status", response.status_code)
        continue

    chunk_data = response.json()
    field_count = len(header)

    if len(chunk_data) % field_count != 0:
        print("  WARNING: Chunk length does not match field count")
        continue

    rows_in_chunk = len(chunk_data) // field_count
    print("  Rows in chunk:", rows_in_chunk)

    for row_num in range(rows_in_chunk):
        start = row_num * field_count
        end = start + field_count
        row_values = chunk_data[start:end]

        row_dict = {}
        for i in range(field_count):
            row_dict[header[i]] = row_values[i]

        all_rows.append(row_dict)

print("\nTotal rows rebuilt:", len(all_rows))

# ------------------------------------------------------------
# STEP 3: FILTER ONLY PRESS RELEASES FROM 2019-2026
# ------------------------------------------------------------

press_rows = []

for row in all_rows:
    row_type = row.get("type")
    row_year = row.get("year")

    # Keep only press releases (type = 1)
    if row_type != PRESS_RELEASE_TYPE_ID:
        continue

    if row_year is None:
        continue

    try:
        row_year = int(row_year)
    except Exception:
        continue

    if row_year < START_YEAR or row_year > END_YEAR:
        continue

    properties = row.get("publicationProperties", {})
    document_types = row.get("documentTypes", [])

    title = get_title(properties)
    subtitle = get_subtitle(properties)
    link = get_best_link(document_types)
    date_str = unix_to_date_string(row.get("pub_timestamp"))

    press_rows.append({
        "doc_type": "press_release",
        "title": title,
        "subtitle": subtitle,
        "date": date_str,
        "year": row_year,
        "link": link,
        "link_type": get_link_type(link),
        "source": "json_dataset"
    })

print("\nPress releases found:", len(press_rows))

print("\nYears found before deduplication:")
year_counts_raw = Counter(row["year"] for row in press_rows)
for year in sorted(year_counts_raw):
    print(f"  {year}: {year_counts_raw[year]}")

# ------------------------------------------------------------
# STEP 4: REMOVE DUPLICATES
# ------------------------------------------------------------

unique_rows = []
seen_links = set()

for row in press_rows:
    link = row["link"]

    if not link:
        continue

    if link in seen_links:
        continue

    seen_links.add(link)
    unique_rows.append(row)

print("\nUnique press releases with links:", len(unique_rows))

# ------------------------------------------------------------
# STEP 5: SORT AND SAVE
# ------------------------------------------------------------

unique_rows = sorted(
    unique_rows,
    key=lambda x: (x["year"], x["date"], x["title"])
)

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    fieldnames = [
        "doc_type",
        "title",
        "subtitle",
        "date",
        "year",
        "link",
        "link_type",
        "source"
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(unique_rows)

print(f"\nSaved to {OUTPUT_FILE}")

# ------------------------------------------------------------
# STEP 6: SUMMARY
# ------------------------------------------------------------

year_counts = Counter(row["year"] for row in unique_rows)

print("\nSUMMARY BY YEAR")
for year in sorted(year_counts):
    print(f"  {year}: {year_counts[year]}")

# Count by link type
html_count = sum(1 for r in unique_rows if r["link_type"] == "html")
pdf_count = sum(1 for r in unique_rows if r["link_type"] == "pdf")
print(f"\nHTML links: {html_count}")
print(f"PDF links:  {pdf_count}")

print("\nFirst 10 press releases:")
for row in unique_rows[:10]:
    print(f"  [{row['date']}] {row['title'][:80]}")
    print(f"     {row['link'][:80]}")

print("\nDone.")
