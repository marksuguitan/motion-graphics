// shapes.ts: path builders whose commands line up, so morph() can turn one into another smoothly.
// A circle is a rounded rectangle whose corner radius is half its size, so disc -> card -> chip all morph.

/** Rounded rectangle centred on (cx, cy), always the same 9 commands (M, 4 L, 4 A). */
export function roundRect(cx: number, cy: number, w: number, h: number, r: number): string {
  const rr = Math.max(0, Math.min(r, w / 2, h / 2));
  const x0 = cx - w / 2, y0 = cy - h / 2, x1 = cx + w / 2, y1 = cy + h / 2;
  return [
    `M ${x0 + rr} ${y0}`,
    `L ${x1 - rr} ${y0}`, `A ${rr} ${rr} 0 0 1 ${x1} ${y0 + rr}`,
    `L ${x1} ${y1 - rr}`, `A ${rr} ${rr} 0 0 1 ${x1 - rr} ${y1}`,
    `L ${x0 + rr} ${y1}`, `A ${rr} ${rr} 0 0 1 ${x0} ${y1 - rr}`,
    `L ${x0} ${y0 + rr}`, `A ${rr} ${rr} 0 0 1 ${x0 + rr} ${y0}`,
    'Z',
  ].join(' ');
}

export const disc = (cx: number, cy: number, r: number) => roundRect(cx, cy, 2 * r, 2 * r, r);
