# Scrapy spider to extract full text from ECB press release pages.
# 1. Reads press release URLs from the CSV created by 01_json_requests.py
# 2. Sends one Scrapy request per HTML page
# 3. Extracts the full text from each press release
# 4. Yields an item that the pipeline saves to CSV

import scrapy
import csv
import os
from ecb_scrapy.items import EcbArticleItem


class EcbPressSpider(scrapy.Spider):
    name = "ecb_press"
    allowed_domains = ["ecb.europa.eu"]

    def start_requests(self):
        """
        Read press release URLs from the Step 1 CSV
        and send one request per HTML link.
        """
        csv_path = os.path.join("..", "data", "ecb_press_releases_json.csv")

        if not os.path.exists(csv_path):
            self.logger.error(f"CSV not found: {csv_path}")
            self.logger.error("Run 01_json_requests.py first.")
            return

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            articles = list(reader)

        self.logger.info(f"Loaded {len(articles)} press releases from CSV")

        html_articles = [
            article for article in articles
            if article.get("link_type", "") == "html" and article.get("link", "")
        ]

        self.logger.info(f"HTML press releases to crawl: {len(html_articles)}")

        for article in html_articles:
            yield scrapy.Request(
                url=article["link"],
                callback=self.parse,
                cb_kwargs={
                    "doc_type": article.get("doc_type", "press_release"),
                    "title": article.get("title", ""),
                    "date": article.get("date", ""),
                    "year": article.get("year", ""),
                },
            )

    def extract_full_text(self, response):
        """
        Try several page areas and return the first one
        that gives enough text.
        """
        selectors = [
            "article ::text",
            "div.section ::text",
            "main ::text",
            "p::text",
        ]

        for selector in selectors:
            text_parts = response.css(selector).getall()
            cleaned_parts = []

            for part in text_parts:
                part = part.strip()
                if part:
                    cleaned_parts.append(part)

            full_text = " ".join(cleaned_parts)

            if len(full_text) >= 500:
                return full_text

        return ""

    def parse(self, response, doc_type="", title="", date="", year=""):
        """
        Extract full text from one press release page
        and yield the result as an item.
        """
        full_text = self.extract_full_text(response)

        if len(full_text) >= 500:
            self.logger.info(f"OK ({len(full_text)} chars): {response.url[:70]}")
        else:
            self.logger.warning(f"Short or empty text: {response.url[:70]}")

        item = EcbArticleItem()
        item["doc_type"] = doc_type
        item["title"] = title
        item["date"] = date
        item["year"] = year
        item["link"] = response.url
        item["full_text"] = full_text

        yield item