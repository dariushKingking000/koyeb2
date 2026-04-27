cat > click.js << 'EOF'
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

(async () => {
  console.log('🚀 Stealth Click v24');
  
  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--disable-web-security'
    ]
  });
  
  const page = await browser.newPage();
  await page.setViewport({width: 1366, height: 768});
  
  console.log('🌐 Loading chatgpt.com...');
  await page.goto('https://chatgpt.com', { 
    waitUntil: 'domcontentloaded',
    timeout: 45000 
  });
  
  // v24: page.waitForTimeout → new Promise
  console.log('⏳ Waiting 5s...');
  await new Promise(r => setTimeout(r, 5000));
  
  await page.screenshot({path: 'before.png', fullPage: true});
  console.log('📸 before.png saved');
  
  console.log('🖱️ CLICK 134,254');
  await page.mouse.click(134, 254);
  
  await new Promise(r => setTimeout(r, 3000));
  
  await page.screenshot({path: 'after.png', fullPage: true});
  console.log('📸 after.png saved');
  
  console.log('✅ SUCCESS!');
  await browser.close();
  
  require('fs').writeFileSync('status.txt', 'OK');
})();
EOF
