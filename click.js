const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

(async () => {
  const config = {x: 134, y: 254, url: 'https://chatgpt.com'};
  
  console.log('🔥 ULTRA STEALTH MODE');
  
  const browser = await puppeteer.launch({
    headless: false,  // VISIBLE = کمتر detect
    executablePath: '/usr/bin/google-chrome-stable',
    slowMo: 250,
    args: [
      '--no-sandbox', '--disable-setuid-sandbox',
      '--disable-dev-shm-usage', '--disable-gpu',
      '--disable-web-security', '--disable-extensions',
      '--window-size=1920,1080', '--start-maximized'
    ]
  });
  
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  await page.setViewport({width: 1920, height: 1080});

  // CLOUDFLARE BYPASS
  await page.evaluateOnNewDocument(() => {
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    window.chrome = {runtime: {}};
  });

  console.log('🌐 Loading...');
  const response = await page.goto(config.url, { 
    waitUntil: 'load', 
    timeout: 90000  // 90 ثانیه!
  });
  
  console.log(`Status: ${response.status()}`)$;
  
  // انتظار MAX برای Cloudflare
  $console.log('⏳ Cloudflare challenge...')$;
  $await page.waitForTimeout(15000);  // 15$ ثانیه
  
  // DEBUG screenshot
  $await page.screenshot({path: 'debug.png', fullPage: true})$;
  
  // CLICK!
  $console.log(`🖱️ CLICK$ {config.x},${config.y}`);
  await page.mouse.click(config.x, config.y);
  await page.waitForTimeout(5000);
  
  await page.screenshot({path: 'after.png', fullPage: true});
  
  console.log('✅ DONE!');
  await browser.close();
  
})();
