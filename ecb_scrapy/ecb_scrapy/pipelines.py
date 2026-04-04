import csv
import os

class CsvPipeline:
    def open_spider(self, spider):
        os.makedirs("data", exist_ok=True)
        self.filepath = "data/ecb_scrapy_output.csv"
        self.file = open(self.filepath, "w", newline="", encoding="utf-8")
        self.fieldnames = ["doc_type", "title", "date", "year", "link", "full_text"]
        self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames)
        self.writer.writeheader()
        self.count = 0
        spider.logger.info(f"Pipeline opened: {self.filepath}")

    def process_item(self, item, spider):
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
        return item

    def close_spider(self, spider):
        self.file.close()
        spider.logger.info(f"Pipeline closed. Saved {self.count} articles to {self.filepath}")
