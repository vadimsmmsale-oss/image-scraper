const express = require('express');
const puppeteer = require('puppeteer');

const app = express();
const PORT = process.env.PORT || 8080;

async function getBrowser() {
    return await puppeteer.launch({
        headless: 'new',
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
        ]
    });
}

// Поиск картинок в Google Images
app.get('/images', async (req, res) => {
    const query = req.query.q;
    const num = parseInt(req.query.num) || 10;
    if (!query) return res.json({ error: 'no query' });

    const browser = await getBrowser();
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');

    await page.goto(`https://www.google.com/search?q=${encodeURIComponent(query)}&tbm=isch&hl=en`);
    await page.waitForSelector('img', { timeout: 10000 });

    const urls = [];
    const images = await page.$$('img.YQ4gaf');

    for (const img of images.slice(0, num * 2)) {
        try {
            await img.click();
            await new Promise(r => setTimeout(r, 1000));
            const src = await page.$eval('img.iPVvYb, img.r48jcc', el => el.src).catch(() => null);
            if (src && src.startsWith('http') && !src.includes('encrypted') && !src.includes('google.com')) {
                urls.push(src);
            }
        } catch {}
        if (urls.length >= num) break;
    }

    await browser.close();
    res.json({ urls, count: urls.length });
});

// Парсинг фото со статьи
app.get('/article', async (req, res) => {
    const url = req.query.url;
    const num = parseInt(req.query.num) || 10;
    if (!url) return res.json({ error: 'no url' });

    const browser = await getBrowser();
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });

    const urls = await page.evaluate(() => {
        const imgs = Array.from(document.querySelectorAll('img'));
        return imgs
            .map(img => img.src)
            .filter(src => src && src.startsWith('http'))
            .filter(src => !['logo','icon','avatar','placeholder','1x1'].some(x => src.includes(x)))
            .filter(src => /\.(jpg|jpeg|png|webp)/i.test(src));
    });

    await browser.close();
    res.json({ urls: [...new Set(urls)].slice(0, num), count: urls.length });
});

app.get('/', (req, res) => res.send('OK'));

app.listen(PORT, () => console.log(`Running on port ${PORT}`));
