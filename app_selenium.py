
from flask import Flask, render_template, request, jsonify
import os, time, json
from bs4 import BeautifulSoup

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

app = Flask(__name__, static_folder='static', template_folder='templates')

# Load fallback FAQs
with open(os.path.join(app.root_path, 'faqs.json'), 'r', encoding='utf-8') as f:
    FAQS = json.load(f)

# Simple in-memory cache
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
    # CHROMEDRIVER_PATH env var or assume 'chromedriver' in PATH
    drv_path = os.environ.get('CHROMEDRIVER_PATH', 'chromedriver')
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    try:
        driver = webdriver.Chrome(executable_path=drv_path, options=chrome_options)
    except TypeError:
        # Newer selenium versions accept just options and find chromedriver in PATH
        driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_placements_selenium():
    url = "https://www.medicaps.ac.in/placements"
    try:
        driver = make_driver()
    except WebDriverException as e:
        return {"error": f"WebDriver error: {e}. Make sure chromedriver is installed and CHROMEDRIVER_PATH is set."}
    try:
        driver.get(url)
        time.sleep(2.5)  # simple wait; can be replaced by explicit waits
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        parts = []
        for h in soup.select("h1,h2,h3,h4"):
            txt = h.get_text(strip=True)
            if txt:
                nxt = h.find_next(["p","div","span"])
                if nxt:
                    parts.append(f"{txt} - {nxt.get_text(' ',strip=True)[:600]}")
        if not parts:
            for p in soup.select("p")[:10]:
                parts.append(p.get_text(" ",strip=True)[:400])
        rows = []
        table = soup.find("table")
        if table:
            for tr in table.find_all("tr")[1:8]:
                cols = [td.get_text(" ",strip=True) for td in tr.find_all(["td","th"])]
                if cols:
                    rows.append(" | ".join(cols))
        return {"summary": "\n\n".join(parts)[:4000], "rows": rows}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            driver.quit()
        except:
            pass

def scrape_admissions_selenium():
    url = "https://www.medicaps.ac.in/admission-24-25.php"
    try:
        driver = make_driver()
    except WebDriverException as e:
        return {"error": f"WebDriver error: {e}. Make sure chromedriver is installed and CHROMEDRIVER_PATH is set."}
    try:
        driver.get(url)
        time.sleep(2)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        parts = []
        for h in soup.select("h2,h3,h4"):
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
            for p in soup.select("p")[:12]:
                parts.append(p.get_text(" ",strip=True)[:400])
        return {"summary": "\n\n".join(parts)[:4000]}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            driver.quit()
        except:
            pass

def scrape_about_selenium():
    url = "https://www.medicaps.ac.in/about"
    try:
        driver = make_driver()
    except WebDriverException as e:
        return {"error": f"WebDriver error: {e}. Make sure chromedriver is installed and CHROMEDRIVER_PATH is set."}
    try:
        driver.get(url)
        time.sleep(1.5)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        main = soup.find("main") or soup
        paras = main.select("p")[:10]
        if paras:
            about = " ".join([p.get_text(" ",strip=True) for p in paras])
            return {"about": about[:4000]}
        div = soup.find("div", class_=lambda x: x and 'about' in x.lower())
        if div:
            return {"about": div.get_text(" ",strip=True)[:4000]}
        return {"about": soup.get_text(" ",strip=True)[:2000]}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            driver.quit()
        except:
            pass

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
        d = cached('placements', scrape_placements_selenium)
        if 'error' in d:
            base = faq_lookup(low) or "Couldn't fetch live placement data right now."
            return jsonify({'reply': base})
        resp = d.get('summary','') or 'No placement summary available.'
        rows = d.get('rows',[])
        if rows:
            resp += "\n\nRecent rows:\n" + "\n".join(rows)
        return jsonify({'reply': resp})

    if any(w in low for w in ['admission','apply','eligibility','deadline','important date','last date']):
        d = cached('admissions', scrape_admissions_selenium)
        if 'error' in d:
            base = faq_lookup(low) or "Couldn't fetch admission info right now."
            return jsonify({'reply': base})
        return jsonify({'reply': d.get('summary','No admission info found.')})

    if any(w in low for w in ['about','who are you','overview','university info','about medicaps']):
        d = cached('about', scrape_about_selenium)
        if 'error' in d:
            base = faq_lookup(low) or "Couldn't fetch about info right now."
            return jsonify({'reply': base})
        return jsonify({'reply': d.get('about','No about info found.')})

    faq = faq_lookup(low)
    if faq:
        return jsonify({'reply': faq})

    return jsonify({'reply': "Sorry, I don't have that information. Try 'placement' or 'admission'."})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
