// comma.ts: Comma Clinical easing for Remotion.
// The values come from the Motion Style Guide, section "Comma Clinical", table "After Effects settings"
// (the "Script curve (cubic-bezier)" column). It is the Remotion twin of library/scripts/adobe/comma_easing.jsx.
// If the guide and this file disagree, the guide wins: update this file (and the .jsx) to match.
//
// Everything takes time in seconds (useTime() from ../lib/timing), because sync points are measured in seconds.
//
//   const t = useTime();
//   const s = ease(t, sync('2A', 'axis'), 0.6, 0, 1);               // snap and settle, 0 -> 1
//   const x = ease(t, 3.2, 0.8, 300, 1200, 'cross');                 // a tracked move across the frame
//   const y = keys(t, [[1, 0], [1.6, 100], [2.4, 40]], 'snap');      // several keys, same curve on every leg
//   const r = overshoot(t, 4, 0.6, 0, 1);                             // snap 8% past, settle back
//   const {sx, sy} = squash(t, 5, 'y');                               // 75/125 on impact, recover in 0.2 s
//   const on = cut(t, sync('3B', 'cooperative'));                     // text cuts on with its word
//   const d = morph(t, 6, 0.6, pathA, pathB);                         // one shape becomes the next

import {Easing} from 'remotion';
import {interpolatePath} from '@remotion/paths';

export type Curve = 'snap' | 'cross' | 'accel' | 'anti' | 'back' | 'linear' | 'warmIn' | 'warmMove';

// cubic-bezier control points, from the style guide
export const BEZIER: Record<Exclude<Curve, 'linear' | 'warmIn' | 'warmMove'>, [number, number, number, number]> = {
  snap: [0.16, 1, 0.3, 1], // snap and settle (default): entrances, morphs, scale changes, 0.5-0.7 s
  cross: [0.33, 0, 0.15, 1], // a move across the frame the viewer tracks, 0.6-0.9 s
  accel: [0.7, 0, 0.84, 0], // accelerate into a swap, 0.2-0.3 s; swap the art on its last frame
  anti: [0.5, 0, 0.5, 1], // anticipation counter-move, 0.15-0.25 s
  back: [0.5, 0, 0.3, 1], // the return leg of an overshoot (influence 50% out / 70% in)
};

export const CURVES: Record<Curve, (x: number) => number> = {
  snap: Easing.bezier(...BEZIER.snap),
  cross: Easing.bezier(...BEZIER.cross),
  accel: Easing.bezier(...BEZIER.accel),
  anti: Easing.bezier(...BEZIER.anti),
  back: Easing.bezier(...BEZIER.back),
  linear: (x) => x, // constant-rate processes only: flow, conduction, a running readout, ambient drift
  warmIn: Easing.out(Easing.cubic), // Warm Clinical entrances, for a video that uses Warm Clinical motion
  warmMove: Easing.inOut(Easing.cubic), // Warm Clinical moves across the frame
};

// Durations and gaps from the guide, in seconds (30 fps)
export const DUR = {snap: 0.6, snapRange: [0.5, 0.7], cross: 0.75, crossRange: [0.6, 0.9], accel: 0.25, accelRange: [0.2, 0.3], anti: 0.2, overshootBack: 0.2, squash: 0.2};
export const HOLD_MIN = 0.4; // hold still at least this long after every landing
export const STAGGER = 2 / 30; // 2-3 frames between items of a group; whole stagger under 0.4 s
export const MONTAGE = 0.3; // 0.25-0.35 s per item in a quick-cut montage
export const FADE_MAX = 0.2; // opacity only for small things (leader lines, secondary labels)

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
type V = number | number[];
const mix = (a: V, b: V, k: number): V =>
  Array.isArray(a) ? a.map((ai, i) => ai + ((b as number[])[i] - ai) * k) : a + ((b as number) - a) * k;

/** Progress 0..1 of a move that starts at t0 and lasts dur, on a curve. Clamped at both ends. */
export function progress(t: number, t0: number, dur: number, curve: Curve = 'snap'): number {
  if (dur <= 0) return t >= t0 ? 1 : 0;
  return CURVES[curve](clamp01((t - t0) / dur));
}

/** One move from `from` to `to`, starting at t0, lasting dur. Works on numbers or arrays ([x, y], colours as [r, g, b]). */
export function ease<T extends V>(t: number, t0: number, dur: number, from: T, to: T, curve: Curve = 'snap'): T {
  return mix(from, to, progress(t, t0, dur, curve)) as T;
}

/** Several keys [[time, value], ...]; every leg gets the same curve (like CommaEase.move in the .jsx). */
export function keys<T extends V>(t: number, list: [number, T][], curve: Curve = 'snap'): T {
  if (t <= list[0][0]) return list[0][1];
  for (let i = 1; i < list.length; i++) {
    const [t0, v0] = list[i - 1];
    const [t1, v1] = list[i];
    if (t < t1) return ease(t, t0, t1 - t0, v0, v1, curve);
  }
  return list[list.length - 1][1];
}

/** Snap past the target by `over` (0.05-0.10) in half of dur, then settle back over `back` s. One rebound only. */
export function overshoot<T extends V>(t: number, t0: number, dur: number, from: T, to: T, over = 0.08, back = DUR.overshootBack): T {
  const t1 = t0 + 0.5 * dur;
  const peak = mix(from, to, 1 + over) as T;
  if (t < t1) return ease(t, t0, t1 - t0, from, peak, 'snap');
  return ease(t, t1, back, peak, to, 'back');
}

/** Squash on impact at tImpact: the impact axis goes to 1 - amount, the other to 1 + amount, back to 1 with snap and settle. */
export function squash(t: number, tImpact: number, axis: 'x' | 'y' = 'y', amount = 0.25, dur = DUR.squash): {sx: number; sy: number} {
  if (t < tImpact) return {sx: 1, sy: 1};
  const k = 1 - progress(t, tImpact, dur, 'snap');
  const hit = 1 - amount * k;
  const other = 1 + amount * k;
  return axis === 'y' ? {sx: other, sy: hit} : {sx: hit, sy: other};
}

/** Anticipation then the main move: a small counter-move (20-40 px or 3-5 deg) before `t0`, then snap and settle. */
export function anticipate(t: number, t0: number, dur: number, from: number, to: number, counter = 30, antiDur = DUR.anti): number {
  const dir = Math.sign(to - from) || 1;
  const back = from - dir * counter;
  if (t < t0 - antiDur) return from;
  if (t < t0) return ease(t, t0 - antiDur, antiDur, from, back, 'anti');
  return ease(t, t0, dur, back, to, 'snap');
}

/** Gravity arc: rise to `top` with snap and settle, hang 3-4 frames, fall back on the accelerate curve. */
export function gravity(t: number, t0: number, from: number, top: number, rise = 0.3, hang = 3.5 / 30, fall = 0.3, to = from): number {
  if (t < t0 + rise) return ease(t, t0, rise, from, top, 'snap');
  if (t < t0 + rise + hang) return top;
  return ease(t, t0 + rise + hang, fall, top, to, 'accel');
}

/** Seconds of offset for item i of a group (2 frames apart by default). */
export const stagger = (i: number, gap = STAGGER) => i * gap;

/** Text and other hard cuts: visible from tOn (its sync word) until tOff. No fades between ideas. */
export const cut = (t: number, tOn: number, tOff = Infinity) => t >= tOn && t < tOff;

/** Opacity for small things only (leader lines, secondary labels): at most 0.2 s. */
export const fadeSmall = (t: number, t0: number, dur = FADE_MAX) => progress(t, t0, Math.min(dur, FADE_MAX), 'linear');

/** Morph one SVG path into another (snap and settle by default). Paths should have similar structure; see @remotion/paths. */
export function morph(t: number, t0: number, dur: number, fromD: string, toD: string, curve: Curve = 'snap'): string {
  const p = progress(t, t0, dur, curve);
  if (p <= 0) return fromD;
  if (p >= 1) return toD;
  return interpolatePath(p, fromD, toD);
}

/**
 * Accelerate into a swap, then snap and settle into the new form (the Comma move).
 * Returns {phase, k}: phase 'a' shows the old art with k going 0 -> 1 on 'accel', phase 'b' the new art with k going 0 -> 1 on 'snap'.
 * Swap the artwork exactly at tSwap, on the fastest frame, where the cut is invisible.
 */
export function swap(t: number, tSwap: number, inDur = DUR.accel, outDur = DUR.snap): {phase: 'a' | 'b'; k: number} {
  if (t < tSwap) return {phase: 'a', k: progress(t, tSwap - inDur, inDur, 'accel')};
  return {phase: 'b', k: progress(t, tSwap, outDur, 'snap')};
}

/** Type a word on at a steady rate (frames per character), or off with each character a frame sooner than the last. */
export function typeOn(text: string, t: number, t0: number, fps = 30, framesPerChar = 2): string {
  const n = Math.floor(Math.max(0, t - t0) * fps / framesPerChar);
  return text.slice(0, Math.min(text.length, n));
}
export function typeOff(text: string, t: number, t0: number, fps = 30, firstGap = 4): string {
  let f = Math.floor((t - t0) * fps);
  if (f < 0) return text;
  let removed = 0;
  let gap = firstGap;
  while (removed < text.length && f >= gap) {
    f -= gap;
    removed++;
    gap = Math.max(1, gap - 1);
  }
  return text.slice(0, text.length - removed);
}
