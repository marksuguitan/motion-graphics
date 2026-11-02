// Lead II-style ECG on a FIXED time grid: the path is generated once per strip and only translated.
export const PXS = 280, PXMV = 112, DT = 0.002;
const g = (t: number, c: number, s: number, a: number) => a * Math.exp(-((t - c) * (t - c)) / (2 * s * s));
export type Kind = 'sinus' | 'avnrt' | 'pause';
export function beatV(t: number, rr: number, kind: Kind) {
  const qt = 0.40 * Math.sqrt(rr), tc = 0.72 * qt, ts = 0.11 * qt;
  let v = 0;
  if (kind === 'sinus') v += g(t, -0.10, 0.024, 0.16);
  v += g(t, 0.012, 0.0055, -0.08) + g(t, 0.030, 0.0095, 1.25) + g(t, 0.052, 0.0075, -0.28);
  if (kind === 'avnrt') v += g(t, 0.080, 0.0095, -0.14);
  v += g(t, tc, ts, 0.30);
  return v;
}
export type Seg = {kind: Kind; bpm?: number; bpmEnd?: number; dur: number};
export type Beat = {t: number; rr: number; kind: Kind};
export function placeBeats(segs: Seg[]): Beat[] {
  const beats: Beat[] = []; let t = 0.25;
  for (const s of segs) {
    const start = t, end = t + s.dur;
    if (s.kind === 'pause') { t = end; continue; }
    while (t < end) {
      const f = (t - start) / s.dur; const bpm = s.bpm! + ((s.bpmEnd ?? s.bpm!) - s.bpm!) * f; const rr = 60 / bpm;
      beats.push({t, rr, kind: s.kind}); t += rr;
    }
  }
  return beats;
}
export type Strip = {d: string; beats: Beat[]; dur: number; v: (t: number) => number};
function build(segs: Seg[], dur = 14): Strip {
  const beats = placeBeats(segs);
  const v = (t: number) => { let s = 0; for (const b of beats) { const d = t - b.t; if (d > -0.25 && d < 0.6) s += beatV(d, b.rr, b.kind); } return s; };
  const n = Math.round(dur / DT); const parts: string[] = [];
  for (let i = 0; i <= n; i++) { const t = i * DT; parts.push(`${i ? 'L' : 'M'}${(t * PXS).toFixed(1)} ${(-v(t) * PXMV).toFixed(2)}`); }
  return {d: parts.join(''), beats, dur, v};
}
const cache: Record<string, Strip> = {};
const DEFS: Record<string, Seg[]> = {
  open170: [{kind: 'sinus', bpm: 170, dur: 14}],
  sinus130: [{kind: 'sinus', bpm: 130, dur: 14}],
  sinus75: [{kind: 'sinus', bpm: 75, dur: 14}],
  avnrt180: [{kind: 'avnrt', bpm: 180, dur: 14}],
  onset: [{kind: 'sinus', bpm: 80, dur: 2.6}, {kind: 'avnrt', bpm: 180, dur: 4.2}, {kind: 'sinus', bpm: 80, dur: 8}],
  convert2: [{kind: 'avnrt', bpm: 180, dur: 14.4}, {kind: 'pause', dur: 1.3}, {kind: 'sinus', bpm: 78, dur: 26}],
  convert: [{kind: 'avnrt', bpm: 180, dur: 3.2}, {kind: 'pause', dur: 1.3}, {kind: 'sinus', bpm: 78, dur: 18}],
};
export const strip = (name: string) => (cache[name] ??= build(DEFS[name], Math.max(14, DEFS[name].reduce((a, s) => a + s.dur, 0))));
