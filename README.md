
Medicaps Chatbot (Selenium - explicit waits)

Files:
- app.py   : Flask app that uses Selenium with explicit waits to scrape live data
- faqs.json         : fallback FAQs
- templates/index.html, static/* : frontend files
- requirements.txt  : Python packages

Steps to run locally:
1. Create and activate a virtualenv:
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate    # Windows PowerShell
2. Install dependencies:
   pip install -r requirements.txt
3. Download Chromedriver matching your Chrome version: https://chromedriver.chromium.org/downloads
   - Put chromedriver executable in PATH or set CHROMEDRIVER_PATH env var to its path.
4. Run:
   export CHROMEDRIVER_PATH="/path/to/chromedriver"   # optional if chromedriver is in PATH
   python app.py
5. Open http://127.0.0.1:5000/ and try queries: placement, admission, about medicaps

Notes:
- Explicit waits (WebDriverWait) are used to make scraping robust against dynamic loading.
- Use CACHE_TTL_SECONDS env var to control scraping frequency (default 300 seconds).
- For heavy usage or cloud deployment, consider Playwright or a server with headless Chrome and driver installed.
