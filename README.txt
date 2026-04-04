README - ECB Web Scraping Project
===================================
Name: Natalia Namyslowska
Course: Web Scraping, WNE UW, Spring 2026
Master's Programme: DSBA, Kozminski University

PROJECT DESCRIPTION
--------------------
This project scrapes the European Central Bank (ECB) website to analyse
how ECB communication about artificial intelligence, digital finance,
and monetary policy has evolved from 2019 to 2026.

The project demonstrates familiarity with:
- requests and BeautifulSoup (Step 1: RSS feeds and archive pages)
- Selenium (Step 2: full text extraction from article pages)
- Scrapy (Step 3: efficient crawling with spider/item/pipeline)
- Python regular expressions (Step 4: keyword analysis)

The final output is a structured dataframe with scraped ECB articles,
enriched with regex-based topic classification.

FILES AND RUN ORDER
--------------------
Run the files in this order:

1. 01_request_BS.py
   - Uses: requests, BeautifulSoup
   - Downloads ECB article listings from index_include pages (2019-2026)
     and RSS feeds
   - Collects article URLs, titles, dates, and descriptions
   - Output: data/ecb_articles.csv

2. 02_selenium.py
   - Uses: Selenium (headless Chrome)
   - Reads URLs from data/ecb_articles.csv
   - Visits each article page and extracts full text
   - Output: data/ecb_full_text.csv
   - Note: Takes several hours for all articles (5s delay per page)
     Set MAX_ARTICLES to a small number (e.g. 50) for testing

3. ecb_scrapy/ (Scrapy project)
   - Uses: Scrapy framework
   - Run from the ecb_scrapy/ folder with: scrapy crawl ecb_articles
   - Crawls article pages using Scrapy's spider/item/pipeline architecture
   - Output: data/ecb_scrapy_output.csv

4. 04_analysis.py (or 04_analysis.ipynb in Jupyter Notebook)
   - Uses: pandas, re (regex), matplotlib
   - Loads scraped data, applies regex patterns for AI/digital/monetary
     mentions, creates analysis charts, saves final dataframe
   - Output: data/ecb_final_dataset.csv
   - Charts: data/chart_ai_by_year.png, data/chart_by_doc_type.png,
     data/chart_topics_over_time.png

HOW TO SET UP THE ENVIRONMENT
-------------------------------
1. Create a virtual environment:   python -m venv venv
2. Activate it:                    venv\Scripts\activate  (Windows)
3. Install packages:               pip install -r requirements.txt
4. Run scripts in order (see above)

For the Scrapy spider:
   cd ecb_scrapy
   scrapy crawl ecb_articles

OTHER FILES
------------
- legal_proof.txt    - Proof that scraping ECB is legal
- requirements.txt   - List of all Python packages used
- README.txt         - This file
- data/              - Folder with output CSV files and charts
                       (created by the scripts)

DATA LINK
----------
If the dataset is too large to include in the ZIP:
Google Drive: [INSERT LINK IF NEEDED]
GitHub: https://github.com/nnamyslowska/ecb-scraper
