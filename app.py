from flask import Flask, request, jsonify
import asyncio
from pyppeteer import launch
import re

app = Flask(__name__)

async def scrape_images(query, num=10):
    browser = await launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    )
    page = await browser.newPage()
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    await page.goto(f'https://www.google.com/search?q={query}&tbm=isch&hl=en&gl=us')
    await page.waitForSelector('img', timeout=10000)
    
    urls = []
    images = await page.querySelectorAll('img.YQ4gaf')
    
    for img in images[:num*2]:
        try:
            await img.click()
            await asyncio.sleep(1)
            big_imgs = await page.querySelectorAll('img.iPVvYb, img.r48jcc, img.sFlh5c')
            for bi in big_imgs:
                src = await page.evaluate('(el) => el.src', bi)
                if src and src.startswith('http') and 'encrypted' not in src and 'google' not in src:
                    urls.append(src)
                    break
        except:
            continue
        if len(urls) >= num:
            break
    
    await browser.close()
    return list(dict.fromkeys(urls))[:num]

async def scrape_article(url, num=8):
    browser = await launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    )
    page = await browser.newPage()
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 30000})
    
    imgs = await page.querySelectorAll('img')
    urls = []
    for img in imgs:
        src = await page.evaluate('(el) => el.src', img)
        if not src or not src.startswith('http'):
            continue
        if any(x in src for x in ['logo','icon','avatar','placeholder','1x1']):
            continue
        if re.search(r'\.(jpg|jpeg|png|webp)', src.lower()):
            urls.append(src)
    
    await browser.close()
    return list(dict.fromkeys(urls))[:num]

@app.route('/images')
def images():
    query = request.args.get('q', '')
    num = int(request.args.get('num', 10))
    if not query:
        return jsonify({"error": "no query"}), 400
    urls = asyncio.get_event_loop().run_until_complete(scrape_images(query, num))
    return jsonify({"urls": urls, "count": len(urls)})

@app.route('/article')
def article():
    url = request.args.get('url', '')
    num = int(request.args.get('num', 8))
    if not url:
        return jsonify({"error": "no url"}), 400
    imgs = asyncio.get_event_loop().run_until_complete(scrape_article(url, num))
    return jsonify({"urls": imgs, "count": len(imgs)})

@app.route('/')
def health():
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
