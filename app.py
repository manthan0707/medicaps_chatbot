
from flask import Flask, render_template, request, jsonify
import os, time, json
import requests
from bs4 import BeautifulSoup

USE_OPENAI = bool(os.environ.get('OPENAI_API_KEY'))
if USE_OPENAI:
    try:
        import openai
        openai.api_key = os.environ.get('OPENAI_API_KEY')
    except Exception as e:
        print("OpenAI import failed:", e)
        USE_OPENAI = False

app = Flask(__name__, static_folder='static', template_folder='templates')

with open(os.path.join(app.root_path, 'faqs.json'), 'r', encoding='utf-8') as f:
    FAQS = json.load(f)

CACHE = {}
CACHE_TTL = int(os.environ.get('CACHE_TTL_SECONDS', 3600))

def cached(key, fn):
    now = time.time()
    if key in CACHE and now - CACHE[key]['ts'] < CACHE_TTL:
        return CACHE[key]['data']
    data = fn()
    CACHE[key] = {'ts': now, 'data': data}
    return data

def scrape(url, selectors=None, paragraphs=6):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        parts = []
        if selectors:
            for sel in selectors:
                for el in soup.select(sel)[:paragraphs]:
                    parts.append(el.get_text(' ',strip=True))
        if not parts:
            for p in soup.select('p')[:paragraphs]:
                parts.append(p.get_text(' ',strip=True))
        return ' \n\n '.join(parts)[:4000]
    except Exception as e:
        return f"ERROR: {e}"

def get_placements():
    url = "https://www.medicaps.ac.in/placements"
    data = cached('placements', lambda: scrape(url, selectors=['.placement','table','h2','h3','p'], paragraphs=10))
    return data

def get_admissions():
    url = "https://www.medicaps.ac.in/admission-24-25.php"
    data = cached('admissions', lambda: scrape(url, selectors=['.admission','h2','h3','p','ul'], paragraphs=12))
    return data

def get_about():
    url = "https://www.medicaps.ac.in/about"
    data = cached('about', lambda: scrape(url, selectors=['.about','h2','h3','p'], paragraphs=12))
    return data

def faq_lookup(msg):
    m = msg.lower()
    for k,v in FAQS.items():
        if k in m:
            return v
    return None

def ai_response(user_msg, context=''):
    if not USE_OPENAI:
        return None
    try:
        prompt = f"""You are an assistant for Medicaps University. Use the context to answer the user's question concisely. Context:\n{context}\n\nUser: {user_msg}\n\nAnswer:"""
        res = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=[{'role':'user','content':prompt}], max_tokens=300)
        return res.choices[0].message.content.strip()
    except Exception as e:
        print('OpenAI error', e)
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
        ctx = get_placements()
        ai = ai_response(msg, ctx) or ctx
        return jsonify({'reply': ai})

    if any(w in low for w in ['admission','apply','eligibility','deadline','important date','last date']):
        ctx = get_admissions()
        ai = ai_response(msg, ctx) or ctx
        return jsonify({'reply': ai})

    if any(w in low for w in ['about','who are you','overview','university info','about medicaps']):
        ctx = get_about()
        ai = ai_response(msg, ctx) or ctx
        return jsonify({'reply': ai})

    faq = faq_lookup(low)
    if faq:
        return jsonify({'reply': faq})

    # fallback: combine about+placements
    ctx = get_about() + " \n\n " + get_placements()
    ai = ai_response(msg, ctx)
    if ai:
        return jsonify({'reply': ai})
    return jsonify({'reply': "Sorry, I couldn't find that. Try asking about 'placement', 'admission', or 'about medicaps'."})

@app.route('/placement', methods=['GET'])
def placement_api():
    return jsonify({'data': get_placements()})

@app.route('/admission', methods=['GET'])
def admission_api():
    return jsonify({'data': get_admissions()})

@app.route('/aboutapi', methods=['GET'])
def about_api():
    return jsonify({'data': get_about()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
