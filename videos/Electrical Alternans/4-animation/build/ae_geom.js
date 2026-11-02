// For every flattened beat SVG: bbox (comp px) of each top-level layer group, its accumulated opacity,
// and needle geometry (pivot + angle) for Gauge/Needle layers.
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
(async () => {
  const dir = process.argv[2]; const map = JSON.parse(fs.readFileSync(path.join(dir, 'layers.json')));
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const out = {};
  for (const beat of Object.keys(map)) {
    const svg = fs.readFileSync(path.join(dir, beat + '.svg'), 'utf8');
    await p.setContent(`<html><body style="margin:0">${svg}</body></html>`);
    out[beat] = await p.evaluate((spec) => {
      const res = {};
      for (const s of spec) {
        const g = document.getElementById(s.id); if (!g) continue;
        // un-hide for measuring
        g.querySelectorAll('[visibility]').forEach(e => e.removeAttribute('visibility'));
        const r = g.getBoundingClientRect();
        let op = 1; let e = g; while (e && e.tagName !== 'svg') { const o = e.getAttribute('opacity'); if (o !== null) op *= parseFloat(o); e = e.parentElement; }
        // content opacity of wrappers inside the layer group
        let inner = g; const ops = [];
        let w = g.firstElementChild; let acc = 1;
        while (w && w.tagName === 'g' && w.children.length === 1 && w.firstElementChild.tagName === 'g') { const o = w.getAttribute('opacity'); if (o !== null) acc *= parseFloat(o); w = w.firstElementChild; }
        if (w) { const o = w.getAttribute && w.getAttribute('opacity'); if (o !== null && w.tagName==='g') acc *= parseFloat(o); }
        const item = { name: s.name, x: r.x, y: r.y, w: r.width, h: r.height, wrapOpacity: acc };
        if (s.name.endsWith('Needle')) {
          const ln = g.querySelector('line');
          if (ln) {
            const m = ln.getScreenCTM();
            const P = (x, y) => { const pt = ln.ownerSVGElement.createSVGPoint(); pt.x = x; pt.y = y; const q = pt.matrixTransform(m); return [q.x, q.y]; };
            const a = P(+ln.getAttribute('x1'), +ln.getAttribute('y1')), c = P(+ln.getAttribute('x2'), +ln.getAttribute('y2'));
            item.needle = { tail: a, tip: c, angle: Math.atan2(c[1] - a[1], c[0] - a[0]) * 180 / Math.PI };
          }
        }
        res[s.name] = item;
      }
      // hub centres
      const hubs = [...document.querySelectorAll('[id$="Hub"], circle#Hub')].map(h => { const r = h.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; });
      res.__hubs = hubs;
      return res;
    }, map[beat]);
  }
  fs.writeFileSync(process.argv[3], JSON.stringify(out, null, 1)); await b.close();
})();
