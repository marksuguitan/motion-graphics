// Logo → red cell dash, built on the approved square→triangle motion study
// (motion-studies/square-triangle-morph v3): fast shove to top speed, the morph hidden
// inside a smear frame at top speed, a short coast, a sudden "pulled back" stop with a
// small recoil, and a stretch spring that overshoots into a squash on the stop.
// Times in seconds, distances in px (1920×1080).
export const IM = {
  hold: 1.2, // static logo
  push: 0.16, // 0 → top speed (morph fires at the end of the push)
  slide: 0.3, friction: 0.3, // coast, bleeding off 30% of top speed
  stop: 0.05, recoilTime: 0.14, recoil: 10, // the yank and the pull-back
  morph: 0.06, // logo → cell, centred on top speed
  smear: 0.75, smearFlatten: 0.45, smearIn: 0.025, smearOut: 0.05,
  startX: 960, endX: 1380, y: 530,
  stretch: 0.1, lean: 5, // stretch at speed (volume kept), lean back under the shove (deg)
  squash: 0.1, squashHz: 7, squashDecay: 13, // impact squash on the stop
};
const clamp = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
export const tPeak = IM.hold + IM.push;
export const tStop = tPeak + IM.slide;
const tStopEnd = tStop + IM.stop, tRecoilEnd = tStopEnd + IM.recoilTime;
const DIST = IM.endX - IM.startX + IM.recoil;

const vUnit = (t: number) => {
  if (t < IM.hold) return 0;
  if (t < tPeak) { const u = (t - IM.hold) / IM.push; return 1 - (1 - u) ** 2; }
  if (t < tStop) return 1 - IM.friction * ((t - tPeak) / IM.slide);
  if (t < tStopEnd) { const u = (t - tStop) / IM.stop; return (1 - IM.friction) * (1 - u) ** 2; }
  return 0;
};
const DT = 1 / 4800, END = 3.0, N = Math.ceil(END / DT) + 2;
let unit = 0;
for (let i = 0; i < N; i++) unit += vUnit(i * DT) * DT;
export const VMAX = DIST / unit;
const VR = (Math.PI * IM.recoil) / (2 * IM.recoilTime);
const vel = (t: number) => (t >= tStopEnd && t < tRecoilEnd ? -VR * Math.sin((Math.PI * (t - tStopEnd)) / IM.recoilTime) : vUnit(t) * VMAX);

const XS = new Float64Array(N), LN = new Float64Array(N), SX = new Float64Array(N);
{
  let x = IM.startX, ln = 0, lnV = 0, sx = 1, sxV = 0;
  const aRef = (2 * VMAX) / IM.push;
  const wL = 2 * Math.PI * 5, zL = 0.5, wS = 2 * Math.PI * 7, zS = 0.32;
  for (let i = 0; i < N; i++) {
    const t = i * DT;
    XS[i] = x; LN[i] = ln; SX[i] = sx;
    const v = vel(t), a = (vel(t + DT) - v) / DT;
    x += v * DT;
    const lnT = t < tStop ? IM.lean * clamp(a / aRef, -1, 1) : 0;
    lnV += (-wL * wL * (ln - lnT) - 2 * zL * wL * lnV) * DT; ln += lnV * DT;
    const sxT = 1 + IM.stretch * Math.max(0, v) / VMAX;
    sxV += (-wS * wS * (sx - sxT) - 2 * zS * wS * sxV) * DT; sx += sxV * DT;
  }
}
const samp = (arr: Float64Array, t: number) => {
  const f = clamp(t / DT, 0, N - 2), i = Math.floor(f), k = f - i;
  return arr[i] * (1 - k) + arr[i + 1] * k;
};
const q5 = (u: number) => { u = clamp(u); return u < 0.5 ? 16 * u ** 5 : 1 - (-2 * u + 2) ** 5 / 2; };

// x position, morph amount (0 logo .. 1 cell) and an SVG transform for the moving body
export const introAt = (t: number) => {
  const x = samp(XS, t);
  const morph = q5((t - (tPeak - IM.morph / 2)) / IM.morph);
  const kS = t - tStop;
  const sq = kS > 0 ? IM.squash * Math.exp(-IM.squashDecay * kS) * Math.sin(2 * Math.PI * IM.squashHz * kS) : 0;
  const sx = samp(SX, t) * (1 - sq), sy = 1 / sx;
  const sm = Math.exp(-(((t - tPeak) / (t < tPeak ? IM.smearIn : IM.smearOut)) ** 2));
  const front = 60; // smear streaks back from just behind the leading edge
  const lean = -samp(LN, t);
  const body =
    `translate(${x.toFixed(2)},${IM.y}) skewX(${lean.toFixed(3)}) translate(${front},0) ` +
    `scale(${(sx * (1 + IM.smear * sm)).toFixed(4)},${(sy * (1 - IM.smearFlatten * sm)).toFixed(4)}) translate(${-front},0) translate(${(-x).toFixed(2)},${-IM.y})`;
  return {x, morph, body};
};
// sound cue times
export const SFX_T = {push: IM.hold, peak: tPeak, stop: tStop, recoilEnd: tRecoilEnd};
