const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());
(async () => {
  try {
    const browser = await puppeteer.launch({
      headless: true,
      userDataDir: './user_data',
      executablePath: '/opt/hostedtoolcache/chromium/latest/x64/chrome',
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    const page = await browser.newPage();
    await page.setViewport({width:1366, height:768});
    console.log('🌐 Navigating to chatgpt.com...');
    await page.goto('https://chatgpt.com', {timeout: 60000});
    await new Promise(r => setTimeout(r, 5000));
    await page.screenshot({path: 'before.png', fullPage: true});
    console.log('🖱️ Clicking at (134, 254)...');
    await page.mouse.click(134, 254);
    await new Promise(r => setTimeout(r, 5000));
    await page.screenshot({path: 'after.png', fullPage: true});
    await browser.close();
    console.log('✅ Script completed successfully');
  } catch (error) {
    console.error('❌ Script failed:', error.message);
  }
})();
