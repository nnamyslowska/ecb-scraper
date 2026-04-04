# ============================================================
# FILE: ecb_spider.py
# THE SCRAPY SPIDER
#
# WHAT IS A SPIDER?
# A Spider is a class that defines:
#   1. Where to start crawling (start_urls or start_requests)
#   2. How to extract data from each page (parse method)
#
# WHAT THIS SPIDER DOES:
# 1. Reads article URLs from the CSV created in Step 1
# 2. Sends a request to each URL
# 3. Extracts the full article text from each page
# 4. Yields an Item (which the Pipeline saves to CSV)
#
# HOW TO RUN:
# From the ecb_scrapy/ folder, run:
#   scrapy crawl ecb_articles
#
# DEFENSE QUESTION: "What is a Scrapy Spider?"
# ANSWER: A Spider is a class that tells Scrapy what pages
# to visit and how to extract data from them. The parse()
# method is called for every page response.
# ============================================================

import scrapy
import csv
import os
from ecb_scrapy.items import EcbArticleItem


class EcbArticleSpider(scrapy.Spider):
    """
    Spider that crawls ECB article pages to extract full text.
    It reads URLs from the CSV file created by Step 1.
    """

    # Name used to run the spider: scrapy crawl ecb_articles
    name = "ecb_articles"

    # Allowed domains — Scrapy will only visit these domains
    allowed_domains = ["ecb.europa.eu"]

    def start_requests(self):
        """
        Instead of hard-coding URLs, we read them from our CSV.
        This method is called once when the spider starts.
        It yields one Request object per article URL.
        """
        # Path to the CSV from Step 1 (relative to where scrapy is run)
        csv_path = os.path.join("..", "data", "ecb_articles.csv")

        # Check if the CSV exists
        if not os.path.exists(csv_path):
            self.logger.error(f"CSV not found at {csv_path}")
            self.logger.error("Run 01_request_BS.py first!")
            return

        # Read URLs from the CSV
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            articles = list(reader)

        self.logger.info(f"Loaded {len(articles)} articles from CSV")

        # Filter out PDF links (we can only parse HTML pages)
        articles = [a for a in articles if not a["link"].endswith(".pdf")]

        # Yield a request for each article
        for article in articles:
            yield scrapy.Request(
                url=article["link"],
                callback=self.parse,
                # Pass article metadata along with the request
                # so we can include it in the output
                cb_kwargs={
                    "doc_type": article.get("doc_type", ""),
                    "title":    article.get("title", ""),
                    "date":     article.get("date", ""),
                    "year":     article.get("year", ""),
                },
            )

    def parse(self, response, doc_type="", title="", date="", year=""):
        """
        Called for each page response. Extracts the article text
        and yields an Item.

        Parameters:
            response: the HTTP response from Scrapy
            doc_type, title, date, year: metadata passed via cb_kwargs
        """
        # --- EXTRACT ARTICLE TEXT ---
        # Try multiple CSS selectors (different page layouts)
        full_text = ""

        # Try 1: <article> tag
        article_elements = response.css("article ::text").getall()
        if article_elements:
            full_text = " ".join(article_elements).strip()

        # Try 2: div.section
        if len(full_text) < 50:
            section_elements = response.css("div.section ::text").getall()
            if section_elements:
                full_text = " ".join(section_elements).strip()

        # Try 3: main tag
        if len(full_text) < 50:
            main_elements = response.css("main ::text").getall()
            if main_elements:
                full_text = " ".join(main_elements).strip()

        # Try 4: all paragraphs (fallback)
        if len(full_text) < 50:
            p_elements = response.css("p ::text").getall()
            if p_elements:
                full_text = " ".join(p_elements).strip()

        # Clean up extra whitespace
        full_text = " ".join(full_text.split())

        # Log progress
        text_length = len(full_text)
        if text_length > 50:
            self.logger.info(f"OK ({text_length} chars): {response.url[:70]}")
        else:
            self.logger.warning(f"No text: {response.url[:70]}")

        # --- YIELD THE ITEM ---
        # The Pipeline will save this to CSV
        item = EcbArticleItem()
        item["doc_type"]  = doc_type
        item["title"]     = title
        item["date"]      = date
        item["year"]      = year
        item["link"]      = response.url
        item["full_text"] = full_text

        yield item
