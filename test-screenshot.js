const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://google.com');
  await page.fill('textarea[name="q"]', 'سلام');
  await page.press('textarea[name="q"]', 'Enter');
  await page.waitForTimeout(3000);
  
  await page.screenshot({ path: 'salam.png', fullPage: true });
  await browser.close();
  
  console.log('✅ salam.png ساخته شد!');
})();
