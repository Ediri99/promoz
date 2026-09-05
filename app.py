"""
PromoZ — Flask web app for Render/Railway deployment.
Auto-refreshes offer data every 6 hours.
"""
import os, re, json, threading
import cloudscraper
from datetime import datetime
from flask import Flask, jsonify, send_from_directory, abort

app = Flask(__name__, static_folder=".", static_url_path="")

# ── Config ──────────────────────────────────────────────────────────────────
REFRESH_INTERVAL_HOURS = 6
BRANDS = {
    "kfc":      ["https://mypromo.lk/kfcsrilanka/promotions",
                 "https://mypromo.lk/kfclk/promotions"],
    "dominos":  ["https://mypromo.lk/dominossl/promotions",
                 "https://mypromo.lk/dominoslk/promotions",
                 "https://mypromo.lk/dominospizza/promotions"],
    "pizzahut": ["https://mypromo.lk/pizzahutlk/promotions",
                 "https://mypromo.lk/pizzahut/promotions"],
    "popeyes":  ["https://mypromo.lk/popeyeslk/promotions"],
}

# ── In-memory cache (+ optional file persistence) ───────────────────────────
_cache = {}
CACHE_FILE = os.path.join(os.path.dirname(__file__), "_cache.json")

def load_cache():
    global _cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                _cache = json.load(f)
            print(f"Cache loaded from disk ({len(_cache)} brands)")
        except Exception as e:
            print(f"Cache load error: {e}")

def save_cache():
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(_cache, f)
    except Exception as e:
        print(f"Cache save error: {e}")

# ── Scraper ──────────────────────────────────────────────────────────────────
scraper = cloudscraper.create_scraper()

def fetch_page(url):
    try:
        r = scraper.get(url, timeout=20)
        if r.status_code == 200:
            return r.text
        print(f"  HTTP {r.status_code} for {url}")
        return None
    except Exception as e:
        print(f"  Fetch error {url}: {e}")
        return None
def scrape_brand(brand):
    urls = BRANDS.get(brand, [])
    html = None
    for url in urls:
        print(f"  Trying {url}...")
        html = fetch_page(url)
        if html and len(html) > 500:
            print(f"  ✓ {len(html)} bytes")
            break
    if not html or len(html) < 500:
        return None, "All URLs failed"

    images = [m for m in re.findall(r'https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)[^\s"\'<>]*', html)
              if not any(x in m.lower() for x in ['icon', 'logo', 'favicon', 'avatar'])]
    images = list(dict.fromkeys(images))

    titles = [t.strip() for t in re.findall(r'<h[2-5][^>]*>([^<]{8,120})</h[2-5]>', html)
              if t.strip() and len(t.strip()) > 5]
    dates  = re.findall(r'(?:Valid|Expires?|Until|Till)[^\d]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|\d{4}-\d{2}-\d{2})', html, re.I)
    prices = re.findall(r'Rs\.?\s*[\d,]+(?:\.\d{2})?', html)

    promos = []
    for i, img in enumerate(images[:15]):
        p = {"image": img, "id": i}
        if i < len(titles):  p["title"]    = titles[i]
        if i < len(dates):   p["validity"] = dates[i]
        if i < len(prices):  p["price"]    = prices[i]
        promos.append(p)

    return promos, None

def refresh_all():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Auto-refreshing all brands...")
    for brand in BRANDS:
        promos, err = scrape_brand(brand)
        if promos is not None:
            _cache[brand] = {
                "promos":  promos,
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "count":   len(promos)
            }
            print(f"  {brand}: {len(promos)} offers cached")
        else:
            print(f"  {brand}: FAILED — {err}")
    save_cache()
    print("Refresh complete.\n")

# ── Background scheduler ─────────────────────────────────────────────────────
def schedule_refresh():
    refresh_all()
    t = threading.Timer(REFRESH_INTERVAL_HOURS * 3600, schedule_refresh)
    t.daemon = True
    t.start()

# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "home.html")

@app.route("/<path:filename>")
def static_files(filename):
    if os.path.exists(os.path.join(".", filename)):
        return send_from_directory(".", filename)
    abort(404)

@app.route("/api/status")
def api_status():
    return jsonify({"status": "ok", "cache": {
        b: {"updated": _cache[b]["updated"], "count": _cache[b]["count"]}
        if b in _cache else {"updated": "never", "count": 0}
        for b in BRANDS
    }})

@app.route("/api/offers/<brand>")
def api_offers(brand):
    if brand not in BRANDS:
        return jsonify({"error": "Unknown brand"}), 404
    if brand not in _cache:
        return jsonify({"error": "No data yet — refresh in progress"}), 404
    return jsonify({"brand": brand, **_cache[brand]})

@app.route("/api/refresh")
@app.route("/api/refresh/<brand>")
def api_refresh(brand=None):
    if brand and brand in BRANDS:
        promos, err = scrape_brand(brand)
        results = {}
        if promos is not None:
            _cache[brand] = {"promos": promos, "updated": datetime.now().strftime("%Y-%m-%d %H:%M"), "count": len(promos)}
            results[brand] = {"ok": True, "count": len(promos)}
        else:
            results[brand] = {"ok": False, "error": err}
    else:
        results = {}
        for b in BRANDS:
            promos, err = scrape_brand(b)
            if promos is not None:
                _cache[b] = {"promos": promos, "updated": datetime.now().strftime("%Y-%m-%d %H:%M"), "count": len(promos)}
                results[b] = {"ok": True, "count": len(promos)}
            else:
                results[b] = {"ok": False, "error": err}
    save_cache()
    return jsonify({"results": results, "updated": datetime.now().strftime("%Y-%m-%d %H:%M")})

# ── Startup ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    load_cache()
    t = threading.Thread(target=schedule_refresh, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
else:
    # Gunicorn startup
    load_cache()
    t = threading.Thread(target=schedule_refresh, daemon=True)
    t.start()
