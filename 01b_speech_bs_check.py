# ============================================================
# FILE: 01b_speech_bs_check.py
# PURPOSE:
# Quick requests + BeautifulSoup validation on a small sample
# of ECB speech HTML pages.
#
# WHAT THIS FILE DOES:
# 1. Reads the speech CSV created by 01_speech_json.py
# 2. Keeps only speech rows with HTML links
# 3. Downloads a small sample of HTML pages with requests
# 4. Parses them with BeautifulSoup
# 5. Extracts visible metadata from the page
# 6. Compares JSON metadata with HTML metadata
# 7. Saves a compact comparison CSV
#
# INPUT:
# data/ecb_speeches_json.csv
#
# OUTPUT:
# data/ecb_speeches_bs_check.csv
# ============================================================

import requests
from bs4 import BeautifulSoup
import csv
import os
import time
import re

INPUT_FILE = "data/ecb_speeches_json.csv"
OUTPUT_FILE = "data/ecb_speeches_bs_check.csv"

# Small sample so it runs quickly
MAX_ARTICLES = 10

# ECB robots.txt asks for 5 seconds
DELAY_SECONDS = 5

os.makedirs("data", exist_ok=True)


def clean_text(text):
    """
    Remove extra spaces and line breaks.
    """
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def normalize_for_compare(text):
    """
    Make text easier to compare.
    """
    return clean_text(text).lower()


def yes_no_match(left, right):
    """
    Return yes if two text values match after cleaning.
    """
    if normalize_for_compare(left) == normalize_for_compare(right):
        return "yes"
    return "no"


def get_page_title(soup):
    """
    Extract title from the page.
    """
    h1 = soup.find("h1")
    if h1:
        return clean_text(h1.get_text())

    if soup.title:
        return clean_text(soup.title.get_text())

    return ""


def get_page_subtitle(soup):
    """
    Extract subtitle from the page.
    ECB speech pages often store it in div.subtitle.
    """
    subtitle_div = soup.find("div", class_="subtitle")
    if subtitle_div:
        return clean_text(subtitle_div.get_text())
    return ""


def get_page_date(soup):
    """
    Extract date from the page.
    """
    date_div = soup.find("div", class_="date")
    if date_div:
        return clean_text(date_div.get_text())

    meta_date = soup.find("meta", attrs={"name": "date"})
    if meta_date and meta_date.get("content"):
        return clean_text(meta_date.get("content"))

    return ""


def get_page_author(soup):
    """
    Try to extract author/speaker from the subtitle text.
    """
    subtitle = get_page_subtitle(soup)

    if subtitle:
        pattern = (
            r"^(Speech by|Keynote speech by|Lecture by|"
            r"Introductory remarks by|Remarks by|Address by|"
            r"Public lecture by)\s+([^,]+)"
        )
        match = re.match(pattern, subtitle, re.IGNORECASE)
        if match:
            return clean_text(match.group(2))

    return ""


print("=" * 60)
print("ECB SPEECH BEAUTIFULSOUP CHECK")
print("=" * 60)

if not os.path.exists(INPUT_FILE):
    print("ERROR: Input file not found.")
    print("Run 01_speech_json.py first.")
    raise SystemExit

rows = []
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

print(f"\nLoaded {len(rows)} speech rows")

html_rows = []
for row in rows:
    if row.get("link_type", "") == "html" and row.get("link", ""):
        html_rows.append(row)

print(f"Rows with HTML links: {len(html_rows)}")

html_rows = html_rows[:MAX_ARTICLES]
print(f"Testing first {len(html_rows)} pages")

results = []

for i, row in enumerate(html_rows, start=1):
    url = row.get("link", "")
    print(f"\n[{i}/{len(html_rows)}] {url}")

    status_code = ""
    html_title = ""
    html_subtitle = ""
    html_date = ""
    html_author = ""

    try:
        response = requests.get(url, timeout=30)
        status_code = response.status_code
        print("  Status:", status_code)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            html_title = get_page_title(soup)
            html_subtitle = get_page_subtitle(soup)
            html_date = get_page_date(soup)
            html_author = get_page_author(soup)

            print("  HTML title:", html_title[:80])

    except requests.exceptions.RequestException as e:
        print("  ERROR:", str(e)[:100])

    json_title = row.get("title", "")
    json_subtitle = row.get("subtitle", "")
    json_date = row.get("date", "")
    json_author = row.get("author", "")

    results.append({
        "link": url,
        "status_code": status_code,

        "json_title": json_title,
        "html_title": html_title,
        "title_match": yes_no_match(json_title, html_title),

        "json_subtitle": json_subtitle,
        "html_subtitle": html_subtitle,
        "subtitle_match": yes_no_match(json_subtitle, html_subtitle),

        "json_date": json_date,
        "html_date": html_date,
        "date_match": yes_no_match(json_date, html_date),

        "json_author": json_author,
        "html_author": html_author,
        "author_match": yes_no_match(json_author, html_author)
    })

    time.sleep(DELAY_SECONDS)

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    fieldnames = [
        "link",
        "status_code",
        "json_title",
        "html_title",
        "title_match",
        "json_subtitle",
        "html_subtitle",
        "subtitle_match",
        "json_date",
        "html_date",
        "date_match",
        "json_author",
        "html_author",
        "author_match"
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print(f"\nSaved to {OUTPUT_FILE}")

title_yes = sum(1 for row in results if row["title_match"] == "yes")
subtitle_yes = sum(1 for row in results if row["subtitle_match"] == "yes")
date_yes = sum(1 for row in results if row["date_match"] == "yes")
author_yes = sum(1 for row in results if row["author_match"] == "yes")

print("\nSUMMARY")
print(f"Title matches:    {title_yes} / {len(results)}")
print(f"Subtitle matches: {subtitle_yes} / {len(results)}")
print(f"Date matches:     {date_yes} / {len(results)}")
print(f"Author matches:   {author_yes} / {len(results)}")
print("Done.")