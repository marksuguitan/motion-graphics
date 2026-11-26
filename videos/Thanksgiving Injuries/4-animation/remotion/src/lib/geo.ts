// geo.ts: shapes whose path commands always line up (M, 4 x L+A, Z), so morph() can turn any one into any
// other: a plate (disc) into a knife blade, a pot, a dish. Each corner has its own elliptical radius.
export type Corner = [number, number];
const z = (c: Corner): Corner => [Math.max(0.01, c[0]), Math.max(0.01, c[1])];

export function rr4(cx: number, cy: number, w: number, h: number, tl: Corner, tr: Corner, br: Corner, bl: Corner): string {
  const [a, b, c, d] = [z(tl), z(tr), z(br), z(bl)];
  const x0 = cx - w / 2, y0 = cy - h / 2, x1 = cx + w / 2, y1 = cy + h / 2;
  const f = (n: number) => n.toFixed(2);
  return [
    `M ${f(x0 + a[0])} ${f(y0)}`,
    `L ${f(x1 - b[0])} ${f(y0)}`, `A ${f(b[0])} ${f(b[1])} 0 0 1 ${f(x1)} ${f(y0 + b[1])}`,
    `L ${f(x1)} ${f(y1 - c[1])}`, `A ${f(c[0])} ${f(c[1])} 0 0 1 ${f(x1 - c[0])} ${f(y1)}`,
    `L ${f(x0 + d[0])} ${f(y1)}`, `A ${f(d[0])} ${f(d[1])} 0 0 1 ${f(x0)} ${f(y1 - d[1])}`,
    `L ${f(x0)} ${f(y0 + a[1])}`, `A ${f(a[0])} ${f(a[1])} 0 0 1 ${f(x0 + a[0])} ${f(y0)}`,
    'Z',
  ].join(' ');
}
export const discP = (cx: number, cy: number, r: number) => rr4(cx, cy, 2 * r, 2 * r, [r, r], [r, r], [r, r], [r, r]);
export const rrP = (cx: number, cy: number, w: number, h: number, r: number) => rr4(cx, cy, w, h, [r, r], [r, r], [r, r], [r, r]);

/** Mix two hex colours. */
export function mixHex(a: string, b: string, k: number): string {
  const p = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const [x, y] = [p(a), p(b)];
  const c = x.map((v, i) => Math.round(v + (y[i] - v) * Math.max(0, Math.min(1, k))));
  return '#' + c.map((v) => v.toString(16).padStart(2, '0')).join('');
}
export const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
