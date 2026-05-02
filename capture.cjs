const puppeteer = require('puppeteer');
const fs = require('fs');
const { execSync } = require('child_process');

async function continuousCapture(page, prefix, durationMs = 5000) {
  fs.mkdirSync('screenshots', { recursive: true });
  const startTime = Date.now();
  let frameNum = 1;
  
  console.log(`📸 شروع ${prefix} (${durationMs/1000}s)`);
  
  while(Date.now() - startTime < durationMs) {
    await page.screenshot({ 
      path: `./screenshots/${prefix}_f${frameNum}.png`, 
      fullPage: true 
    });
    console.log(`📸 screenshots/${prefix}_f${frameNum}.png`);
    frameNum++;
    await new Promise(r => setTimeout(r, 1000));
  }
  console.log(`✅ ${prefix} تمام (${frameNum-1} frame)\n`);
}

(async () => {
  console.log('🚀 Screen Capture Bot شروع شد\n');
  
  const browser = await puppeteer.launch({
    headless: false,
    args: [
      '--no-sandbox', 
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--disable-background-timer-throttling',
      '--disable-backgrounding-occluded-windows',
      '--disable-renderer-backgrounding'
    ]
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1366, height: 768 });
  await page.goto('https://app.n8n.cloud/register', { waitUntil: 'networkidle0' });
  console.log('✅ صفحه n8n لود شد\n');
  
  let actionCount = 0;
  const instructions = [
    '[click 564 264]',
    '[type kingking@gmail.com]',
    '[click 640 330]',
    '[wait 10]',
    '[type 234568]',
    '[click 583 492]'
  ];
  
  // Capture اولیه
  await continuousCapture(page, `start_0_initial`, 5000);
  actionCount++;
  
  for(let action of instructions) {
    console.log(`🔄 STEP ${actionCount}: ${action}`);
    
    // قبل از action
    await continuousCapture(page, `${actionCount}_before_${action.replace(/[\[\] ]/g,'')}`, 5000);
    
    // اجرای action  
    if(action.startsWith('[click ')){
      const [x, y] = action.slice(7, -1).split(' ').map(Number);
      await page.mouse.click(x, y);
      console.log(`🖱️ Clicked (${x},${y})`);
    } else if(action.startsWith('[type ')){
      const text = action.slice(6, -1).trim();
      
      if(text === '234568'){
        console.log('🔍 منتظر OTP...');
        let otp = '';
        let attempts = 0;
        
        while(attempts < 30) {
          console.log(`⏳ تلاش ${attempts + 1}/30`);
          try {
            execSync('git fetch origin main && git reset --hard origin/main', {timeout: 30000});
            if(fs.existsSync('numbers.txt')) {
              otp = fs.readFileSync('numbers.txt', 'utf8').trim();
              console.log(`📄 OTP: ${otp}`);
              if(otp.length === 6 && /^\d{6}$/.test(otp)) break;
            }
          } catch(e) {}
          attempts++;
          await new Promise(r => setTimeout(r, 30000));
        }
        
        if(otp) {
          for(let char of otp) {
            await page.keyboard.type(char, {delay: 300});
          }
          console.log(`✅ OTP ${otp} تایپ شد`);
        } else {
          throw new Error('❌ OTP پیدا نشد');
        }
      } else {
        await page.keyboard.type(text, {delay: 150});
        console.log(`✅ ${text} تایپ شد`);
      }
    } else if(action.includes('wait 10')) {
      await new Promise(r => setTimeout(r, 10000));
      console.log('⏳ 10 ثانیه صبر');
    }
    
    // بعد از action
    await continuousCapture(page, `${actionCount}_after_${action.replace(/[\[\] ]/g,'')}`, 5000);
    actionCount++;
  }
  
  // نهایی
  await continuousCapture(page, `end_final_result`, 5000);
  await browser.close();
  
  const totalFrames = require('child_process').execSync('ls screenshots/*.png 2>/dev/null | wc -l', {encoding: 'utf8'}).trim();
  console.log(`🎉 تمام! کل ${totalFrames} frame گرفته شد`);
})();

