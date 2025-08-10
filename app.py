
from flask import Flask, render_template, request, jsonify
import os, time, json
import requests
from bs4 import BeautifulSoup

# Optional OpenAI integration (use OPENAI_API_KEY env var)
USE_OPENAI = bool(os.environ.get('OPENAI_API_KEY'))
if USE_OPENAI:
    try:
        import openai
        openai.api_key = os.environ.get('OPENAI_API_KEY')
    except Exception as e:
        print("OpenAI import error:", e)
        USE_OPENAI = False

app = Flask(__name__, static_folder='static', template_folder='templates')

# Load fallback FAQs
with open(os.path.join(app.root_path, 'faqs.json'), 'r', encoding='utf-8') as f:
    FAQS = json.load(f)

# Simple cache
CACHE = {}
CACHE_TTL = int(os.environ.get('CACHE_TTL_SECONDS', 3600))  # default 1 hour

def cached(key, fetch_fn):
    now = time.time()
    if key in CACHE and now - CACHE[key]['ts'] < CACHE_TTL:
        return CACHE[key]['data']
    data = fetch_fn()
    CACHE[key] = {'ts': now, 'data': data}
    return data

# Scrapers
def scrape_placements():
    url = "https://www.medicaps.ac.in/placements"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        parts = []
        for h in soup.select('h1,h2,h3,h4'):
            txt = h.get_text(strip=True)
            if txt:
                nxt = h.find_next(['p','div','span'])
                if nxt:
                    parts.append(f"{txt} - {nxt.get_text(' ',strip=True)[:600]}")
        if not parts:
            for p in soup.select('p')[:8]:
                parts.append(p.get_text(' ',strip=True)[:500])
        rows = []
        table = soup.find('table')
        if table:
            for tr in table.find_all('tr')[1:8]:
                cols = [td.get_text(' ',strip=True) for td in tr.find_all(['td','th'])]
                if cols:
                    rows.append(" | ".join(cols))
        return {'summary': '\n\n'.join(parts)[:4000], 'rows': rows}
    except Exception as e:
        return {'error': str(e)}

def scrape_admissions():
    url = "https://www.medicaps.ac.in/admission-24-25.php"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        parts = []
        for h in soup.select('h2,h3,h4'):
            txt = h.get_text(strip=True)
            if txt:
                nxts = []
                for sib in h.find_next_siblings():
                    if sib.name in ['p','ul','div']:
                        nxts.append(sib.get_text(' ',strip=True)[:400])
                    if len(nxts) >= 3:
                        break
                if nxts:
                    parts.append(f"{txt} - {' '.join(nxts)}")
        if not parts:
            for p in soup.select('p')[:10]:
                parts.append(p.get_text(' ',strip=True)[:400])
        return {'summary': '\n\n'.join(parts)[:4000]}
    except Exception as e:
        return {'error': str(e)}

def scrape_about():
    url = "https://www.medicaps.ac.in/about"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        main = soup.find('main') or soup
        paras = main.select('p')[:10]
        if paras:
            return {'about': ' '.join([p.get_text(' ',strip=True) for p in paras])[:4000]}
        div = soup.find('div', class_=lambda x: x and 'about' in x.lower())
        if div:
            return {'about': div.get_text(' ',strip=True)[:4000]}
        return {'about': soup.get_text(' ',strip=True)[:2000]}
    except Exception as e:
        return {'error': str(e)}

def ai_enrich(user_msg, context_text):
    if not USE_OPENAI:
        return None
    try:
        prompt = f"""You are a helpful assistant for Medicaps University. Use the following context to answer the user's question.

Context:
{context_text}

User question: {user_msg}

Answer concisely."""
        resp = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=[{'role':'user','content':prompt}], max_tokens=300)
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return None

def faq_lookup(msg):
    m = msg.lower()
    for k,v in FAQS.items():
        if k in m:
            return v
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    msg = data.get('message','').strip()
    if not msg:
        return jsonify({'reply':'Please type something.'})

    low = msg.lower()
    if any(w in low for w in ['placement','package','placements','highest','average']):
        d = cached('placements', scrape_placements)
        if 'error' in d:
            base = faq_lookup(low) or "Couldn't fetch live placement data right now."
            return jsonify({'reply': base})
        context = d.get('summary','') + '\n' + '\n'.join(d.get('rows',[]))
        ai = ai_enrich(msg, context)
        if ai:
            return jsonify({'reply': ai})
        return jsonify({'reply': context if context else 'No placement info found.'})

    if any(w in low for w in ['admission','apply','eligibility','deadline','important date','last date']):
        d = cached('admissions', scrape_admissions)
        if 'error' in d:
            base = faq_lookup(low) or "Couldn't fetch admission info right now."
            return jsonify({'reply': base})
        ai = ai_enrich(msg, d.get('summary',''))
        if ai:
            return jsonify({'reply': ai})
        return jsonify({'reply': d.get('summary','No admission info found.')})

    if any(w in low for w in ['about','who are you','overview','university info','about medicaps']):
        d = cached('about', scrape_about)
        if 'error' in d:
            base = faq_lookup(low) or "Couldn't fetch about info right now."
            return jsonify({'reply': base})
        ai = ai_enrich(msg, d.get('about',''))
        if ai:
            return jsonify({'reply': ai})
        return jsonify({'reply': d.get('about','No about info found.')})

    faq = faq_lookup(low)
    if faq:
        return jsonify({'reply': faq})

    ctx = cached('about', scrape_about).get('about','') + "\n" + cached('placements', scrape_placements).get('summary','')
    ai = ai_enrich(msg, ctx)
    if ai:
        return jsonify({'reply': ai})
    return jsonify({'reply': "Sorry, I don't have that information. Try asking about 'placement', 'admission', or 'about medicaps'. "})

@app.route('/placement', methods=['GET'])
def placement_api():
    d = cached('placements', scrape_placements)
    return jsonify(d)

@app.route('/admission', methods=['GET'])
def admission_api():
    d = cached('admissions', scrape_admissions)
    return jsonify(d)

@app.route('/aboutinfo', methods=['GET'])
def about_api():
    d = cached('about', scrape_about)
    return jsonify(d)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
