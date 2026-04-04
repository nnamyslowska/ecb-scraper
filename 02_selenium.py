# ============================================================
# FILE: 02_selenium.py
# STEP 2 — SELENIUM FOR SPEECH FULL TEXT
#
# WHAT THIS FILE DOES:
# Reads speech URLs from data/ecb_speeches_json.csv,
# opens each HTML page in a headless Chrome browser,
# and extracts the full speech text.
#
# WHY SELENIUM?
# Selenium controls a real web browser (Chrome). It can
# render JavaScript content. This demonstrates browser
# automation skills required for the course.
#
# FALLBACK:
# If Selenium's element selectors fail, we fall back to
# parsing the page source with BeautifulSoup. This is
# more robust because some ECB pages have unusual HTML.
#
# INPUT:  data/ecb_speeches_json.csv (from Step 1)
# OUTPUT: data/ecb_speeches_full_text.csv
# ============================================================

import csv
import os
import time
import re
from bs4 import BeautifulSoup
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

INPUT_FILE = "data/ecb_speeches_json.csv"
OUTPUT_FILE = "data/ecb_speeches_full_text.csv"

# Polite delay (ECB robots.txt: Crawl-delay: 5)
DELAY_SECONDS = 5

# Set to a small number for testing, None for ALL
MAX_ARTICLES = None

# Page load timeout
PAGE_TIMEOUT = 20

# Minimum characters for a valid speech text
# A real speech is thousands of characters.
# 124 chars = just page boilerplate, not real content.
MIN_TEXT_LENGTH = 500

# Save every N articles (crash protection)
SAVE_EVERY = 10

os.makedirs("data", exist_ok=True)


# ============================================================
# STEP 1: READ SPEECH URLS
# ============================================================

print("=" * 60)
print("ECB SPEECH FULL TEXT EXTRACTOR (Selenium)")
print("=" * 60)

print(f"\nReading speech URLs from {INPUT_FILE}")

articles = []
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        articles.append(row)

print(f"Loaded {len(articles)} speeches")

# Keep only HTML links
html_articles = [a for a in articles if a.get("link_type", "") == "html"]
print(f"Speeches with HTML pages: {len(html_articles)}")

if MAX_ARTICLES is not None:
    html_articles = html_articles[:MAX_ARTICLES]
    print(f"Limited to first {MAX_ARTICLES} (for testing)")


# ============================================================
# STEP 2: SET UP HEADLESS CHROME
# ============================================================

print("\nSetting up headless Chrome browser...")

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.set_page_load_timeout(PAGE_TIMEOUT)

print("Browser ready!\n")


# ============================================================
# STEP 3: TEXT EXTRACTION FUNCTIONS
# ============================================================

def extract_with_selenium(driver):
    """
    Try to extract text using Selenium's element selectors.
    Returns text if found, empty string otherwise.
    """
    # CSS selectors to try, from most specific to most general
    selectors = [
        "div.section",          # ECB main content area
        "article",              # HTML5 article element
        "div.content-box",      # ECB content wrapper
        "main",                 # HTML5 main element
    ]

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                text = elements[0].text.strip()
                if len(text) >= MIN_TEXT_LENGTH:
                    return text
        except Exception:
            continue

    return ""


def extract_with_beautifulsoup(page_source):
    """
    FALLBACK: Parse the page source with BeautifulSoup.
    This is more reliable than Selenium's element selectors
    for some ECB page layouts.
    """
    soup = BeautifulSoup(page_source, "html.parser")

    # --- TRY 1: Find the main content section ---
    # ECB speeches typically have content in div.section
    section = soup.find("div", class_="section")
    if section:
        # Remove script and style tags (they contain code, not text)
        for tag in section.find_all(["script", "style"]):
            tag.decompose()

        text = section.get_text(separator="\n", strip=True)
        if len(text) >= MIN_TEXT_LENGTH:
            return text

    # --- TRY 2: Find the article tag ---
    article = soup.find("article")
    if article:
        for tag in article.find_all(["script", "style"]):
            tag.decompose()

        text = article.get_text(separator="\n", strip=True)
        if len(text) >= MIN_TEXT_LENGTH:
            return text

    # --- TRY 3: Find main tag ---
    main = soup.find("main")
    if main:
        for tag in main.find_all(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        text = main.get_text(separator="\n", strip=True)
        if len(text) >= MIN_TEXT_LENGTH:
            return text

    # --- TRY 4: Collect all <p> tags ---
    paragraphs = soup.find_all("p")
    if paragraphs:
        text = "\n".join(
            p.get_text(strip=True) for p in paragraphs
            if p.get_text(strip=True)
        )
        if len(text) >= MIN_TEXT_LENGTH:
            return text

    return ""


# ============================================================
# STEP 4: VISIT EACH SPEECH PAGE
# ============================================================

results = []
already_done = set()

# Resume: load previously scraped URLs if output exists
if os.path.exists(OUTPUT_FILE):
    print("Found existing output — resuming...")
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
            already_done.add(row["link"])
    print(f"  Previously scraped: {len(results)} speeches")

remaining = [a for a in html_articles if a["link"] not in already_done]
print(f"Speeches to scrape now: {len(remaining)}")

fieldnames = ["doc_type", "title", "subtitle", "date", "year",
              "author", "boardmember", "link", "full_text"]

for i, article in enumerate(remaining):
    url = article["link"]
    print(f"\n[{i+1}/{len(remaining)}] {url[:80]}...")

    full_text = ""

    try:
        # Navigate to the page
        driver.get(url)

        # Wait for the body to load
        WebDriverWait(driver, PAGE_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Give the page extra time to finish rendering
        time.sleep(3)

        # --- ATTEMPT 1: Selenium selectors ---
        full_text = extract_with_selenium(driver)

        # --- ATTEMPT 2: BeautifulSoup fallback ---
        if len(full_text) < MIN_TEXT_LENGTH:
            page_source = driver.page_source
            full_text = extract_with_beautifulsoup(page_source)

        # Clean up whitespace
        full_text = re.sub(r'\s+', ' ', full_text).strip()

        if len(full_text) >= MIN_TEXT_LENGTH:
            print(f"  OK — {len(full_text)} characters")
        else:
            print(f"  SHORT — only {len(full_text)} chars (might be a redirect or empty page)")

    except Exception as e:
        print(f"  ERROR — {str(e)[:100]}")
        full_text = ""

    results.append({
        "doc_type":     "speech",
        "title":        article.get("title", ""),
        "subtitle":     article.get("subtitle", ""),
        "date":         article.get("date", ""),
        "year":         article.get("year", ""),
        "author":       article.get("author", ""),
        "boardmember":  article.get("boardmember", ""),
        "link":         url,
        "full_text":    full_text,
    })

    # Save progress periodically
    if (i + 1) % SAVE_EVERY == 0:
        print(f"  --- Saving progress ({len(results)} speeches) ---")
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

    time.sleep(DELAY_SECONDS)


# ============================================================
# STEP 5: SAVE FINAL RESULTS
# ============================================================

print("\n\nSaving final results...")

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

driver.quit()

total = len(results)
with_text = sum(1 for r in results if len(r.get("full_text", "")) >= MIN_TEXT_LENGTH)

print(f"\n{'='*60}")
print(f"SELENIUM SCRAPING COMPLETE")
print(f"{'='*60}")
print(f"Total speeches: {total}")
print(f"  With full text (>={MIN_TEXT_LENGTH} chars): {with_text}")
print(f"  Short or empty:  {total - with_text}")
print(f"Saved to: {OUTPUT_FILE}")
print(f"\nNext: run Scrapy for press releases (Step 3)")