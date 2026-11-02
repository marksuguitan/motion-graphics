// sample the 2A epicardium line (comp px) and the 1C underline, for the Scene 1 -> 2 morph
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const svg = fs.readFileSync('/tmp/claude-0/ai/svg/2A_inhale.svg', 'utf8');
  await p.setContent(`<html><body style="margin:0">${svg}</body></html>`);
  const EPI_ID = JSON.parse(fs.readFileSync('/tmp/claude-0/ai/svg/layers.json'))['2A_inhale'].filter(x => x.name === 'Heart/Epicardium_line')[0].id;
  const out = await p.evaluate((EPI_ID) => {
    const g = document.getElementById(EPI_ID); const paths = g.querySelectorAll('path,circle,ellipse');
    const res = [];
    for (const e of paths) {
      const L = e.getTotalLength(), m = e.getCTM(), N = 96, pts = [];
      for (let i = 0; i < N; i++) { const q = e.getPointAtLength(L * i / N); pts.push([m.a * q.x + m.c * q.y + m.e, m.b * q.x + m.d * q.y + m.f]); }
      res.push({ tag: e.tagName, len: L, sw: parseFloat(getComputedStyle(e).strokeWidth) * Math.sqrt(m.a * m.d - m.b * m.c), stroke: getComputedStyle(e).stroke, pts });
    }
    return res;
  }, EPI_ID);
  fs.writeFileSync('/tmp/claude-0/ae/epi.json', JSON.stringify(out)); await b.close();
  console.log(out.map(o => [o.tag, o.len, o.sw, o.stroke, o.pts.length]));
})();
