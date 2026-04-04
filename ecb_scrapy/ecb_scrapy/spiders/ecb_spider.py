# ============================================================
# FILE: ecb_spider.py
# THE SCRAPY SPIDER — FOR PRESS RELEASES
#
# WHAT IS A SPIDER?
# A Spider is a class that defines:
#   1. Where to start crawling (start_requests)
#   2. How to extract data from each page (parse method)
#
# WHAT THIS SPIDER DOES:
# 1. Reads press release URLs from the CSV created by
#    01c_press_json_requests.py
# 2. Sends a request to each HTML URL
# 3. Extracts the full article text from each page
# 4. Yields an Item (which the Pipeline saves to CSV)
#
# WHY SCRAPY FOR PRESS RELEASES?
# The project uses Selenium for speeches and Scrapy for
# press releases. This shows we can use both tools on
# different content types, which is more interesting
# than using them for the same thing.
#
# HOW TO RUN:
# From the ecb_scrapy/ folder, run:
#   scrapy crawl ecb_press
#
# DEFENSE QUESTION: "What is a Scrapy Spider?"
# ANSWER: A Spider tells Scrapy what pages to visit and
# how to extract data from them. The parse() method is
# called automatically for every downloaded page.
# ============================================================

import scrapy
import csv
import os
from ecb_scrapy.items import EcbArticleItem


class EcbPressSpider(scrapy.Spider):
    """
    Spider that crawls ECB press release pages to extract
    their full text content.
    """

    # Name used to run the spider: scrapy crawl ecb_press
    name = "ecb_press"

    # Scrapy will only visit pages on this domain
    allowed_domains = ["ecb.europa.eu"]

    def start_requests(self):
        """
        Reads press release URLs from the CSV file created
        by 01c_press_json_requests.py.

        This method is called once when the spider starts.
        It yields one Request per press release URL.
        """
        # Path to the CSV (relative to ecb_scrapy/ folder)
        csv_path = os.path.join("..", "data", "ecb_press_releases_json.csv")

        if not os.path.exists(csv_path):
            self.logger.error(f"CSV not found at {csv_path}")
            self.logger.error("Run 01c_press_json_requests.py first!")
            return

        # Read all press release rows from CSV
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            articles = list(reader)

        self.logger.info(f"Loaded {len(articles)} press releases from CSV")

        # Keep only HTML links (skip PDFs — Scrapy can't parse them)
        html_articles = [
            a for a in articles
            if a.get("link_type", "") == "html" and a.get("link", "")
        ]
        self.logger.info(f"HTML press releases to crawl: {len(html_articles)}")

        # Yield a Scrapy Request for each press release
        for article in html_articles:
            yield scrapy.Request(
                url=article["link"],
                callback=self.parse,
                # cb_kwargs passes metadata to the parse method
                cb_kwargs={
                    "doc_type": article.get("doc_type", "press_release"),
                    "title":    article.get("title", ""),
                    "date":     article.get("date", ""),
                    "year":     article.get("year", ""),
                },
            )

    def parse(self, response, doc_type="", title="", date="", year=""):
        """
        Called for each downloaded press release page.
        Extracts the full text and yields an Item.

        DEFENSE QUESTION: "What does parse() do?"
        ANSWER: parse() is called automatically by Scrapy
        for every page it downloads. It receives the HTTP
        response and extracts the data we need.
        """
        # --- EXTRACT ARTICLE TEXT ---
        # Try multiple CSS selectors for different page layouts
        full_text = ""

        # Try 1: <article> tag (most ECB pages use this)
        article_text = response.css("article ::text").getall()
        if article_text:
            full_text = " ".join(article_text).strip()

        # Try 2: div.section
        if len(full_text) < 50:
            section_text = response.css("div.section ::text").getall()
            if section_text:
                full_text = " ".join(section_text).strip()

        # Try 3: main tag
        if len(full_text) < 50:
            main_text = response.css("main ::text").getall()
            if main_text:
                full_text = " ".join(main_text).strip()

        # Try 4: all paragraphs (fallback)
        if len(full_text) < 50:
            p_text = response.css("p ::text").getall()
            if p_text:
                full_text = " ".join(p_text).strip()

        # Clean up whitespace
        full_text = " ".join(full_text.split())

        # Log progress
        if len(full_text) > 50:
            self.logger.info(
                f"OK ({len(full_text)} chars): {response.url[:70]}"
            )
        else:
            self.logger.warning(f"No text: {response.url[:70]}")

        # --- YIELD THE ITEM ---
        # The Pipeline (pipelines.py) saves this to CSV
        item = EcbArticleItem()
        item["doc_type"]  = doc_type
        item["title"]     = title
        item["date"]      = date
        item["year"]      = year
        item["link"]      = response.url
        item["full_text"] = full_text

        yield item
