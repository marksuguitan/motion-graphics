// Short.tsx: "Tall. Short." An Electrical Alternans short in Comma Clinical: anatomy art, on-screen text and
// sound effects, no voice-over. v2 (Mark, Nov 25, 2026: "i want anatomy art, not just text").
// Every on-screen line comes from the approved script (Gate 2, Oct 23, 2026): beats 1A, 1B, 2C, 3C, 3D, 3E, 6A, 6B.
// One metronome runs under the whole short: a beat every 0.5 s (120/min, regular and fast). Even beats are
// "tall", odd beats are "short". The picture and sfx.py both read src/data/timeline.json, so they stay in step.
// The rhythm strip comes from Kardiograph's engine and only ever scrolls (v3, Mark: "too jittery, use the kardiograph engine").
import React from 'react';
import {AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import TL from './data/timeline.json';
import {HEART_ART} from './data/heartArt';
import strip from './data/strip.json';
import {C, FONT} from './style/theme';
import {cut, ease, fadeSmall, overshoot, progress} from './style/comma';

const B = (k: number) => TL.t0 + k * TL.beat; // time of beat k
const K = TL.k;
const CX = 540; // scenes shrink into, and grow out of, this point
const CY = 900;
const EFFUSION = '#5E9BD6'; // the effusion blue from this video's approved key frames

// ---------------------------------------------------------------- pieces

/** A scene that shrinks into the centre point, accelerating, just before t1 (and can grow out of it at t0). */
const Scene: React.FC<{t: number; t0: number; t1: number; grow?: boolean; children: React.ReactNode}> = ({t, t0, t1, grow = true, children}) => {
  if (t < t0 || t >= t1) return null;
  const sIn = grow ? ease(t, t0, 0.6, 0, 1) : 1;
  const sOut = ease(t, t1 - 0.25, 0.25, 1, 0, 'accel');
  return (
    <AbsoluteFill style={{transform: `scale(${sIn * sOut})`, transformOrigin: `${CX}px ${CY}px`}}>{children}</AbsoluteFill>
  );
};

/** A word that cuts on at t0 and lands with one small overshoot. */
const Word: React.FC<{t: number; t0: number; size: number; color?: string; children: React.ReactNode}> = ({t, t0, size, color = C.ink, children}) => (
  <span style={{display: 'inline-block', visibility: cut(t, t0) ? 'visible' : 'hidden', fontFamily: FONT.head, fontWeight: 600, fontSize: size, lineHeight: 1, color, transform: `scale(${overshoot(t, t0, 0.3, 0.86, 1, 0.08, 0.15)})`, transformOrigin: '50% 80%'}}>
    {children}
  </span>
);

type RollLine = {at: number; kicker?: string; size?: number; text: React.ReactNode};
/** Lines that swap in one place: the old line rolls up and out, the new one rolls up into place, clipped to the box. */
const Roll: React.FC<{t: number; lines: RollLine[]; until: number; top: number; height: number}> = ({t, lines, until, top, height}) => (
  <div style={{position: 'absolute', left: 60, width: 960, top, height, overflow: 'hidden'}}>
    {lines.map((l, i) => {
      const last = i + 1 === lines.length;
      const next = last ? until : lines[i + 1].at;
      if (t < l.at || t >= next) return null;
      const yIn = ease(t, l.at, 0.3, 40 + height, 0);
      const yOut = ease(t, next - 0.25, 0.25, 0, -(40 + height), 'accel');
      return (
        <div key={i} style={{position: 'absolute', inset: 0, transform: `translateY(${yIn + yOut}px)`, textAlign: 'center'}}>
          {l.kicker ? <div style={{fontFamily: FONT.head, fontWeight: 700, fontSize: 30, letterSpacing: 4, color: C.ink2, marginBottom: 20}}>{l.kicker}</div> : null}
          <div style={{fontFamily: FONT.head, fontWeight: 600, fontSize: l.size ?? 68, lineHeight: 1.12, color: C.ink}}>{l.text}</div>
        </div>
      );
    })}
  </div>
);

const Line: React.FC<{t: number; at: number; top: number; size?: number; color?: string; weight?: number; head?: boolean; children: React.ReactNode}> = ({t, at, top, size = 52, color = C.ink2, weight = 500, head = false, children}) =>
  cut(t, at) ? (
    <div style={{position: 'absolute', left: 60, width: 960, top, textAlign: 'center', fontFamily: head ? FONT.head : FONT.body, fontWeight: weight, fontSize: size, lineHeight: 1.15, color}}>{children}</div>
  ) : null;

// ---------------------------------------------------------------- the rhythm strip
// Lead V5 from Kardiograph's engine (kardiograph_strip.ts -> data/strip.json), drawn at true scale on ECG paper:
// 25 mm/s and 10 mm/mV. It only ever scrolls: paper and trace move together under a fixed pen, and the trace is
// drawn from the recording's own samples, so its shape is identical on every frame.

const STRIP = strip as {hz: number; mv: number[]; rPeakS: number; lead: string; mmPerS: number; mmPerMv: number};
const HEAD = 930; // the pen: every QRS is written here, on its beat
const STRIP_L = 50;
const STRIP_R = 1030;
const MM_BIG = 15.6; // px per mm while the strip is the subject: 390 px/s, 13 px a frame
const MM_SMALL = 10.8; // px per mm under the heart: 270 px/s, 9 px a frame
const MM_UP = 19; // paper above the baseline, mm
const MM_DOWN = 5;
const GRID_MAJOR = '#E3E0DA';
const GRID_MINOR = '#F0EEEA';
/** The recording at strip time ts (seconds), between samples. */
function mvAt(ts: number): number {
  if (ts <= 0) return 0;
  const f = ts * STRIP.hz, i = Math.floor(f);
  if (i >= STRIP.mv.length - 1) return 0;
  return STRIP.mv[i] + (STRIP.mv[i + 1] - STRIP.mv[i]) * (f - i);
}

const Strip: React.FC<{t: number}> = ({t}) => {
  // big and centred while it is the subject; it moves down and gets smaller when the heart arrives
  const tMove = B(K.cause);
  const mm = ease(t, tMove, 0.75, MM_BIG, MM_SMALL, 'cross');
  const top = ease(t, tMove, 0.75, 690, 1230, 'cross');
  const h = (MM_UP + MM_DOWN) * mm;
  const base = top + MM_UP * mm;
  const speed = STRIP.mmPerS * mm;
  const pxMv = STRIP.mmPerMv * mm;
  const ts = t - TL.t0 + STRIP.rPeakS; // strip time: the R peak of beat k is under the pen at B(k)
  // paper grid, 1 mm and 5 mm, riding with the trace
  const lines: React.ReactNode[] = [];
  const shift = (ts * speed) % (5 * mm);
  for (let i = -5; HEAD - i * mm + 5 * mm > STRIP_L; i++) {
    const x = HEAD + (STRIP_R - HEAD) - i * mm - shift;
    if (x < STRIP_L || x > STRIP_R) continue;
    const big = ((i % 5) + 5) % 5 === 0;
    lines.push(<line key={`v${i}`} x1={x} x2={x} y1={top} y2={top + h} stroke={big ? GRID_MAJOR : GRID_MINOR} strokeWidth={big ? 2 : 1} />);
  }
  for (let j = -MM_UP; j <= MM_DOWN; j++) {
    const y = base + j * mm;
    const big = j % 5 === 0;
    lines.push(<line key={`h${j}`} x1={STRIP_L} x2={STRIP_R} y1={y} y2={y} stroke={big ? GRID_MAJOR : GRID_MINOR} strokeWidth={big ? 2 : 1} />);
  }
  // the trace: one point per recorded sample, placed by the sample's own time
  const i0 = Math.max(0, Math.ceil((ts - (HEAD - STRIP_L) / speed) * STRIP.hz));
  const i1 = Math.min(STRIP.mv.length - 1, Math.floor(ts * STRIP.hz));
  const pts: string[] = [];
  for (let i = i0; i <= i1; i++) pts.push(`${(HEAD - speed * (ts - i / STRIP.hz)).toFixed(2)},${(base - pxMv * STRIP.mv[i]).toFixed(2)}`);
  const yHead = base - pxMv * mvAt(ts);
  pts.push(`${HEAD},${yHead.toFixed(2)}`);
  // hook: "Tall." and "Short." are written above the first eight beats and ride away with the paper
  const labels: React.ReactNode[] = [];
  for (let k = K.hook; k < K.row; k++) {
    const x = HEAD - speed * (t - B(k));
    if (t < B(k) || x < -160) continue;
    const tall = k % 2 === 0;
    labels.push(
      <div key={k} style={{position: 'absolute', left: x - 200, width: 400, top: top - 150, height: 130, display: 'flex', justifyContent: 'center', alignItems: 'flex-end'}}>
        <Word t={t} t0={B(k)} size={tall ? 100 : 52}>{tall ? 'Tall.' : 'Short.'}</Word>
      </div>,
    );
  }
  return (
    <>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <defs>
          <clipPath id="paperClip"><rect x={STRIP_L} y={top} width={STRIP_R - STRIP_L} height={h} rx={20} /></clipPath>
        </defs>
        <g clipPath="url(#paperClip)">
          <rect x={STRIP_L} y={top} width={STRIP_R - STRIP_L} height={h} fill="#FCFBF9" />
          {lines}
          <polyline points={pts.join(' ')} fill="none" stroke={C.signal} strokeWidth={6} strokeLinejoin="round" strokeLinecap="round" />
          <circle cx={HEAD} cy={yHead} r={9} fill={C.signal} />
        </g>
        <rect x={STRIP_L} y={top} width={STRIP_R - STRIP_L} height={h} rx={20} fill="none" stroke={GRID_MAJOR} strokeWidth={2} />
      </svg>
      {labels}
    </>
  );
};

// ---------------------------------------------------------------- the heart in its sac

const PIV = {x: 470, y: 590}; // where the great vessels hold the heart: it swings from here
const ART_PIV = {x: 470, y: 150}; // the same point in the art's own coordinates
const ART_SCALE = 0.62;
const SWING = 10; // degrees each way
const SAC_FULL = {cx: 487, cy: 900, rx: 300, ry: 255};
const SAC_DRAINED = {cx: 487, cy: 872, rx: 242, ry: 227};
const ELEC = {x: 886, y: 900};

const Heart: React.FC<{t: number}> = ({t}) => {
  const tIn = B(K.cause) + 0.4; // after the strip has moved down out of its way
  if (t < tIn) return null;
  const tDrain = B(K.drain);
  const k = progress(t, tDrain, 0.9, 'cross');
  const sac = {
    cx: SAC_FULL.cx + (SAC_DRAINED.cx - SAC_FULL.cx) * k,
    cy: SAC_FULL.cy + (SAC_DRAINED.cy - SAC_FULL.cy) * k,
    rx: SAC_FULL.rx + (SAC_DRAINED.rx - SAC_FULL.rx) * k,
    ry: SAC_FULL.ry + (SAC_DRAINED.ry - SAC_FULL.ry) * k,
  };
  // one swing (there and back) takes two beats; on even beats the apex is nearest the electrode
  const amp = SWING * progress(t, B(K.swing), 1.5, 'cross') * (1 - progress(t, tDrain, 1.5, 'cross'));
  const theta = -amp * Math.cos((2 * Math.PI * (t - B(K.swing))) / (2 * TL.beat));
  const grow = ease(t, tIn, 0.6, 0, 1); // anatomy: plain snap and settle, no overshoot
  const small = fadeSmall(t, tIn + 0.6);
  return (
    <>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <g transform={`translate(${SAC_FULL.cx} ${SAC_FULL.cy}) scale(${grow}) translate(${-SAC_FULL.cx} ${-SAC_FULL.cy})`}>
          {/* chest wall and the electrode on it */}
          <path d="M 842 610 Q 930 900 842 1190" fill="none" stroke={C.divider} strokeWidth={14} strokeLinecap="round" />
          <rect x={ELEC.x - 17} y={ELEC.y - 44} width={34} height={88} rx={12} fill={C.signal} />
          {/* pericardial sac, filled with the effusion */}
          <ellipse cx={sac.cx} cy={sac.cy} rx={sac.rx} ry={sac.ry} fill={EFFUSION} fillOpacity={0.2} stroke={EFFUSION} strokeWidth={5} />
          {/* Mark's heart, hanging from its great vessels */}
          <g transform={`translate(${PIV.x} ${PIV.y}) rotate(${theta}) scale(${ART_SCALE}) translate(${-ART_PIV.x} ${-ART_PIV.y})`} dangerouslySetInnerHTML={{__html: HEART_ART}} />
        </g>
      </svg>
      <div style={{position: 'absolute', left: ELEC.x + 26, top: ELEC.y - 22, fontFamily: FONT.body, fontWeight: 500, fontSize: 30, color: C.ink2, opacity: small}}>electrode</div>
      {t < tDrain ? (
        <div style={{position: 'absolute', left: SAC_FULL.cx - 150, width: 300, top: SAC_FULL.cy + SAC_FULL.ry - 62, textAlign: 'center', fontFamily: FONT.body, fontWeight: 500, fontSize: 30, color: '#3F74A8', opacity: small}}>fluid</div>
      ) : null}
    </>
  );
};

// ---------------------------------------------------------------- the short

/** Everything up to the recap is one continuous scene: the strip never leaves, the text and the heart come to it. */
const Main: React.FC<{t: number}> = ({t}) => (
  <>
    <Roll
      t={t}
      top={225}
      height={335}
      until={B(K.recap)}
      lines={[
        {at: B(K.rowRegular), text: <>Regular rhythm.<br /><span style={{visibility: cut(t, B(K.rowFast)) ? 'visible' : 'hidden'}}>Fast rate.</span></>},
        {at: B(K.title), kicker: 'THIS IS', size: 112, text: <>Electrical<br />alternans</>},
        {at: B(K.cause), kicker: 'THE CAUSE TO KNOW', text: <>A large pericardial<br />effusion</>},
        {at: B(K.causeSwings), text: <>The heart swings<br />in a bag of fluid.</>},
        {at: B(K.causeReadout), text: <>Toward the electrode: tall.<br />Away: short.</>},
        {at: B(K.drain), text: <>Drain the fluid.</>},
        {at: B(K.drainStops), text: <>The swinging stops.<br />So does the alternans.</>},
      ]}
    />
    <Roll
      t={t}
      top={1110}
      height={230}
      until={B(K.cause)}
      lines={[
        {at: B(K.rowHeading), text: <>Every other QRS<br />changes height.</>},
        {at: B(K.titleSub), size: 56, text: <span style={{fontFamily: FONT.body, fontWeight: 500, color: C.ink2}}>A sign, not a diagnosis.</span>},
      ]}
    />
    <Strip t={t} />
    <Heart t={t} />
  </>
);

/** Recap: the hook again on one line, then what to think and do. */
const Recap: React.FC<{t: number}> = ({t}) => (
  <>
    <div style={{position: 'absolute', left: 0, width: 1080, top: 600, height: 160, display: 'flex', justifyContent: 'center', alignItems: 'baseline', gap: 26}}>
      {['Tall.', 'Short.', 'Tall.', 'Short.'].map((w, i) => (
        <Word key={i} t={t} t0={B(K.recap + i)} size={i % 2 === 0 ? 118 : 58}>
          {w}
        </Word>
      ))}
    </div>
    <Line t={t} at={B(K.recapThink)} top={840} size={104} color={C.ink} weight={600} head>
      Think
      <br />
      <span style={{color: C.focus}}>swinging heart.</span>
    </Line>
    <Line t={t} at={B(K.recapEcho)} top={1130}>Then get the echo.</Line>
  </>
);

const Logo: React.FC<{t: number}> = ({t}) => {
  const s = overshoot(t, B(K.logo), 0.6, 0, 1);
  return (
    <svg viewBox="0 0 69.66 44.72" width={300} style={{position: 'absolute', left: CX - 150, top: CY - 96, transform: `scale(${s})`, color: C.ink}} fill="currentColor">
      <polygon points="13.98 28.07 4.31 28.07 0 35.85 18.54 35.85 23.46 27.04 34.59 44.72 38.86 36.91 23.06 11.81 13.98 28.07" />
      <polygon points="61.63 19.81 50.85 1.86 41.25 18.59 29.55 0 25.33 7.9 41.56 33.67 51 17.22 57.23 27.59 65.77 27.59 69.66 19.81 61.63 19.81" />
    </svg>
  );
};

export const Short: React.FC<{review: boolean; label: string}> = ({review, label}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  return (
    <AbsoluteFill style={{background: C.bg}}>
      <Audio src={staticFile('sfx.wav')} />
      <Scene t={t} t0={0} t1={B(K.recap)} grow={false}><Main t={t} /></Scene>
      <Scene t={t} t0={B(K.recap)} t1={B(K.logo)} grow={false}><Recap t={t} /></Scene>
      {t >= B(K.logo) ? <Logo t={t} /> : null}
      {review ? (
        <div style={{position: 'absolute', left: 40, bottom: 40, padding: '8px 14px', borderRadius: 8, background: 'rgba(34,34,34,0.8)', color: '#fff', fontFamily: 'monospace', fontSize: 28}}>
          {label} {Math.floor(t / 60)}:{String(Math.floor(t % 60)).padStart(2, '0')}:{String(frame % fps).padStart(2, '0')}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
