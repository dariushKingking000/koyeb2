import puppeteer from 'puppeteer';
import { spawn } from 'child_process';
import fs from 'fs/promises';

(async () => {
  // instructions.txt
  const instructions = await fs.readFile('./instructions.txt', 'utf8')
    .then(c => c.split('\n').map(l=>l.trim()).filter(l=>l&&l.startsWith('[')&&l.endsWith(']')))
    .catch(() => { console.log('❌ instructions.txt پیدا نشد!'); process.exit(1); });
  
  console.log(`📋 ${instructions.length} دستور`);

  // Xvfb + FFmpeg
  spawn('Xvfb', [':99', '-screen', '0', '1366x768x24']);
  spawn('ffmpeg', ['-f','x11grab','-s','1366x768','-r','25','-i',':99+0,0','-t','120','-c:v','libx264','./record/demo_full.mp4']);

  // Browser
  const browser = await puppeteer.launch({headless:false,args:['--display=:99','--no-sandbox']});
  const page = await browser.newPage();
  await page.setViewport({width:1366,height:768});
  
  await page.goto('https://chatgpt.com',{waitUntil:'networkidle0'});
  console.log('🌐 ChatGPT آماده\n🎥 ضبط...\n');
  await page.waitForTimeout(2000);

  // اجرا
  for(let i=0; i<instructions.length; i++){
    const cmd = instructions[i];
    console.log(`🔄 #${i+1}/${instructions.length}: ${cmd}`);
    
    if(cmd.startsWith('[type ')){
      const text = cmd.slice(6,-1);
      await page.click('textarea',{timeout:5000});
      await page.keyboard.type(text,{delay:80});
      console.log(`✅ "${text}"`);
    }
    else if(cmd.startsWith('[click ')){
      const [x,y]=cmd.slice(7,-1).split(' ').map(Number);
      await page.mouse.click(x,y);
      console.log(`🖱️ (${x},${y})`);
    }
    else if(cmd.startsWith('[wait ')){
      const s=parseInt(cmd.slice(6,-1));
      await page.waitForTimeout(s*1000);
      console.log(`⏳ ${s}s`);
    }
    console.log('');
  }

  await page.waitForTimeout(5000);
  await browser.close();
  console.log('🎉 demo_full.mp4 آماده!');
})();
