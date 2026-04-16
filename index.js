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

    try {
        const browser = await getBrowser();
        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
        
        await page.goto(`https://www.google.com/search?q=${encodeURIComponent(query)}&tbm=isch&hl=en`, {
            waitUntil: 'networkidle2',
            timeout: 30000
        });

        // Берём все src из img тегов напрямую без ожидания селектора
        const urls = await page.evaluate((n) => {
            const imgs = Array.from(document.querySelectorAll('img'));
            return imgs
                .map(img => img.src)
                .filter(src => src && src.startsWith('http') && !src.includes('google') && !src.includes('gstatic'))
                .slice(0, n);
        }, num);

        await browser.close();
        res.json({ urls, count: urls.length });
    } catch(e) {
        res.json({ error: e.message, urls: [], count: 0 });
    }
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

// Поиск статей по теме и сбор фото
app.get('/news', async (req, res) => {
    const query = req.query.q;
    const num = parseInt(req.query.num) || 15;
    if (!query) return res.json({ error: 'no query' });

    try {
        const browser = await getBrowser();
        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');

        // Ищем статьи через Google News
        await page.goto(`https://news.google.com/search?q=${encodeURIComponent(query)}&hl=en`, {
            waitUntil: 'networkidle2',
            timeout: 30000
        });

        // Берём ссылки на статьи
        const articleLinks = await page.evaluate(() => {
            const links = Array.from(document.querySelectorAll('a[href*="./articles/"]'));
            return links.slice(0, 5).map(a => a.href);
        });

        const allPhotos = [];

        // Заходим на каждую статью и берём фото
        for (const link of articleLinks) {
            try {
                await page.goto(link, { waitUntil: 'networkidle2', timeout: 20000 });
                const photos = await page.evaluate(() => {
                    return Array.from(document.querySelectorAll('img'))
                        .map(img => img.src)
                        .filter(src => src && src.startsWith('http'))
                        .filter(src => !['logo','icon','avatar','placeholder','1x1','sprite'].some(x => src.includes(x)))
                        .filter(src => /\.(jpg|jpeg|png|webp)/i.test(src));
                });
                allPhotos.push(...photos.slice(0, 5));
            } catch {}
            if (allPhotos.length >= num) break;
        }

        await browser.close();
        const unique = [...new Set(allPhotos)].slice(0, num);
        res.json({ urls: unique, count: unique.length });
    } catch(e) {
        res.json({ error: e.message, urls: [], count: 0 });
    }
});

app.listen(PORT, () => console.log(`Running on port ${PORT}`));
