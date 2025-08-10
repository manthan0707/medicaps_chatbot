
Medicaps University Chatbot (Live scraping + optional OpenAI)

Files in this package:
- app.py            : Flask backend with scraping and optional OpenAI enrichment
- faqs.json         : local fallback FAQs
- templates/index.html  : frontend responsive UI
- static/css/style.css  : styles
- static/js/script.js   : frontend JS
- requirements.txt  : Python dependencies
- render.yaml       : Render blueprint for easy deployment

How to run locally:
1. Unzip the package.
2. (Optional) Create virtual env:
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate    # Windows
3. Install dependencies:
   pip install -r requirements.txt
4. (Optional) Set OPENAI_API_KEY if you want AI-enriched replies:
   export OPENAI_API_KEY='sk-...'
5. Run:
   python app.py
6. Open http://127.0.0.1:5000/

Deploy to Render (quick):
- Create GitHub repo, push code.
- On Render, choose New -> Web Service -> Connect repo
- Render will use render.yaml if you use Blueprint deploy.
- Make sure to set OPENAI_API_KEY env var on Render if you want AI responses.

Notes:
- Scraping depends on the remote site structure and may break if they change layout.
- Cache default is 3600 seconds (1 hour). Change via CACHE_TTL_SECONDS env var.
- This package includes a placeholder for OpenAI integration; add your key as env var to enable.
