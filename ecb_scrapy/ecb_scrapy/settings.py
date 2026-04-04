BOT_NAME = "ecb_scrapy"
SPIDER_MODULES = ["ecb_scrapy.spiders"]
NEWSPIDER_MODULE = "ecb_scrapy.spiders"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 5
CONCURRENT_REQUESTS = 1

ITEM_PIPELINES = {
    "ecb_scrapy.pipelines.CsvPipeline": 300,
}

COOKIES_ENABLED = False
DOWNLOAD_TIMEOUT = 30
LOG_LEVEL = "INFO"
TELNETCONSOLE_ENABLED = False

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en",
}
