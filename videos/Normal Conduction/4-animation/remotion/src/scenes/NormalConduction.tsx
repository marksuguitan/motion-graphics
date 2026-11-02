// NormalConduction.tsx: the whole piece (no VO). A small orb is the electrical impulse of one normal beat:
// SA node -> atria -> AV node (delay) -> bundle of His -> bundle branches -> Purkinje fibers, on Mark's gray
// conduction heart, then the same beat against its ECG, slowed and at real speed.
// Look: Comma's monochrome (light grey ground, charcoal dot). Motion: Comma Clinical (src/style/comma.ts).
import React, {useEffect, useState} from 'react';
import {AbsoluteFill, cancelRender, continueRender, delayRender, staticFile} from 'remotion';
import {useTime} from '../lib/timing';
import {ease, keys, overshoot, progress, squash, typeOff, typeOn} from '../style/comma';
import {COND, T_BIF, TL, along, alongClamped, ecg, recovery, warp} from '../lib/conduction';
import {COND_ART} from '../data/heartArt';
import {Caption, CaptionItem} from './Caption';
import {M, FONT_HEAD} from '../style/mono';

// ------------------------------------------------------------------ layout
const VB = COND.viewBox; // Mark's simplified heart: 984 391 6031 7351
const K = 960 / VB[3]; // must match DISPLAY_H in conduction_geo.py // heart scale (SVG unit -> px): the heart is 960 px tall
const OX = 620 - (VB[2] / 2) * K; // screen x of SVG x = VB[0]: heart centred at x 620
const OY = 60; // screen y of SVG y = VB[1]
const HEART_C: [number, number] = [VB[0] + VB[2] / 2, VB[1] + VB[3] * 0.55]; // squeeze origin (SVG units)
const ORB_R = 15; // px
const FRONT_R = 5.5; // px
const [SA_X, SA_Y] = COND.points.SA;

const TITLE_SIZE = 80;
const TITLE_BASE = 568; // baseline y of the title
const DOT_R = 7; // the period
const DOT_GAP = 5;

// ------------------------------------------------------------------ images (heart, activation map), loaded once as data URLs
// so they are in the frame before Remotion captures it
const cache: Record<string, string> = {};
const pending: Record<string, Promise<string>> = {};
const load = (file: string) =>
  (pending[file] ??= fetch(staticFile(file))
    .then((r) => r.blob())
    .then((b) => new Promise<string>((res) => {
      const fr = new FileReader();
      fr.onload = () => res((cache[file] = fr.result as string));
      fr.readAsDataURL(b);
    })));
function useDataUrl(file: string): string | null {
  const [url, setUrl] = useState<string | null>(cache[file] ?? null);
  const [handle] = useState(() => (cache[file] ? null : delayRender(`Loading ${file}`)));
  useEffect(() => {
    if (url) return;
    load(file)
      .then((u) => {
        setUrl(u);
        if (handle !== null) continueRender(handle);
      })
      .catch((e) => cancelRender(e));
  }, [url, handle, file]);
  return url;
}

// ------------------------------------------------------------------ text measurement (fonts are loaded before frames render)
let ctx: CanvasRenderingContext2D | null = null;
function textWidth(s: string, font: string): number {
  if (typeof document === 'undefined') return s.length * 40;
  if (!ctx) ctx = document.createElement('canvas').getContext('2d');
  ctx!.font = font;
  return ctx!.measureText(s).width;
}

// ------------------------------------------------------------------ beat state at video time t
type Mode = 'pre' | 'walk' | 'reset' | 'ecg' | 'post';
function beatState(t: number) {
  const W = TL.walk;
  const E = TL.ecg;
  const realEnd = E.realStart + E.realBeats * COND.beat;
  if (t < W.warp[0][0]) return {mode: 'pre' as Mode, tau: 0, total: 0};
  if (t < TL.reset.t) return {mode: 'walk' as Mode, tau: warp(t, W.warp), total: 0};
  if (t < E.slowWarp[0][0]) return {mode: 'reset' as Mode, tau: 0, total: 0};
  let total: number;
  if (t < E.realStart) total = warp(t, E.slowWarp);
  else total = COND.beat + Math.min(t, realEnd) - E.realStart;
  if (t >= E.off) return {mode: 'post' as Mode, tau: 0, total};
  const n = Math.floor(total / COND.beat + 1e-6); // tolerate float error at a beat boundary
  return {mode: 'ecg' as Mode, tau: Math.max(0, total - n * COND.beat), total};
}

// time (video) at which the beat reaches tau, inside the current walk or ECG segment (for shrink timings)
function timeOfTau(tau: number, t: number): number {
  const E = TL.ecg;
  if (t < TL.reset.t) {
    const k = TL.walk.warp;
    for (let i = 1; i < k.length; i++) if (tau <= k[i][1] && k[i][1] > k[i - 1][1]) return k[i - 1][0] + ((tau - k[i - 1][1]) / (k[i][1] - k[i - 1][1])) * (k[i][0] - k[i - 1][0]);
    return k[k.length - 1][0];
  }
  if (t < E.realStart) {
    const k = E.slowWarp;
    for (let i = 1; i < k.length; i++) if (tau <= k[i][1]) return k[i - 1][0] + ((tau - k[i - 1][1]) / (k[i][1] - k[i - 1][1])) * (k[i][0] - k[i - 1][0]);
    return k[k.length - 1][0];
  }
  const beatStart = E.realStart + Math.floor((t - E.realStart) / COND.beat + 1e-6) * COND.beat;
  return beatStart + tau;
}

export const NormalConduction: React.FC = () => {
  const t = useTime();
  const act = useDataUrl('maps/act.png');
  const heartPng = useDataUrl('maps/heart.png');
  const HI = COND.heartImage;
  const st = beatState(t);

  // ---------------------------------------------------------------- heart transform
  const grow = t < TL.heart.shrink ? progress(t, TL.heart.grow, 0.7, 'snap') : 1 - progress(t, TL.heart.shrink, 0.3, 'accel');
  let squeeze = 0;
  if (st.mode === 'walk' || st.mode === 'reset') {
    const s0 = TL.walk.squeeze;
    squeeze = t < s0 ? 0 : t < s0 + 0.35 ? progress(t, s0, 0.35, 'snap') : 1 - progress(t, s0 + 0.35, 0.8, 'snap');
  } else if (st.mode === 'ecg') {
    const x = st.tau;
    const tQ = timeOfTau(0.19, t);
    const tR = timeOfTau(0.33, t);
    squeeze = x < 0.19 ? 0 : x < 0.33 ? progress(t, tQ, Math.max(0.12, tR - tQ), 'snap') : 1 - progress(t, tR, Math.max(0.15, timeOfTau(0.55, t) - tR), 'snap');
  }
  const sq = 1 - 0.025 * squeeze;
  // SVG units -> screen px
  const toScreen = (x: number, y: number) => {
    // squeeze about the heart centre, then grow about the SA node, then the layout
    let X = HEART_C[0] + (x - HEART_C[0]) * sq;
    let Y = HEART_C[1] + (y - HEART_C[1]) * sq;
    const sa = [HEART_C[0] + (SA_X - HEART_C[0]) * sq, HEART_C[1] + (SA_Y - HEART_C[1]) * sq];
    X = sa[0] + (X - sa[0]) * grow;
    Y = sa[1] + (Y - sa[1]) * grow;
    return {x: OX + (X - VB[0]) * K, y: OY + (Y - VB[1]) * K};
  };
  const saScreen = toScreen(SA_X, SA_Y);
  const sqT = `translate(${HEART_C[0]} ${HEART_C[1]}) scale(${sq}) translate(${-HEART_C[0]} ${-HEART_C[1]})`;
  const saSq = [HEART_C[0] + (SA_X - HEART_C[0]) * sq, HEART_C[1] + (SA_Y - HEART_C[1]) * sq];
  const growT = `translate(${saSq[0]} ${saSq[1]}) scale(${Math.max(grow, 0.0001)}) translate(${-saSq[0]} ${-saSq[1]})`;
  const layoutT = `translate(${OX} ${OY}) scale(${K}) translate(${-VB[0]} ${-VB[1]})`;
  const heartOn = grow > 0.001;

  // ---------------------------------------------------------------- lit threshold
  let litTau = -1;
  let litOpacity = 1;
  if (st.mode === 'walk') litTau = st.tau;
  else if (st.mode === 'reset') litTau = COND.times.ventEnd * (1 - progress(t, TL.reset.t, 0.55, 'accel'));
  else if (st.mode === 'ecg') {
    litTau = st.tau;
    litOpacity = recovery(st.tau);
  }
  const tauN = (litTau / COND.actMax) * (250 / 255);
  const KT = 90;

  // ---------------------------------------------------------------- orbs
  const R = COND.routes;
  const endA = R.lbb[R.lbb.length - 1][2];
  const endB = R.rbb[R.rbb.length - 1][2];
  type Orb = {x: number; y: number; r: number; sx?: number; sy?: number};
  const orbs: Orb[] = [];
  const fronts: Orb[] = [];

  // the title dot / orb A before it enters the heart
  const title = TL.title.text;
  const font = `600 ${TITLE_SIZE}px Manrope`;
  const fullW = textWidth(title, font);
  const x0 = 960 - (fullW + DOT_GAP + 2 * DOT_R) / 2;
  let typed = '';
  if (t < TL.title.typeOff) typed = typeOn(title, t, TL.title.typeOn, 30, 2);
  else if (t < TL.dot.grow) typed = typeOff(title, t, TL.title.typeOff, 30, 4);
  else if (t >= TL.title.retype) typed = typeOn(title, t, TL.title.retype, 30, 2);
  const dotAt = (s: string) => ({x: x0 + (s ? textWidth(s, font) : 0) + DOT_GAP + DOT_R, y: TITLE_BASE - DOT_R});

  if (t < TL.dot.land) {
    // pops in, types the title as its cursor, deletes it, grows into the orb, hops into the heart
    const pop = overshoot(t, 0.0, 0.3, 0, 1, 0.1);
    let p = dotAt(typed);
    let r = DOT_R * pop;
    if (t >= TL.dot.grow) {
      const p0 = dotAt('');
      const k = progress(t, TL.dot.grow, 0.6, 'snap');
      p = {x: p0.x + (960 - p0.x) * k, y: p0.y + (540 - p0.y) * k};
      r = DOT_R + (ORB_R - DOT_R) * k;
    }
    if (t >= TL.dot.jump) {
      // anticipation (a small dip), a rise, then down into the SA node
      const tj = TL.dot.jump;
      const dur = TL.dot.land - tj - 0.15;
      const yA = keys(t, [[tj, 540], [tj + 0.15, 556]], 'snap');
      const k = progress(t, tj + 0.15, dur, 'cross');
      const lift = Math.sin(Math.PI * Math.min(1, Math.max(0, (t - tj - 0.15) / dur))) * 140;
      p = {x: 960 + (saScreen.x - 960) * k, y: (t < tj + 0.15 ? yA : 556 + (saScreen.y - 556) * k) - lift};
    }
    orbs.push({...p, r});
  } else if (t < TL.reset.t) {
    // walk-through: orb A rides the left-bundle route, orb B splits off at the bifurcation down the right bundle
    const tau = st.tau;
    const sqA = squash(t, TL.dot.land, 'y', 0.25);
    const a = alongClamped(R.lbb, tau);
    const shrinkA = tau >= endA ? 1 - progress(t, timeOfTau(endA, t), 0.3, 'accel') : 1;
    const sA = toScreen(a.x, a.y);
    // a small squash as the orb runs into the AV node's slow tissue
    const sqAV = squash(t, TL.walk.warp[2][0], 'x', 0.18);
    orbs.push({...sA, r: ORB_R * shrinkA, sx: sqA.sx * sqAV.sx, sy: sqA.sy * sqAV.sy});
    if (tau >= T_BIF) {
      const b = alongClamped(R.rbb, Math.max(tau, T_BIF));
      const shrinkB = tau >= endB ? 1 - progress(t, timeOfTau(endB, t), 0.3, 'accel') : 1;
      orbs.push({...toScreen(b.x, b.y), r: ORB_R * shrinkB});
    }
  } else if (st.mode === 'reset') {
    // the old orbs are gone; a new one grows on the SA node
    const r = overshoot(t, TL.reset.orb, 0.5, 0, ORB_R, 0.1);
    orbs.push({...saScreen, r});
  } else if (st.mode === 'ecg') {
    const tau = st.tau;
    let rA = ORB_R;
    if (tau >= endA) rA = ORB_R * (1 - progress(t, timeOfTau(endA, t), t < TL.ecg.realStart ? 0.3 : 0.05, 'accel'));
    else if (t >= TL.ecg.slowWarp[TL.ecg.slowWarp.length - 1][0]) {
      // later beats: the orb reappears on the SA node as each beat starts
      const tb = timeOfTau(0, t);
      rA = t < TL.ecg.realStart ? ease(t, TL.ecg.slowWarp[TL.ecg.slowWarp.length - 1][0], 0.4, 0, ORB_R) : ORB_R * progress(t, tb, 0.04, 'snap');
    }
    const a = alongClamped(R.lbb, tau);
    orbs.push({...toScreen(a.x, a.y), r: rA});
    if (tau >= T_BIF && tau < endB + 0.02) {
      const b = alongClamped(R.rbb, tau);
      const rB = tau >= endB ? ORB_R * (1 - progress(t, timeOfTau(endB, t), t < TL.ecg.realStart ? 0.3 : 0.05, 'accel')) : ORB_R;
      orbs.push({...toScreen(b.x, b.y), r: rB});
    }
  } else if (st.mode === 'post') {
    // the orb sits on the SA node while the heart folds into it, then becomes the title's period again
    const p0 = saScreen;
    const tm = TL.heart.shrink + 0.35;
    const pEnd = dotAt('');
    const k = progress(t, tm, 0.75, 'cross');
    let p = {x: p0.x + (pEnd.x - p0.x) * k, y: p0.y + (pEnd.y - p0.y) * k};
    let r = ORB_R + (DOT_R - ORB_R) * k;
    if (t >= TL.title.retype) p = dotAt(typed);
    const reappear = t < TL.ecg.off + 0.4 ? ease(t, TL.ecg.off, 0.4, ORB_R * 0.0, ORB_R) : r;
    orbs.push({...p, r: t < TL.ecg.off + 0.4 ? reappear : r});
  }

  // small fronts on the other branches (walk and ECG modes)
  if (heartOn && (st.mode === 'walk' || st.mode === 'ecg')) {
    for (const f of COND.fronts) {
      const q = along(f, st.tau);
      if (q) fronts.push({...toScreen(q.x, q.y), r: FRONT_R * grow});
    }
  }

  // ---------------------------------------------------------------- emphasis: SA pings, AV ring
  const rings: {x: number; y: number; r: number; w: number; dash?: number}[] = [];
  for (const tp of TL.walk.pings) {
    if (t >= tp && t < tp + 0.45) {
      const k = progress(t, tp, 0.45, 'snap');
      rings.push({...saScreen, r: ORB_R * (1 + 1.6 * k), w: 4 * (1 - k)});
    }
  }
  const tAV = TL.walk.steps[2].t + 0.1;
  if (t >= tAV && t < tAV + 1.0) {
    const on = progress(t, tAV, 0.3, 'snap');
    const off = progress(t, tAV + 0.7, 0.3, 'accel');
    const c = toScreen(COND.points.AV[0], COND.points.AV[1]);
    rings.push({...c, r: 44, w: 4, dash: on - off});
  }

  // ---------------------------------------------------------------- captions
  const W = TL.walk;
  const walkItems: CaptionItem[] = W.steps.map((s) => ({t: s.t, head: s.head, body: s.body}));
  const E = TL.ecg;
  const ecgItems: CaptionItem[] = [
    ...E.labels.map((l) => ({t: l.t, head: l.head, body: l.body})),
    {t: E.realStart, head: E.realHead, body: E.realBody},
  ];
  const stepIndex = W.steps.filter((s) => t >= s.t).length - 1;

  return (
    <AbsoluteFill style={{background: M.bg}}>
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0}}>
        <defs>
          <filter id="thr" x="0" y="0" width="1" height="1" colorInterpolationFilters="sRGB">
            <feColorMatrix type="matrix" values={`0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  ${-KT} 0 0 0 ${KT * tauN + 0.5}`} />
          </filter>
          <mask id="lit" maskUnits="userSpaceOnUse" x={VB[0]} y={VB[1]} width={VB[2]} height={VB[3]}>
            {act && litTau >= 0 ? (
              <image href={act} x={VB[0]} y={VB[1]} width={VB[2]} height={VB[3]} preserveAspectRatio="none" filter="url(#thr)" />
            ) : null}
          </mask>
        </defs>

        {heartOn ? (
          <g transform={layoutT}>
            <g transform={growT}>
              <g transform={sqT}>
                {heartPng ? <image href={heartPng} x={HI.x} y={HI.y} width={HI.w} height={HI.h} /> : null}
                <g>
                  {COND_ART.map(([d, fill], i) => (
                    <path key={i} d={d} fill={fill} stroke={fill} strokeWidth={0.73} />
                  ))}
                </g>
                {litTau >= 0 ? (
                  <g mask="url(#lit)" opacity={litOpacity}>
                    {COND_ART.map(([d, , lit], i) => (
                      <path key={i} d={d} fill={lit} stroke={lit} strokeWidth={0.73} />
                    ))}
                  </g>
                ) : null}
              </g>
            </g>
          </g>
        ) : null}

        {/* title */}
        {typed ? (
          <text x={x0} y={TITLE_BASE} fontFamily={FONT_HEAD} fontWeight={600} fontSize={TITLE_SIZE} fill={M.ink} letterSpacing={0}>
            {typed}
          </text>
        ) : null}

        {/* ECG strip */}
        <EcgStrip t={t} total={st.total} />

        {/* emphasis rings */}
        {rings.map((g, i) => (
          <circle
            key={i}
            cx={g.x}
            cy={g.y}
            r={g.r}
            fill="none"
            stroke={M.ink}
            strokeWidth={g.w}
            pathLength={1}
            strokeDasharray={g.dash === undefined ? undefined : `${Math.max(0, g.dash)} 1`}
            transform={g.dash === undefined ? undefined : `rotate(-90 ${g.x} ${g.y})`}
          />
        ))}

        {/* fronts and orbs */}
        {fronts.map((f, i) => (
          <circle key={`f${i}`} cx={f.x} cy={f.y} r={f.r} fill={M.orb} stroke={M.ring} strokeWidth={1.5} />
        ))}
        {orbs.map((o, i) =>
          o.r > 0.05 ? (
            <ellipse
              key={`o${i}`}
              cx={o.x}
              cy={o.y}
              rx={o.r * (o.sx ?? 1)}
              ry={o.r * (o.sy ?? 1)}
              fill={M.orb}
              stroke={heartOn && t > TL.dot.land - 0.1 ? M.ring : 'none'}
              strokeWidth={3}
            />
          ) : null,
        )}
      </svg>

      {/* step dots and walk-through captions */}
      <StepDots t={t} index={stepIndex} n={W.steps.length} x={1090} y={404} on={W.steps[0].t} off={W.end} />
      <Caption items={walkItems} t={t} end={W.end} x={1090} y={436} />
      {/* ECG captions */}
      <Caption items={ecgItems} t={t} end={E.off} x={1040} y={708} />
      <Kicker t={t} x={1040} y={300} />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ step dots: where we are on the path
const StepDots: React.FC<{t: number; index: number; n: number; x: number; y: number; on: number; off: number}> = ({t, index, n, x, y, on, off}) => {
  if (t < on || t > off + 0.5) return null;
  return (
    <svg width={400} height={40} style={{position: 'absolute', left: x - 10, top: y - 20}}>
      {Array.from({length: n}).map((_, i) => {
        const s = t < off ? overshoot(t, on + i * (2 / 30), 0.4, 0, 1, 0.1) : 1 - progress(t, off - 0.25 + i * (1 / 30), 0.25, 'accel');
        const done = i <= index;
        const pulse = i === index ? 1 + 0.25 * (1 - progress(t, TL.walk.steps[i]?.t ?? 0, 0.3, 'snap')) : 1;
        return <circle key={i} cx={10 + i * 30} cy={20} r={7 * Math.max(0, s) * pulse} fill={done ? M.ink : 'none'} stroke={done ? M.ink : M.inactive} strokeWidth={2.5} />;
      })}
    </svg>
  );
};

// ------------------------------------------------------------------ kicker above the ECG
const Kicker: React.FC<{t: number; x: number; y: number}> = ({t, x, y}) => {
  const E = TL.ecg;
  const items: CaptionItem[] = [
    {t: E.kickerSlow, head: '', body: '', kicker: 'One beat, slowed down'},
    {t: E.realStart, head: '', body: '', kicker: 'Real speed'},
  ];
  return <Caption items={items} t={t} end={E.off} x={x} y={y} kickerOnly />;
};

// ------------------------------------------------------------------ the ECG strip
const ECG = {x0: 1040, x1: 1840, base: 560, amp: 190, pxPerS: 1000};
const EcgStrip: React.FC<{t: number; total: number}> = ({t, total}) => {
  const E = TL.ecg;
  if (t < E.axisOn) return null;
  // baseline draws on, then the trace draws with the beat; draws out in reverse at the end
  const axisK = t < E.off ? progress(t, E.axisOn, 0.6, 'snap') : 1 - progress(t, E.off + 0.15, 0.55, 'accel');
  const traceK = t < E.off ? 1 : 1 - progress(t, E.off, 0.45, 'accel');
  if (axisK <= 0.001 && traceK <= 0.001) return null;
  const pen = ECG.x0 + total * ECG.pxPerS;
  const scroll = Math.max(0, pen - (ECG.x1 - 40));
  const pts: string[] = [];
  const visStart = (ECG.x0 + scroll - ECG.x0) / ECG.pxPerS;
  const visEndTau = total;
  const step = 0.0015;
  const begin = Math.max(0, visStart - 0.01);
  if (t >= E.slowWarp[0][0]) {
    for (let s = begin; s <= visEndTau + 1e-9; s += step) {
      pts.push(`${(ECG.x0 + s * ECG.pxPerS - scroll).toFixed(1)},${(ECG.base - ecg(s) * ECG.amp).toFixed(1)}`);
    }
    pts.push(`${(pen - scroll).toFixed(1)},${(ECG.base - ecg(visEndTau) * ECG.amp).toFixed(1)}`);
  }
  // trace draws out from its start (left) as it leaves
  const traceLen = pts.length;
  const keep = Math.round(traceLen * traceK);
  const shown = pts.slice(traceLen - keep);
  // bracket under the component being labelled (slow beat only)
  const lab = t < E.realStart ? [...E.labels].reverse().find((l) => t >= l.t) : undefined;
  let bracket: React.ReactNode = null;
  if (lab && t < E.realStart) {
    const prev = E.labels[E.labels.indexOf(lab) - 1];
    const k = prev ? progress(t, lab.t, 0.45, 'snap') : progress(t, lab.t, 0.45, 'snap');
    const fx = prev ? prev.from + (lab.from - prev.from) * k : lab.from;
    const tx = prev ? prev.to + (lab.to - prev.to) * k : lab.from + (lab.to - lab.from) * k;
    const bx0 = ECG.x0 + fx * ECG.pxPerS;
    const bx1 = ECG.x0 + tx * ECG.pxPerS;
    const by = 646;
    bracket = <path d={`M${bx0},${by - 10} L${bx0},${by} L${bx1},${by} L${bx1},${by - 10}`} fill="none" stroke={M.ink} strokeWidth={3} strokeLinejoin="round" />;
  }
  return (
    <g>
      <defs>
        <clipPath id="ecgclip">
          <rect x={ECG.x0 - 4} y={200} width={ECG.x1 - ECG.x0 + 8} height={500} />
        </clipPath>
      </defs>
      <line x1={ECG.x0} y1={ECG.base} x2={ECG.x0 + (ECG.x1 - ECG.x0) * Math.max(0, axisK)} y2={ECG.base} stroke={M.inactive} strokeWidth={2} />
      <g clipPath="url(#ecgclip)">
        {shown.length > 1 ? <polyline points={shown.join(' ')} fill="none" stroke={M.ink} strokeWidth={4.5} strokeLinejoin="round" strokeLinecap="round" /> : null}
        {t >= E.slowWarp[0][0] && t < E.off ? <circle cx={pen - scroll} cy={ECG.base - ecg(total) * ECG.amp} r={7} fill={M.ink} /> : null}
      </g>
      {bracket}
    </g>
  );
};
