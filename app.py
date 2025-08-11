
from flask import Flask, render_template, request, jsonify
import os, time, json
from bs4 import BeautifulSoup

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException

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

def wait_for_selectors(driver, selectors, timeout=15):
    try:
        for sel in selectors:
            try:
                WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                return True
            except TimeoutException:
                continue
        return False
    except Exception:
        return False

def scrape_placements():
    url = "https://www.medicaps.ac.in/placements"
    try:
        driver = make_driver()
    except WebDriverException as e:
        return {"error": str(e)}
    try:
        driver.get(url)
        selectors = ["table", ".placement", ".placement-section", ".container", "h2", "h3"]
        _ = wait_for_selectors(driver, selectors, timeout=12)
        time.sleep(0.8)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        parts = []
        for header in soup.select("h1, h2, h3"):
            text = header.get_text(strip=True)
            if text:
                nxt = header.find_next(["p", "div", "span"])
                if nxt and nxt.get_text(strip=True):
                    parts.append(f"{text} - {nxt.get_text(' ', strip=True)[:700]}")
        if not parts:
            for p in soup.select("p")[:12]:
                parts.append(p.get_text(" ", strip=True)[:600])
        rows = []
        table = soup.find("table")
        if table:
            for tr in table.find_all("tr")[1:12]:
                cols = [td.get_text(" ", strip=True) for td in tr.find_all(["td","th"])]
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

def scrape_admissions():
    url = "https://www.medicaps.ac.in/admission-24-25.php"
    try:
        driver = make_driver()
    except WebDriverException as e:
        return {"error": str(e)}
    try:
        driver.get(url)
        selectors = ["#content", ".admission", "h2", "h3", "table"]
        _ = wait_for_selectors(driver, selectors, timeout=12)
        time.sleep(0.6)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        parts = []
        for header in soup.select("h2, h3, h4"):
            txt = header.get_text(strip=True)
            if txt:
                nxts = []
                for sib in header.find_next_siblings():
                    if sib.name in ['p','ul','div']:
                        nxts.append(sib.get_text(" ", strip=True)[:500])
                    if len(nxts) >= 4:
                        break
                if nxts:
                    parts.append(f"{txt} - {' '.join(nxts)}")
        if not parts:
            for p in soup.select("p")[:12]:
                parts.append(p.get_text(" ", strip=True)[:500])
        tables = []
        for table in soup.find_all("table")[:2]:
            rows = []
            for tr in table.find_all("tr"):
                cols = [td.get_text(" ", strip=True) for td in tr.find_all(["td","th"])]
                if cols:
                    rows.append(" | ".join(cols))
            if rows:
                tables.append(rows)
        return {"summary": "\n\n".join(parts)[:4000], "tables": tables}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            driver.quit()
        except:
            pass

def scrape_about():
    url = "https://www.medicaps.ac.in/about"
    try:
        driver = make_driver()
    except WebDriverException as e:
        return {"error": str(e)}
    try:
        driver.get(url)
        selectors = ["main", ".about", "h2", "h3", "p"]
        _ = wait_for_selectors(driver, selectors, timeout=10)
        time.sleep(0.5)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        main = soup.find("main") or soup.find("section") or soup
        paras = main.select("p")[:12]
        if paras:
            about = " ".join([p.get_text(" ", strip=True) for p in paras])
            return {"about": about[:4000]}
        div = soup.find("div", class_=lambda x: x and 'about' in x.lower() if x else False)
        if div:
            return {"about": div.get_text(" ", strip=True)[:4000]}
        return {"about": soup.get_text(" ", strip=True)[:2000]}
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
        d = cached('placements', scrape_placements)
        if 'error' in d:
            base = faq_lookup(low) or "Couldn't fetch live placement data right now."
            return jsonify({'reply': base})
        resp = d.get('summary','') or 'No placement summary available.'
        rows = d.get('rows',[])
        if rows:
            resp += "\n\nRecent rows:\n" + "\n".join(rows)
        return jsonify({'reply': resp})

    if any(w in low for w in ['admission','apply','eligibility','deadline','important date','last date']):
        d = cached('admissions', scrape_admissions)
        if 'error' in d:
            base = faq_lookup(low) or "Couldn't fetch admission info right now."
            return jsonify({'reply': base})
        resp = d.get('summary','') or 'No admission info available.'
        tables = d.get('tables', [])
        if tables:
            resp += "\n\nTables:\n" + "\n\n".join(["\n".join(t) for t in tables])
        return jsonify({'reply': resp})

    if any(w in low for w in ['about','who are you','overview','university info','about medicaps']):
        d = cached('about', scrape_about)
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
