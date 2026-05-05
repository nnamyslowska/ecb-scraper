import scrapy

class EcbArticleItem(scrapy.Item):
    """
    Defines the fields we collect for each ECB article.
    """
    doc_type = scrapy.Field()
    title = scrapy.Field()
    date = scrapy.Field()
    year = scrapy.Field()
    link = scrapy.Field()
    full_text = scrapy.Field()
