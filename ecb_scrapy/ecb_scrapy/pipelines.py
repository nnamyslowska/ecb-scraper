# ============================================================
# FILE: pipelines.py
# WHAT IS A SCRAPY PIPELINE?
# A Pipeline processes each Item after the spider scrapes it.
# It's like an assembly line: the spider finds the data,
# then the pipeline does something with it (save to CSV,
# clean it, store in a database, etc.)
#
# Our pipeline saves each scraped article to a CSV file.
#
# DEFENSE QUESTION: "What is a Scrapy Pipeline?"
# ANSWER: A pipeline is a class that processes items after
# they are scraped. It runs automatically for every item
# the spider yields. We use it to save data to CSV.
# ============================================================

import csv
import os


class CsvPipeline:
    """
    Saves each scraped item to a CSV file.
    - open_spider() runs once when the spider starts
    - process_item() runs for every item the spider yields
    - close_spider() runs once when the spider finishes
    """

    def open_spider(self, spider):
        """
        Called when the spider starts.
        Opens the CSV file and writes the header row.
        """
        # Create data folder if needed
        os.makedirs("data", exist_ok=True)

        self.filepath = "data/ecb_scrapy_output.csv"
        self.file = open(self.filepath, "w", newline="", encoding="utf-8")

        self.fieldnames = ["doc_type", "title", "date", "year", "link", "full_text"]
        self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames)
        self.writer.writeheader()

        self.count = 0
        spider.logger.info(f"Pipeline opened: {self.filepath}")

    def process_item(self, item, spider):
        """
        Called for every item the spider yields.
        Writes one row to the CSV file.
        """
        # Convert Scrapy Item to a regular dictionary
        row = {
            "doc_type":  item.get("doc_type", ""),
            "title":     item.get("title", ""),
            "date":      item.get("date", ""),
            "year":      item.get("year", ""),
            "link":      item.get("link", ""),
            "full_text": item.get("full_text", ""),
        }
        self.writer.writerow(row)
        self.count += 1

        # Return the item so other pipelines can also process it
        return item

    def close_spider(self, spider):
        """
        Called when the spider finishes.
        Closes the CSV file and prints a summary.
        """
        self.file.close()
        spider.logger.info(f"Pipeline closed. Saved {self.count} articles to {self.filepath}")
