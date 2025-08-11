
from flask import Flask, render_template, request, jsonify
import os, time, json, logging
from bs4 import BeautifulSoup

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException

# Optional OpenAI integration (set OPENAI_API_KEY as env var)
USE_OPENAI = bool(os.environ.get('OPENAI_API_KEY'))
if USE_OPENAI:
    try:
        import openai
        openai.api_key = os.environ.get('OPENAI_API_KEY')
    except Exception as e:
        print("OpenAI import error:", e)
        USE_OPENAI = False

app = Flask(__name__, static_folder='static', template_folder='templates')

logging.basicConfig(level=logging.INFO)

# load faqs
with open(os.path.join(app.root_path, 'faqs.json'), 'r', encoding='utf-8') as f:
    FAQS = json.load(f)

CACHE = {}
CACHE_TTL = int(os.environ.get('CACHE_TTL_SECONDS', 300))  # default 5 minutes

def cached(key, fn):
    now = time.time()
    if key in CACHE and now - CACHE[key]['ts'] < CACHE_TTL:
        return CACHE[key]['data']
    data = fn()
    CACHE[key] = {'ts': now, 'data': data}
    return data

def make_driver():
    drv_path = os.environ.get('CHROMEDRIVER_PATH', None)
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36")
    try:
        if drv_path:
            driver = webdriver.Chrome(executable_path=drv_path, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        raise WebDriverException(f"Error creating Chrome WebDriver: {e}")

def wait_for_any(driver, selectors, timeout=12):
    try:
        for sel in selectors:
            try:
                WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                return True
            except TimeoutException:
                continue
        return False
    except Exception as e:
        app.logger.warning("wait_for_any exception: %s", e)
        return False

def scrape_page(url, selectors=None, paragraphs=10):
    try:
        driver = make_driver()
    except WebDriverException as e:
        return {"error": str(e)}
    try:
        driver.get(url)
        if selectors:
            wait_for_any(driver, selectors, timeout=12)
        time.sleep(0.6)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        parts = []
        # try structured extraction
        for h in soup.select('h1,h2,h3,h4'):
            txt = h.get_text(strip=True)
            if txt:
                nxt = h.find_next(['p','div','span'])
                if nxt and nxt.get_text(strip=True):
                    parts.append(f"{txt} - {nxt.get_text(' ',strip=True)[:700]}")
        if not parts:
            for p in soup.select('p')[:paragraphs]:
                parts.append(p.get_text(' ',strip=True)[:600])
        # try table row extraction
        rows = []
        table = soup.find('table')
        if table:
            for tr in table.find_all('tr')[1:15]:
                cols = [td.get_text(' ',strip=True) for td in tr.find_all(['td','th'])]
                if cols:
                    rows.append(' | '.join(cols))
        return {'summary': '\n\n'.join(parts)[:4000], 'rows': rows}
    except Exception as e:
        return {'error': str(e)}
    finally:
        try:
            driver.quit()
        except:
            pass

def fetch_placements():
    url = 'https://www.medicaps.ac.in/placements'
    return scrape_page(url, selectors=['table','.placement','.placement-section','h2','h3'], paragraphs=12)

def fetch_admissions():
    url = 'https://www.medicaps.ac.in/admission-24-25.php'
    return scrape_page(url, selectors=['#content','.admission','h2','h3','table'], paragraphs=14)

def fetch_about():
    url = 'https://www.medicaps.ac.in/about'
    return scrape_page(url, selectors=['main','.about','h2','h3','p'], paragraphs=12)

def faq_lookup(msg):
    m = msg.lower()
    for k,v in FAQS.items():
        if k in m:
            return v
    return None

def ai_enrich(user_msg, context):
    if not USE_OPENAI:
        return None
    try:
        prompt = f"""You are an assistant for Medicaps University. Use the context below (scraped website content and FAQ) to answer the user's query concisely and helpfully.

Context:\n{context}\n\nUser question: {user_msg}\n\nAnswer:"""
        resp = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=[{'role':'user','content':prompt}], max_tokens=300)
        return resp.choices[0].message.content.strip()
    except Exception as e:
        app.logger.warning('OpenAI error: %s', e)
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
    # placements
    if any(w in low for w in ['placement','package','placements','highest','average','recruiter','offer','offers']):
        d = cached('placements', fetch_placements)
        if 'error' in d:
            base = faq_lookup(low) or 'Sorry — could not fetch live placement data.'
            return jsonify({'reply': base})
        context = d.get('summary','') + '\n' + '\n'.join(d.get('rows',[]))
        ai = ai_enrich(msg, context)
        return jsonify({'reply': ai or context or 'No placement info found.'})
    # admissions
    if any(w in low for w in ['admission','apply','eligibility','deadline','important date','last date','fees','cutoff']):
        d = cached('admissions', fetch_admissions)
        if 'error' in d:
            base = faq_lookup(low) or 'Sorry — could not fetch live admission data.'
            return jsonify({'reply': base})
        context = d.get('summary','') + '\n' + '\n'.join([' | '.join(t) for t in d.get('rows',[])]) if isinstance(d.get('rows',[]), list) else d.get('summary','')
        ai = ai_enrich(msg, context)
        return jsonify({'reply': ai or context or 'No admission info found.'})
    # about
    if any(w in low for w in ['about','who are you','overview','university info','about medicaps','campus']):
        d = cached('about', fetch_about)
        if 'error' in d:
            base = faq_lookup(low) or 'Sorry — could not fetch about info.'
            return jsonify({'reply': base})
        context = d.get('summary','') or d.get('rows','') or d.get('about','')
        ai = ai_enrich(msg, context)
        return jsonify({'reply': ai or context or 'No about info found.'})
    # faq fallback
    fa = faq_lookup(low)
    if fa:
        return jsonify({'reply': fa})
    # last resort: combine about+placements
    ctx = cached('about', fetch_about).get('summary','') + '\n' + cached('placements', fetch_placements).get('summary','')
    ai = ai_enrich(msg, ctx)
    return jsonify({'reply': ai or "Sorry, I don't have that information. Try asking about 'placement', 'admission', or 'about medicaps'."})

@app.route('/api/placements')
def api_placements():
    return jsonify(fetch_placements())

@app.route('/api/admissions')
def api_admissions():
    return jsonify(fetch_admissions())

@app.route('/api/about')
def api_about():
    return jsonify(fetch_about())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
