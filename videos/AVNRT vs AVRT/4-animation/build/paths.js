// paths.js: samples the stroked paths the build animates along (loops, pathways, channels) from build/ai_src/<beat>.svg,
// in comp pixels, into build/paths.json, and every layer's bounds into build/bboxes.json. Needs Node + Playwright (the cloud workspace has both). Run: node paths.js
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const SRC = path.join(__dirname, 'ai_src');
const WANT = /^(Heart\/(SmallLoop|Loop\/(Down|Up|Across)|HisActive|AccessoryPathway|Gate|FibrousRing)|Diagram\/(Slow|Fast|Stem|His|Channels|Active)|ECG(\/.*)?\/Trace|Bracket\/.*|Focus\/.*)$/;
(async () => {
  const layers = JSON.parse(fs.readFileSync(path.join(SRC, 'layers.json'), 'utf8'));
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const out = {}, boxes = {};
  for (const beat of Object.keys(layers)) {
    const svg = fs.readFileSync(path.join(SRC, beat + '.svg'), 'utf8');
    await p.setContent(`<html><body style="margin:0">${svg}</body></html>`);
    boxes[beat] = await p.evaluate((ls) => { const r = {}; for (const l of ls) { const b = document.getElementById(l.id).getBoundingClientRect(); r[l.name] = [+b.left.toFixed(1), +b.top.toFixed(1), +b.right.toFixed(1), +b.bottom.toFixed(1)]; } return r; }, layers[beat].layers);
    const want = layers[beat].layers.filter(l => WANT.test(l.name));
    if (!want.length) continue;
    out[beat] = await p.evaluate((want) => {
      const r = {};
      for (const l of want) {
        const g = document.getElementById(l.id); const polys = [];
        for (const e of g.querySelectorAll('path,line,circle,ellipse,polyline')) {
          const st = getComputedStyle(e);
          if (st.stroke === 'none' || parseFloat(st.strokeWidth) === 0) continue;
          const L = e.getTotalLength(); const n = Math.max(2, Math.ceil(L * (e.getScreenCTM().a) / 4));
          const m = e.getScreenCTM(); const pts = [];
          for (let i = 0; i <= n; i++) { const q = e.getPointAtLength(L * i / n); pts.push([+(m.a * q.x + m.c * q.y + m.e).toFixed(2), +(m.b * q.x + m.d * q.y + m.f).toFixed(2)]); }
          polys.push({ tag: e.tagName, width: +(parseFloat(st.strokeWidth) * m.a).toFixed(2), color: st.stroke, pts });
        }
        r[l.name] = polys;
      }
      return r;
    }, want);
  }
  fs.writeFileSync(path.join(__dirname, 'paths.json'), JSON.stringify(out));
  fs.writeFileSync(path.join(__dirname, 'bboxes.json'), JSON.stringify(boxes));
  for (const [k, v] of Object.entries(out)) console.log(k, Object.entries(v).map(([n, ps]) => n + ':' + ps.map(q => q.tag + q.pts.length).join(',')).join(' | '));
  await b.close();
})();
