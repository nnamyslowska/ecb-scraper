import scrapy

class EcbArticleItem(scrapy.Item):
    """
    Defines the fields we collect for each ECB article.
    Each field is like a column in our final CSV.
    """
    doc_type    = scrapy.Field()
    title       = scrapy.Field()
    date        = scrapy.Field()
    year        = scrapy.Field()
    link        = scrapy.Field()
    full_text   = scrapy.Field()
