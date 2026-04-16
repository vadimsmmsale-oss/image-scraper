from flask import Flask, request, jsonify
import requests, re

app = Flask(__name__)

PROXY = "http://nlozqyrk:5dj3126kbcyi@31.59.20.176:6754"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def scrape_google(query, num=10):
    try:
        r = requests.get(
            "https://www.google.com/search",
            params={"q": query, "tbm": "isch", "hl": "en", "gl": "us"},
            headers=HEADERS,
            proxies={"http": PROXY, "https": PROXY},
            timeout=20
        )
        urls = re.findall(r'ou":"(https?://[^"]+)"', r.text)
        urls = [u for u in urls if 'google' not in u and 'gstatic' not in u]
        return list(dict.fromkeys(urls))[:num]
    except Exception as e:
        return []

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    num = int(request.args.get('num', 10))
    if not query:
        return jsonify({"error": "no query"}), 400
    urls = scrape_google(query, num)
    return jsonify({"urls": urls, "count": len(urls)})

@app.route('/')
def health():
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
