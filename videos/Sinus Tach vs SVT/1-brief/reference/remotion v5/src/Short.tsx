import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Audio, continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {T, LEAD} from './theme';
import {HeartLayer, stageTransform} from './Heart';
import {StripCard, Marker} from './Strip';
import {LoopCard, lapFlash} from './Loops';
import {Intro, INTRO, INTRO_STOP, INTRO_HOLD, INTRO_REC_END, PREPRINT} from './Intro';
import {At, Chip, Sub, S, FontFaces, appear, clamp, lerp} from './ui';
import {beatState, lastCross, avnrtPhase, avnrtPhase2, ADENO_TICK, CONVERT_T0, Col, Slot} from './Main';
import WORDS from './data/words.json';
import WORDS4 from './data/words-short4.json';

// Vertical (1080x1920) cuts of the SVT video. Each short is a list of VO-time segments played back to back;
// every element below is timed in VO seconds exactly like the main video, so motion stays word-synced.
export type Seg = {a: number; b: number};
export const SHORTS: Record<string, {intro: boolean; segs: Seg[]; tail: number}> = {
  answering: {intro: true, segs: [{a: -1.5, b: 8.6}, {a: 39.3, b: 47.85}, {a: 73.55, b: 85.6}, {a: 155.6, b: 163.5}], tail: 8.6},
  // segment 0 (VO -1.5..0) is the silent lead-in: the logo lands on an SVT strip before the narration starts
  adenosine: {intro: true, segs: [{a: -1.5, b: 60.6}], tail: 8.6},
};
export const shortFrames = (id: string, fps = 30) => { const s = SHORTS[id]; return Math.round(((s.intro ? INTRO : 0) + s.segs.reduce((n, g) => n + g.b - g.a, 0) + s.tail) * fps); };

// short time -> {seg index, VO time}
function voTime(id: string, st: number) {
  const s = SHORTS[id]; let o = s.intro ? INTRO : 0;
  if (st < o) return {i: -1, t: -99};
  for (let i = 0; i < s.segs.length; i++) { const g = s.segs[i], d = g.b - g.a; if (st < o + d || i === s.segs.length - 1) return {i, t: Math.min(g.a + (st - o), g.b + 12)}; o += d; }
  return {i: -1, t: -99};
}

// ---- captions: short phrases from the VO word timings, current word in coral
type W = {text: string; start: number; end: number; type?: string};
const WL = (WORDS as unknown as {words?: W[]}).words ?? (WORDS as unknown as W[]);
const phrasesOf = (WL: W[]): W[][] => {
  const out: W[][] = []; let cur: W[] = [];
  for (const w of WL.filter(x => (x.type ?? 'word') === 'word')) {
    cur.push(w);
    if (cur.length >= 4 || /[.,?!:]$/.test(w.text)) { out.push(cur); cur = []; }
  }
  if (cur.length) out.push(cur);
  return out;
};
const PHRASES = phrasesOf(WL);
const PH4 = phrasesOf((WORDS4 as unknown as {words: W[]}).words);
const Captions: React.FC<{t: number; seg: Seg; phrases?: W[][]}> = ({t, seg, phrases = PHRASES}) => {
  const p = phrases.find(ph => t >= ph[0].start - 0.05 && t <= ph[ph.length - 1].end + 0.25 && ph[0].start >= seg.a - 0.05 && ph[0].start < seg.b);
  if (!p) return null;
  return (
    <div style={{position: 'absolute', left: 60, right: 60, top: 1500, display: 'flex', justifyContent: 'center'}}>
      <div style={{background: T.card, borderRadius: 22, padding: '18px 30px', boxShadow: `inset 0 0 0 2px ${T.line}`, fontWeight: 700, fontSize: 50, lineHeight: 1.2, textAlign: 'center', maxWidth: 960}}>
        {p.map((w, i) => <span key={i} style={{color: t >= w.start && t < w.end + 0.06 ? T.coral : T.ink}}>{w.text.replace(/[,]$/, '')}{i < p.length - 1 ? ' ' : ''}</span>)}
      </div>
    </div>
  );
};

// ---- vertical type
const Eyebrow: React.FC<{t: number; tin: number; tout: number; color: string; text: string}> = ({t, tin, tout, color, text}) => (
  <At t={t} tin={tin} tout={tout} x={60} y={200} w={960}><div style={{...S.eyebrow, fontSize: 26, color}}>{text}</div></At>
);
const Head: React.FC<{t: number; tin: number; tout: number; y?: number; color?: string; align?: 'left' | 'center' | 'right'; children: React.ReactNode}> = ({t, tin, tout, y = 240, color = T.ink, align = 'left', children}) => (
  <At t={t} tin={tin} tout={tout} x={60} y={y} w={960}><div style={{...S.h2, fontSize: 68, color, textAlign: align}}>{children}</div></At>
);
// a 1920x1080 "landscape stage" box mapped into the vertical frame, so landscape-positioned pieces (the cold-open
// strip and the logo intro that lands on it) line up exactly: landscape (260,390) -> vertical (x,y) at scale k
const Stage: React.FC<{x: number; y: number; k: number; children: React.ReactNode}> = ({x, y, k, children}) => (
  <div style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, transformOrigin: '0 0', transform: `translate(${x - 260 * k}px, ${y - 390 * k}px) scale(${k})`}}>{children}</div>
);
const STRIP_X = 60, STRIP_Y = 760, STRIP_K = 0.96, STRIP_W = 1000;
const LOGO_S = 5.0;   // smaller mark in the vertical frame
// the strip keeps printing from the moment the morph lands, so the card's paper starts that much further along
const OPEN_T0 = -1.5 - PREPRINT - (INTRO - INTRO_STOP);
const START_X = 260 + (540 - STRIP_X) / STRIP_K; // logo starts centred in the vertical frame; strip is 960 px wide on screen, ~3.6 s of paper

const useReady = () => {
  const [ready, setReady] = useState(false);
  const [h] = useState(() => delayRender('fonts'));
  useEffect(() => { Promise.all([400, 500, 700].map(w => document.fonts.load(`${w} 30px "DM Sans"`))).then(() => { setReady(true); requestAnimationFrame(() => setTimeout(() => continueRender(h), 120)); }); }, [h]);
  return ready;
};

// the heart, centred in the vertical frame (stage layout chosen so the heart's middle sits at (540, 830))
const VHEART = {x: 540 - 0.92 * 959, y: 790 - 0.92 * 540, s: 0.92};

// outro beats, in seconds after the last VO word: recap card, then a rewind that hands the first beat back to the logo
const OUT = {rewind: 4.2, handoff: 5.1};
const easeIO = (x: number) => (x < 0.5 ? 4 * x ** 3 : 1 - (-2 * x + 2) ** 3 / 2);

const RecapCol: React.FC<{t: number; tin: number; color: string; ink: string; tint: string; title: string; sub: string; items: string[]}> = ({t, tin, color, ink, tint, title, sub, items}) => (
  <Slot t={t} tin={tin}>
    <div style={{width: 468, boxSizing: 'border-box', background: T.card, borderRadius: 28, padding: '30px 30px 34px', boxShadow: `inset 0 0 0 2px ${T.line}, inset 0 8px 0 ${color}`, display: 'flex', flexDirection: 'column', gap: 18}}>
      <div style={{...S.h2, fontSize: 46, color: ink}}>{title}</div>
      <div style={{fontWeight: 500, fontSize: 28, color: T.ink2, marginTop: -8}}>{sub}</div>
      {items.map((x, i) => (
        <div key={i} style={{display: 'flex', gap: 14, alignItems: 'flex-start', fontWeight: 500, fontSize: 31, lineHeight: 1.25}}>
          <span style={{flex: 'none', width: 14, height: 14, borderRadius: 7, background: tint, marginTop: 11}} />
          <span>{x}</span>
        </div>
      ))}
    </div>
  </Slot>
);
const Recap: React.FC<{t: number; tin: number; tout: number}> = ({t, tin, tout}) => (
  <At t={t} tin={tin} tout={tout} x={60} y={1180} rise={0}>
    <div style={{display: 'flex', gap: 24, alignItems: 'stretch'}}>
      <RecapCol t={t} tin={tin} color={T.teal} ink={T.tealInk} tint={T.teal} title="Answering" sub="Sinus tachycardia" items={['P wave before every QRS', 'Speeds up and slows down gradually', 'Treat the cause']} />
      <RecapCol t={t} tin={tin + 0.6} color={T.coral} ink={T.coralInk} tint={T.coral} title="Looping" sub="SVT (re-entry)" items={['P waves hidden or after the QRS', 'Starts and stops abruptly', 'Break the loop at the AV node']} />
    </div>
  </At>
);
// end card for short 1: the logo is back where the short began, so the loop restarts seamlessly
const LogoCTA: React.FC<{t: number; tin: number}> = ({t, tin}) => (
  <At t={t} tin={tin} tout={1e9} x={60} y={1200} w={960}>
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 22, textAlign: 'center'}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
        <svg width={76} height={53} viewBox="0 0 132 92"><rect width={132} height={92} rx={26} fill={T.coral} /><path d="M54 28 L84 46 L54 64 Z" fill={T.card} /></svg>
        <div style={{...S.eyebrow, fontSize: 30, color: T.coralInk}}>Full video on YouTube</div>
      </div>
      <div style={{...S.h2, fontSize: 60}}>SVT vs Sinus Tachycardia</div>
    </div>
  </At>
);

// ===================================================================== Short 1: answering or looping?
const Answering: React.FC<{t: number; i: number; st: number}> = ({t, i, st}) => {
  const seg = SHORTS.answering.segs[i];
  const phA = t >= 77.2 ? avnrtPhase(t) : null;
  const crossA = phA === null ? -1 : lastCross(avnrtPhase, 0.5, 77.2, t);
  const cardAHeart = {...(crossA > 0 ? lapFlash(t, crossA) : {atr: 0, vent: 0, lit: 0}), avGlow: t >= 76.5 ? 0.8 : 0};
  return (
    <>
      {i === 0 && (<>
        <Stage x={STRIP_X} y={STRIP_Y} k={STRIP_K}>
          <At t={t} tin={-1.5} tout={1e9} x={260} y={390} rise={0}>
            <StripCard id="open" t={t} t0={OPEN_T0} name="open170" w={STRIP_W} h={300} label="Lead II · 25 mm/s" rate={170} />
          </At>
        </Stage>
        <Head t={t} tin={5.56} tout={1e9} y={630} color={T.tealInk}>Answering a call,</Head>
        <Head t={t} tin={7.52} tout={1e9} y={1080} color={T.coralInk} align="right">or stuck in a loop?</Head>
      </>)}
      {i === 1 && (<>
        <Eyebrow t={t} tin={seg.a} tout={1e9} color={T.tealInk} text="Sinus tachycardia" />
        <Head t={t} tin={seg.a} tout={1e9}>The heart <span style={{color: T.tealInk}}>answering</span></Head>
        <div style={{position: 'absolute', inset: 0, opacity: appear(t, seg.a, 1e9, 0).o}}>
          <HeartLayer s={beatState(t)} transform={stageTransform(VHEART)} />
        </div>
        <At t={t} tin={41.06} tout={1e9} x={60} y={1290} rise={0}>
          <Col gap={14}><Slot t={t} tin={41.06}><Chip size={34}>same route, just faster</Chip></Slot><Slot t={t} tin={44.58}><Chip kind="teal" size={34}>SA node firing &gt; 100 /min</Chip></Slot></Col>
        </At>
      </>)}
      {i === 2 && (<>
        <Eyebrow t={t} tin={seg.a} tout={1e9} color={T.coralInk} text="SVT" />
        <Head t={t} tin={seg.a} tout={1e9}>The heart in a <span style={{color: T.coralInk}}>loop</span></Head>
        <At t={t} tin={seg.a + 0.1} tout={1e9} x={60} y={380} rise={0}>
          <LoopCard uid="vA" kind="avnrt" w={960} h={860} draw={clamp((t - 76.06) / 0.8)} phase={phA} heart={cardAHeart} />
        </At>
        <At t={t} tin={76.06} tout={80.4} x={60} y={1290} rise={0}><Col gap={14}><Chip kind="coral" size={34}>Re-entry</Chip></Col></At>
        <At t={t} tin={81.02} tout={1e9} x={60} y={1290} rise={0}>
          <Col gap={14}><Slot t={t} tin={81.94}><Chip kind="coral" size={34}>AVNRT</Chip></Slot><Slot t={t} tin={84.02}><Chip size={34}>circuit inside the AV node</Chip></Slot></Col>
        </At>
      </>)}
      {i === 3 && (() => {
        // outro, timed from the end of the VO (u): recap -> the strip rewinds -> its first beat flies back into the logo
        const u = t - seg.b;
        const sLand = PREPRINT + INTRO - INTRO_STOP;                 // strip time the card had when it took over from the intro
        const sNow = t - 155.7;
        const rw = easeIO(clamp((u - OUT.rewind) / (OUT.handoff - OUT.rewind)));
        const sCard = u < OUT.rewind ? sNow : lerp(OUT.rewind + seg.b - 155.7, sLand, rw);
        const cardO = 1 - clamp((u - (OUT.handoff - 0.2)) / 0.2);
        // reversed intro clock: fast through the un-printing, then the real flight backwards
        const r = u - OUT.handoff, r1 = (INTRO - INTRO_REC_END) / 1.6;
        const ti = r < 0 ? INTRO + (sCard - sLand) : r < r1 ? INTRO - 1.6 * r : Math.max(INTRO_HOLD, INTRO_REC_END - (r - r1));
        const landed = r - r1 - (INTRO_REC_END - INTRO_HOLD);
        return (<>
          {cardO > 0 && <div style={{position: 'absolute', inset: 0, opacity: cardO}}><Stage x={STRIP_X} y={STRIP_Y} k={STRIP_K}>
            <At t={t} tin={seg.a} tout={1e9} x={260} y={390} rise={0}>
              <StripCard id="close" t={155.7 + sCard} t0={155.7} name="open170" w={STRIP_W} h={300} label="Lead II · 25 mm/s" rate={170} />
            </At>
          </Stage></div>}
          {u > OUT.handoff - 0.2 && <Stage x={STRIP_X} y={STRIP_Y} k={STRIP_K}><Intro startX={START_X} logoScale={LOGO_S} printFrom={INTRO_STOP} time={ti} settle={landed >= 0 ? landed : undefined} /></Stage>}
          <At t={t} tin={156.6} tout={160.7} x={60} y={600} rise={0}>
            <div style={{display: 'flex', gap: 16}}>
              <Slot t={t} tin={156.7}><Chip kind="amber" size={34}>Fast</Chip></Slot>
              <Slot t={t} tin={157.4}><Chip kind="amber" size={34}>Narrow QRS</Chip></Slot>
              <Slot t={t} tin={158.06}><Chip kind="amber" size={34}>Regular</Chip></Slot>
            </div>
          </At>
          <Head t={t} tin={161.4} tout={seg.b + OUT.rewind} y={630} color={T.tealInk}>Answering?</Head>
          <Head t={t} tin={162.66} tout={seg.b + OUT.rewind} y={1080} color={T.coralInk} align="right">Looping?</Head>
          <Recap t={t} tin={seg.b + 0.15} tout={seg.b + OUT.rewind} />
          <LogoCTA t={u} tin={landed >= -9 ? OUT.handoff + r1 + (INTRO_REC_END - INTRO_HOLD) + 0.15 : 1e9} />
        </>);
      })()}
      <Captions t={t} seg={seg} />
      {/* logo intro lands on the cold-open strip */}
      {st < INTRO + 0.5 && <Stage x={STRIP_X} y={STRIP_Y} k={STRIP_K}><Intro startX={START_X} logoScale={LOGO_S} printFrom={INTRO_STOP} /></Stage>}
    </>
  );
};

// ===================================================================== Short 4: how adenosine stops SVT
// Short 4 v2 runs on its own narration (take B of the short-4 script); t here is seconds into that take
const C2_T0 = 31.4;                     // convert2 strip: SVT until "brief pause" (45.8), then sinus at "normal sinus rhythm"
const C2_TICK = 39.02 - C2_T0;          // adenosine marker printed as the word is spoken
const S4_END = 60.6;
const Adenosine: React.FC<{t: number; i: number; st: number}> = ({t, st}) => {
  const seg = SHORTS.adenosine.segs[0];
  // scene B: full-heart loop, driven by the main video's AVNRT phase (its "re-entry" word sits at 76.06)
  const tB = t + 70.14;
  const phA = t >= 4.1 && t < 13.7 && tB >= 77.2 ? avnrtPhase(tB) : null;
  const crossA = phA === null ? -1 : lastCross(avnrtPhase, 0.5, 77.2, tB);
  const heartA = {...(crossA > 0 ? lapFlash(tB, crossA) : {atr: 0, vent: 0, lit: 0}), avGlow: tB >= 76.5 ? 0.8 : 0};
  // scenes C-D: zoom on the AV node, the loop keeps lapping until the block lands on "blocked"
  const tC = t + 113.5, blocked = t >= 28.6;
  const ph6 = avnrtPhase2(tC), cross6 = lastCross(avnrtPhase2, 0.5, 127.5, tC);
  const heartC = !blocked && cross6 > 0 ? {...lapFlash(tC, cross6), avGlow: 0.8} : {atr: 0, vent: 0, lit: 0};
  // outro (same recipe as short 1)
  const u = t - S4_END;
  const sLand = PREPRINT + INTRO - INTRO_STOP;
  const rw = easeIO(clamp((u - OUT.rewind) / (OUT.handoff - OUT.rewind)));
  const sCard = u < OUT.rewind ? t - C2_T0 : lerp(S4_END + OUT.rewind - C2_T0, sLand, rw);
  const cardO = 1 - clamp((u - (OUT.handoff - 0.2)) / 0.2);
  const gx = lerp(60, STRIP_X, rw), gy = lerp(400, STRIP_Y, rw), gk = lerp(1.3, STRIP_K, rw), gw = lerp(738, STRIP_W, rw);
  const r = u - OUT.handoff, r1 = (INTRO - INTRO_REC_END) / 1.6;
  const ti = r < 0 ? INTRO + (sCard - sLand) : r < r1 ? INTRO - 1.6 * r : Math.max(INTRO_HOLD, INTRO_REC_END - (r - r1));
  const landed = r - r1 - (INTRO_REC_END - INTRO_HOLD);
  return (
    <>
      <Eyebrow t={t} tin={-1.5} tout={S4_END + OUT.rewind} color={T.coralInk} text="Breaking the loop" />
      <Head t={t} tin={-1.5} tout={S4_END + OUT.rewind}>How <span style={{color: T.coralInk}}>adenosine</span> stops SVT</Head>

      {/* A: the logo lands on the SVT strip, which keeps printing (with monitor beeps) */}
      {t < 4.4 && <Stage x={STRIP_X} y={STRIP_Y} k={STRIP_K}>
        <At t={t} tin={-1.5} tout={4.1} x={260} y={390} rise={0}>
          <StripCard id="svt" t={t} t0={OPEN_T0} name="avnrt180" w={STRIP_W} h={300} label="Lead II · 25 mm/s" rate={180} />
        </At>
      </Stage>}
      <At t={t} tin={0.66} tout={4.1} x={60} y={1100} rise={0}><Col gap={14}><Chip kind="coral" size={34}>SVT · fast, narrow, regular</Chip></Col></At>

      {/* B: re-entry, a signal caught in a loop; every lap fires the ventricles */}
      <At t={t} tin={4.1} tout={13.75} x={60} y={400} rise={0}>
        <LoopCard uid="a4b" kind="avnrt" w={960} h={820} draw={clamp((tB - 76.06) / 0.8)} phase={phA} heart={heartA} />
      </At>
      <At t={t} tin={5.92} tout={13.75} x={60} y={1260} rise={0}>
        <Col gap={14}><Chip kind="coral" size={34}>Re-entry · one signal, going around</Chip><Slot t={t} tin={11.68}><Chip size={34}>every lap fires the ventricles</Chip></Slot></Col>
      </At>

      {/* C-D: zoom into the AV node; the circuit runs through it, so slowing it breaks the loop */}
      <At t={t} tin={13.75} tout={33.0} x={60} y={400} rise={0}>
        <LoopCard uid="a4c" kind="avnrt" w={960} h={820} view={2500} center={{x: 3650, y: 3950}} draw={1} phase={blocked ? null : ph6 + 0.5} block={blocked} heart={heartC} />
      </At>
      <At t={t} tin={15.4} tout={24.0} x={60} y={1260} rise={0}>
        <Col gap={14}><Chip kind="coral" size={34}>AVNRT</Chip><Slot t={t} tin={17.9}><Chip size={34}>two pathways inside the AV node</Chip></Slot></Col>
      </At>
      <At t={t} tin={24.42} tout={33.0} x={60} y={1260} rise={0}>
        <Col gap={14}>
          <Chip kind="ink" size={34}>Slow the AV node for a moment</Chip>
          <Slot t={t} tin={29.9}><Chip kind="coral" size={34}>→ the loop breaks</Chip></Slot>
          <Slot t={t} tin={31.08}><Chip kind="teal" size={34}>→ the sinus node takes over</Chip></Slot>
        </Col>
      </At>

      {/* E: treatment on a monitor strip: SVT, adenosine, a brief pause, then sinus rhythm */}
      {t >= 32.9 && cardO > 0 && <div style={{position: 'absolute', inset: 0, opacity: cardO}}><Stage x={gx} y={gy} k={gk}>
        <At t={t} tin={33.0} tout={1e9} x={260} y={390} rise={0}>
          <StripCard id="conv2" t={C2_T0 + sCard} t0={C2_T0} name="convert2" w={gw} h={300} label="Lead II · 25 mm/s" markers={[{kind: 'tick', t: C2_TICK, text: 'adenosine', color: T.amber, anchor: 'start', showAt: 39.02}] as Marker[]} />
        </At>
      </Stage></div>}
      {u > OUT.handoff - 0.2 && <Stage x={STRIP_X} y={STRIP_Y} k={STRIP_K}><Intro startX={START_X} stripName="convert2" logoScale={LOGO_S} printFrom={INTRO_STOP} time={ti} settle={landed >= 0 ? landed : undefined} /></Stage>}
      <At t={t} tin={33.1} tout={53.5} x={60} y={870} rise={0}>
        <Col gap={18}>
          <Slot t={t} tin={33.36}><div style={{...S.eyebrow, fontSize: 28, color: T.tealInk}}>Stable</div></Slot>
          <Slot t={t} tin={34.9}><Chip size={34}>1 · Vagal maneuver <Sub>modified Valsalva</Sub></Chip></Slot>
          <Slot t={t} tin={39.02}><Chip size={34}>2 · Adenosine <Sub>rapid IV push + flush</Sub></Chip></Slot>
          <Slot t={t} tin={45.42}><Chip kind="amber" size={34}>brief pause, then sinus rhythm</Chip></Slot>
          <Slot t={t} tin={49.48}><div style={{...S.eyebrow, fontSize: 28, color: T.coralInk, marginTop: 22}}>Unstable</div></Slot>
          <Slot t={t} tin={51.64}><Chip kind="coral" size={34}>Synchronized cardioversion</Chip></Slot>
        </Col>
      </At>

      {/* F: sinus tach has no loop to break */}
      <At t={t} tin={53.82} tout={S4_END + 0.1} x={60} y={870} rise={0}>
        <Col gap={18}>
          <div style={{...S.eyebrow, fontSize: 28, color: T.tealInk}}>Sinus tachycardia</div>
          <Slot t={t} tin={55.94}><div style={{...S.h2, fontSize: 60, color: T.tealInk}}>No loop to break</div></Slot>
          <Slot t={t} tin={58.86}><Chip kind="teal" size={34}>Find and treat the cause</Chip></Slot>
        </Col>
      </At>

      {/* recap, then the strip rewinds and its first beat flies back into the logo */}
      <At t={t} tin={S4_END + 0.15} tout={S4_END + OUT.rewind} x={60} y={870} rise={0}>
        <div style={{display: 'flex', gap: 24, alignItems: 'stretch'}}>
          <RecapCol t={t} tin={S4_END + 0.15} color={T.coral} ink={T.coralInk} tint={T.coral} title="Looping" sub="SVT (re-entry)" items={['The AV node is part of the circuit', 'Vagal maneuver or adenosine blocks it', 'Loop breaks, sinus rhythm returns']} />
          <RecapCol t={t} tin={S4_END + 0.75} color={T.teal} ink={T.tealInk} tint={T.teal} title="Answering" sub="Sinus tachycardia" items={['No loop to break', 'The fast rate is a response', 'Find and treat the cause']} />
        </div>
      </At>
      <LogoCTA t={u} tin={OUT.handoff + r1 + (INTRO_REC_END - INTRO_HOLD) + 0.15} />

      <Captions t={t} seg={seg} phrases={PH4} />
      {st < INTRO + 0.5 && <Stage x={STRIP_X} y={STRIP_Y} k={STRIP_K}><Intro startX={START_X} stripName="avnrt180" logoScale={LOGO_S} printFrom={INTRO_STOP} /></Stage>}
    </>
  );
};

// ---- end card: send viewers to the full video
const CTA: React.FC<{st: number; end: number}> = ({st, end}) => {
  const a = appear(st, end, 1e9, 30);
  if (!a.live) return null;
  return (
    <div style={{position: 'absolute', inset: 0, background: `rgba(246,241,232,${0.9 * a.o})`, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <div style={{opacity: a.o, transform: `translateY(${a.dy}px)`, background: T.card, borderRadius: 36, padding: '52px 60px', width: 860, boxShadow: `0 18px 50px rgba(31,29,27,0.14), inset 0 0 0 2px ${T.line}`, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 26, textAlign: 'center'}}>
        <svg width={132} height={92} viewBox="0 0 132 92"><rect width={132} height={92} rx={26} fill={T.coral} /><path d="M54 28 L84 46 L54 64 Z" fill={T.card} /></svg>
        <div style={{...S.eyebrow, fontSize: 28, color: T.coralInk}}>Full video on YouTube</div>
        <div style={{...S.h2, fontSize: 64}}>SVT vs Sinus Tachycardia</div>
        <div style={{...S.lead, fontSize: 38}}>Is the heart answering or looping?</div>
      </div>
    </div>
  );
};

export const Short: React.FC<{id: 'answering' | 'adenosine'}> = ({id}) => {
  const {fps} = useVideoConfig();
  const st = useCurrentFrame() / fps;
  const ready = useReady();
  const {i, t} = voTime(id, st);
  void LEAD; void lerp;
  return (
    <AbsoluteFill style={{background: T.bg, fontFamily: T.font, color: T.ink}}>
      <FontFaces />
      {fps === 30 && <Audio src={staticFile(id === 'answering' ? 'short-answering-beeps.mp3' : `short-${id}.mp3`)} />}
      {ready && (id === 'answering'
        ? (i >= 0 ? <Answering t={t} i={i} st={st} /> : <Stage x={STRIP_X} y={STRIP_Y} k={STRIP_K}><Intro startX={START_X} logoScale={LOGO_S} printFrom={INTRO_STOP} /></Stage>)
        : (i >= 0 ? <Adenosine t={t} i={i} st={st} /> : <Stage x={STRIP_X} y={STRIP_Y} k={STRIP_K}><Intro startX={START_X} stripName="avnrt180" logoScale={LOGO_S} printFrom={INTRO_STOP} /></Stage>))}
      {ready && false && <CTA st={st} end={shortFrames(id) / 30 - SHORTS[id].tail + 0.15} />}
    </AbsoluteFill>
  );
};
