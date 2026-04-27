const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');

puppeteer.use(StealthPlugin());

const config = {
  url: 'https://chatgpt.com',
  x: 134, y: 254,
  timestamp: new Date().toISOString()
};
fs.writeFileSync('config.json', JSON.stringify(config, null, 2));

(async () => {
  console.log('🚀 Launching stealth browser...');
  
  const browser = await puppeteer.launch({
    headless: 'new',  // جدیدتر
    slowMo: 100,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--no-first-run',
      '--no-zygote',
      '--disable-gpu',
      '--disable-web-security',
      '--disable-features=VizDisplayCompositor',
      '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  
  // WebGL و Canvas fingerprinting
  await page.evaluateOnNewDocument(() => {
    const getParameter = WebGLRenderingContext.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
      if (parameter === 37445) return 'Intel Inc.';
      if (parameter === 37446) return 'Intel Iris OpenGL Engine';
      return getParameter(parameter);
    };
  });

  // Headers واقعی‌تر
  await page.setExtraHTTPHeaders({
    'Accept-Language': 'en-US,en;q=0.9',
    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"'
  });

  console.log('🌐 Navigating...');
  await page.goto(config.url, { 
    waitUntil: 'domcontentloaded',  // سریع‌تر
    timeout: 60000 
  });

  // صبر برای Cloudflare
  console.log('⏳ Waiting for Cloudflare...');
  await page.waitForTimeout(8000);

  await page.screenshot({path: 'before.png', fullPage: true});
  
  console.log('🖱️ Clicking...');
  await page.mouse.click(config.x, config.y);
  await page.waitForTimeout(3000);

  // Marker
  await page.evaluate((x, y) => {
    const circle = document.createElement('div');
    circle.style.cssText = `position:fixed;left:${x}px;top:${y}px;width:10px;height:10px;background:red;border-radius:50%;z-index:999999;pointer-events:none;box-shadow:0 0 10px red;`;
    document.body.appendChild(circle);
  }, config.x, config.y);

  await page.screenshot({path: 'after.png', fullPage: true});
  
  console.log(`✅ Success! Check after.png`);
  await browser.close();
  
  fs.writeFileSync('status.txt', `Clicked at ${config.x},${config.y}\nSuccess: true`);
})();
