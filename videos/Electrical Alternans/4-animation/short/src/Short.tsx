// Short.tsx: "Tall. Short." An Electrical Alternans short in Comma Clinical: anatomy art, on-screen text and
// sound effects, no voice-over. v2 (Mark, Nov 25, 2026: "i want anatomy art, not just text").
// Every on-screen line comes from the approved script (Gate 2, Oct 23, 2026): beats 1A, 1B, 2C, 3C, 3D, 3E, 6A, 6B.
// One metronome runs under the whole short: a beat every 0.5 s (120/min, regular and fast). Even beats are
// "tall", odd beats are "short". The picture and sfx.py both read src/data/timeline.json, so they stay in step.
// The rhythm strip only ever scrolls: the paper moves left at a constant speed and each QRS is written at the pen.
import React from 'react';
import {AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import TL from './data/timeline.json';
import {HEART_ART} from './data/heartArt';
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

const HEAD = 900; // the pen: every QRS is written here, on its beat
const SPEED = 400; // paper speed, px per second (constant: the strip only scrolls)
const STRIP_L = 50;
const STRIP_R = 1030;

/** Height of the R wave of beat k, as a share of the tallest: alternating until the fluid is drained. */
const rOf = (k: number) => (k >= K.steady || k % 2 === 0 ? 1 : 0.5);
const g = (x: number, mu: number, sigma: number) => Math.exp(-((x - mu) ** 2) / (2 * sigma * sigma));
/** The lead at time tau: P, QRS and T of the beats around it. Only the QRS changes height from beat to beat. */
function ecg(tau: number): number {
  if (tau < 0) return 0;
  const k0 = Math.round((tau - TL.t0) / TL.beat);
  let v = 0;
  for (let k = Math.max(0, k0 - 1); k <= Math.min(TL.lastBeep, k0 + 1); k++) {
    const x = tau - B(k);
    const r = rOf(k);
    v += 0.1 * g(x, -0.125, 0.018) - 0.07 * r * g(x, -0.02, 0.006) + r * g(x, 0, 0.0085) - 0.2 * r * g(x, 0.022, 0.008) + 0.17 * g(x, 0.17, 0.034);
  }
  return v;
}

const Strip: React.FC<{t: number}> = ({t}) => {
  // big and centred while it is the subject; it moves down and gets smaller when the heart arrives
  const tMove = B(K.cause);
  const top = ease(t, tMove, 0.75, 700, 1255, 'cross');
  const h = ease(t, tMove, 0.75, 400, 230, 'cross');
  const base = top + h * (ease(t, tMove, 0.75, 0.74, 0.76, 'cross'));
  const amp = ease(t, tMove, 0.75, 235, 135, 'cross');
  const x0 = Math.max(STRIP_L + 24, HEAD - SPEED * t);
  let d = '';
  for (let x = x0; x <= HEAD; x += 2) {
    const y = base - amp * ecg(t - (HEAD - x) / SPEED);
    d += `${d ? 'L' : 'M'}${x.toFixed(1)} ${y.toFixed(1)}`;
  }
  const yHead = base - amp * ecg(t);
  // hook: "Tall." and "Short." are written above the first eight beats and ride away with the paper
  const labels: React.ReactNode[] = [];
  for (let k = K.hook; k < K.row; k++) {
    const x = HEAD - SPEED * (t - B(k));
    if (t < B(k) || x < -160) continue;
    const tall = k % 2 === 0;
    labels.push(
      <div key={k} style={{position: 'absolute', left: x - 200, width: 400, top: top - 150, height: 130, display: 'flex', justifyContent: 'center', alignItems: 'flex-end'}}>
        <Word t={t} t0={B(k)} size={tall ? 104 : 54}>{tall ? 'Tall.' : 'Short.'}</Word>
      </div>,
    );
  }
  return (
    <>
      <div style={{position: 'absolute', left: STRIP_L, width: STRIP_R - STRIP_L, top, height: h, borderRadius: 24, background: C.soft}} />
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <line x1={STRIP_L + 24} x2={STRIP_R - 24} y1={base} y2={base} stroke={C.divider} strokeWidth={3} />
        <path d={d} fill="none" stroke={C.signal} strokeWidth={7} strokeLinejoin="round" strokeLinecap="round" />
        <circle cx={HEAD} cy={yHead} r={11} fill={C.signal} />
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
      top={1180}
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
