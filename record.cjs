const puppeteer = require('puppeteer');
const fs = require('fs/promises');

async function safeWait(timeout) {
  return new Promise(resolve => setTimeout(resolve, timeout));
}

(async () => {
  let browser = null;
  let page = null;
  
  try {
    const data = await fs.readFile('./instructions.txt', 'utf8');
    const instructions = data.split('\n')
      .map(l => l.trim())
      .filter(l => l && l.startsWith('[') && l.endsWith(']'));
    
    console.log(`📋 ${instructions.length} دستور`);
    
    browser = await puppeteer.launch({
      headless: false,
      args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
    });
    
    page = await browser.newPage();
    await page.setViewport({ width: 1366, height: 768 });
    await page.goto('https://chatgpt.com', { waitUntil: 'networkidle0', timeout: 15000 });
    await safeWait(3000);
    console.log('🌐 ChatGPT آماده');
    
    const selectors = [
      'div[contenteditable]', 'textarea', '[contenteditable="true"]', 
      '[data-id="root"] textarea', '.ProseMirror', '[role="textbox"]'
    ];

    for (let i = 0; i < instructions.length; i++) {
      const cmd = instructions[i];
      console.log(`#${i+1}/${instructions.length}: ${cmd}`);
      
      if (!page || page.isClosed?.()) {
        console.log('⚠️ Page بسته');
        break;
      }
      
      const start = Date.now();
      const maxTime = 20000;
      
      if (cmd.startsWith('[type ')) {
        console.log('⌨️ تایپ (20s max)...');
        const text = cmd.slice(6, -1);
        
        try {
          await page.waitForSelector(selectors.join(','), { timeout: 3000 });
          await page.click(selectors.join(','));
          await page.keyboard.type(text, { delay: 25 });
          await page.keyboard.press('Enter');
          console.log(`✅ "${text}"`);
        } catch {
          await page.keyboard.type(text, { delay: 25 });
          await page.keyboard.press('Enter');
          console.log(`✅ "${text}"`);
        }
        
      } else if (cmd.startsWith('[click ')) {
        console.log('🖱️ کلیک (20s max)...');
        const [x, y] = cmd.slice(7, -1).split(' ').map(Number);
        
        try {
          await page.mouse.click(x, y);
          console.log(`✅ کلیک (${x},${y})`);
        } catch {
          console.log('⚠️ کلیک');
        }
        
      } else if (cmd.startsWith('[wait ')) {
        const s = Math.min(parseInt(cmd.slice(6, -1)), 20);
        console.log(`⏳ ${s}s`);
        await safeWait(s * 1000);
      }
      
      const elapsed = Date.now() - start;
      const remaining = Math.max(0, maxTime - elapsed);
      if (remaining > 0) await safeWait(remaining);
      
      const totalTime = Math.round((Date.now() - start) / 1000);
      if (i === instructions.length - 1) {
        console.log('🏁 تمام شد!');
      } else {
        console.log(`⏱️ ${totalTime}s تمام → #${i+2}`);
      }
    }
    
  } catch(e) {
    console.log('❌ خطا:', e.message);
  } finally {
    console.log('🔒 بستن...');
    try { if (page) await page.close(); } catch(e) {}
    try { if (browser) await browser.close(); } catch(e) {}
    console.log('✅ OK');
  }
})();
