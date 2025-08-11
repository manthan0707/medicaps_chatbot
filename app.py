
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os, time, json
import requests
from bs4 import BeautifulSoup

USE_SELENIUM = os.environ.get('USE_SELENIUM','0') == '1'
if USE_SELENIUM:
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except Exception as e:
        print('Selenium import failed:', e)
        USE_SELENIUM = False

app = FastAPI(title='Medicaps Chatbot API')
app.mount('/static', StaticFiles(directory='static'), name='static')

with open('faqs.json','r',encoding='utf-8') as f:
    FAQS = json.load(f)

CACHE = {}
CACHE_TTL = int(os.environ.get('CACHE_TTL_SECONDS', 300))

def cached(key, fn):
    now = time.time()
    if key in CACHE and now - CACHE[key]['ts'] < CACHE_TTL:
        return CACHE[key]['data']
    data = fn()
    CACHE[key] = {'ts': now, 'data': data}
    return data

def requests_scrape(url, selectors=None, paragraphs=8):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        parts = []
        if selectors:
            for sel in selectors:
                for el in soup.select(sel)[:paragraphs]:
                    parts.append(el.get_text(' ',strip=True))
        if not parts:
            for p in soup.select('p')[:paragraphs]:
                parts.append(p.get_text(' ',strip=True))
        rows = []
        table = soup.find('table')
        if table:
            for tr in table.find_all('tr')[1:12]:
                cols = [td.get_text(' ',strip=True) for td in tr.find_all(['td','th'])]
                if cols:
                    rows.append(' | '.join(cols))
        return {'summary': '\n\n'.join(parts)[:3000], 'rows': rows}
    except Exception as e:
        return {'error': str(e)}

def selenium_scrape(url, selectors=None, paragraphs=8):
    try:
        opts = Options()
        opts.add_argument('--headless=new')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--window-size=1200,800')
        drv = webdriver.Chrome(options=opts)
        drv.get(url)
        if selectors:
            for sel in selectors:
                try:
                    WebDriverWait(drv,8).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, sel)))
                    break
                except Exception:
                    continue
        time.sleep(0.6)
        soup = BeautifulSoup(drv.page_source,'html.parser')
        drv.quit()
        parts = []
        for h in soup.select('h1,h2,h3'):
            txt = h.get_text(strip=True)
            if txt:
                nxt = h.find_next(['p','div','span'])
                if nxt and nxt.get_text(strip=True):
                    parts.append(f"{txt} - {nxt.get_text(' ',strip=True)[:600]}")
        if not parts:
            for p in soup.select('p')[:paragraphs]:
                parts.append(p.get_text(' ',strip=True)[:paragraphs])
        rows = []
        table = soup.find('table')
        if table:
            for tr in table.find_all('tr')[1:12]:
                cols = [td.get_text(' ',strip=True) for td in tr.find_all(['td','th'])]
                if cols:
                    rows.append(' | '.join(cols))
        return {'summary': '\n\n'.join(parts)[:3000], 'rows': rows}
    except Exception as e:
        return {'error': str(e)}

def scrape(url, selectors=None, paragraphs=8):
    if USE_SELENIUM:
        s = selenium_scrape(url, selectors=selectors, paragraphs=paragraphs)
        if isinstance(s, dict) and 'error' in s:
            return requests_scrape(url, selectors=selectors, paragraphs=paragraphs)
        return s
    else:
        return requests_scrape(url, selectors=selectors, paragraphs=paragraphs)

@app.get('/', response_class=HTMLResponse)
async def homepage():
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        return HTMLResponse(f.read())

@app.post('/chat')
async def chat_endpoint(req: Request):
    body = await req.json()
    msg = (body.get('message') or '').strip().lower()
    if not msg:
        return JSONResponse({'reply':'Type a question.'})
    if any(k in msg for k in ['placement','placements','package','highest','average','recruiter']):
        data = cached('placements', lambda: scrape('https://www.medicaps.ac.in/placements', selectors=['h2','h3','table','p'], paragraphs=12))
        if 'error' in data:
            return JSONResponse({'reply': 'Sorry — could not fetch placement data.'})
        return JSONResponse({'reply': data.get('summary') + ('\n\nRecent rows:\n' + '\n'.join(data.get('rows',[])) if data.get('rows') else '')})
    if any(k in msg for k in ['admission','apply','eligibility','deadline','date','fees']):
        data = cached('admissions', lambda: scrape('https://www.medicaps.ac.in/admission-24-25.php', selectors=['h2','h3','p','table'], paragraphs=14))
        if 'error' in data:
            return JSONResponse({'reply': 'Sorry — could not fetch admission data.'})
        return JSONResponse({'reply': data.get('summary') + ('\n\nTables:\n' + '\n\n'.join(['\n'.join(t) for t in data.get('rows',[])] ) if data.get('rows') else '')})
    if any(k in msg for k in ['about','who are you','overview','campus']):
        data = cached('about', lambda: scrape('https://www.medicaps.ac.in/about', selectors=['p','h2','h3'], paragraphs=12))
        if 'error' in data:
            return JSONResponse({'reply': 'Sorry — could not fetch about info.'})
        return JSONResponse({'reply': data.get('summary')})
    for q,a in FAQS.items():
        if q in msg:
            return JSONResponse({'reply': a})
    return JSONResponse({'reply': "I can help with 'placement', 'admission', or 'about medicaps'. Try those."})

@app.get('/api/placements')
async def api_placements():
    return JSONResponse(cached('placements', lambda: scrape('https://www.medicaps.ac.in/placements', selectors=['h2','h3','table','p'], paragraphs=12)))

@app.get('/api/admissions')
async def api_admissions():
    return JSONResponse(cached('admissions', lambda: scrape('https://www.medicaps.ac.in/admission-24-25.php', selectors=['h2','h3','p','table'], paragraphs=14)))

@app.get('/api/about')
async def api_about():
    return JSONResponse(cached('about', lambda: scrape('https://www.medicaps.ac.in/about', selectors=['p','h2','h3'], paragraphs=12)))
