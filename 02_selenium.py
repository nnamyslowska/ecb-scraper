# ============================================================
# FILE: 02_selenium.py
# STEP 2 of the ECB Web Scraping Project
#
# WHAT THIS FILE DOES:
# Reads the article URLs from Step 1 (data/ecb_articles.csv),
# opens each page in a headless Chrome browser using Selenium,
# and extracts the full article text.
#
# WHY SELENIUM?
# Selenium controls a real web browser (Chrome). This means
# it can see content that JavaScript generates — unlike
# requests, which only gets the raw HTML skeleton. While many
# ECB article pages are static HTML, using Selenium ensures
# we get everything and demonstrates browser automation.
#
# WHAT IS HEADLESS MODE?
# The browser runs invisibly in the background (no window
# pops up). This is faster and works on servers.
#
# POLITE SCRAPING:
# ECB's robots.txt specifies Crawl-delay: 5, so we wait
# 5 seconds between each page visit.
#
# LIBRARIES USED:
# - selenium: controls the Chrome browser
# - webdriver-manager: automatically downloads the right
#   ChromeDriver version (no manual setup needed)
# - csv: reads input CSV and writes output CSV
# - time: adds delays between requests
# - os: file/folder operations
#
# INPUT:  data/ecb_articles.csv (from Step 1)
# OUTPUT: data/ecb_full_text.csv
# ============================================================

import csv
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "data/ecb_articles.csv"
OUTPUT_FILE = "data/ecb_full_text.csv"

# How many seconds to wait between page visits (polite scraping)
DELAY_SECONDS = 5

# Maximum articles to scrape (set to None for ALL articles)
# Start with a small number to test, then set to None for full run
MAX_ARTICLES = None

# How many seconds to wait for a page to load before giving up
PAGE_TIMEOUT = 15

# Save progress every N articles (in case of crashes)
SAVE_EVERY = 10

os.makedirs("data", exist_ok=True)


# ============================================================
# STEP 1: READ ARTICLE URLS FROM THE CSV
# ============================================================

print("Reading article URLs from", INPUT_FILE)

articles = []
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        articles.append(row)

print(f"Loaded {len(articles)} articles")

# Filter out PDF links (Selenium cannot extract text from PDFs)
articles = [a for a in articles if not a["link"].endswith(".pdf")]
print(f"After removing PDFs: {len(articles)} articles")

# Apply the limit if set
if MAX_ARTICLES is not None:
    articles = articles[:MAX_ARTICLES]
    print(f"Limited to first {MAX_ARTICLES} articles (for testing)")


# ============================================================
# STEP 2: SET UP THE CHROME BROWSER (headless)
# ============================================================

print("\nSetting up headless Chrome browser...")

# Chrome options: headless means no visible window
chrome_options = Options()
chrome_options.add_argument("--headless")           # no visible browser
chrome_options.add_argument("--no-sandbox")          # needed on some systems
chrome_options.add_argument("--disable-gpu")         # disable GPU (not needed)
chrome_options.add_argument("--window-size=1920,1080")  # virtual screen size
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# webdriver-manager automatically downloads the correct ChromeDriver
service = Service(ChromeDriverManager().install())

# Create the browser instance
driver = webdriver.Chrome(service=service, options=chrome_options)

# Set a timeout for page loading
driver.set_page_load_timeout(PAGE_TIMEOUT)

print("Browser ready!\n")


# ============================================================
# STEP 3: VISIT EACH ARTICLE AND EXTRACT FULL TEXT
# ============================================================

def extract_article_text(driver):
    """
    Extracts the main article text from the current page.
    Tries multiple CSS selectors because different ECB page
    types have slightly different HTML structures.

    Returns:
        str: the article text, or empty string if nothing found
    """
    # List of CSS selectors to try, in order of preference.
    # We stop at the first one that returns substantial text.
    selectors_to_try = [
        "article",                  # HTML5 article element
        "div.section",              # ECB uses this for main content
        "div.content-box",          # another ECB content wrapper
        "main",                     # HTML5 main element
        "div#main-wrapper",         # fallback wrapper
    ]

    for selector in selectors_to_try:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                text = elements[0].text.strip()
                # Only accept if we got meaningful text (more than 50 chars)
                if len(text) > 50:
                    return text
        except Exception:
            continue

    # FALLBACK: if no selector worked, grab all paragraph text
    try:
        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        text = "\n".join([p.text for p in paragraphs if p.text.strip()])
        if len(text) > 50:
            return text
    except Exception:
        pass

    return ""


# This list will store our results
results = []

# Track which URLs we've already processed (for resuming)
already_done = set()

# If the output file already exists, load previously scraped URLs
# This lets us resume if the script was interrupted
if os.path.exists(OUTPUT_FILE):
    print("Found existing output file — loading previous results...")
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
            already_done.add(row["link"])
    print(f"  Loaded {len(results)} previously scraped articles")

# Count how many articles we need to scrape
remaining = [a for a in articles if a["link"] not in already_done]
print(f"Articles to scrape: {len(remaining)}")

# --- MAIN LOOP: Visit each article page ---
for i, article in enumerate(remaining):
    url = article["link"]

    print(f"[{i+1}/{len(remaining)}] {url[:80]}...")

    full_text = ""

    try:
        # Navigate to the article page
        driver.get(url)

        # Wait for the page body to load
        WebDriverWait(driver, PAGE_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Give the page a moment to finish rendering
        time.sleep(2)

        # Extract the article text
        full_text = extract_article_text(driver)

        if full_text:
            print(f"  OK — extracted {len(full_text)} characters")
        else:
            print(f"  WARNING — no text extracted")

    except Exception as e:
        print(f"  ERROR — {str(e)[:100]}")
        full_text = ""

    # Add result to our list
    results.append({
        "doc_type":  article.get("doc_type", ""),
        "title":     article.get("title", ""),
        "date":      article.get("date", ""),
        "year":      article.get("year", ""),
        "link":      url,
        "full_text": full_text,
    })

    # Save progress periodically (every SAVE_EVERY articles)
    if (i + 1) % SAVE_EVERY == 0:
        print(f"  Saving progress ({len(results)} articles so far)...")
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["doc_type", "title", "date", "year", "link", "full_text"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

    # Wait before the next request (polite scraping)
    time.sleep(DELAY_SECONDS)


# ============================================================
# STEP 4: SAVE FINAL RESULTS
# ============================================================

print("\nSaving final results...")

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    fieldnames = ["doc_type", "title", "date", "year", "link", "full_text"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

# Close the browser
driver.quit()

# Print summary
total = len(results)
with_text = sum(1 for r in results if r["full_text"])
without_text = total - with_text

print(f"\n{'='*60}")
print(f"SELENIUM SCRAPING COMPLETE")
print(f"{'='*60}")
print(f"Total articles processed: {total}")
print(f"  With text extracted:    {with_text}")
print(f"  Without text (errors):  {without_text}")
print(f"Saved to: {OUTPUT_FILE}")
print(f"\nNext: run the Scrapy spider (Step 3) or go to analysis (Step 4).")
