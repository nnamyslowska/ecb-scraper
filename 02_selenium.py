# Selenium script to extract full text from ECB speech pages.
# 1. Reads speech URLs from the CSV created by 01_json_requests.py
# 2. Opens each HTML page in a headless Chrome browser
# 3. Extracts the full text from each speech
# 4. Saves the results to a CSV file

import csv
import os
import time
import re
import sys
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

max_int = sys.maxsize
while True:
    try:
        csv.field_size_limit(max_int)
        break
    except OverflowError:
        max_int = int(max_int / 10)

INPUT_FILE = "data/ecb_speeches_json.csv"
OUTPUT_FILE = "data/ecb_speeches_full_text.csv"

DELAY_SECONDS = 5
MAX_ARTICLES = None
PAGE_TIMEOUT = 20
MIN_TEXT_LENGTH = 500
SAVE_EVERY = 10

os.makedirs("data", exist_ok=True)


# Reading speech URLs:

print("Reading speech URLs...")

articles = []
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        articles.append(row)

print(f"Loaded {len(articles)} speeches")

html_articles = [row for row in articles if row.get("link_type", "") == "html"]
print(f"Speeches with HTML pages: {len(html_articles)}")

if MAX_ARTICLES is not None:
    html_articles = html_articles[:MAX_ARTICLES]
    print(f"Limited to first {MAX_ARTICLES} speeches")


# Setting up headless Chrome:

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

print("Browser ready!")


# Text extraction functions:

def extract_with_selenium(driver):
    """Try to extract speech text using Selenium selectors."""
    selectors = [
        "div.section",
        "article",
        "div.content-box",
        "main",
    ]

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)

            if not elements:
                continue

            parts = []
            for element in elements:
                text = element.text.strip()
                if text:
                    parts.append(text)

            full_text = " ".join(parts)

            if len(full_text) >= MIN_TEXT_LENGTH:
                return full_text

        except Exception:
            continue

    return ""


def extract_with_beautifulsoup(page_source):
    """Fallback: parse page source with BeautifulSoup.""" # This is more reliable for some ECB page layouts. It can find text even when Selenium's selectors fail. It tries the same areas as Selenium but uses BeautifulSoup's parsing, which can handle more complex HTML structures.
    soup = BeautifulSoup(page_source, "html.parser")

    section = soup.find("div", class_="section")
    if section:
        for tag in section.find_all(["script", "style"]):
            tag.decompose()
        text = section.get_text(separator=" ", strip=True)
        if len(text) >= MIN_TEXT_LENGTH:
            return text

    article = soup.find("article")
    if article:
        for tag in article.find_all(["script", "style"]):
            tag.decompose()
        text = article.get_text(separator=" ", strip=True)
        if len(text) >= MIN_TEXT_LENGTH:
            return text

    main = soup.find("main")
    if main:
        for tag in main.find_all(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        text = main.get_text(separator=" ", strip=True)
        if len(text) >= MIN_TEXT_LENGTH:
            return text

    paragraphs = soup.find_all("p")
    if paragraphs:
        text = " ".join(
            p.get_text(strip=True)
            for p in paragraphs
            if p.get_text(strip=True)
        )
        if len(text) >= MIN_TEXT_LENGTH:
            return text

    return ""


# Loading previous results if they exist:

results = []
already_done = set()

if os.path.exists(OUTPUT_FILE):
    print("\nFound existing output file - resuming...")
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
            already_done.add(row["link"])
    print(f"Previously scraped: {len(results)} speeches")

remaining = [row for row in html_articles if row["link"] not in already_done]
print(f"Speeches to scrape now: {len(remaining)}")

fieldnames = [
    "doc_type",
    "title",
    "subtitle",
    "date",
    "year",
    "author",
    "boardmember",
    "link",
    "full_text"
]


# Visiting each speech page:

for i, article in enumerate(remaining, start=1):
    url = article["link"]
    print(f"\n[{i}/{len(remaining)}] {url[:80]}...")

    full_text = ""

    try:
        driver.get(url)

        WebDriverWait(driver, PAGE_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(3)

        full_text = extract_with_selenium(driver)

        if len(full_text) < MIN_TEXT_LENGTH:
            page_source = driver.page_source
            full_text = extract_with_beautifulsoup(page_source)

        full_text = re.sub(r"\s+", " ", full_text).strip()

        if len(full_text) >= MIN_TEXT_LENGTH:
            print(f"OK - {len(full_text)} characters")
        else:
            print(f"SHORT - only {len(full_text)} characters")

    except Exception as e:
        print(f"ERROR - {str(e)[:100]}")
        full_text = ""

    results.append({
        "doc_type": "speech",
        "title": article.get("title", ""),
        "subtitle": article.get("subtitle", ""),
        "date": article.get("date", ""),
        "year": article.get("year", ""),
        "author": article.get("author", ""),
        "boardmember": article.get("boardmember", ""),
        "link": url,
        "full_text": full_text,
    })

    if i % SAVE_EVERY == 0:
        print(f"Saving progress ({len(results)} speeches)...")
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

    time.sleep(DELAY_SECONDS)


# Saving final results:
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

driver.quit()

total = len(results)
with_text = sum(1 for row in results if len(row.get("full_text", "")) >= MIN_TEXT_LENGTH)

print(f"\nTotal speeches: {total}")
print(f"With full text: {with_text}")
print(f"Short or empty: {total - with_text}")
print(f"Saved to: {OUTPUT_FILE}")