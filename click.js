- name: Create Click Script
      run: |
        cat > click.js << 'EOF'
        const puppeteer = require('puppeteer-extra');
        const StealthPlugin = require('puppeteer-extra-plugin-stealth');
        const fs = require('fs');
        
        puppeteer.use(StealthPlugin());
        
        const config = {
          url: 'https://chatgpt.com',
          x: 134, 
          y: 254,
          timestamp: new Date().toISOString()
        };
        
        fs.writeFileSync('config.json', JSON.stringify(config, null, 2));
        
        (async () => {
          console.log('🚀 Stealth Browser');
          
          const browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
          });
          
          const page = await browser.newPage();
          await page.setViewport({width: 1366, height: 768});
          
          console.log('🌐 Loading...');
          await page.goto(config.url, {waitUntil: 'domcontentloaded', timeout: 60000});
          
          console.log('⏳ Waiting...');
          await new Promise(r => setTimeout(r, 8000));
          
          await page.screenshot({path: 'before.png', fullPage: true});
          
          console.log('🖱️ Click ' + config.x + ',' + config.y);
          await page.mouse.click(config.x, config.y);
          
          // Red circle
          await page.evaluate(function(x, y) {
            var circle = document.createElement('div');
            circle.style.cssText = 'position:fixed;left:' + (x-10) + 'px;top:' + (y-10) + 'px;width:20px;height:20px;background:#f00;border-radius:50%;z-index:99999;pointer-events:none;box-shadow:0 0 10px #f00';
            document.body.appendChild(circle);
          }, config.x, config.y);
          
          await new Promise(r => setTimeout(r, 3000));
          
          await page.screenshot({path: 'after.png', fullPage: true});
          
          console.log('✅ Done!');
          await browser.close();
          
          fs.writeFileSync('status.txt', 'SUCCESS\nClicked: ' + config.x + ',' + config.y + '\nTime: ' + config.timestamp);
        })().catch(function(e) {
          console.error('Error:', e.message);
          fs.writeFileSync('status.txt', 'ERROR: ' + e.message);
          process.exit(1);
        });
        EOF
