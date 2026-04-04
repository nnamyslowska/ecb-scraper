# ============================================================
# FILE: settings.py
# SCRAPY CONFIGURATION
#
# This file controls how Scrapy behaves: how fast it crawls,
# what user agent it sends, which pipelines process items, etc.
#
# DEFENSE QUESTION: "Why is DOWNLOAD_DELAY important?"
# ANSWER: It makes our scraper polite by waiting between
# requests. ECB's robots.txt says Crawl-delay: 5, so we
# respect that to avoid overloading their server.
# ============================================================

# Name of the Scrapy project
BOT_NAME = "ecb_scrapy"

# Where to find our spiders
SPIDER_MODULES = ["ecb_scrapy.spiders"]
NEWSPIDER_MODULE = "ecb_scrapy.spiders"

# Identify ourselves as a polite academic scraper
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Wait 5 seconds between requests (as per ECB robots.txt)
DOWNLOAD_DELAY = 5

# Only send 1 request at a time (polite scraping)
CONCURRENT_REQUESTS = 1

# Enable our CSV pipeline
ITEM_PIPELINES = {
    "ecb_scrapy.pipelines.CsvPipeline": 300,
    # The number 300 is the priority (lower = runs first)
}

# Disable cookies (not needed for public pages)
COOKIES_ENABLED = False

# Set a timeout for page downloads (in seconds)
DOWNLOAD_TIMEOUT = 30

# Log level: INFO shows progress without too much detail
LOG_LEVEL = "INFO"

# Disable Scrapy's built-in telnet console (not needed)
TELNETCONSOLE_ENABLED = False

# Set default request headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en",
}
