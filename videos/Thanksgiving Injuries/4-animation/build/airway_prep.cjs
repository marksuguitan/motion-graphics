#!/usr/bin/env node
// airway_prep.cjs: turns Mark's airway illustration (3-board/art/airways original.svg, uploaded Nov 25, 2026) into
// inline art for the dinner scene: drops Illustrator's invisible guide paths and the page background, and maps its
// colours onto this video's palette (coral, teal and amber stay free for injury, fix and ECG).
// Writes ../remotion/src/data/airway.json {viewBox, markup}.  Run:  node airway_prep.cjs   (Playwright/Chromium)
const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');

const SRC = path.join(__dirname, '../../3-board/art/airways original.svg');
const OUT = path.join(__dirname, '../remotion/src/data/airway.json');
const MAP = {
  '71,87,104': '#ECE9E3', // body silhouette
  '205,205,203': '#D8D4CC', // bone
  '246,245,240': '#F7F7F5', // discs, teeth
  '212,239,248': '#FFFFFF', // air: nose, mouth, pharynx, larynx
  '243,162,168': '#F0C4B5', // soft tissue: tongue, palate, epiglottis folds, esophagus wall
  '63,136,186': '#B9B5AE', // tracheal cartilage rings
  '253,141,122': '#F7E0D7', // lungs
  '202,113,96': '#EBC6BA', // lung edge
  '228,59,59': '#E9B5A7', // vessels
  '171,79,64': '#E3AC9D',
};

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.setContent(fs.readFileSync(SRC, 'utf8').replace(/<\?xml[^>]*>/, ''));
  const res = await p.evaluate((MAP) => {
    const svg = document.querySelector('svg');
    let dropped = 0, kept = 0;
    const unknown = {};
    svg.querySelectorAll('path,polygon,rect,ellipse,circle,polyline,line').forEach((e) => {
      if (e.closest('clipPath,defs')) return;
      const st = getComputedStyle(e);
      const fill = st.fill.replace(/[^0-9,]/g, '');
      const bb = e.getBBox();
      if (st.fill === 'none' || (fill === '246,245,240' && bb.width > 1500)) { e.remove(); dropped++; return; }
      const to = MAP[fill];
      if (!to) unknown[st.fill] = (unknown[st.fill] || 0) + 1;
      e.removeAttribute('style');
      e.setAttribute('fill', to || st.fill);
      kept++;
    });
    // empty groups left behind
    let again = true;
    while (again) { again = false; svg.querySelectorAll('g').forEach((g) => { if (!g.children.length) { g.remove(); again = true; } }); }
    return {markup: svg.innerHTML.replace(/\s+/g, ' ').replace(/> </g, '><').trim(), dropped, kept, unknown, viewBox: svg.getAttribute('viewBox')};
  }, MAP);
  await b.close();
  fs.writeFileSync(OUT, JSON.stringify({note: "Mark's airway illustration, cleaned and recoloured by build/airway_prep.cjs", viewBox: res.viewBox, markup: res.markup}));
  console.log(`kept ${res.kept}, dropped ${res.dropped}, unmapped ${JSON.stringify(res.unknown)}, ${(res.markup.length / 1024).toFixed(0)} KB`);
})();
