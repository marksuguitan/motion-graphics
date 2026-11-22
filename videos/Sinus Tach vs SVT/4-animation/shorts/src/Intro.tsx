import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig, spring} from 'remotion';
import {T, FPS} from './theme';
import {strip, PXS, PXMV} from './ecg';
import {clamp, lerp} from './ui';

// Medzcool mark (Mark's SVG, viewBox 69.66 x 44.72): two polygons forming an "M" of ECG zigzags.
const POLYS: number[][][] = [
  [[13.98, 28.07], [4.31, 28.07], [0, 35.85], [18.54, 35.85], [23.46, 27.04], [34.59, 44.72], [38.86, 36.91], [23.06, 11.81]],
  [[61.63, 19.81], [50.85, 1.86], [41.25, 18.59], [29.55, 0], [25.33, 7.9], [41.56, 33.67], [51, 17.22], [57.23, 27.59], [65.77, 27.59], [69.66, 19.81]],
];
const LW = 69.66, LH = 44.72, N = 240;
export const INTRO = 2.2;                 // seconds before the main timeline
export const PREPRINT = 0.6;              // strip seconds already on the paper when the main timeline starts
// where the cold-open strip sits on stage (must match Main): card at (260, 390), header 56, baseline 0.62 of the rest
const SX = 260, SY = 390 + 56 + (300 - 56) * 0.62;

const resample = (P: number[][]) => {
  const segs = P.map((p, i) => { const q = P[(i + 1) % P.length]; return {p, q, len: Math.hypot(q[0] - p[0], q[1] - p[1])}; });
  const total = segs.reduce((a, s) => a + s.len, 0); const out: number[][] = []; let si = 0, acc = 0;
  for (let k = 0; k < N; k++) { const d = (k / N) * total; while (acc + segs[si].len < d) { acc += segs[si].len; si++; } const f = (d - acc) / segs[si].len, s = segs[si]; out.push([s.p[0] + (s.q[0] - s.p[0]) * f, s.p[1] + (s.q[1] - s.p[1]) * f]); }
  return out;
};
const startAtLeftmost = (pts: number[][]) => { let b = 0; pts.forEach((p, i) => { if (p[0] + p[1] * 0.01 < pts[b][0] + pts[b][1] * 0.01) b = i; }); return pts.slice(b).concat(pts.slice(0, b)); };
const signedArea = (P: number[][]) => P.reduce((a, p, i) => { const q = P[(i + 1) % P.length]; return a + p[0] * q[1] - q[0] * p[1]; }, 0) / 2;
const orient = (P: number[][], sign: number) => (Math.sign(signedArea(P)) === sign ? P : [P[0], ...P.slice(1).reverse()]);

// a thin band (3.2 px) around the strip's trace between strip times a..b, as a closed polygon in stage px
function traceBand(a: number, b: number, hw = 1.6, name = 'open170') {
  const s = strip(name); const pts: number[][] = [];
  for (let t = a; t <= b + 1e-9; t += 0.002) pts.push([SX + t * PXS, SY - s.v(t) * PXMV]);
  const top: number[][] = [], bot: number[][] = [];
  pts.forEach((p, i) => { const q = pts[Math.min(i + 1, pts.length - 1)], o = pts[Math.max(i - 1, 0)]; let nx = -(q[1] - o[1]), ny = q[0] - o[0]; const l = Math.hypot(nx, ny) || 1; nx /= l; ny /= l; top.push([p[0] + nx * hw, p[1] + ny * hw]); bot.push([p[0] - nx * hw, p[1] - ny * hw]); });
  return top.concat(bot.reverse());
}
const LOGO = POLYS.map(P => startAtLeftmost(resample(orient(P, 1))));
const SPLIT = 0.268;
// band geometry per strip (the shorts land the logo on other strips); centre = the slide target
type Geo = {BANDS: number[][][]; HEAVY: number[][][]; CX: number; CY: number; BW: number};
const GEOS = new Map<string, Geo>();
const geo = (name: string): Geo => {
  const hit = GEOS.get(name); if (hit) return hit;
  const BANDS = [traceBand(0, SPLIT, 1.6, name), traceBand(SPLIT, PREPRINT, 1.6, name)].map(B => startAtLeftmost(resample(orient(B, 1))));
  // a heavier version of the trace for while it is flying (thickness follows speed), so the motion blur doesn't wash it out
  const HEAVY = [traceBand(0, SPLIT, 5, name), traceBand(SPLIT, PREPRINT, 5, name)].map(B => startAtLeftmost(resample(orient(B, 1))));
  const BB = BANDS.flat(), xs = BB.map(p => p[0]), ys = BB.map(p => p[1]);
  const g = {BANDS, HEAVY, CX: (Math.min(...xs) + Math.max(...xs)) / 2, CY: (Math.min(...ys) + Math.max(...ys)) / 2, BW: (Math.max(...xs) - Math.min(...xs)) / 2};
  GEOS.set(name, g); return g;
};

const LS = 7.2, S0X = 960;                // logo holds at baseline height, so the slide is purely horizontal (leftward)
const DIR = -1;

// ── motion: same recipe and knobs as Mark's square→triangle study (v3) ──
const M = {
  hold: 1.2, push: 0.16, slide: 0.22, friction: 0.3, stop: 0.05, recoilTime: 0.14, recoil: 12,
  morph: 0.06, smear: 0.75, smearFlatten: 0.45, smearIn: 0.025, smearOut: 0.05,
  stretch: 0.08, lean: 4,
  tip: 9, tipIn: 35, tipOut: 7,            // inertia pitches the trace forward after the yank, then it settles back
  stopShake: 2.5,
};
const tPeak = M.hold + M.push, tStop = tPeak + M.slide, tStopEnd = tStop + M.stop, tRecEnd = tStopEnd + M.recoilTime;
const q5u = (u: number) => { u = clamp(u); return u < 0.5 ? 16 * u ** 5 : 1 - (-2 * u + 2) ** 5 / 2; };
const vUnit = (t: number) => {
  if (t < M.hold) return 0;
  if (t < tPeak) { const u = (t - M.hold) / M.push; return 1 - (1 - u) ** 2; }
  if (t < tStop) return 1 - M.friction * ((t - tPeak) / M.slide);
  if (t < tStopEnd) { const u = (t - tStop) / M.stop; return (1 - M.friction) * (1 - u) ** 2; }
  return 0;
};
const DT = 1 / 4800, NS = Math.ceil((INTRO + 0.5) / DT);
let unitDist = 0; for (let i = 0; i < NS; i++) unitDist += vUnit(i * DT) * DT;
const VR = (Math.PI * M.recoil) / (2 * M.recoilTime);
// the slide is simulated per start x (the vertical shorts start the logo at a different landscape x)
type Sim = {VMAX: number; vel: (t: number) => number; XS: Float64Array; LN: Float64Array; SXT: Float64Array};
const SIMS = new Map<string, Sim>();
const sim = (s0x: number, CX: number): Sim => {
  const key = `${s0x}|${CX}`; const hit = SIMS.get(key); if (hit) return hit;
  const VMAX = (s0x - CX + M.recoil) / unitDist;   // forward slide overshoots by the recoil, the pull-back lands it exactly
  const vel = (t: number) => (t >= tStopEnd && t < tRecEnd ? -VR * Math.sin((Math.PI * (t - tStopEnd)) / M.recoilTime) : vUnit(t) * VMAX);
  const XS = new Float64Array(NS), LN = new Float64Array(NS), SXT = new Float64Array(NS);
  let x = 0, ln = 0, lnV = 0, sx = 1, sxV = 0;
  const aRef = (2 * VMAX) / M.push, wL = 2 * Math.PI * 5, zL = 0.5, wS = 2 * Math.PI * 7, zS = 0.32;
  for (let i = 0; i < NS; i++) {
    const t = i * DT; XS[i] = x; LN[i] = ln; SXT[i] = sx;
    const v = vel(t), a = (vel(t + DT) - v) / DT; x += v * DT;
    const lnT = t < tStop ? M.lean * clamp(a / aRef, -1, 1) : 0;
    lnV += (-wL * wL * (ln - lnT) - 2 * zL * wL * lnV) * DT; ln += lnV * DT;
    const sxT = 1 + M.stretch * Math.max(0, v) / VMAX;
    sxV += (-wS * wS * (sx - sxT) - 2 * zS * wS * sxV) * DT; sx += sxV * DT;
  }
  const r = {VMAX, vel, XS, LN, SXT}; SIMS.set(key, r); return r;
};
const samp = (arr: Float64Array, t: number) => { const f = clamp(t / DT, 0, NS - 1.001), i = Math.floor(f), k = f - i; return arr[i] * (1 - k) + arr[i + 1] * k; };
const TIPN = (() => { let m = 0; for (let k = 0; k < 1; k += 0.001) m = Math.max(m, Math.exp(-M.tipOut * k) - Math.exp(-M.tipIn * k)); return m; })();
const tipDeg = (t: number) => { const k = t - tStop; return k > 0 ? (M.tip * (Math.exp(-M.tipOut * k) - Math.exp(-M.tipIn * k))) / TIPN : 0; };

export const INTRO_HOLD = M.hold, INTRO_REC_END = tRecEnd;
export const INTRO_STOP = tStop;            // when the yank lands (shorts start printing the strip here)
// printFrom: keep printing the strip from the landed beat from this time on, so the trace never pauses before the card takes over
// time: drive the intro clock from outside (the short's outro plays it backwards, beat -> logo);
// settle: seconds since that reversed flight landed, adds a squash-and-settle on arrival
export const Intro: React.FC<{startX?: number; stripName?: string; logoScale?: number; printFrom?: number; time?: number; settle?: number}> = ({startX = S0X, stripName = 'open170', logoScale = LS, printFrom, time, settle}) => {
  const {fps} = useVideoConfig(); const fr = useCurrentFrame(); const t = time ?? fr / fps;
  const {BANDS, HEAVY, CX, CY, BW} = geo(stripName);
  const {VMAX, vel, XS, LN, SXT} = sim(startX, CX);
  if (t > INTRO + 0.4) return null;
  const pop = spring({frame: t * FPS, fps: FPS, config: {damping: 16, stiffness: 320}});
  const morph = q5u((t - (tPeak - M.morph / 2)) / M.morph);
  const kL = settle ?? -1, land = kL >= 0 ? 1 - 0.16 * Math.exp(-8 * kL) * Math.sin(2 * Math.PI * 4.2 * kL) : 1;
  const sx = samp(SXT, t) * land, sy = 1 / sx;
  const lean = (samp(LN, t) - tipDeg(t)) * (Math.PI / 180);   // + leans back against the motion, − pitches forward
  const x = startX + DIR * samp(XS, t);
  const sm = Math.exp(-(((t - tPeak) / (t < tPeak ? M.smearIn : M.smearOut)) ** 2));
  const half = lerp(LW * logoScale / 2, BW, morph), front = DIR * 0.6 * half * sx;
  const kS = t - tStop, shake = kS > 0 ? M.stopShake * Math.exp(-30 * kS) * Math.sin(2 * Math.PI * 16 * kS) : 0;
  const sc = logoScale * (0.9 + 0.1 * pop);
  const op = clamp(pop * 1.5) * (time !== undefined ? 1 : 1 - clamp((t - INTRO - 0.1) / 0.25));
  const sweep = clamp((t - 0.3) / 0.7);   // a quick ECG sweep reads across the mark while it holds
  const place = (rx: number, ry: number) => {
    let px = rx * sx, py = ry * sy;
    if (sm > 1e-4) { px = front + (px - front) * (1 + M.smear * sm); py *= 1 - M.smearFlatten * sm; }  // streak trails behind the front
    px += DIR * Math.tan(lean) * py;       // skew about the baseline
    return [x + px, CY + py + shake];
  };
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <svg width={1920} height={1080} viewBox="0 0 1920 1080">
        <defs>
          <linearGradient id="sweep" gradientUnits="userSpaceOnUse" x1={startX - LW * logoScale / 2} x2={startX + LW * logoScale / 2} y1={0} y2={0}>
            <stop offset={Math.max(0, sweep - 0.18)} stopColor={T.ink} />
            <stop offset={sweep} stopColor={T.coral} />
            <stop offset={Math.min(1, sweep + 0.015)} stopColor={T.ink} />
          </linearGradient>
        </defs>
        <g opacity={op}>
          {LOGO.map((P, j) => {
            const B0 = BANDS[j], B1 = HEAVY[j], hv = clamp(Math.abs(vel(t)) / VMAX * 1.4);
            const B = B0.map((q, i) => [lerp(q[0], B1[i][0], hv), lerp(q[1], B1[i][1], hv)]);
            const dd = P.map((p, i) => {
              const [wx, wy] = place(lerp((p[0] - LW / 2) * sc, B[i][0] - CX, morph), lerp((p[1] - LH / 2) * sc, B[i][1] - CY, morph));
              return `${i ? 'L' : 'M'}${wx.toFixed(2)} ${wy.toFixed(2)}`;
            }).join('') + 'Z';
            return <path key={j} d={dd} fill={sweep > 0 && sweep < 1 && morph === 0 ? 'url(#sweep)' : T.ink} />;
          })}
          {printFrom !== undefined && t > printFrom && (() => {
            const sv = strip(stripName), end = PREPRINT + (t - printFrom), pts: string[] = [];
            let hx = 0, hy = 0;
            for (let u = PREPRINT - 0.004; u <= end + 1e-9; u += 0.002) { const [wx, wy] = place(SX + u * PXS - CX, SY - sv.v(u) * PXMV - CY); pts.push(`${pts.length ? 'L' : 'M'}${wx.toFixed(2)} ${wy.toFixed(2)}`); hx = wx; hy = wy; }
            return <g><path d={pts.join('')} fill="none" stroke={T.ink} strokeWidth={3.2} strokeLinejoin="round" strokeLinecap="round" /><circle cx={hx} cy={hy} r={6} fill={T.ink} opacity={0.9} /></g>;
          })()}
        </g>
      </svg>
    </AbsoluteFill>
  );
};
