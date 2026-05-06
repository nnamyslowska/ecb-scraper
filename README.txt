README - ECB web scraping project
===================================
Name: Natalia Namysłowska

PROJECT DESCRIPTION
--------------------
This project scrapes the European Central Bank (ECB) website to analyse how ECB communication about artificial intelligence, digital finance, and monetary policy has evolved from 1997 to 2026.

Two ECB content types are scraped:
- Speeches (collected via JSON dataset + full text via Selenium)
- Press releases (collected via JSON dataset + full text via Scrapy)

The project demonstrates familiarity with:
- requests and BeautifulSoup
- Selenium (speech full text extraction)
- Scrapy (press release full text extraction)
- Python regular expressions (keyword analysis)

The final output is a structured dataframe with scraped ECB documents, enriched with regex-based topic classification.

FILES AND RUN ORDER
--------------------
Run the files in this order:

1. 01_requests_json.py
    - Uses: requests + Selenium (for metadata endpoint discovery)
    - Automatically detects the current ECB metadata dataset URL
    - Downloads speech and press release metadata from the ECB JSON dataset
    - Filters speeches and press releases from 1997-2026
    - Output:
      data/ecb_speeches_json.csv
      data/ecb_press_releases_json.csv

2. 02_selenium.py
    - Uses: Selenium + BeautifulSoup
    - Reads speech URLs from data/ecb_speeches_json.csv
    - Visits each speech HTML page and extracts full text
    - Uses BeautifulSoup as a fallback parser if Selenium selectors return too little text
    - Output: data/ecb_speeches_full_text.csv
    - Note: Takes time due to 5-second delay per page.

3.  ecb_scrapy/
    - Uses: Scrapy framework (spider, items, pipeline)
    - Run from the ecb_scrapy/ folder with: scrapy crawl ecb_press
    - Crawls press release HTML pages using Scrapy
    - Output: data/ecb_scrapy_output.csv

4.  04_analysis.ipynb
    - Uses: pandas, re (regex), matplotlib
    - Loads speech and press release data
    - Applies regex for AI, digital finance, monetary policy mentions
    - Creates charts and final dataframe
    - Output: data/ecb_final_dataset.csv

HOW TO SET UP THE ENVIRONMENT
-------------------------------
1. Create a virtual environment:   python -m venv venv
2. Activate it:                    venv\Scripts\activate
3. Install packages:               pip install -r requirements.txt
4. Run scripts in order: 01, 02, ecb_scrapy/ , 04

For the Scrapy spider:
   cd ecb_scrapy
   scrapy crawl ecb_press
   cd ..

OTHER FILES
------------
- legal_proof.txt    - Proof that scraping ECB is legal
- requirements.txt   - List of all Python packages used
- README.txt         - This file
- discover_types.py  - Helper script to find ECB publication type IDs
- data/              - Output folder (created by the scripts)

DATA LINK
----------
GitHub: https://github.com/nnamyslowska/ecb-scraper
Google Drive: https://drive.google.com/drive/folders/1iPdb4PMB6AjEAp6MaGfwAU3u2Xs-vnj-?usp=sharing