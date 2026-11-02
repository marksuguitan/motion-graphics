// Pre-render the lit conduction system at N wavefront levels (atrial from the SA node, ventricular from the AV node).
const {chromium} = require('playwright'); const fs = require('fs'); const path = require('path');
const art = JSON.parse(fs.readFileSync(path.join(__dirname, 'src/data/art.json'), 'utf8'));
const pub = path.join(__dirname, 'public/maps');
const b64 = f => 'data:image/png;base64,' + fs.readFileSync(path.join(pub, f)).toString('base64');
const MAPS = {a: {img: b64('atr.png'), dmax: 975.5, E: 18, B: 110, N: 96}, v: {img: b64('vent.png'), dmax: 2029.8, E: 26, B: 220, N: 128}};
function tables(F, dmax, E, B) {
  const lit = [], band = [];
  for (let i = 0; i < 256; i++) {
    const v = i / 255;
    if (v < 0.035 || F <= 0) { lit.push(0); band.push(0); continue; }
    const d = (1 - (v - 0.05) / 0.95) * dmax;
    const a = Math.max(0, Math.min(1, (F + E - d) / E));
    const b = F >= dmax ? 0 : a * Math.max(0, Math.min(1, 1 - (F - d) / B));
    lit.push(+a.toFixed(3)); band.push(+b.toFixed(3));
  }
  return {lit: lit.join(' '), band: band.join(' ')};
}
const COND = art.cond.map(([d, f]) => `<path d="${d}" fill="${f}" stroke="${f}" stroke-width="0.73"/>`).join('');
const HOT = art.cond.map(([d]) => `<path d="${d}" fill="#FFF0C2" stroke="#FFF0C2" stroke-width="0.73"/>`).join('');
const ftr = (id, tv) => `<filter id="${id}" x="0" y="0" width="8000" height="8000" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB"><feComponentTransfer><feFuncR type="table" tableValues="${tv}"/><feFuncG type="table" tableValues="${tv}"/><feFuncB type="table" tableValues="${tv}"/></feComponentTransfer><feColorMatrix type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  1 0 0 0 0"/></filter>`;
function page(m, F) {
  const t = tables(F, m.dmax, m.E, m.B);
  return `<body style="margin:0;background:transparent"><svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2000" viewBox="0 0 8000 8000"><defs>${ftr('fl', t.lit)}${ftr('fb', t.band)}
  <mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="8000" height="8000"><image href="${m.img}" width="8000" height="8000" filter="url(#fl)"/></mask>
  <mask id="mb" maskUnits="userSpaceOnUse" x="0" y="0" width="8000" height="8000"><image href="${m.img}" width="8000" height="8000" filter="url(#fb)"/></mask>
  <filter id="glow" x="0" y="0" width="8000" height="8000" filterUnits="userSpaceOnUse"><feGaussianBlur stdDeviation="60" in="SourceGraphic" result="b"/><feColorMatrix in="b" type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.85 0" result="bb"/><feMerge><feMergeNode in="bb"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs><g filter="url(#glow)"><g mask="url(#m)">${COND}</g><g mask="url(#mb)" opacity="0.9">${HOT}</g></g></svg></body>`;
}
(async () => {
  const br = await chromium.launch();
  const jobs = [];
  for (const [k, m] of Object.entries(MAPS)) for (let i = 1; i < m.N; i++) jobs.push([k, i, m]);
  const worker = async () => {
    const pg = await br.newPage({viewport: {width: 2000, height: 2000}});
    while (jobs.length) {
      const [k, i, m] = jobs.shift();
      await pg.setContent(page(m, (i / (m.N - 1)) * m.dmax));
      await pg.waitForTimeout(30);
      await pg.screenshot({path: path.join(pub, 'lit', `${k}${String(i).padStart(3, '0')}.png`), omitBackground: true});
    }
  };
  await Promise.all([worker(), worker(), worker(), worker()]);
  await br.close();
})();
