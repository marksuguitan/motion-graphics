// conduction.ts: where the impulse is at each moment of a beat, and the ECG that goes with it.
// Geometry and timing come from src/data/conduction.json (made by 4-animation/build/conduction_geo.py from
// Mark's gray conduction heart); the hand-set video timeline is src/data/timeline.json.
import conductionJson from '../data/conduction.json';
import timelineJson from '../data/timeline.json';

type P3 = [number, number, number];
export const COND = conductionJson as unknown as {
  viewBox: [number, number, number, number];
  heartImage: {x: number; y: number; w: number; h: number};
  actMax: number;
  beat: number;
  times: {avIn: number; avOut: number; ventEnd: number; atriaEnd: number};
  points: Record<'SA' | 'AV' | 'BIF' | 'RBB_END' | 'LBB_END' | 'HIS_OUT', [number, number]>;
  routes: Record<'toAV' | 'toBif' | 'rbb' | 'lbb', P3[]>;
  fronts: P3[][];
};
export const TL = timelineJson;

export const T_BIF = COND.routes.toBif[COND.routes.toBif.length - 1][2];

/** Piecewise-linear map through [x, y] keys, clamped. Conduction runs at a constant rate between keys. */
export function warp(x: number, keysList: number[][]): number {
  const k = keysList;
  if (x <= k[0][0]) return k[0][1];
  for (let i = 1; i < k.length; i++) {
    if (x <= k[i][0]) {
      const [x0, y0] = k[i - 1];
      const [x1, y1] = k[i];
      return x1 === x0 ? y1 : y0 + ((x - x0) / (x1 - x0)) * (y1 - y0);
    }
  }
  return k[k.length - 1][1];
}

/** Position along a timed polyline at beat time tau; null before it starts or after it ends. */
export function along(pts: P3[], tau: number): {x: number; y: number} | null {
  if (tau < pts[0][2] || tau > pts[pts.length - 1][2]) return null;
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0, t0] = pts[i - 1];
    const [x1, y1, t1] = pts[i];
    if (tau <= t1) {
      const k = t1 === t0 ? 1 : (tau - t0) / (t1 - t0);
      return {x: x0 + (x1 - x0) * k, y: y0 + (y1 - y0) * k};
    }
  }
  const l = pts[pts.length - 1];
  return {x: l[0], y: l[1]};
}

/** Clamp to the ends of the route (the orb waits at its start, and sits on its end). */
export function alongClamped(pts: P3[], tau: number) {
  if (tau <= pts[0][2]) return {x: pts[0][0], y: pts[0][1]};
  return along(pts, tau) ?? {x: pts[pts.length - 1][0], y: pts[pts.length - 1][1]};
}

/** One normal beat of a lead II-like ECG, in arbitrary units (R = 1). tau in seconds within the beat.
 *  P 0-0.09 s, PR interval 0.16 s, QRS 0.16-0.24 s, T about 0.33-0.48 s (StatPearls: PR 120-200 ms, QRS < 120 ms). */
const g = (x: number, c: number, s: number) => Math.exp(-0.5 * ((x - c) / s) ** 2);
export function ecg(tau: number): number {
  const x = ((tau % COND.beat) + COND.beat) % COND.beat;
  return (
    0.14 * g(x, 0.045, 0.017) - // P
    0.1 * g(x, 0.172, 0.006) + // Q
    1.0 * g(x, 0.192, 0.0075) - // R
    0.24 * g(x, 0.212, 0.0065) + // S
    0.28 * g(x, 0.405, 0.042) // T
  );
}

/** How lit the conduction system is at beat time tau: fully lit after depolarization, fading during the T wave. */
export const recovery = (tau: number) => {
  const x = ((tau % COND.beat) + COND.beat) % COND.beat;
  if (x < 0.33) return 1;
  if (x > 0.48) return 0;
  return 1 - (x - 0.33) / 0.15;
};
