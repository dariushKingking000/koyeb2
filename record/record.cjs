const puppeteer = require('puppeteer');
(async () => {
  try {
    const instructions = [
      '[click 200 400]'
    ];
    console.log(`📋 ${instructions.length} instructions loaded`);
    
    const browser = await puppeteer.launch({
      headless: false,
      args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1366, height: 768 });
    await page.goto('https://chatgpt.com', { waitUntil: 'networkidle0' });
    await new Promise(r=>setTimeout(r,5000));
    console.log('🌐 ChatGPT loaded');

    const selectors = ['textarea','[contenteditable="true"]','[data-id="root"] textarea','div[contenteditable]','.ProseMirror','prompt-textarea','[role="textbox"]'];

    for(let i=0; i<instructions.length; i++){
      const cmd = instructions[i];
      console.log(`🔄 ${i+1}/9: ${cmd}`);
      
      if(cmd.startsWith('[type ')){
        let found=false;
        for(const selector of selectors){
          try{
            await page.waitForSelector(selector,{timeout:3000});
            const el=await page.$(selector);
            await el.click();
            const text=cmd.slice(6,-1);
            await page.keyboard.type(text,{delay:80});
            console.log(`✅ Typed: "${text}"`);
            found=true;
            break;
          }catch(e){}
        }
        if(!found) await page.keyboard.press('Enter');
      }else if(cmd.startsWith('[click ')){
        const [x,y]=cmd.slice(7,-1).split(' ').map(Number);
        await page.mouse.click(x,y);
        console.log(`🖱️ Clicked (${x},${y})`);
      }else if(cmd.startsWith('[wait ')){
        const s=parseInt(cmd.slice(6,-1));
        await new Promise(r=>setTimeout(r,s*1000));
        console.log(`⏳ Waited ${s}s`);
      }
    }
    
    console.log('🎬 Closing...');
    await new Promise(r=>setTimeout(r,5000));
    await browser.close();
    console.log('✅ Complete!');
  }catch(e){
    console.error('❌',e.message);
    process.exit(1);
  }
})();
