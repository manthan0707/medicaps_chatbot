
Medicaps Chatbot (API-style) - FastAPI

Overview
--------
This project provides a simple API-based chatbot for Medicaps University.
It exposes API endpoints and a frontend UI that calls them.

Features
--------
- /chat (POST) : send {'message':'...'} and get {'reply':'...'}
- /api/placements, /api/admissions, /api/about : GET endpoints returning scraped JSON
- Uses requests-based scraping by default; set USE_SELENIUM=1 env var to use Selenium (requires ChromeDriver)

Setup (local)
-------------
1. Create & activate virtualenv:
   python3 -m venv venv
   source venv/bin/activate   # Linux/Mac
2. Install deps:
   pip install -r requirements.txt
3. Run:
   uvicorn app:app --reload --port 8000
   Open http://127.0.0.1:8000/

Using Selenium (optional)
-------------------------
- Install ChromeDriver and set CHROMEDRIVER_PATH if needed.
- Set environment variable USE_SELENIUM=1 before running.
- Selenium requires ChromeDriver binary compatible with installed Chrome.

Notes
-----
- Scraping depends on the target site's structure; if it changes, selectors may need updates.
- Cache TTL: change CACHE_TTL_SECONDS env var (default 300 seconds).
