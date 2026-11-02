import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Audio, continueRender, delayRender, staticFile, useCurrentFrame} from 'remotion';
import {T, FPS, LEAD, END_VO} from './theme';
import {HeartLayer, HeartState, Layout, stageTransform, toStage, SA, AV, ATR_MAX, VENT_MAX, AV_REACH, SA_BODY} from './Heart';
import {StripCard, Marker} from './Strip';
import {LoopCard, Schematic, lapFlash, AVRT_AV, AVRT_ACC} from './Loops';
import {strip} from './ecg';
import {PREPRINT} from './Intro';
import {At, Chip, Sub, S, FontFaces, appear, clamp, ramp, lerp, easeIO, easeOut} from './ui';

// ------------------------------------------------------------------ timing helpers
const span = (t: number, a: number, b: number, v0: number, v1: number, e = (x: number) => x) => v0 + (v1 - v0) * e(clamp((t - a) / (b - a)));

// beats (QRS onset times, VO seconds) for the main heart
function makeBeats(): number[] {
  const out: number[] = []; let q = 27.25;
  while (q < 66) { out.push(q); const rr = q < 44.1 ? 0.8 : q < 45.3 ? lerp(0.8, 60 / 130, (q - 44.1) / 1.2) : 60 / 130; q += rr; }
  q = 149.25; while (q < 156.5) { out.push(q); q += 60 / 130; }
  return out;
}
const BEATS = makeBeats();
// one sinus beat: atrial wave (P), AV hold (PR), ventricular wave (QRS), then recovery
export function beatState(t: number): HeartState {
  let q = -1; for (const b of BEATS) { if (b - 0.2 <= t) q = b; else break; }
  if (q < 0) return {atr: 0, vent: 0, lit: 0};
  const atr = span(t, q - 0.2, q - 0.07, 0, ATR_MAX), vent = span(t, q - 0.02, q + 0.1, 0, VENT_MAX);
  const lit = 1 - clamp((t - (q + 0.1)) / 0.16);
  const avGlow = t > q - 0.12 && t < q ? 0.8 : 0;
  return {atr, vent, lit, avGlow};
}
// the slow, narrated first beat (section 2)
function narrativeState(t: number): HeartState {
  let atr = 0;
  if (t >= 11.94) atr = span(t, 11.94, 12.4, 0, SA_BODY, easeOut);
  if (t >= 14.3) atr = span(t, 14.3, 17.3, SA_BODY, AV_REACH);
  if (t >= 17.3) atr = span(t, 17.3, 19.6, AV_REACH, ATR_MAX, easeOut);
  const vent = t < 23.78 ? 0 : span(t, 23.78, 25.4, 0, VENT_MAX, x => x * x * (2 - x));
  const saGlow = t < 11.94 ? 0 : Math.max(0.35, 1 - clamp((t - 12.4) / 1.6) * 0.65);
  const avGlow = t > 17.5 && t < 23.9 ? (0.55 + 0.35 * Math.sin((t - 17.5) * Math.PI * 1.6)) * clamp((t - 17.5) / 0.4) : 0;
  return {atr, vent, lit: 1, saGlow, avGlow};
}

const FULL: Layout = {x: 0, y: 0, s: 1}, LEFT: Layout = {x: -80, y: 60, s: 0.82}, TACH: Layout = {x: -40, y: 150, s: 0.8};
const mixL = (a: Layout, b: Layout, k: number): Layout => ({x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), s: lerp(a.s, b.s, k)});
function heartLayout(t: number): Layout {
  if (t < 26.98) return FULL;
  if (t < 39.56) return mixL(FULL, LEFT, ramp(t, 26.98, 27.8));
  if (t < 140) return mixL(LEFT, TACH, ramp(t, 39.56, 40.4));
  return TACH;
}

// loop phase with a period that eases from p0 to p1 over R seconds (integral of 1/period)
function rampPhase(tau: number, p0: number, p1: number, R: number) {
  if (tau <= 0) return 0;
  if (p0 === p1) return tau / p0;
  const k = (p1 - p0) / R;
  if (tau < R) return Math.log((p0 + k * tau) / p0) / k;
  return Math.log(p1 / p0) / k + (tau - R) / p1;
}
// latest time <= t at which phaseFn crossed (n + frac); -1 if none since t0
export function lastCross(phaseFn: (x: number) => number, frac: number, t0: number, t: number) {
  const n = Math.floor(phaseFn(t) - frac); if (n < 0) return -1;
  const target = n + frac; let lo = t0, hi = t;
  for (let i = 0; i < 40; i++) { const m = (lo + hi) / 2; if (phaseFn(m) < target) lo = m; else hi = m; }
  return hi;
}
export const avnrtPhase = (t: number) => rampPhase(t - 77.2, 1.3, 1 / 3, 3.0);           // sections 4
export const avnrtPhase2 = (t: number) => rampPhase(t - 127.5, 1 / 3, 1 / 3, 1);        // section 6, already running
const AVRT_KEYS: [number, number][] = [[91.38, 0], [92.58, AVRT_AV + 0.02], [93.54, AVRT_ACC], [94.44, 1]];
function avrtPhase(t: number) {
  if (t <= AVRT_KEYS[0][0]) return 0;
  for (let i = 1; i < AVRT_KEYS.length; i++) { const [t0, p0] = AVRT_KEYS[i - 1], [t1, p1] = AVRT_KEYS[i]; if (t <= t1) return lerp(p0, p1, easeIO(clamp((t - t0) / (t1 - t0))) * 0.4 + clamp((t - t0) / (t1 - t0)) * 0.6); }
  return 1 + (t - 94.44) / 0.36;
}

// strip timings tied to words
const ONSET_TICK = 3.18, OFFSET_TICK = 7.45, ONSET_T0 = 100.62 - ONSET_TICK;
export const ADENO_TICK = 3.62, CONVERT_T0 = 143.08 - ADENO_TICK;
const F17_T0 = 95.3;

// ------------------------------------------------------------------ small pieces
const Eyebrow: React.FC<{t: number; tin: number; tout: number; color: string; text: string}> = ({t, tin, tout, color, text}) => (
  <At t={t} tin={tin} tout={tout} x={120} y={84}><div style={{...S.eyebrow, color}}>{text}</div></At>
);
const H2: React.FC<{t: number; tin: number; tout: number; x?: number; y?: number; w?: number; children: React.ReactNode; color?: string; align?: 'left' | 'right' | 'center'}> = ({t, tin, tout, x = 120, y = 120, w = 1300, children, color = T.ink, align = 'left'}) => (
  <At t={t} tin={tin} tout={tout} x={x} y={y} w={w}><div style={{...S.h2, color, textAlign: align}}>{children}</div></At>
);
export const Col: React.FC<{gap?: number; children: React.ReactNode}> = ({gap = 16, children}) => <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap}}>{children}</div>;
// a chip that appears in place inside a flex column, keeping its slot
export const Slot: React.FC<{t: number; tin: number; children: React.ReactNode}> = ({t, tin, children}) => {
  const a = appear(t, tin, 1e9, 16);
  return <div style={{opacity: a.o, transform: `translateY(${a.dy}px)`}}>{children}</div>;
};

// leader-line label in stage coords
const Label: React.FC<{t: number; tin: number; tout: number; from: {x: number; y: number}; to: {x: number; y: number}; text: string; anchor: 'start' | 'end'}> = ({t, tin, tout, from, to, text, anchor}) => {
  const a = appear(t, tin, tout, 0); if (!a.live) return null;
  const k = easeOut(clamp((t - tin) / 0.45));
  const ex = lerp(from.x, to.x, k), ey = lerp(from.y, to.y, k);
  return (
    <g opacity={a.o}>
      <path d={`M${from.x} ${from.y}L${ex} ${ey}`} stroke={T.ink2} strokeWidth={2} fill="none" />
      <circle cx={from.x} cy={from.y} r={4} fill={T.ink2} />
      <text x={to.x + (anchor === 'end' ? -12 : 12)} y={to.y + 9} fontFamily={T.font} fontSize={30} fontWeight={500} fill={T.ink} textAnchor={anchor} opacity={clamp((t - tin - 0.2) / 0.3)}>{text}</text>
    </g>
  );
};

// ------------------------------------------------------------------ main
export const Main: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS - LEAD;            // VO time
  const [ready, setReady] = useState(false);
  const [handle] = useState(() => delayRender('fonts + maps'));
  useEffect(() => {
    const imgs = ([] as string[]).map(u => new Promise<void>(res => { const i = new Image(); i.onload = () => i.decode().then(() => res(), () => res()); i.onerror = () => res(); i.src = staticFile(u); }));
    const fonts = [400, 500, 700].map(w => document.fonts.load(`${w} 30px "DM Sans"`));
    Promise.all([...imgs, ...fonts]).then(() => { setReady(true); requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(() => continueRender(handle), 120))); });
  }, [handle]);

  // ---------- main heart (sections 2, 3 and the "treat the cause" beat)
  const heartVis = (t >= 9.8 && t < 64.6) || (t >= 148.9 && t < 155.9);
  let hs: HeartState = {atr: 0, vent: 0, lit: 0};
  if (t < 26.98) hs = narrativeState(t);
  else if (t < 27.25) { const n = narrativeState(26.9); hs = {...n, lit: 1 - clamp((t - 26.98) / 0.2), avGlow: 0, saGlow: 0}; }
  else hs = beatState(t);
  const L = heartLayout(t);
  const heartIn = t < 100 ? appear(t, 9.85, 64.28, 0) : appear(t, 149.04, 155.5, 0);
  const heartDX = t < 100 ? -60 * easeIO(clamp((t - 64.28) / 0.4)) : -60 * easeIO(clamp((t - 155.5) / 0.4));
  const heartScaleIn = t < 100 ? lerp(0.96, 1, easeOut(clamp((t - 9.85) / 0.7))) : lerp(0.96, 1, easeOut(clamp((t - 149.04) / 0.7)));

  // ---------- loop sections
  const sec4 = t >= 73.6 && t < 95.8;
  const cardA_draw = clamp((t - 76.06) / 0.8);
  const phA = t >= 77.2 ? avnrtPhase(t) : null;
  const crossA = phA === null ? -1 : lastCross(avnrtPhase, 0.5, 77.2, t);
  const cardAHeart = {...(crossA > 0 ? lapFlash(t, crossA) : {atr: 0, vent: 0, lit: 0}), avGlow: t >= 76.5 ? 0.8 : 0};
  const cardAScale = lerp(1, 0.82, ramp(t, 86.32, 87.0));
  const phB = t >= 91.38 ? avrtPhase(t) : null;
  const crossB = phB === null ? -1 : lastCross(avrtPhase, AVRT_AV + 0.02, 91.38, t);
  const cardBHeart = {...(crossB > 0 ? lapFlash(t, crossB) : {atr: 0, vent: 0, lit: 0}), avGlow: t >= 91.3 ? 0.6 : 0};
  const drawB = t < 91.38 ? 0 : t < 94.44 ? clamp(avrtPhase(t)) : 1;

  // f17 schematic synced to strip: bottom of loop (phase .5) at every QRS of the avnrt180 strip
  const schPhase17 = (x: number) => (x - F17_T0 - 0.25) * 3 + 0.5;
  const sch17Cross = lastCross(x => schPhase17(x) + 10, 0.5, F17_T0 - 3.5, t);
  const flash17 = sch17Cross > 0 ? 1 - clamp((t - sch17Cross) / 0.28) : 0;
  // section 6 loops (block at 135.62)
  const blocked = t >= 135.62;
  const ph6 = avnrtPhase2(t);
  const cross6 = lastCross(avnrtPhase2, 0.5, 127.5, t);
  const flash6 = cross6 > 0 ? 1 - clamp((t - cross6) / 0.28) : 0;
  const card6Heart = !blocked && cross6 > 0 ? {...lapFlash(t, cross6), avGlow: 0.8} : {atr: 0, vent: 0, lit: 0};

  const sinus130 = strip('sinus130'), avnrt180 = strip('avnrt180'), sinus75 = strip('sinus75');
  const pMarks = (beats: {t: number}[], showAt: number): Marker[] => beats.map(b => ({kind: 'P', t: b.t - 0.1, showAt}));

  // compare table geometry
  const CX = {label: 120, a: 370, b: 1110}, colW = 700;

  // final fade
  const endFade = clamp((t - (END_VO - 0.5)) / 0.5);

  return (
    <AbsoluteFill style={{background: T.bg, fontFamily: T.font, color: T.ink}}>
      <FontFaces />
      <Audio src={staticFile('vo.mp3')} />
      {ready && (
        <AbsoluteFill style={{opacity: 1 - endFade}}>
          {/* ================= 1. Cold open + title ================= */}
          <At t={t} tin={-1.5} tout={9.75} x={260} y={span(t, 8.2, 8.8, 390, 560, easeIO)} rise={0}>
            <StripCard id="open" t={t} t0={-1.5 - PREPRINT} name="open170" w={1400} h={300} label="Lead II · 25 mm/s" rate={170} dim={ramp(t, 8.2, 8.6)} />
          </At>
          <H2 t={t} tin={5.56} tout={8.2} x={260} y={232} w={1400} color={T.tealInk}>Answering a call,</H2>
          <H2 t={t} tin={7.52} tout={8.2} x={260} y={736} w={1400} color={T.coralInk}>or stuck in a loop?</H2>
          <At t={t} tin={8.3} tout={9.75} x={260} y={300} w={1400}><div style={{...S.h1, textAlign: 'center'}}>Sinus tach <span style={{color: T.ink3, fontWeight: 400}}>vs</span> SVT</div></At>
          <At t={t} tin={8.5} tout={9.75} x={260} y={430} w={1400}><div style={{...S.lead, textAlign: 'center'}}>Answering, or looping?</div></At>

          {/* ================= main heart ================= */}
          {heartVis && (
            <div style={{position: 'absolute', inset: 0, opacity: heartIn.o, transform: `translateX(${heartDX}px) scale(${heartScaleIn})`, transformOrigin: '50% 50%'}}>
              <HeartLayer s={hs} transform={stageTransform(L)} />
              <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{position: 'absolute', left: 0, top: 0}}>
                {t < 27.4 && (() => {
                  const sa = toStage(SA.x - 260, SA.y - 60, FULL), av = toStage(AV.x - 300, AV.y + 120, FULL), hp = toStage(6300, 5500, FULL);
                  return <g>
                    <Label t={t} tin={11.94} tout={26.98} from={sa} to={{x: 560, y: 222}} text="SA node" anchor="end" />
                    <Label t={t} tin={17.38} tout={26.98} from={av} to={{x: 560, y: 600}} text="AV node" anchor="end" />
                    <Label t={t} tin={24.46} tout={26.98} from={{x: hp.x + 10, y: hp.y}} to={{x: 1420, y: hp.y}} text="His-Purkinje" anchor="start" />
                  </g>;
                })()}
                {t >= 35.6 && t < 39.8 && (() => {
                  const a = appear(t, 35.84, 39.4, 0); const y = toStage(0, AV.y, LEFT).y; const top = toStage(0, 900, LEFT).y; const xl = toStage(0, 0, LEFT).x + 300 * 0.82 - toStage(0, 0, LEFT).x;
                  const x1 = -80 + 300 * 0.82, x2 = lerp(x1, -80 + 1420 * 0.82, easeOut(clamp((t - 35.84) / 0.6))), bx = -80 + 1440 * 0.82;
                  void xl;
                  return <g opacity={a.o}>
                    <line x1={x1} y1={y} x2={x2} y2={y} stroke={T.ink} strokeWidth={3} strokeDasharray="14 12" />
                    <g opacity={clamp((t - 37.08) / 0.4)}><path d={`M${bx} ${top}V${y}`} stroke={T.ink} strokeWidth={3} fill="none" /><path d={`M${bx - 12} ${top}h12M${bx - 12} ${y}h12`} stroke={T.ink} strokeWidth={3} /></g>
                  </g>;
                })()}
              </svg>
            </div>
          )}
          <At t={t} tin={18.44} tout={23.6} x={300} y={640}><Chip kind="amber">holds ≈ 0.1 s</Chip></At>

          {/* f08 narrow QRS */}
          <At t={t} tin={27.0} tout={30.0} x={1180} y={300}>
            <StripCard id="beat" t={t} t0={27.0} name="sinus75" w={620} h={360} baseline={0.55} label="Lead II" markers={[{kind: 'bracket', t: 1.04, t2: 1.125, text: 'QRS < 120 ms', showAt: 28.34}]} />
          </At>
          <At t={t} tin={29.14} tout={30.0} x={1180} y={700}><Chip kind="amber">Fast lane → narrow QRS</Chip></At>
          {/* f09 */}
          <At t={t} tin={34.58} tout={39.4} x={1180} y={330} w={640}><div style={S.h3}>Both rhythms start <span style={{color: T.coralInk}}>at or above</span> the AV node</div></At>
          <At t={t} tin={30.22} tout={39.4} x={1180} y={480} rise={0}>
            <Col><Slot t={t} tin={30.22}><Chip kind="ink">Narrow QRS</Chip></Slot><Slot t={t} tin={32.22}><Chip>→ ventricles still use the fast lane</Chip></Slot><Slot t={t} tin={34.98}><Chip>→ origin at or above the AV node</Chip></Slot></Col>
          </At>

          {/* ================= 3. Sinus tachycardia ================= */}
          <Eyebrow t={t} tin={39.56} tout={73.5} color={T.tealInk} text="Sinus tachycardia" />
          <H2 t={t} tin={39.56} tout={64.1}>The heart <span style={{color: T.tealInk}}>answering</span></H2>
          <At t={t} tin={41.06} tout={48.3} x={1180} y={400} rise={0}>
            <Col><Slot t={t} tin={41.06}><Chip>same route, just faster</Chip></Slot><Slot t={t} tin={44.58}><Chip kind="teal">SA node firing &gt; 100 /min</Chip></Slot></Col>
          </At>
          <At t={t} tin={45.8} tout={48.3} x={1180} y={560} w={620}><div style={S.lead}>because the body is asking for more output</div></At>
          <At t={t} tin={49.52} tout={64.1} x={1180} y={300}><div style={S.eyebrow}>Harmless</div></At>
          <At t={t} tin={50.4} tout={64.1} x={1180} y={340} rise={0}>
            <Col gap={12}>{[['Exercise', 50.56], ['Stress', 51.5], ['Pain', 52.22], ['Anxiety', 52.84]].map(([s, a]) => <Slot key={s} t={t} tin={a as number}><Chip kind="teal">{s}</Chip></Slot>)}</Col>
          </At>
          <At t={t} tin={54.78} tout={64.1} x={1500} y={300}><div style={{...S.eyebrow, color: T.coralInk}}>Serious</div></At>
          <At t={t} tin={55.9} tout={64.1} x={1500} y={340} rise={0}>
            <Col gap={12}>{[['Low oxygen', 56.04], ['Blood loss', 56.84], ['Dehydration', 57.66], ['Sepsis', 58.76]].map(([s, a]) => <Slot key={s} t={t} tin={a as number}><Chip kind="coral">{s}</Chip></Slot>)}</Col>
          </At>
          <At t={t} tin={59.88} tout={64.1} x={1180} y={700} w={640}><div style={S.lead}>A fast resting heart rate can be one of the earliest signs that something is wrong.</div></At>
          {/* f13 */}
          <H2 t={t} tin={64.4} tout={73.5}>A normal beat, only faster</H2>
          <At t={t} tin={64.4} tout={73.5} x={260} y={300}>
            <StripCard id="s130" t={t} t0={64.5} name="sinus130" w={1400} h={320} label="Lead II · 25 mm/s" rate={130} markers={pMarks(sinus130.beats, 68.56)} />
          </At>
          <At t={t} tin={69.22} tout={73.5} x={260} y={680} rise={0}>
            <div style={{display: 'flex', gap: 16}}><Slot t={t} tin={69.22}><Chip kind="teal">Upright P in I, II and aVL</Chip></Slot><Slot t={t} tin={71.6}><Chip kind="teal">One P before every QRS</Chip></Slot></div>
          </At>

          {/* ================= 4. SVT ================= */}
          <Eyebrow t={t} tin={73.7} tout={107.6} color={T.coralInk} text="SVT" />
          <H2 t={t} tin={73.7} tout={86.2}>The heart in a <span style={{color: T.coralInk}}>loop</span></H2>
          <H2 t={t} tin={86.4} tout={95.3}>Two kinds of loop</H2>
          <H2 t={t} tin={95.44} tout={97.6}>Every lap fires the ventricles</H2>
          <H2 t={t} tin={97.76} tout={107.6}>A switch, not a dial</H2>
          {sec4 && (
            <At t={t} tin={73.9} tout={95.3} x={120} y={260} rise={0} style={{transform: `scale(${cardAScale * lerp(0.94, 1, easeOut(clamp((t - 73.9) / 0.6)))})`, transformOrigin: '0 0'}}>
              <LoopCard uid="cA" kind="avnrt" w={1000} h={720} draw={cardA_draw} phase={phA} heart={cardAHeart} />
            </At>
          )}
          <At t={t} tin={76.06} tout={80.4} x={1180} y={300}><Chip kind="coral">Re-entry</Chip></At>
          <At t={t} tin={77.2} tout={80.4} x={1180} y={400} w={620}><div style={S.lead}>A signal caught in a circuit, going around and around.</div></At>
          <At t={t} tin={80.9} tout={86.2} x={1180} y={300} rise={0}>
            <Col><Slot t={t} tin={81.02}><Chip>the most common type</Chip></Slot><Slot t={t} tin={81.94}><Chip kind="coral">AVNRT</Chip></Slot><Slot t={t} tin={84.02}><Chip>circuit inside the AV node</Chip></Slot></Col>
          </At>
          {t >= 86.2 && t < 95.8 && (
            <At t={t} tin={86.32} tout={95.3} x={980} y={260} style={{}}>
              <LoopCard uid="cB" kind="avrt" w={820} h={590} draw={drawB} phase={phB} heart={cardBHeart} accGlow={appear(t, 88.18, 90.4, 0).o + (t > 93.3 && t < 93.9 ? 1 : 0)} />
            </At>
          )}
          <At t={t} tin={86.6} tout={95.3} x={120} y={880}><div style={{display: 'flex', gap: 12}}><Chip kind="coral">AVNRT</Chip><Chip>circuit inside the AV node</Chip></div></At>
          <At t={t} tin={86.9} tout={95.3} x={980} y={880}><div style={{display: 'flex', gap: 12}}><Chip kind="coral">AVRT</Chip><Chip>down the AV node, back up an extra pathway</Chip></div></At>
          {/* f17 */}
          <At t={t} tin={95.44} tout={97.6} x={120} y={260}>
            <Schematic w={640} h={560} phase={schPhase17(t)} flash={flash17} />
          </At>
          <At t={t} tin={95.44} tout={97.6} x={820} y={340}>
            <StripCard id="lap" t={t} t0={F17_T0} name="avnrt180" w={980} h={300} label="Lead II · 25 mm/s" rate={180} markers={avnrt180.beats.map(b => ({kind: 'lap', t: b.t + 0.03}))} />
          </At>
          <At t={t} tin={96.16} tout={97.6} x={820} y={700}><Chip kind="coral">one lap → one QRS</Chip></At>
          {/* f18 */}
          <At t={t} tin={97.76} tout={107.6} x={120} y={300}>
            <StripCard id="onset" t={t} t0={ONSET_T0} name="onset" w={1680} h={320} label="Lead II · 25 mm/s" markers={[{kind: 'tick', t: ONSET_TICK, text: 'starts suddenly', showAt: 100.62}, {kind: 'tick', t: OFFSET_TICK, text: 'stops abruptly', anchor: 'end', dx: -12, showAt: 104.9}]} />
          </At>
          <At t={t} tin={100.5} tout={107.6} x={120} y={680} rise={0}>
            <div style={{display: 'flex', gap: 16}}><Slot t={t} tin={100.62}><Chip kind="coral">Starts suddenly</Chip></Slot><Slot t={t} tin={103.58}><Chip kind="coral">150 – 220 /min, regular</Chip></Slot><Slot t={t} tin={105.76}><Chip kind="coral">Stops abruptly</Chip></Slot></div>
          </At>

          {/* ================= 5. Side by side ================= */}
          <Eyebrow t={t} tin={107.8} tout={127.2} color={T.ink2} text="Side by side" />
          <At t={t} tin={107.9} tout={127.2} x={CX.a} y={130}><div style={{...S.h3, color: T.tealInk}}>Sinus tach <span style={{fontWeight: 400, color: T.ink2}}>· answering</span></div></At>
          <At t={t} tin={108.1} tout={127.2} x={CX.b} y={130}><div style={{...S.h3, color: T.coralInk}}>SVT <span style={{fontWeight: 400, color: T.ink2}}>· looping</span></div></At>
          {[[214, 109.6], [370, 112.0], [480, 120.9]].map(([y, a], i) => { const o = appear(t, a, 127.2, 0); const k = easeOut(clamp((t - a) / 0.6)); return o.live ? <div key={i} style={{position: 'absolute', left: 120, top: y, width: 1690 * k, height: 1.5, background: T.line, opacity: o.o}} /> : null; })}
          <At t={t} tin={109.6} tout={127.2} x={CX.label} y={252}><div style={S.eyebrow}>Trigger</div></At>
          <At t={t} tin={109.84} tout={127.2} x={CX.a} y={236}><Chip kind="teal">A reason you can find</Chip></At>
          <At t={t} tin={113.76} tout={127.2} x={CX.b} y={236}><Chip kind="coral">Often none</Chip></At>
          <At t={t} tin={116.08} tout={127.2} x={CX.b} y={306}><div style={{...S.lead, fontSize: 26}}>sometimes caffeine, stimulants, stress</div></At>
          <At t={t} tin={112.0} tout={127.2} x={CX.label} y={408}><div style={S.eyebrow}>Start and stop</div></At>
          <At t={t} tin={112.24} tout={127.2} x={CX.a} y={392}><Chip kind="teal">Follows the reason</Chip></At>
          <At t={t} tin={119.36} tout={127.2} x={CX.b} y={392}><Chip kind="coral">Switches on and off</Chip></At>
          <At t={t} tin={120.9} tout={127.2} x={CX.label} y={600}><div style={S.eyebrow}>P waves</div></At>
          <At t={t} tin={121.0} tout={127.2} x={CX.a} y={508}>
            <StripCard id="cmpA" t={t} t0={121.0} name="sinus130" w={colW} h={190} markers={pMarks(sinus130.beats, 121.4)} />
          </At>
          <At t={t} tin={121.06} tout={127.2} x={CX.b} y={508}>
            <StripCard id="cmpB" t={t} t0={121.0} name="avnrt180" w={colW} h={190} markers={avnrt180.beats.map(b => ({kind: 'noP', t: b.t + 0.03, showAt: 122.56}))} />
          </At>
          <At t={t} tin={121.6} tout={127.2} x={CX.a} y={716}><Chip kind="teal">Upright P before every QRS</Chip></At>
          <At t={t} tin={124.92} tout={127.2} x={CX.b} y={716}><Chip kind="coral">Hidden inside the QRS</Chip></At>

          {/* ================= 6. The AV node is the key ================= */}
          <Eyebrow t={t} tin={127.36} tout={148.9} color={T.coralInk} text="Breaking the loop" />
          <H2 t={t} tin={127.36} tout={148.9}>The AV node is the key</H2>
          <At t={t} tin={127.5} tout={137.9} x={120} y={260}>
            <Schematic w={480} h={600} phase={ph6 + 0.5} flash={flash6} block={blocked} />
          </At>
          {t >= 127.3 && t < 138.3 && (
            <At t={t} tin={127.7} tout={137.9} x={630} y={260}>
              <LoopCard uid="c6" kind="avnrt" w={520} h={600} view={2500} center={{x: 3650, y: 3950}} draw={1} phase={blocked ? null : ph6 + 0.5} block={blocked} heart={card6Heart} />
            </At>
          )}
          <At t={t} tin={129.6} tout={137.9} x={1200} y={300} rise={0}>
            <Col><Slot t={t} tin={129.76}><Chip kind="ink">Vagal maneuvers</Chip></Slot><Slot t={t} tin={130.64}><Chip kind="ink">Adenosine</Chip></Slot><Slot t={t} tin={131.64}><Chip>→ slow conduction through the AV node</Chip></Slot></Col>
          </At>
          <At t={t} tin={136.74} tout={137.9} x={1200} y={560} w={600}><div style={S.lead}>Block the node for a moment and the loop breaks.</div></At>
          {/* f23 */}
          <At t={t} tin={138.0} tout={148.9} x={120} y={290}>
            <StripCard id="conv" t={t} t0={CONVERT_T0} name="convert" w={1100} h={300} label="Lead II · 25 mm/s" markers={[{kind: 'tick', t: ADENO_TICK, text: 'adenosine', color: T.amber, anchor: 'start', showAt: 143.08}]} />
          </At>
          <At t={t} tin={138.1} tout={148.9} x={1280} y={290} rise={0}>
            <Col gap={14}>
              <Slot t={t} tin={138.22}><div style={{...S.eyebrow, color: T.tealInk}}>Stable</div></Slot>
              <Slot t={t} tin={139.62}><Chip>1 · Vagal maneuver <Sub>Valsalva, lying flat</Sub></Chip></Slot>
              <Slot t={t} tin={142.74}><Chip>2 · Adenosine <Sub>rapid IV push</Sub></Chip></Slot>
              <Slot t={t} tin={145.9}><div style={{...S.eyebrow, color: T.coralInk, marginTop: 18}}>Unstable</div></Slot>
              <Slot t={t} tin={147.08}><Chip kind="coral">Synchronized cardioversion</Chip></Slot>
            </Col>
          </At>
          {/* f24 */}
          <Eyebrow t={t} tin={149.04} tout={155.5} color={T.tealInk} text="Sinus tachycardia" />
          <H2 t={t} tin={149.04} tout={155.5}>No loop to break</H2>
          <At t={t} tin={151.34} tout={155.5} x={1180} y={500} w={620}><div style={S.lead}>Slowing the rate doesn&apos;t fix the reason it&apos;s fast.</div></At>
          <At t={t} tin={154.22} tout={155.5} x={1180} y={400} w={640}><div style={{...S.h2, color: T.tealInk}}>Treat the cause</div></At>

          {/* ================= 7. Close ================= */}
          <At t={t} tin={155.66} tout={1e9} x={260} y={390}>
            <StripCard id="close" t={t} t0={155.7} name="open170" w={1400} h={300} label="Lead II · 25 mm/s" rate={170} />
          </At>
          <H2 t={t} tin={161.4} tout={1e9} x={260} y={232} w={1400} color={T.tealInk}>Answering?</H2>
          <H2 t={t} tin={162.66} tout={1e9} x={260} y={736} w={1400} color={T.coralInk} align="right">Looping?</H2>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
