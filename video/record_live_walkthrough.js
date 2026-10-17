const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://127.0.0.1:8080';
const OUT_DIR = path.join(__dirname, 'raw_recordings');
const TIMINGS_FILE = path.join(__dirname, 'walkthrough_recording_timings.json');

if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

async function injectCursor(page) {
  await page.evaluate(() => {
    if (document.getElementById('playwright-cursor')) return;
    const cursor = document.createElement('div');
    cursor.id = 'playwright-cursor';
    cursor.style.position = 'fixed';
    cursor.style.width = '24px';
    cursor.style.height = '24px';
    cursor.style.borderRadius = '50%';
    cursor.style.backgroundColor = 'rgba(234, 88, 12, 0.85)';
    cursor.style.border = '2.5px solid #ffffff';
    cursor.style.boxShadow = '0 0 12px rgba(0,0,0,0.6)';
    cursor.style.pointerEvents = 'none';
    cursor.style.zIndex = '999999';
    cursor.style.transition = 'transform 0.12s ease-out, background-color 0.12s';
    cursor.style.transform = 'translate(-50%, -50%)';
    cursor.style.left = '960px';
    cursor.style.top = '540px';
    document.body.appendChild(cursor);

    window.addEventListener('mousemove', e => {
      cursor.style.left = e.clientX + 'px';
      cursor.style.top = e.clientY + 'px';
    });
    window.addEventListener('mousedown', () => {
      cursor.style.backgroundColor = 'rgba(56, 189, 248, 0.95)';
      cursor.style.transform = 'translate(-50%, -50%) scale(0.8)';
    });
    window.addEventListener('mouseup', () => {
      cursor.style.backgroundColor = 'rgba(234, 88, 12, 0.85)';
      cursor.style.transform = 'translate(-50%, -50%) scale(1.0)';
    });
  });
}

async function smoothMove(page, targetX, targetY, steps = 25) {
  await page.mouse.move(targetX, targetY, { steps });
}

async function run() {
  console.log('====================================================');
  console.log('RECORDING ACTUAL RUNNING TRIPLINE WEBSITE WALKTHROUGH');
  console.log('Target URL: ' + BASE_URL);
  console.log('Viewport: 1920x1080 (1080p Desktop)');
  console.log('====================================================');

  const browser = await chromium.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true
  });

  const context = await browser.newContext({
    recordVideo: {
      dir: OUT_DIR,
      size: { width: 1920, height: 1080 }
    },
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1
  });

  const page = await context.newPage();
  const timings = [];
  const startTime = Date.now();

  function mark(beatId, title, url) {
    const elapsed = (Date.now() - startTime) / 1000;
    console.log(`[*] [${elapsed.toFixed(2)}s] ${beatId}: ${title} (${url})`);
    timings.push({ beatId, title, url, timestamp: elapsed });
  }

  // --- BEAT 1: Homepage Hero & Overview ---
  mark('W01', 'Homepage Hero & System Status', BASE_URL + '/');
  await page.goto(BASE_URL + '/', { waitUntil: 'networkidle' });
  await injectCursor(page);
  await page.waitForTimeout(1000);
  await smoothMove(page, 450, 320); // Hover over Mode B integration tag
  await page.waitForTimeout(1500);
  await smoothMove(page, 240, 480); // Hover over "Launch Governed Demo"
  await page.waitForTimeout(2000);
  await smoothMove(page, 420, 480); // Hover over "Explore 4-Plane Architecture"
  await page.waitForTimeout(2500);
  await smoothMove(page, 960, 500);
  await page.waitForTimeout(3000);
  await smoothMove(page, 1400, 350); // Hover over decisions telemetry chart
  await page.waitForTimeout(4000);

  // --- BEAT 2: 4-Plane Security Architecture Section ---
  mark('W02', '4-Plane Security Architecture View', BASE_URL + '/#architecture');
  await page.evaluate(() => {
    document.getElementById('architecture')?.scrollIntoView({ behavior: 'smooth' });
  });
  await page.waitForTimeout(2000);
  await smoothMove(page, 300, 300); // Hover Plane 0
  await page.waitForTimeout(2500);
  await smoothMove(page, 650, 300); // Hover Plane 1
  await page.waitForTimeout(2500);
  await smoothMove(page, 1050, 300); // Hover Plane 2
  await page.waitForTimeout(2500);
  await smoothMove(page, 1450, 300); // Hover Plane 3
  await page.waitForTimeout(3500);

  // --- BEAT 3: Governed Execution Demo Console ---
  mark('W03', 'Live Execution Console & Triage Queue', BASE_URL + '/#workflow');
  await page.evaluate(() => {
    document.getElementById('workflow')?.scrollIntoView({ behavior: 'smooth' });
  });
  await page.waitForTimeout(2000);
  await smoothMove(page, 320, 300); // Hover Task 1: Multi-Layer Security Proof
  await page.waitForTimeout(2000);
  await smoothMove(page, 580, 300); // Hover Task 2: Jail Burst
  await page.waitForTimeout(2000);
  await smoothMove(page, 850, 300); // Hover Task 3: REA
  await page.waitForTimeout(2000);
  await smoothMove(page, 320, 300); // Select Task 1
  await page.click('[data-local="select-task-scenario"]');
  await page.waitForTimeout(2000);
  await smoothMove(page, 600, 650); // Move over terminal stream box
  await page.waitForTimeout(4000);

  // --- BEAT 4: Interactive Security Lab (Credential Scanner) ---
  mark('W04', 'Interactive Credential Scanner & DLP Guard', BASE_URL + '/#demo-console');
  await smoothMove(page, 450, 180);
  await page.click('[data-local="tab-credential-scan"]');
  await page.waitForTimeout(2500);
  await smoothMove(page, 500, 350); // View entropy calculations
  await page.waitForTimeout(3000);
  await smoothMove(page, 1200, 450); // Inspect ArmorIQ interception badge
  await page.waitForTimeout(4000);

  // --- BEAT 5: Governed Agent Console (/agent) ---
  mark('W05', 'Governed Agent Console & Scoped Delegation', BASE_URL + '/agent');
  await page.goto(BASE_URL + '/agent', { waitUntil: 'networkidle' });
  await injectCursor(page);
  await page.waitForTimeout(2000);
  await smoothMove(page, 400, 260); // Hover Orchestrator Crew
  await page.waitForTimeout(2500);
  await smoothMove(page, 800, 260); // Hover Reader Crew
  await page.waitForTimeout(2500);
  await smoothMove(page, 1200, 260); // Hover Responder Crew
  await page.waitForTimeout(2500);
  await smoothMove(page, 600, 600); // Inspect Live SSE Stream box
  await page.waitForTimeout(4500);

  // --- BEAT 6: How It Works & Invariants (/how-it-works) ---
  mark('W06', 'How It Works & Technical Architecture Walkthrough', BASE_URL + '/how-it-works');
  await page.goto(BASE_URL + '/how-it-works', { waitUntil: 'networkidle' });
  await injectCursor(page);
  await page.waitForTimeout(2000);
  await smoothMove(page, 500, 350);
  await page.waitForTimeout(2500);
  await page.mouse.wheel(0, 500); // Scroll down
  await page.waitForTimeout(3000);
  await smoothMove(page, 600, 500);
  await page.waitForTimeout(3500);

  // --- BEAT 7: Path Jail 24-Probe Burst Probe (/jail-burst) ---
  mark('W07', 'Path Jail 24-Probe Burst Fuzzer', BASE_URL + '/jail-burst');
  await page.goto(BASE_URL + '/jail-burst', { waitUntil: 'networkidle' });
  await injectCursor(page);
  await page.waitForTimeout(2000);
  await smoothMove(page, 400, 300); // Inspect 24/24 trapped probes badge
  await page.waitForTimeout(2500);
  await smoothMove(page, 700, 450); // Probe table
  await page.waitForTimeout(3000);
  await page.mouse.wheel(0, 400); // Scroll down probe list
  await page.waitForTimeout(3500);

  // --- BEAT 8: Forensic Incident Receipts Explorer (/receipts) ---
  mark('W08', 'Forensic Incident Receipts Explorer', BASE_URL + '/receipts');
  await page.goto(BASE_URL + '/receipts', { waitUntil: 'networkidle' });
  await injectCursor(page);
  await page.waitForTimeout(2000);
  await smoothMove(page, 500, 280); // Inspect receipts list
  await page.waitForTimeout(2500);
  await smoothMove(page, 1400, 280); // View HMAC signature column
  await page.waitForTimeout(3000);
  // Click first receipt item or verify button if available
  const firstReceipt = await page.$('tr, [data-testid^="receipt-"], .receipt-card');
  if (firstReceipt) {
    await firstReceipt.click();
    await page.waitForTimeout(3000);
  }
  await page.waitForTimeout(3000);

  // --- BEAT 9: Witness Log Chain Viewer (/witness) ---
  mark('W09', 'Witness Log HMAC Hash Chain', BASE_URL + '/witness');
  await page.goto(BASE_URL + '/witness', { waitUntil: 'networkidle' });
  await injectCursor(page);
  await page.waitForTimeout(2000);
  await smoothMove(page, 450, 300); // Sequential hash links
  await page.waitForTimeout(3000);
  await smoothMove(page, 950, 400); // Chain verification badge
  await page.waitForTimeout(3500);

  // --- BEAT 10: Measured Evaluation Scoreboard (/measured) ---
  mark('W10', 'Empirical 86-Run Benchmark Matrix', BASE_URL + '/measured');
  await page.goto(BASE_URL + '/measured', { waitUntil: 'networkidle' });
  await injectCursor(page);
  await page.waitForTimeout(2000);
  await smoothMove(page, 400, 320); // Arm A: 0% Defense
  await page.waitForTimeout(2500);
  await smoothMove(page, 750, 320); // Arm B: 37.5% Defense
  await page.waitForTimeout(2500);
  await smoothMove(page, 1150, 320); // Arm C: 100% Defense
  await page.waitForTimeout(3000);
  await page.mouse.wheel(0, 350);
  await page.waitForTimeout(3500);

  // --- BEAT 11: Claims & Truth Ledger (/claims) ---
  mark('W11', 'Verified Security Claims Ledger', BASE_URL + '/claims');
  await page.goto(BASE_URL + '/claims', { waitUntil: 'networkidle' });
  await injectCursor(page);
  await page.waitForTimeout(2000);
  await smoothMove(page, 500, 350); // Inspect 22 claims list
  await page.waitForTimeout(3000);
  await page.mouse.wheel(0, 400);
  await page.waitForTimeout(3500);

  // --- BEAT 12: Layer Attribution Matrix (/attribution) ---
  mark('W12', 'Three-Layer Defense Attribution', BASE_URL + '/attribution');
  await page.goto(BASE_URL + '/attribution', { waitUntil: 'networkidle' });
  await injectCursor(page);
  await page.waitForTimeout(2000);
  await smoothMove(page, 600, 350); // Attribution breakdown
  await page.waitForTimeout(3500);

  // --- BEAT 13: Closing Return to Homepage (/) ---
  mark('W13', 'Platform Summary & Closing Walkthrough', BASE_URL + '/');
  await page.goto(BASE_URL + '/', { waitUntil: 'networkidle' });
  await injectCursor(page);
  await page.waitForTimeout(1500);
  await smoothMove(page, 960, 450); // Center brand title
  await page.waitForTimeout(3500);

  // Finalize video
  const totalDuration = (Date.now() - startTime) / 1000;
  console.log(`[+] Walkthrough completed in ${totalDuration.toFixed(2)}s`);

  const videoPath = await page.video().path();
  await context.close();
  await browser.close();

  fs.writeFileSync(TIMINGS_FILE, JSON.stringify({
    totalDuration,
    rawVideoPath: videoPath,
    beats: timings
  }, null, 2));

  console.log('Saved raw recording to:', videoPath);
  console.log('Saved timings to:', TIMINGS_FILE);
}

run().catch(err => {
  console.error('Fatal recording error:', err);
  process.exit(1);
});
