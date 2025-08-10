
Medicaps University Chatbot (Enhanced)

This package includes:
- Live web-scraping for placements, admissions, and about sections
- Expanded FAQs (fallback)
- Optional OpenAI integration (set OPENAI_API_KEY to enable)
- Responsive, attractive UI with quick links and dark mode
- render.yaml for Render deployment

Run locally:
1. unzip
2. python -m venv venv
3. source venv/bin/activate   # or venv\Scripts\activate on Windows
4. pip install -r requirements.txt
5. python app.py
6. Open http://127.0.0.1:5000/

Deploy to Render:
- Push to GitHub and connect repo to Render (use render.yaml blueprint)
- Set OPENAI_API_KEY in Render environment if you want AI responses
- Set CACHE_TTL_SECONDS to control scrape caching
