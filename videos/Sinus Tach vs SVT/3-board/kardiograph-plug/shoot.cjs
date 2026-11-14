// node shoot.cjs  -> frames/K1.png..K4.png (1920x1080) from keyframes.html
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + path.join(__dirname, 'keyframes.html'));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(300);
  fs.mkdirSync(path.join(__dirname, 'frames'), { recursive: true });
  const els = await p.$$('.f');
  for (let i = 0; i < els.length; i++) await els[i].screenshot({ path: path.join(__dirname, 'frames', `K${i + 1}.png`) });
  await b.close();
})();
