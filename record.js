const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());
const { spawn } = require('child_process');

(async () => {
  try {
    console.log('🚀 Browser launch...');
    const browser = await puppeteer.launch({
      headless: false,
      userDataDir: './user_data',
      executablePath: '/opt/hostedtoolcache/chromium/latest/x64/chrome',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--window-size=1366,768'
      ]
    });
    
    const page = await browser.newPage();
    await page.setViewport({width: 1366, height: 768});
    
    const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
    
    console.log('🎥 Starting screen record...');
    const ffmpeg = require('ffmpeg-static');
    const recordProc = spawn(ffmpeg, [
      '-f', 'x11grab',
      '-s', '1366x768',
      '-r', '25',
      '-i', ':99.0',
      '-t', '30',
      '-c:v', 'libx264',
      '-pix_fmt', 'yuv420p',
      './record/demo.mp4'
    ]);
    
    // ChatGPT
    console.log('🌐 Loading chatgpt.com...');
    await page.goto('https://chatgpt.com', { timeout: 60000 });
    await delay(4000);
    await page.screenshot({ path: 'step1_chatgpt.png' });
    
    // Click
    console.log('🖱️ Clicking (134, 254)...');
    await page.mouse.click(134, 254);
    await delay(2500);
    await page.screenshot({ path: 'step2_clicked.png' });
    
    // Type
    console.log('⌨️ Typing "سلام! چطوری؟"...');
    await page.keyboard.type('سلام! چطوری؟', { delay: 100 });
    await delay(4000);
    await page.screenshot({ path: 'step3_typed.png' });
    
    // Finish
    console.log('⏹️ Stopping record...');
    recordProc.kill('SIGINT');
    await delay(3000);
    await browser.close();
    
    console.log('✅ Video saved: record/demo.mp4');
    console.log('📸 Screenshots: step1.png, step2.png, step3.png');
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
})();
