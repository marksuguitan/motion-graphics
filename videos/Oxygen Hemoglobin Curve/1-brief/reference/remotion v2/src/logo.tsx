import React from 'react';
// Medzcool logo (Mark's SVG, /mnt/project-files/assets/logo/medzcool-logo.svg, viewBox 69.66 x 44.72)
// and a point-for-point morph of both polygons into the red cell's outline.
const POLYS: number[][][] = [
  [[13.98, 28.07], [4.31, 28.07], [0, 35.85], [18.54, 35.85], [23.46, 27.04], [34.59, 44.72], [38.86, 36.91], [23.06, 11.81]],
  [[61.63, 19.81], [50.85, 1.86], [41.25, 18.59], [29.55, 0], [25.33, 7.9], [41.56, 33.67], [51, 17.22], [57.23, 27.59], [65.77, 27.59], [69.66, 19.81]],
];
export const LOGO_W = 69.66, LOGO_H = 44.72;
const N = 180;

// resample a closed polygon to N points evenly spaced by arc length
const resample = (P: number[][]) => {
  const segs = P.map((p, i) => { const q = P[(i + 1) % P.length]; return {p, q, len: Math.hypot(q[0] - p[0], q[1] - p[1])}; });
  const total = segs.reduce((a, s) => a + s.len, 0);
  const out: number[][] = [];
  let si = 0, acc = 0;
  for (let k = 0; k < N; k++) {
    const d = (k / N) * total;
    while (acc + segs[si].len < d) { acc += segs[si].len; si++; }
    const f = (d - acc) / segs[si].len, s = segs[si];
    out.push([s.p[0] + (s.q[0] - s.p[0]) * f, s.p[1] + (s.q[1] - s.p[1]) * f]);
  }
  return out;
};
const area = (P: number[][]) => P.reduce((a, p, i) => { const q = P[(i + 1) % P.length]; return a + p[0] * q[1] - q[0] * p[1]; }, 0) / 2;
const SAMPLES = POLYS.map((P) => {
  const pts = resample(P);
  const cx = pts.reduce((a, p) => a + p[0], 0) / N, cy = pts.reduce((a, p) => a + p[1], 0) / N;
  // start at the sample pointing most to the right of its centroid, so it maps to ellipse angle 0
  let best = 0, bv = -Infinity;
  pts.forEach((p, i) => { const v = Math.atan2(p[1] - cy, p[0] - cx); const sc = Math.cos(v) * Math.hypot(p[0] - cx, p[1] - cy); if (sc > bv) { bv = sc; best = i; } });
  const rot = pts.slice(best).concat(pts.slice(0, best));
  return {pts: rot, dir: Math.sign(area(P)) || 1};
});

// logo centred at (lx, ly) with scale s; ellipse centred at (ex, ey) radii (rx, ry); k = 0 logo .. 1 ellipse
export const LogoMorph: React.FC<{lx: number; ly: number; s: number; ex: number; ey: number; rx: number; ry: number; k: number; fill: string; op?: number}> =
  ({lx, ly, s, ex, ey, rx, ry, k, fill, op = 1}) => (
    <g opacity={op}>
      {SAMPLES.map(({pts, dir}, j) => {
        let d = '';
        pts.forEach((p, i) => {
          const ax = lx + (p[0] - LOGO_W / 2) * s, ay = ly + (p[1] - LOGO_H / 2) * s;
          const th = dir * (i / N) * Math.PI * 2;
          const bx = ex + Math.cos(th) * rx, by = ey + Math.sin(th) * ry;
          d += (i ? 'L' : 'M') + (ax + (bx - ax) * k).toFixed(1) + ',' + (ay + (by - ay) * k).toFixed(1);
        });
        return <path key={j} d={d + 'Z'} fill={fill} />;
      })}
    </g>);
