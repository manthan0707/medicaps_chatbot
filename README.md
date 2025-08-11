
Medicaps Chatbot — Complete

Overview
--------
This project provides a responsive web chatbot that scrapes Medicaps University site for live placement, admission, and about information. It includes a fallback FAQ, optional OpenAI enrichment, and uses Selenium (headless Chrome) with explicit waits to handle JavaScript-loaded pages.

Files
-----
- app.py                : Flask backend (Selenium scrapers + chat endpoints)
- templates/index.html  : Frontend UI (Bootstrap)
- static/css/style.css  : Styles
- static/js/script.js   : Frontend JS
- faqs.json             : Local fallback FAQ data
- requirements.txt      : Python dependencies
- render.yaml           : Render blueprint
- README.md             : This file

Setup (local)
-------------
1. Create & activate virtualenv:
   python3 -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate    # Windows PowerShell

2. Install packages:
   pip install -r requirements.txt

3. Download ChromeDriver that matches your Chrome browser version:
   https://chromedriver.chromium.org/downloads
   - Place the executable in your PATH or set CHROMEDRIVER_PATH to its full path:
     export CHROMEDRIVER_PATH="/home/user/chromedriver"   # Linux/Mac
     $env:CHROMEDRIVER_PATH = "C:\tools\chromedriver.exe"  # Windows PowerShell

4. (Optional) Set OpenAI API key to enable AI-enriched replies:
   export OPENAI_API_KEY="sk-..."

5. Run:
   python app.py
   Open http://127.0.0.1:5000/

Notes
-----
- The scraper uses explicit waits to improve stability, but site structure changes may still require selector updates.
- For production deployment, consider Playwright or a hosted browser solution that provides headless Chrome; Selenium+ChromeDriver requires extra server configuration.
- Respect the target site's terms of service and use caching to reduce load on the site.

