import React from 'react';
import {AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {T} from './theme';
import {HeartLayer, HeartState, Layout, stageTransform, toStage, SA, AV} from './Heart';
import {StripCard, Marker} from './Strip';
import {Schematic} from './Loops';
import {strip} from './ecg';
import {Intro, INTRO, INTRO_STOP, INTRO_HOLD, INTRO_REC_END, PREPRINT} from './Intro';
import {At, Chip, S, FontFaces, appear, clamp, lerp, ramp, easeIO, easeOut} from './ui';
import {beatState, narrativeState, lastCross, Col, Slot, ONSET_TICK, OFFSET_TICK, ONSET_T0, F17_T0} from './Main';
import {Captions, Eyebrow, Head, Stage, STRIP_X, STRIP_Y, STRIP_K, STRIP_W, LOGO_S, START_X, OUT, RecapCol, LogoCTA, useReady} from './Short';

// Shorts 2, 3 and 5 (Nov 22, 2026): vertical cuts of v9, one continuous stretch of the locked VO each.
// Timeline: logo intro lands on a strip (INTRO) -> the strip prints under the hook title (HOOK) -> VO a..b -> outro (TAIL).
// Everything inside the VO stretch is timed in VO seconds, exactly like the main video, so motion stays word-synced.
export type ShortId = 'narrow' | 'reason' | 'tells';
const HOOK = 1.5, TAIL = 8.6;
export const SHORTS9: Record<ShortId, {a: number; b: number; strip: string; eyebrow: string; eyebrowColor: string; title: React.ReactNode}> = {
  narrow: {a: 8.6, b: 36.85, strip: 'sinus75', eyebrow: 'ECG basics', eyebrowColor: T.amberInk, title: <>Why is the QRS <span style={{color: T.amberInk}}>narrow?</span></>},
  reason: {a: 39.3, b: 73.35, strip: 'sinus130', eyebrow: 'Sinus tachycardia', eyebrowColor: T.tealInk, title: <>Fast heart? <span style={{color: T.tealInk}}>Find the reason.</span></>},
  tells: {a: 95.15, b: 126.95, strip: 'avnrt180', eyebrow: 'Fast, narrow, regular', eyebrowColor: T.coralInk, title: <>Sinus tach or SVT? <span style={{color: T.coralInk}}>3 tells</span></>},
};
export const short9Frames = (id: ShortId, fps = 30) => { const s = SHORTS9[id]; return Math.round((INTRO + HOOK + (s.b - s.a) + TAIL) * fps); };
const LEAD_T0 = -HOOK - PREPRINT - (INTRO - INTRO_STOP);   // lead-in strip: keeps printing from where the intro's morph landed

// heart placement in the vertical frame: centre (cx, cy), scale s (1 = the landscape full-frame heart, ~960 px tall)
const VL = (cx: number, cy: number, s: number): Layout => ({x: cx - s * 959, y: cy - s * 540, s});
const mixL = (a: Layout, b: Layout, k: number): Layout => ({x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), s: lerp(a.s, b.s, k)});

// leader-line label in vertical px
const VLabel: React.FC<{t: number; tin: number; tout: number; from: {x: number; y: number}; to: {x: number; y: number}; text: string; anchor: 'start' | 'end'}> = ({t, tin, tout, from, to, text, anchor}) => {
  const a = appear(t, tin, tout, 0); if (!a.live) return null;
  const k = easeOut(clamp((t - tin) / 0.45));
  const ex = lerp(from.x, to.x, k), ey = lerp(from.y, to.y, k);
  return (
    <g opacity={a.o}>
      <path d={`M${from.x} ${from.y}L${ex} ${ey}`} stroke={T.ink2} strokeWidth={2.5} fill="none" />
      <circle cx={from.x} cy={from.y} r={5} fill={T.ink2} />
      <text x={to.x + (anchor === 'end' ? -12 : 12)} y={to.y + 11} fontFamily={T.font} fontSize={34} fontWeight={500} fill={T.ink} textAnchor={anchor} opacity={clamp((t - tin - 0.2) / 0.3)}>{text}</text>
    </g>
  );
};
const Sub3: React.FC<{t: number; tin: number; tout: number; y?: number; children: React.ReactNode}> = ({t, tin, tout, y = 430, children}) => (
  <At t={t} tin={tin} tout={tout} x={60} y={y} w={960}><div style={{...S.h3, fontSize: 44}}>{children}</div></At>
);
const Lead: React.FC<{t: number; tin: number; tout: number; x?: number; y: number; w?: number; size?: number; children: React.ReactNode}> = ({t, tin, tout, x = 60, y, w = 960, size = 34, children}) => (
  <At t={t} tin={tin} tout={tout} x={x} y={y} w={w}><div style={{...S.lead, fontSize: size}}>{children}</div></At>
);
const RecapWide: React.FC<{t: number; tin: number; tout: number; color: string; ink: string; title: string; sub: string; items: string[]}> = ({t, tin, tout, color, ink, title, sub, items}) => (
  <At t={t} tin={tin} tout={tout} x={60} y={1180} rise={0}>
    <Slot t={t} tin={tin}>
      <div style={{width: 960, boxSizing: 'border-box', background: T.card, borderRadius: 28, padding: '30px 36px 34px', boxShadow: `inset 0 0 0 2px ${T.line}, inset 0 8px 0 ${color}`, display: 'flex', flexDirection: 'column', gap: 16}}>
        <div style={{display: 'flex', alignItems: 'baseline', gap: 18}}><div style={{...S.h2, fontSize: 46, color: ink}}>{title}</div><div style={{fontWeight: 500, fontSize: 28, color: T.ink2}}>{sub}</div></div>
        {items.map((x, i) => (
          <div key={i} style={{display: 'flex', gap: 14, alignItems: 'flex-start', fontWeight: 500, fontSize: 32, lineHeight: 1.25}}>
            <span style={{flex: 'none', width: 14, height: 14, borderRadius: 7, background: color, marginTop: 12}} />
            <span>{x}</span>
          </div>
        ))}
      </div>
    </Slot>
  </At>
);

// ===================================================================== Short 2: why is the QRS narrow? (VO 8.6 - 36.85)
const N_BIG = VL(540, 820, 0.72), N_SMALL = VL(540, 690, 0.5);
const Narrow: React.FC<{t: number}> = ({t}) => {
  const b = SHORTS9.narrow.b;
  let hs: HeartState = {atr: 0, vent: 0, lit: 0};
  if (t < 26.98) hs = narrativeState(t);
  else if (t < 27.25) { const n = narrativeState(26.9); hs = {...n, lit: 1 - clamp((t - 26.98) / 0.2), avGlow: 0, saGlow: 0}; }
  else hs = beatState(t);
  const L = mixL(N_BIG, N_SMALL, ramp(t, 26.98, 27.8));
  const hin = appear(t, 9.85, b, 0);
  const sc = lerp(0.96, 1, easeOut(clamp((t - 9.85) / 0.7)));
  const sa = toStage(SA.x - 260, SA.y - 60, N_BIG), av = toStage(AV.x - 300, AV.y + 120, N_BIG), hp = toStage(6300, 5500, N_BIG);
  // "at or above the AV node": a dashed line through the AV node, bracket up to the top of the heart
  const lineY = toStage(0, AV.y, N_SMALL).y, top = toStage(0, 900, N_SMALL).y;
  const x1 = toStage(300, 0, N_SMALL).x, x2full = toStage(7000, 0, N_SMALL).x, bx = x2full + 20;
  const la = appear(t, 35.84, b, 0);
  return (
    <>
      {hin.live && (
        <div style={{position: 'absolute', inset: 0, opacity: hin.o, transform: `scale(${sc})`, transformOrigin: '540px 820px'}}>
          <HeartLayer s={hs} transform={stageTransform(L)} />
          <svg width={1080} height={1920} viewBox="0 0 1080 1920" style={{position: 'absolute', left: 0, top: 0}}>
            {t < 27.4 && <g>
              <VLabel t={t} tin={11.94} tout={26.98} from={sa} to={{x: 230, y: sa.y - 40}} text="SA node" anchor="end" />
              <VLabel t={t} tin={17.38} tout={26.98} from={av} to={{x: 230, y: av.y + 60}} text="AV node" anchor="end" />
              <VLabel t={t} tin={24.46} tout={26.98} from={{x: hp.x + 8, y: hp.y}} to={{x: 640, y: 1235}} text="His-Purkinje" anchor="start" />
            </g>}
            {la.live && <g opacity={la.o}>
              <line x1={x1} y1={lineY} x2={lerp(x1, x2full, easeOut(clamp((t - 35.84) / 0.6)))} y2={lineY} stroke={T.ink} strokeWidth={3} strokeDasharray="14 12" />
              <g opacity={clamp((t - 36.2) / 0.4)}><path d={`M${bx} ${top}V${lineY}`} stroke={T.ink} strokeWidth={3} fill="none" /><path d={`M${bx - 12} ${top}h12M${bx - 12} ${lineY}h12`} stroke={T.ink} strokeWidth={3} /></g>
            </g>}
          </svg>
        </div>
      )}
      <At t={t} tin={18.44} tout={23.6} x={60} y={av.y + 110}><Chip kind="amber" size={34}>holds ≈ 0.1 s</Chip></At>
      {/* the beat on a strip: QRS < 120 ms */}
      <At t={t} tin={27.0} tout={30.0} x={60} y={980}>
        <StripCard id="beat" t={t} t0={27.0} name="sinus75" w={960} h={340} baseline={0.55} label="Lead II" markers={[{kind: 'bracket', t: 1.04, t2: 1.125, text: 'QRS < 120 ms', showAt: 28.34}]} />
      </At>
      <At t={t} tin={29.14} tout={30.0} x={60} y={1345}><Chip kind="amber" size={34}>Fast lane → narrow QRS</Chip></At>
      <At t={t} tin={30.22} tout={b} x={60} y={990} rise={0}>
        <Col gap={16}><Slot t={t} tin={30.22}><Chip kind="ink" size={34}>Narrow QRS</Chip></Slot><Slot t={t} tin={32.22}><Chip size={34}>→ ventricles still use the fast lane</Chip></Slot><Slot t={t} tin={34.98}><Chip kind="coral" size={34}>→ origin at or above the AV node</Chip></Slot></Col>
      </At>
    </>
  );
};

// ===================================================================== Short 3: fast for a reason (VO 39.3 - 73.35)
const R_HEART = VL(540, 690, 0.5);
const Reason: React.FC<{t: number}> = ({t}) => {
  const sinus130 = strip('sinus130');
  const hin = appear(t, 39.4, 64.28, 0);
  const pMarks = (beats: {t: number}[], showAt: number): Marker[] => beats.map(x => ({kind: 'P', t: x.t - 0.1, showAt}));
  return (
    <>
      {hin.live && <div style={{position: 'absolute', inset: 0, opacity: hin.o}}><HeartLayer s={beatState(t)} transform={stageTransform(R_HEART)} /></div>}
      <At t={t} tin={41.06} tout={48.3} x={60} y={990} rise={0}>
        <Col gap={16}><Slot t={t} tin={41.06}><Chip size={34}>same route, just faster</Chip></Slot><Slot t={t} tin={44.58}><Chip kind="teal" size={34}>SA node firing &gt; 100 /min</Chip></Slot></Col>
      </At>
      <Lead t={t} tin={45.8} tout={48.3} y={1190}>because the body is asking for more output</Lead>
      <At t={t} tin={49.52} tout={64.1} x={60} y={975}><div style={{...S.eyebrow, fontSize: 26}}>Harmless</div></At>
      <At t={t} tin={50.4} tout={64.1} x={60} y={1020} rise={0}>
        <Col gap={12}>{([['Exercise', 50.56], ['Stress', 51.5], ['Pain', 52.22], ['Anxiety', 52.84]] as [string, number][]).map(([s, a]) => <Slot key={s} t={t} tin={a}><Chip kind="teal" size={34}>{s}</Chip></Slot>)}</Col>
      </At>
      <At t={t} tin={54.78} tout={64.1} x={560} y={975}><div style={{...S.eyebrow, fontSize: 26, color: T.coralInk}}>Serious</div></At>
      <At t={t} tin={55.9} tout={64.1} x={560} y={1020} rise={0}>
        <Col gap={12}>{([['Low oxygen', 56.04], ['Blood loss', 56.84], ['Dehydration', 57.66], ['Sepsis', 58.76]] as [string, number][]).map(([s, a]) => <Slot key={s} t={t} tin={a}><Chip kind="coral" size={34}>{s}</Chip></Slot>)}</Col>
      </At>
      <Lead t={t} tin={59.88} tout={64.1} y={1355} size={32}>A fast resting heart rate can be one of the earliest signs that something is wrong.</Lead>
      {/* a normal beat, only faster */}
      <Sub3 t={t} tin={64.4} tout={73.35}>A normal beat, only faster</Sub3>
      <At t={t} tin={64.4} tout={73.35} x={60} y={520}>
        <StripCard id="s130" t={t} t0={64.5} name="sinus130" w={960} h={340} label="Lead II · 25 mm/s" rate={130} markers={pMarks(sinus130.beats, 68.56)} />
      </At>
      <At t={t} tin={69.22} tout={73.35} x={60} y={900} rise={0}>
        <Col gap={16}><Slot t={t} tin={69.22}><Chip kind="teal" size={34}>Upright P in I, II and aVL</Chip></Slot><Slot t={t} tin={71.6}><Chip kind="teal" size={34}>One P before every QRS</Chip></Slot></Col>
      </At>
    </>
  );
};

// ===================================================================== Short 5: sinus tach or SVT, 3 tells (VO 95.15 - 126.95)
const Tells: React.FC<{t: number}> = ({t}) => {
  const b = SHORTS9.tells.b;
  const sinus130 = strip('sinus130'), avnrt180 = strip('avnrt180');
  const schPhase = (x: number) => (x - F17_T0 - 0.25) * 3 + 0.5;
  const cross = lastCross(x => schPhase(x) + 10, 0.5, F17_T0 - 3.5, t);
  const flash = cross > 0 ? 1 - clamp((t - cross) / 0.28) : 0;
  const pMarks = (beats: {t: number}[], showAt: number): Marker[] => beats.map(x => ({kind: 'P', t: x.t - 0.1, showAt}));
  const A = 60, B = 555, colW = 465;
  const Row: React.FC<{y: number; tin: number}> = ({y, tin}) => { const o = appear(t, tin, b, 0); const k = easeOut(clamp((t - tin) / 0.6)); return o.live ? <div style={{position: 'absolute', left: 60, top: y, width: 960 * k, height: 2, background: T.line, opacity: o.o}} /> : null; };
  return (
    <>
      {/* every lap fires the ventricles */}
      <Sub3 t={t} tin={95.44} tout={97.6}>Every lap fires the ventricles</Sub3>
      <At t={t} tin={95.44} tout={97.6} x={300} y={500}><Schematic w={480} h={420} phase={schPhase(t)} flash={flash} /></At>
      <At t={t} tin={95.44} tout={97.6} x={60} y={960}>
        <StripCard id="lap" t={t} t0={F17_T0} name="avnrt180" w={960} h={300} label="Lead II · 25 mm/s" rate={180} markers={avnrt180.beats.map(x => ({kind: 'lap', t: x.t + 0.03}))} />
      </At>
      <At t={t} tin={96.16} tout={97.6} x={60} y={1290}><Chip kind="coral" size={34}>one lap → one QRS</Chip></At>
      {/* a switch, not a dial: the whole episode on one strip (landscape strip, 6 s of paper like the main video, scaled to fit) */}
      <Sub3 t={t} tin={97.76} tout={107.6}>A switch, not a dial</Sub3>
      <At t={t} tin={97.76} tout={107.6} x={60} y={520}>
        <div style={{width: 960, height: 185}}><div style={{transform: `scale(${960 / 1680})`, transformOrigin: '0 0'}}>
          <StripCard id="onset" t={t} t0={ONSET_T0} name="onset" w={1680} h={320} label="Lead II · 25 mm/s" markers={[{kind: 'tick', t: ONSET_TICK, text: 'starts suddenly', showAt: 100.62}, {kind: 'tick', t: OFFSET_TICK, text: 'stops abruptly', anchor: 'end', dx: -12, showAt: 104.9}]} />
        </div></div>
      </At>
      <At t={t} tin={100.5} tout={107.6} x={60} y={740} rise={0}>
        <Col gap={16}><Slot t={t} tin={100.62}><Chip kind="coral" size={34}>Starts suddenly</Chip></Slot><Slot t={t} tin={103.58}><Chip kind="coral" size={34}>150 – 220 /min, regular</Chip></Slot><Slot t={t} tin={105.76}><Chip kind="coral" size={34}>Stops abruptly</Chip></Slot></Col>
      </At>
      {/* side by side: the three tells */}
      <At t={t} tin={107.9} tout={b} x={A} y={440}><div style={{...S.h3, fontSize: 40, color: T.tealInk}}>Sinus tach <span style={{fontWeight: 400, color: T.ink2, fontSize: 30}}>· answering</span></div></At>
      <At t={t} tin={108.1} tout={b} x={B} y={440}><div style={{...S.h3, fontSize: 40, color: T.coralInk}}>SVT <span style={{fontWeight: 400, color: T.ink2, fontSize: 30}}>· looping</span></div></At>
      <Row y={515} tin={109.6} />
      <At t={t} tin={109.6} tout={b} x={A} y={540}><div style={{...S.eyebrow, fontSize: 24}}>1 · Trigger</div></At>
      <At t={t} tin={109.84} tout={b} x={A} y={585}><Chip kind="teal" size={32}>A reason you can find</Chip></At>
      <At t={t} tin={113.76} tout={b} x={B} y={585}><Chip kind="coral" size={32}>Often none</Chip></At>
      <Lead t={t} tin={116.08} tout={b} x={B} y={665} w={colW} size={27}>sometimes caffeine, stimulants, stress</Lead>
      <Row y={760} tin={112.0} />
      <At t={t} tin={112.0} tout={b} x={A} y={785}><div style={{...S.eyebrow, fontSize: 24}}>2 · Start and stop</div></At>
      <At t={t} tin={112.24} tout={b} x={A} y={830}><Chip kind="teal" size={32}>Follows the reason</Chip></At>
      <At t={t} tin={119.36} tout={b} x={B} y={830}><Chip kind="coral" size={32}>Switches on and off</Chip></At>
      <Row y={940} tin={120.9} />
      <At t={t} tin={120.9} tout={b} x={A} y={965}><div style={{...S.eyebrow, fontSize: 24}}>3 · P waves</div></At>
      <At t={t} tin={121.0} tout={b} x={A} y={1010}><StripCard id="cmpA" t={t} t0={121.0} name="sinus130" w={colW} h={190} markers={pMarks(sinus130.beats, 121.4)} /></At>
      <At t={t} tin={121.06} tout={b} x={B} y={1010}><StripCard id="cmpB" t={t} t0={121.0} name="avnrt180" w={colW} h={190} markers={avnrt180.beats.map(x => ({kind: 'noP', t: x.t + 0.03, showAt: 122.56}))} /></At>
      <At t={t} tin={121.6} tout={b} x={A} y={1220}><Chip kind="teal" size={28}>Upright P before every QRS</Chip></At>
      <At t={t} tin={124.92} tout={b} x={B} y={1220}><Chip kind="coral" size={28}>Hidden inside the QRS</Chip></At>
      <Lead t={t} tin={122.0} tout={b} x={B} y={1290} w={colW} size={27}>in AVNRT, the most common SVT</Lead>
    </>
  );
};

// ===================================================================== outro: recap, the strip rewinds, its first beat flies back into the logo
const Outro: React.FC<{id: ShortId; u: number}> = ({id, u}) => {
  const s = SHORTS9[id]; const S0 = 2.0;
  const sLand = PREPRINT + INTRO - INTRO_STOP;
  const rw = easeIO(clamp((u - OUT.rewind) / (OUT.handoff - OUT.rewind)));
  const sCard = u < OUT.rewind ? u + S0 : lerp(OUT.rewind + S0, sLand, rw);
  const cardO = 1 - clamp((u - (OUT.handoff - 0.2)) / 0.2);
  const r = u - OUT.handoff, r1 = (INTRO - INTRO_REC_END) / 1.6;
  const ti = r < 0 ? INTRO + (sCard - sLand) : r < r1 ? INTRO - 1.6 * r : Math.max(INTRO_HOLD, INTRO_REC_END - (r - r1));
  const landed = r - r1 - (INTRO_REC_END - INTRO_HOLD);
  return (<>
    {cardO > 0 && <div style={{position: 'absolute', inset: 0, opacity: cardO}}><Stage x={STRIP_X} y={STRIP_Y} k={STRIP_K}>
      <At t={u} tin={0.05} tout={1e9} x={260} y={390} rise={0}>
        <StripCard id="close" t={sCard} t0={0} name={s.strip} w={STRIP_W} h={300} label="Lead II · 25 mm/s" />
      </At>
    </Stage></div>}
    {u > OUT.handoff - 0.2 && <Stage x={STRIP_X} y={STRIP_Y} k={STRIP_K}><Intro startX={START_X} stripName={s.strip} logoScale={LOGO_S} printFrom={INTRO_STOP} time={ti} settle={landed >= 0 ? landed : undefined} /></Stage>}
    {id === 'narrow' && <RecapWide t={u} tin={0.15} tout={OUT.rewind} color={T.amber} ink={T.amberInk} title="Narrow QRS" sub="the fast lane is intact" items={['SA node → atria → AV node → His-Purkinje', 'The AV node holds the signal ≈ 0.1 s', 'QRS < 120 ms: ventricles use the fast lane', 'Origin at or above the AV node']} />}
    {id === 'reason' && <RecapWide t={u} tin={0.15} tout={OUT.rewind} color={T.teal} ink={T.tealInk} title="Sinus tachycardia" sub="the heart answering" items={['SA node firing > 100 /min, same route', 'Upright P before every QRS', 'Harmless or serious: find the reason']} />}
    {id === 'tells' && <At t={u} tin={0.15} tout={OUT.rewind} x={60} y={1180} rise={0}>
      <div style={{display: 'flex', gap: 24, alignItems: 'stretch'}}>
        <RecapCol t={u} tin={0.15} color={T.teal} ink={T.tealInk} tint={T.teal} title="Answering" sub="Sinus tachycardia" items={['A reason you can find', 'Follows the reason', 'Upright P before every QRS']} />
        <RecapCol t={u} tin={0.75} color={T.coral} ink={T.coralInk} tint={T.coral} title="Looping" sub="SVT (re-entry)" items={['Often no trigger', 'Switches on and off', 'AVNRT: P hidden in the QRS']} />
      </div>
    </At>}
    <LogoCTA t={u} tin={OUT.handoff + r1 + (INTRO_REC_END - INTRO_HOLD) + 0.15} />
  </>);
};

// cover: a still without captions, for the Short's cover image
export const ShortV9: React.FC<{id: ShortId; cover?: boolean}> = ({id, cover}) => {
  const {fps} = useVideoConfig();
  const st = useCurrentFrame() / fps;
  const ready = useReady();
  const s = SHORTS9[id];
  const tau = st - INTRO - HOOK;          // seconds from the first VO frame of the stretch
  const t = s.a + tau;                    // VO time
  const u = t - s.b;                      // seconds after the stretch
  const titleOut = INTRO + HOOK + (s.b - s.a) + OUT.rewind;
  return (
    <AbsoluteFill style={{background: T.bg, fontFamily: T.font, color: T.ink}}>
      <FontFaces />
      {fps === 30 && <Audio src={staticFile(`short9-${id}.mp3`)} />}
      {ready && (<>
        <Eyebrow t={st} tin={0.1} tout={titleOut} color={s.eyebrowColor} text={s.eyebrow} />
        <Head t={st} tin={0.1} tout={titleOut}>{s.title}</Head>
        {st >= INTRO && tau < 0.4 && <Stage x={STRIP_X} y={STRIP_Y} k={STRIP_K}>
          <At t={tau} tin={-HOOK} tout={0} x={260} y={390} rise={0}>
            <StripCard id="lead" t={tau} t0={LEAD_T0} name={s.strip} w={STRIP_W} h={300} label="Lead II · 25 mm/s" />
          </At>
        </Stage>}
        {tau >= 0 && u < 0.4 && (id === 'narrow' ? <Narrow t={t} /> : id === 'reason' ? <Reason t={t} /> : <Tells t={t} />)}
        {u >= 0 && <Outro id={id} u={u} />}
        {tau >= 0 && !cover && <Captions t={t} seg={{a: s.a, b: s.b}} />}
        {st < INTRO + 0.5 && <Stage x={STRIP_X} y={STRIP_Y} k={STRIP_K}><Intro startX={START_X} stripName={s.strip} logoScale={LOGO_S} printFrom={INTRO_STOP} /></Stage>}
      </>)}
    </AbsoluteFill>
  );
};
