# فقط این بخش record.cjs رو جایگزین کن:

- name: Create record.cjs (FINAL FIXED)
  run: |
    cat > record.cjs << 'JS_EOF'
    const puppeteer = require('puppeteer');
    const fs = require('fs/promises');

    (async () => {
      try {
        const data = await fs.readFile('./record/instructions.txt', 'utf8');
        const instructions = data.split('\n')
          .map(l => l.trim())
          .filter(l => l && l.startsWith('[') && l.endsWith(']'));
        
        console.log(`📋 ${instructions.length} دستور\\n🎥 شروع...`);
        
        const browser = await puppeteer.launch({
          headless: false,
          args: ['--no-sandbox', '--disable-dev-shm-usage']
        });
        
        const page = await browser.newPage();
        await page.setViewport({ width: 1366, height: 768 });
        await page.goto('https://chatgpt.com', { waitUntil: 'networkidle0' });
        
        await new Promise(r => setTimeout(r, 5000));
        console.log('🌐 لود شد');

        const selectors = ['textarea','[contenteditable="true"]','[role="textbox"]'];

        for (let i = 0; i < instructions.length; i++) {
          const cmd = instructions[i];
          console.log(\`🔄 #\${i + 1}: \${cmd}\`);
          
          if (cmd.startsWith('[type ')) {
            let found = false;
            for (const selector of selectors) {
              try {
                await page.waitForSelector(selector, { timeout: 5000 });
                const el = await page.$(selector);
                await el.click();
                const text = cmd.slice(6, -1);
                await page.keyboard.type(text);
                console.log(\`✅ "\${text}" تایپ شد\`);
                found = true;
                break;
              } catch(e) {}
            }
            if (!found) {
              console.log('⚠️ input پیدا نشد');
              await page.keyboard.press('Enter');
            }
          } else if (cmd.startsWith('[click ')) {
            const [x, y] = cmd.slice(7, -1).split(' ').map(Number);
            await page.mouse.click(x, y);
          } else if (cmd.startsWith('[wait ')) {
            const s = parseInt(cmd.slice(6, -1));
            await new Promise(r => setTimeout(r, s * 1000));
          }
        }
        
        await new Promise(r => setTimeout(r, 10000));
        await browser.close();
        console.log('✅ تمام!');
      } catch (e) {
        console.error('❌ خطا:', e.message);
        process.exit(1);
      }
    })();
    JS_EOF
