from flask import Flask, request, jsonify
import asyncio, re, os
from pyppeteer import launch

app = Flask(__name__)

async def scrape_google_images(query, num=10):
    browser = await launch(
        headless=True,
        executablePath='/usr/bin/chromium',
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
        ]
    )
    page = await browser.newPage()
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    await page.goto(f'https://www.google.com/search?q={query}&tbm=isch&hl=en&gl=us')
    await asyncio.sleep(3)

    urls = []
    images = await page.querySelectorAll('img.YQ4gaf')
    for img in images[:num*2]:
        try:
            await img.click()
            await asyncio.sleep(1)
            for sel in ['img.iPVvYb', 'img.r48jcc', 'img.sFlh5c']:
                big = await page.querySelectorAll(sel)
                for bi in big:
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

async def scrape_article_images(url, num=8):
    browser = await launch(
        headless=True,
        executablePath='/usr/bin/chromium',
        args=['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage','--disable-gpu']
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
        if any(x in src for x in ['logo','icon','avatar','placeholder','1x1','sprite']):
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
    loop = asyncio.new_event_loop()
    urls = loop.run_until_complete(scrape_google_images(query, num))
    loop.close()
    return jsonify({"urls": urls, "count": len(urls)})

@app.route('/article')
def article():
    url = request.args.get('url', '')
    num = int(request.args.get('num', 8))
    if not url:
        return jsonify({"error": "no url"}), 400
    loop = asyncio.new_event_loop()
    imgs = loop.run_until_complete(scrape_article_images(url, num))
    loop.close()
    return jsonify({"urls": imgs, "count": len(imgs)})

@app.route('/')
def health():
    return "OK"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
