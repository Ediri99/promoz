#!/usr/bin/env python3
"""
PromoZ Local Server
Run this to serve the PromoZ pages with live offer refreshing.
Access at: http://localhost:8080
"""
import http.server, json, os, re, urllib.request, urllib.error
from html.parser import HTMLParser
from datetime import datetime

PORT = 8080
BASE = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE, "_cache.json")

BRANDS = {
    "kfc":      ["https://mypromo.lk/kfcsrilanka/promotions",
                 "https://mypromo.lk/kfclk/promotions",
                 "https://mypromo.lk/kfc/promotions"],
    "dominos":  ["https://mypromo.lk/dominossl/promotions",
                 "https://mypromo.lk/dominoslk/promotions",
                 "https://mypromo.lk/dominos/promotions",
                 "https://mypromo.lk/dominospizza/promotions",
                 "https://mypromo.lk/dominospizzalk/promotions",
                 "https://mypromo.lk/dominossrilanka/promotions",
                 "https://mypromo.lk/dominos-pizza/promotions",
                 "https://mypromo.lk/domino/promotions"],
    "pizzahut": ["https://mypromo.lk/pizzahutlk/promotions",
                 "https://mypromo.lk/pizzahut/promotions",
                 "https://mypromo.lk/pizzahutsl/promotions"],
    "popeyes":  ["https://mypromo.lk/popeyeslk/promotions",
                 "https://mypromo.lk/popeyes/promotions"],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

class PromoParser(HTMLParser):
    """Parse mypromo.lk promotion cards."""
    def __init__(self):
        super().__init__()
        self.promos = []
        self._current = {}
        self._in_card = False
        self._in_title = False
        self._in_date = False
        self._depth = 0
        self._card_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        cls = attrs.get("class", "")
        self._depth += 1

        if "promotion-card" in cls or "promo-card" in cls or "offer-card" in cls:
            self._in_card = True
            self._card_depth = self._depth
            self._current = {}

        if self._in_card:
            if tag == "img" and "src" in attrs:
                src = attrs["src"]
                if src and not src.startswith("data:"):
                    if src.startswith("//"):
                        src = "https:" + src
                    elif src.startswith("/"):
                        src = "https://mypromo.lk" + src
                    self._current["image"] = src
            if tag == "a" and "href" in attrs:
                href = attrs["href"]
                if href and "/promotions/" in href:
                    if href.startswith("/"):
                        href = "https://mypromo.lk" + href
                    self._current.setdefault("link", href)
            if "promotion-title" in cls or "promo-title" in cls or "card-title" in cls:
                self._in_title = True
            if "valid" in cls or "date" in cls or "expiry" in cls:
                self._in_date = True

    def handle_endtag(self, tag):
        if self._in_card and self._depth == self._card_depth:
            if self._current.get("title") or self._current.get("image"):
                self.promos.append(dict(self._current))
            self._in_card = False
            self._current = {}
        self._depth -= 1
        self._in_title = False
        self._in_date = False

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        if self._in_card:
            if self._in_title:
                self._current["title"] = data
            elif self._in_date:
                self._current["validity"] = data


def fetch_page(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f'  Fetch error: {e}')
        return None


def scrape_brand(brand):
    """Scrape offers for a brand from mypromo.lk."""
    urls = BRANDS[brand] if isinstance(BRANDS[brand], list) else [BRANDS[brand]]
    html = None
    tried = []
    for url in urls:
        print(f"  Trying {url}...")
        html = fetch_page(url)
        if html and len(html) > 500:
            print(f"  Got {len(html)} bytes")
            break
        tried.append(url)
    if not html or len(html) < 500:
        return None, "No URL worked: " + str(tried)

    # Extract promo cards via regex as fallback (mypromo.lk uses specific patterns)
    promos = []

    # Try to find JSON data embedded in the page (Next.js / SPA sites often do this)
    json_match = re.search(r'"promotions"\s*:\s*(\[.*?\])', html, re.DOTALL)
    if not json_match:
        json_match = re.search(r'"offers"\s*:\s*(\[.*?\])', html, re.DOTALL)

    # Extract image URLs from CDN
    images = re.findall(r'https://(?:mypromo\.azureedge\.net|promolkwebsite\.blob\.core\.windows\.net|mypromo\.lk)/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)', html)
    images = list(dict.fromkeys(images))  # deduplicate

    # Extract titles - look for heading patterns near images
    titles = re.findall(r'<h[2-4][^>]*>([^<]{10,100})</h[2-4]>', html)
    titles = [t.strip() for t in titles if t.strip() and len(t.strip()) > 5]

    # Extract validity dates
    dates = re.findall(r'(?:Valid|Expires?|Until|Till)[^\d]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|\d{4}-\d{2}-\d{2})', html, re.IGNORECASE)

    # Extract prices
    prices = re.findall(r'Rs\.?\s*[\d,]+(?:\.\d{2})?', html)

    # Build promo list by pairing images with titles
    for i, img in enumerate(images[:12]):
        promo = {"image": img, "id": i}
        if i < len(titles):
            promo["title"] = titles[i]
        if i < len(dates):
            promo["validity"] = dates[i]
        if i < len(prices):
            promo["price"] = prices[i]
        promos.append(promo)

    return promos, None


def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}


def save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE, **kwargs)

    def do_GET(self):
        if self.path == "/api/status":
            cache = load_cache()
            self.send_json({"status": "ok", "cache": {
                b: cache.get(b, {}).get("updated", "never") for b in BRANDS
            }})
        elif self.path.startswith("/api/offers"):
            brand = self.path.split("/")[-1].split("?")[0]
            cache = load_cache()
            if brand in cache:
                self.send_json({"brand": brand, "promos": cache[brand]["promos"],
                                "updated": cache[brand]["updated"], "cached": True})
            else:
                self.send_json({"error": "No cached data. Click Refresh."}, 404)
        elif self.path.startswith("/api/refresh"):
            brand = self.path.split("=")[-1] if "=" in self.path else "all"
            cache = load_cache()
            results = {}
            brands_to_refresh = [brand] if brand in BRANDS else list(BRANDS.keys())
            for b in brands_to_refresh:
                print(f"Scraping {b}...")
                promos, err = scrape_brand(b)
                if promos is not None:
                    cache[b] = {
                        "promos": promos,
                        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "count": len(promos)
                    }
                    results[b] = {"ok": True, "count": len(promos)}
                else:
                    results[b] = {"ok": False, "error": err}
            save_cache(cache)
            self.send_json({"results": results,
                            "updated": datetime.now().strftime("%Y-%m-%d %H:%M")})
        else:
            super().do_GET()

    def send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {fmt % args}")


if __name__ == "__main__":
    os.chdir(BASE)
    print(f"\n🔥 PromoZ Server running at http://localhost:{PORT}")
    print(f"   Press Ctrl+C to stop\n")
    with http.server.ThreadingHTTPServer(("", PORT), Handler) as s:
        s.serve_forever()
