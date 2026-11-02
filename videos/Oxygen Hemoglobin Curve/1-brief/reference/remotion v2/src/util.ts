import {spring} from 'remotion';
export const FPS = 30;
export const clamp = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
export const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
export const ss = (a: number, b: number, x: number) => ease(clamp((x - a) / (b - a)));
export const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
export const mix = (a: string, b: string, t: number) => {
  const p = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const A = p(a), B = p(b);
  return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * clamp(t)).toString(16).padStart(2, '0')).join('');
};
// physical spring from time t0 (seconds); returns 0..~1.05..1
export const spr = (t: number, t0: number, cfg: any = {}) =>
  t < t0 ? 0 : spring({frame: (t - t0) * FPS, fps: FPS, config: {damping: 15, mass: 0.9, stiffness: 120, ...cfg}});
// visibility window: fades in at a, out at b
export const win = (t: number, a: number, b: number, fi = 0.4, fo = 0.4) => Math.min(ss(a, a + fi, t), 1 - ss(b - fo, b, t));
