const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const base = process.env.BASE_URL || 'http://localhost:3000';
  const url = `${base}/dashboard`;
  const outDir = path.resolve(__dirname, '..', 'test_results');
  try { fs.mkdirSync(outDir, { recursive: true }); } catch (e) {}

  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  const consoleMessages = [];
  const failedRequests = [];
  const responses = [];

  page.on('console', msg => {
    consoleMessages.push({ type: msg.type(), text: msg.text() });
  });

  page.on('requestfailed', req => {
    failedRequests.push({ url: req.url(), method: req.method(), failure: req.failure()?.errorText });
  });

  page.on('response', async res => {
    const url = res.url();
    if (url.includes('/api/')) {
      let body = null;
      try { body = await res.text(); } catch (e) { body = '<unreadable>'; }
      responses.push({ url, status: res.status(), ok: res.ok(), body: body ? (body.length>1000? body.slice(0,1000)+"...": body) : null });
    }
  });

  console.log('Opening', url);
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
  } catch (e) {
    console.error('Navigation failed:', e.message);
  }

  // wait a moment for sockets and background fetches
  await page.waitForTimeout(2000);

  const report = { url, consoleMessages, failedRequests, responses };
  const outPath = path.join(outDir, 'playwright_check.json');
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2));
  console.log('Report written to', outPath);

  await browser.close();
  process.exit(0);
})();
