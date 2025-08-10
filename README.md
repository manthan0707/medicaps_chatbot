
Medicaps Chatbot (Selenium version)

Files:
- app_selenium.py   : Flask app that uses Selenium to scrape live data
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
   python app_selenium.py
5. Open http://127.0.0.1:5000/ and try queries: placement, admission, about medicaps

Notes:
- Selenium opens a headless browser to render dynamic content; it's best for pages that load data via JavaScript.
- Use CACHE_TTL_SECONDS env var to control caching (default 300 seconds).
- For deployment to cloud, Selenium requires additional setup (browsers, drivers). Local run is recommended for simplicity.
