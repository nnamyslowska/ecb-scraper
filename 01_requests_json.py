# Collecting ECB speeches and press releases from the JSON dataset

import requests
import csv
import os
import math
import re
from datetime import datetime, UTC
from collections import Counter

BASE_DATASET = "https://www.ecb.europa.eu/foedb/dbs/foedb/publications.en/1775134838/wr3YWp5G"
METADATA_URL = BASE_DATASET + "/metadata.json"

OUTPUT_FILE_SPEECHES = "data/ecb_speeches_json.csv"
OUTPUT_FILE_PRESS = "data/ecb_press_releases_json.csv"

SPEECH_TYPE_ID = 19
PRESS_RELEASE_TYPE_ID = 1

START_YEAR = 1997
END_YEAR = 2026

os.makedirs("data", exist_ok=True)


# Helper functions:

def unix_to_date_string(timestamp_value):
    """Convert Unix timestamp to YYYY-MM-DD."""
    if timestamp_value is None:
        return ""
    try:
        timestamp_value = int(timestamp_value)
        return datetime.fromtimestamp(timestamp_value, UTC).strftime("%Y-%m-%d")
    except Exception:
        return ""


def get_best_link(document_types):
    """Return the best link: English HTML > English PDF > any PDF."""
    if not document_types:
        return ""

    for item in document_types:
        if isinstance(item, str) and item.endswith(".en.html"):
            return "https://www.ecb.europa.eu" + item if item.startswith("/") else item

    for item in document_types:
        if isinstance(item, str) and item.endswith(".en.pdf"):
            return "https://www.ecb.europa.eu" + item if item.startswith("/") else item

    for item in document_types:
        if isinstance(item, str) and item.endswith(".pdf"):
            return "https://www.ecb.europa.eu" + item if item.startswith("/") else item

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
    """Label the link as HTML or PDF."""
    if link.endswith(".html"):
        return "html"
    if link.endswith(".pdf"):
        return "pdf"
    return ""


def filter_rows(all_rows, target_type, doc_type_name, include_extra_fields=False):
    """Filter all rows for one publication type and keep useful fields."""
    filtered_rows = []

    for row in all_rows:
        row_type = row.get("type")
        row_year = row.get("year")

        if row_type != target_type:
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
        link = get_best_link(document_types)

        date_str = get_date_from_link(link)
        if not date_str:
            date_str = unix_to_date_string(row.get("pub_timestamp"))

        row_dict = {
            "doc_type": doc_type_name,
            "title": get_title(properties),
            "subtitle": get_subtitle(properties),
            "date": date_str,
            "year": row_year,
            "link": link,
            "link_type": get_link_type(link),
            "source": "json_dataset"
        }

        if include_extra_fields:
            row_dict["author"] = row.get("Authors", "")
            row_dict["boardmember"] = row.get("boardmember", "")
            row_dict["taxonomy"] = row.get("Taxonomy", "")

        filtered_rows.append(row_dict)

    return filtered_rows


def deduplicate_rows(rows):
    """Remove duplicates based on link."""
    unique_rows = []
    seen_links = set()

    for row in rows:
        link = row["link"]

        if not link:
            continue

        if link in seen_links:
            continue

        seen_links.add(link)
        unique_rows.append(row)

    unique_rows.sort(key=lambda x: (x["year"], x["date"], x["title"]))
    return unique_rows


def save_csv(rows, output_file, fieldnames):
    """Save rows to CSV."""
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def get_date_from_link(link):
    """Extract date from ECB speech or press release URL."""
    if not link:
        return ""

    match = re.search(r'(?:sp|pr)(\d{2})(\d{2})(\d{2})', link)
    if not match:
        return ""

    yy, mm, dd = match.groups()
    year = int(yy)

    if year <= 26:
        year += 2000
    else:
        year += 1900

    return f"{year:04d}-{mm}-{dd}"

# Downloading metadata and reading dataset structure:

print("Downloading metadata...")
meta_response = requests.get(METADATA_URL, timeout=30)
print("Metadata status:", meta_response.status_code)

if meta_response.status_code != 200:
    print("ERROR: Could not download metadata.")
    raise SystemExit

metadata = meta_response.json()

header = metadata["header"]
total_records = metadata["total_records"]
chunk_size = metadata["chunk_size"]
num_chunks = math.ceil(total_records / chunk_size)

print(f"Total records in dataset: {total_records}")
print(f"Chunks to download: {num_chunks}")


# Downloading chunks and rebuilding rows:

all_rows = []

for chunk_number in range(num_chunks):
    chunk_url = f"{BASE_DATASET}/data/0/chunk_{chunk_number}.json"
    response = requests.get(chunk_url, timeout=60)

    if response.status_code != 200:
        print(f"Chunk {chunk_number + 1}: skipped (status {response.status_code})")
        continue

    chunk_data = response.json()
    field_count = len(header)

    if len(chunk_data) % field_count != 0:
        print(f"Chunk {chunk_number + 1}: skipped (wrong field count)")
        continue

    rows_in_chunk = len(chunk_data) // field_count
    print(f"Chunk {chunk_number + 1}/{num_chunks}: {rows_in_chunk} rows")

    for row_number in range(rows_in_chunk):
        start = row_number * field_count
        end = start + field_count
        row_values = chunk_data[start:end]
        row_dict = dict(zip(header, row_values))
        all_rows.append(row_dict)

print(f"\nTotal rows rebuilt: {len(all_rows)}")


# Filtering for speeches:

speech_rows = filter_rows(
    all_rows=all_rows,
    target_type=SPEECH_TYPE_ID,
    doc_type_name="speech",
    include_extra_fields=True
)

unique_speeches = deduplicate_rows(speech_rows)

save_csv(
    rows=unique_speeches,
    output_file=OUTPUT_FILE_SPEECHES,
    fieldnames=[
        "doc_type",
        "title",
        "subtitle",
        "date",
        "year",
        "author",
        "boardmember",
        "taxonomy",
        "link",
        "link_type",
        "source"
    ]
)

print(f"\nSaved {len(unique_speeches)} speeches to {OUTPUT_FILE_SPEECHES}")


# Filtering for press releases:

press_rows = filter_rows(
    all_rows=all_rows,
    target_type=PRESS_RELEASE_TYPE_ID,
    doc_type_name="press_release",
    include_extra_fields=False
)

unique_press = deduplicate_rows(press_rows)

save_csv(
    rows=unique_press,
    output_file=OUTPUT_FILE_PRESS,
    fieldnames=[
        "doc_type",
        "title",
        "subtitle",
        "date",
        "year",
        "link",
        "link_type",
        "source"
    ]
)

print(f"Saved {len(unique_press)} press releases to {OUTPUT_FILE_PRESS}")


# Summaries:

speech_year_counts = Counter(row["year"] for row in unique_speeches)
press_year_counts = Counter(row["year"] for row in unique_press)

print("\nSpeech summary by year:")
for year in sorted(speech_year_counts):
    print(f"{year}: {speech_year_counts[year]}")

print("\nPress release summary by year:")
for year in sorted(press_year_counts):
    print(f"{year}: {press_year_counts[year]}")