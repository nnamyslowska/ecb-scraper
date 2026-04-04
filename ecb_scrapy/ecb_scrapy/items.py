# ============================================================
# FILE: items.py
# WHAT IS A SCRAPY ITEM?
# An Item is like a dictionary with pre-defined fields.
# It tells Scrapy what data we want to collect for each
# article. Think of it as a template or schema.
#
# DEFENSE QUESTION: "What is a Scrapy Item?"
# ANSWER: An Item defines the structure of the data we scrape.
# It's like a form with specific fields that every scraped
# page fills in. This makes our data consistent.
# ============================================================

import scrapy


class EcbArticleItem(scrapy.Item):
    """
    Defines the fields we collect for each ECB article.
    Each field is like a column in our final CSV.
    """
    doc_type    = scrapy.Field()  # e.g. "speech", "press_release"
    title       = scrapy.Field()  # article title
    date        = scrapy.Field()  # publication date
    year        = scrapy.Field()  # year (integer)
    link        = scrapy.Field()  # URL of the article
    full_text   = scrapy.Field()  # full article text content
