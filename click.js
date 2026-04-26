const puppeteer = require('puppeteer');
(async () => {
  console.log("🚀 Launching browser...");
  const browser = await puppeteer.launch({
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--single-process"
    ]
  });
  
  const page = await browser.newPage();
  await page.setViewport({width:1920, height:1080});
  
  console.log("🌐 Going to chatgpt.com...");
  await page.goto("https://chatgpt.com", {timeout: 60000});
  
  await page.screenshot({path: "before.png"});
  console.log("📸 Before screenshot OK");
  
  await page.mouse.click(831, 589);
  console.log("🖱️ Clicked!");
  
  await page.waitForTimeout(3000);
  await page.screenshot({path: "after.png"});
  console.log("📸 After screenshot OK");
  
  await browser.close();
  console.log("✅ Complete!");
})().catch(e => {
  console.error("❌", e.message);
  process.exit(1);
});
