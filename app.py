from flask import Flask, request, jsonify
import requests, re, os
from bs4 import BeautifulSoup

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def scrape_article(url, num=10):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        urls = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or ''
            if not src.startswith('http'):
                continue
            if any(x in src for x in ['logo','icon','avatar','placeholder','1x1','sprite','grey']):
                continue
            if re.search(r'\.(jpg|jpeg|png|webp)', src.lower()):
                urls.append(src)
        return list(dict.fromkeys(urls))[:num]
    except Exception as e:
        return []

def search_bing_images(query, num=10):
    try:
        r = requests.get(
            "https://www.bing.com/images/search",
            params={"q": query, "form": "HDRSC2", "first": 1},
            headers=HEADERS,
            timeout=15
        )
        urls = re.findall(r'murl&quot;:(.*?)&quot;', r.text)
        urls = [u for u in urls if u.startswith('http')]
        return list(dict.fromkeys(urls))[:num]
    except:
        return []

@app.route('/images')
def images():
    query = request.args.get('q', '')
    num = int(request.args.get('num', 10))
    if not query:
        return jsonify({"error": "no query"}), 400
    urls = search_bing_images(query, num)
    return jsonify({"urls": urls, "count": len(urls)})

@app.route('/article')
def article():
    url = request.args.get('url', '')
    num = int(request.args.get('num', 10))
    if not url:
        return jsonify({"error": "no url"}), 400
    imgs = scrape_article(url, num)
    return jsonify({"urls": imgs, "count": len(imgs)})

@app.route('/')
def health():
    return "OK"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
