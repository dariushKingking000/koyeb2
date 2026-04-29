cat > record.cjs << 'JS_EOF'
const puppeteer = require('puppeteer');
const fs = require('fs/promises');

(async () => {
  let browser = null;
  let page = null;
  
  const TIMEOUT = 20000;
  const POLL_INTERVAL = 500;
  
  try {
    const data = await fs.readFile('./instructions.txt', 'utf8');
    const instructions = data.split('\n')
      .map(l => l.trim())
      .filter(l => l && l.startsWith('[') && l.endsWith(']'));
    
    console.log(`📋 ${instructions.length} دستور\n🎥 شروع...`);
    
    browser = await puppeteer.launch({
      headless: false,
      args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--disable-web-security']
    });
    
    page = await browser.newPage();
    await page.setViewport({ width: 1366, height: 768 });
    await page.goto('https://chatgpt.com', { waitUntil: 'networkidle0', timeout: 30000 });
    
    await new Promise(r => setTimeout(r, 4000));
    console.log('🌐 صفحه لود شد');

    const selectors = [
      'div[contenteditable]', 'textarea', '[contenteditable="true"]', 
      '[data-id="root"] textarea', '.ProseMirror', 'prompt-textarea', 
      '[role="textbox"]', 'textarea[placeholder*="message"]'
    ];

    for (let i = 0; i < instructions.length; i++) {
      const cmd = instructions[i];
      console.log(`🔄 #${i + 1}/${instructions.length}: ${cmd}`);
      
      if (!page || page.isClosed()) {
        console.log('⚠️ Page بسته → skip');
        continue;
      }
      
      const cmdStart = Date.now();
      
      if (cmd.startsWith('[type ')) {
        const text = cmd.slice(6, -1);
        console.log('⌨️ تایپ...');
        
        let success = false;
        const typeStart = Date.now();
        
        while (Date.now() - typeStart < TIMEOUT && page && !page.isClosed()) {
          try {
            const input = await page.waitForSelector(selectors.join(','), { timeout: 1500 });
            await input.click({ timeout: 1000 });
            await page.keyboard.type(text, { delay: 30 });
            await page.keyboard.press('Enter');
            console.log(`✅ "${text}" تایپ (${Math.round((Date.now()-typeStart)/1000)}s)`);
            success = true;
            break;
          } catch(e) {
            await new Promise(r => setTimeout(r, POLL_INTERVAL));
          }
        }
        
        if (!success) {
          console.log('⚠️ مستقیم تایپ (safe)...');
          try {
            await page.keyboard.type(text.slice(0, 50), { delay: 30 }); // کوتاه
            await page.keyboard.press('Enter');
            console.log(`✅ safe تایپ`);
          } catch(e) {
            console.log('⚠️ حتی safe هم نشد');
          }
        }
        
      } else if (cmd.startsWith('[click ')) {
        const [x, y] = cmd.slice(7, -1).split(' ').map(Number);
        console.log(`🖱️ کلیک (${x},${y})`);
        try {
          await page.mouse.click(x, y, { timeout: 2000 });
          console.log('✅ کلیک OK');
        } catch(e) {
          console.log('⚠️ کلیک skip');
        }
        
      } else if (cmd.startsWith('[wait ')) {
        const s = parseInt(cmd.slice(6, -1));
        console.log(`⏳ ${s}s...`);
        await new Promise(r => setTimeout(r, s * 1000));
      }
      
      if (Date.now() - cmdStart > TIMEOUT) {
        console.log('⏰ 20s → بعدی!');
      }
    }
    
    console.log('🏁 تمام!');
    
  } catch (e) {
    console.error('❌ خطا:', e.message);
  } finally {
    try {
      if (page) await page.close();
      if (browser) await browser.close();
    } catch(e) {}
  }
})();
JS_EOF
