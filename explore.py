# ============================================================
# EXPLORATION SCRIPT — run this to find where ECB stores
# its full article lists. We'll check 3 things:
#   1. Does ECB have a sitemap.xml?
#   2. Do year-based archive pages work with requests?
#   3. What HTML structure do the archive pages have?
#
# This is NOT part of the final project — just investigation.
# ============================================================

import requests
from bs4 import BeautifulSoup

# --- CHECK 1: Sitemap ---
print("=" * 60)
print("CHECK 1: Does ECB have a sitemap?")
print("=" * 60)

for url in [
    "https://www.ecb.europa.eu/sitemap.xml",
    "https://www.ecb.europa.eu/robots.txt",
]:
    print(f"\nTrying: {url}")
    r = requests.get(url)
    print(f"  Status: {r.status_code}")
    # Print first 2000 characters to see what's there
    print(f"  Content (first 2000 chars):\n{r.text[:2000]}")
    print()

# --- CHECK 2: Year-based archive pages ---
# ECB often has pages like /press/key/date/2024/html/index.en.html
print("=" * 60)
print("CHECK 2: Year-based archive pages")
print("=" * 60)

archive_patterns = [
    # Speeches
    "https://www.ecb.europa.eu/press/key/date/2024/html/index.en.html",
    # Press releases
    "https://www.ecb.europa.eu/press/pr/date/2024/html/index.en.html",
    # Blog
    "https://www.ecb.europa.eu/press/blog/date/2024/html/index.en.html",
    # Interviews
    "https://www.ecb.europa.eu/press/inter/date/2024/html/index.en.html",
    # Working papers
    "https://www.ecb.europa.eu/pub/research/working-papers/html/index.en.html",
    # Main press page
    "https://www.ecb.europa.eu/press/key/html/index.en.html",
]

for url in archive_patterns:
    print(f"\nTrying: {url}")
    r = requests.get(url)
    print(f"  Status: {r.status_code}")
    print(f"  Content length: {len(r.text)} characters")

    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")

        # Count how many links we find
        all_links = soup.find_all("a", href=True)
        print(f"  Total <a> links found: {len(all_links)}")

        # Look for article-like links
        article_links = [
            a["href"] for a in all_links
            if "/press/" in a["href"] or "/pub/" in a["href"]
        ]
        print(f"  Article-like links: {len(article_links)}")

        # Print first 5 article links as examples
        for link in article_links[:5]:
            print(f"    -> {link}")

        # Check if the page has a specific content div
        # (if it's empty, the content is loaded by JavaScript)
        main_content = soup.find("main") or soup.find("div", class_="content")
        if main_content:
            text_length = len(main_content.get_text(strip=True))
            print(f"  Main content text length: {text_length} chars")
            if text_length < 100:
                print(f"  ⚠ Very little text — probably JS-rendered!")
            else:
                print(f"  ✓ Has content — requests can see it!")

print()
print("=" * 60)
print("CHECK 3: Quick look at the ECB search API")
print("=" * 60)

# Some ECB pages use a JSON API behind the scenes
# Let's check a common pattern
search_urls = [
    "https://www.ecb.europa.eu/press/key/date/2024/html/index_include.en.html",
    "https://www.ecb.europa.eu/press/pr/date/2024/html/index_include.en.html",
]

for url in search_urls:
    print(f"\nTrying: {url}")
    r = requests.get(url)
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        print(f"  Content length: {len(r.text)} chars")
        print(f"  First 1000 chars:\n{r.text[:1000]}")
    print()