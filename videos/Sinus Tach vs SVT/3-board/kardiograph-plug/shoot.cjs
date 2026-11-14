// node shoot.cjs  -> frames/<id>.png (1920x1080) from keyframes.html, plus opener-sheet.png and end-sheet.png
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const { execFileSync } = require('child_process');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + path.join(__dirname, 'keyframes.html'));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(300);
  const out = path.join(__dirname, 'frames');
  fs.mkdirSync(out, { recursive: true });
  for (const el of await p.$$('.f')) {
    const id = await el.getAttribute('id');
    await el.screenshot({ path: path.join(out, `${id}.png`) });
  }
  await b.close();
  for (const [sheet, ids] of [['opener-sheet.png', ['K1', 'K2', 'K3', 'K4']], ['end-sheet.png', ['E1', 'E2', 'E3', 'E4']]]) {
    const args = ids.flatMap((id) => ['-i', path.join(out, `${id}.png`)]);
    const scale = ids.map((_, i) => `[${i}]scale=960:540,pad=980:560:10:10:0xC8C8C8[s${i}]`).join(';');
    execFileSync('ffmpeg', ['-v', 'error', '-y', ...args, '-filter_complex',
      `${scale};${ids.map((_, i) => `[s${i}]`).join('')}xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0`, path.join(__dirname, sheet)]);
  }
})();
