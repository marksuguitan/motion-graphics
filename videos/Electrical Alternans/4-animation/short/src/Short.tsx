// Short.tsx: "Tall. Short." An Electrical Alternans short in Comma Clinical: type and sound effects only.
// Every on-screen line comes from the approved script (Gate 2, Oct 23, 2026): beats 1A, 1B, 2C, 3C, 3D, 3E, 6A, 6B.
// One metronome runs under the whole short: a beat every 0.5 s (120/min, regular and fast). Even beats are
// "tall", odd beats are "short". The picture and sfx.py both read src/data/timeline.json, so they stay in step.
import React from 'react';
import {AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import TL from './data/timeline.json';
import {C, FONT} from './style/theme';
import {cut, ease, fadeSmall, overshoot, progress} from './style/comma';

const B = (k: number) => TL.t0 + k * TL.beat; // time of beat k
const K = TL.k;
const CX = 540; // every scene shrinks into, and grows out of, this point
const CY = 900;
const beatAt = (t: number) => Math.floor((t - TL.t0) / TL.beat + 1e-6); // index of the latest beat

// ---------------------------------------------------------------- pieces

/** A scene that grows out of the centre point at t0 and shrinks back into it, accelerating, just before t1. */
const Scene: React.FC<{t: number; t0: number; t1: number; grow?: boolean; children: React.ReactNode}> = ({t, t0, t1, grow = true, children}) => {
  if (t < t0 || t >= t1) return null;
  const sIn = grow ? ease(t, t0, 0.6, 0, 1) : 1;
  const sOut = ease(t, t1 - 0.25, 0.25, 1, 0, 'accel');
  return (
    <AbsoluteFill style={{transform: `scale(${sIn * sOut})`, transformOrigin: `${CX}px ${CY}px`}}>{children}</AbsoluteFill>
  );
};

/** A word that cuts on at t0 and lands with one small overshoot; `ping` re-pulses it on later beats. */
const Word: React.FC<{t: number; t0: number; size: number; color?: string; weight?: number; pingAt?: number[]; children: React.ReactNode}> = ({t, t0, size, color = C.ink, weight = 600, pingAt = [], children}) => {
  let s: number = overshoot(t, t0, 0.3, 0.86, 1, 0.08, 0.15);
  for (const p of pingAt) if (t >= p) s = ease(t, p, 0.3, 1.08, 1);
  return (
    <span style={{display: 'inline-block', visibility: cut(t, t0) ? 'visible' : 'hidden', fontFamily: FONT.head, fontWeight: weight, fontSize: size, lineHeight: 1, color, transform: `scale(${s})`, transformOrigin: '50% 80%'}}>
      {children}
    </span>
  );
};

/** Lines that swap in one place: the old line rolls up and out, the new one rolls up into place, clipped to the box. */
const Roll: React.FC<{t: number; lines: {at: number; kicker?: string; text: React.ReactNode}[]; until: number; top: number; height: number; size?: number}> = ({t, lines, until, top, height, size = 68}) => (
  <div style={{position: 'absolute', left: 90, width: 900, top, height, overflow: 'hidden'}}>
    {lines.map((l, i) => {
      const next = i + 1 < lines.length ? lines[i + 1].at : until;
      if (t < l.at || t >= next) return null;
      const yIn = i === 0 ? 0 : ease(t, l.at, 0.3, 40 + height, 0);
      const yOut = i + 1 < lines.length ? ease(t, next - 0.25, 0.25, 0, -(40 + height), 'accel') : 0;
      return (
        <div key={i} style={{position: 'absolute', inset: 0, transform: `translateY(${yIn + yOut}px)`, textAlign: 'center'}}>
          {l.kicker ? <div style={{fontFamily: FONT.head, fontWeight: 700, fontSize: 30, letterSpacing: 4, color: C.ink2, marginBottom: 22}}>{l.kicker}</div> : null}
          <div style={{fontFamily: FONT.head, fontWeight: 600, fontSize: size, lineHeight: 1.12, color: C.ink}}>{l.text}</div>
        </div>
      );
    })}
  </div>
);

const Line: React.FC<{t: number; at: number; top: number; size?: number; color?: string; weight?: number; head?: boolean; children: React.ReactNode}> = ({t, at, top, size = 52, color = C.ink2, weight = 500, head = false, children}) =>
  cut(t, at) ? (
    <div style={{position: 'absolute', left: 90, width: 900, top, textAlign: 'center', fontFamily: head ? FONT.head : FONT.body, fontWeight: weight, fontSize: size, lineHeight: 1.15, color}}>{children}</div>
  ) : null;

// ---------------------------------------------------------------- scenes

/** 1. Hook: the words themselves are tall and short, one per beat. */
const Hook: React.FC<{t: number}> = ({t}) => {
  const words = ['Tall.', 'Short.', 'Tall.', 'Short.'];
  return (
    <div style={{position: 'absolute', left: 0, width: 1080, top: 430, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 34}}>
      {words.map((w, i) => (
        <Word key={i} t={t} t0={B(K.hook + i)} size={i % 2 === 0 ? 290 : 120} pingAt={[B(K.hook + 4 + i)]}>
          {w}
        </Word>
      ))}
    </div>
  );
};

/** 2. The same idea as a rhythm strip made of type: QRS, tall then short, on one baseline. */
const Row: React.FC<{t: number}> = ({t}) => {
  const k = beatAt(t);
  return (
    <>
      <Line t={t} at={B(K.rowRegular)} top={470}>Regular rhythm.</Line>
      <Line t={t} at={B(K.rowFast)} top={552}>Fast rate.</Line>
      <div style={{position: 'absolute', left: 0, width: 1080, top: 720, height: 220, display: 'flex', justifyContent: 'center', alignItems: 'baseline', gap: 30}}>
        {[0, 1, 2, 3].map((i) => {
          // each beat pulses the next complex, left to right, like a sweep
          const pings: number[] = [];
          for (let j = K.row + 1; j <= k && j < K.title; j++) if ((j - K.row) % 4 === i) pings.push(B(j));
          return (
            <Word key={i} t={t} t0={B(K.row)} size={i % 2 === 0 ? 128 : 66} color={C.signal} weight={700} pingAt={pings.slice(-1)}>
              QRS
            </Word>
          );
        })}
      </div>
      <div style={{position: 'absolute', left: 110, width: 860, top: 902, height: 5, borderRadius: 3, background: C.divider}} />
      <Line t={t} at={B(K.rowHeading)} top={1010} size={72} color={C.ink} weight={600} head>
        Every other QRS
        <br />
        changes height.
      </Line>
    </>
  );
};

/** 3. The name. The title itself alternates: full size on tall beats, smaller on short beats. */
const Title: React.FC<{t: number}> = ({t}) => {
  const k = beatAt(t);
  let s = 1;
  if (k >= K.titleAlternate) {
    const from = k === K.titleAlternate ? 1 : k % 2 === 0 ? 0.84 : 1;
    s = ease(t, B(k), 0.25, from, k % 2 === 0 ? 1 : 0.84);
  }
  return (
    <>
      <div style={{position: 'absolute', left: 0, width: 1080, top: 640, textAlign: 'center', fontFamily: FONT.head, fontWeight: 700, fontSize: 30, letterSpacing: 4, color: C.ink2}}>THIS IS</div>
      <div style={{position: 'absolute', left: 0, width: 1080, top: 720, textAlign: 'center', fontFamily: FONT.head, fontWeight: 600, fontSize: 138, lineHeight: 1.04, color: C.ink, transform: `scale(${s})`, transformOrigin: '50% 100%'}}>
        Electrical
        <br />
        alternans
      </div>
      <Line t={t} at={B(K.titleSub)} top={1090}>A sign, not a diagnosis.</Line>
    </>
  );
};

/** 4 and 5. The cause: the word "heart" swings in a ring of fluid, toward the electrode and away; then the fluid is drained. */
const RX = 600; // ring centre
const RY = 930;
const R_FULL = 300;
const R_DRAINED = 170;
const EX = 150; // electrode
const Cause: React.FC<{t: number}> = ({t}) => {
  const k = beatAt(t);
  const tDrain = B(K.drain);
  const r = ease(t, tDrain, 0.9, R_FULL, R_DRAINED, 'cross');
  // one swing (there and back) takes two beats; on even beats the heart is nearest the electrode
  const amp = 26 * progress(t, B(K.swing), 1.5, 'cross') * (1 - progress(t, tDrain, 1.5, 'cross'));
  const theta = amp * Math.cos((2 * Math.PI * (t - B(K.swing))) / (2 * TL.beat));
  const armLen = 250;
  const rad = (theta * Math.PI) / 180;
  const pivotY = RY - 250;
  const hx = RX - armLen * Math.sin(rad);
  const hy = pivotY + armLen * Math.cos(rad);
  const steady = k >= K.steady;
  const tall = steady || k % 2 === 0;
  const readoutOn = cut(t, B(K.causeReadout));
  return (
    <>
      <Roll
        t={t}
        top={250}
        height={280}
        until={B(K.recap)}
        lines={[
          {at: B(K.cause), kicker: 'THE CAUSE TO KNOW', text: <>A large pericardial<br />effusion</>},
          {at: B(K.causeSwings), text: <>The heart swings<br />in a bag of fluid.</>},
          {at: B(K.causeReadout), text: <>Toward the electrode: tall.<br />Away: short.</>},
          {at: B(K.drain), text: <>Drain the fluid.</>},
          {at: B(K.drainStops), text: <>The swinging stops.<br />So does the alternans.</>},
        ]}
      />
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <circle cx={RX} cy={RY} r={r} fill={C.soft} stroke={C.divider} strokeWidth={8} />
        <rect x={EX - 34} y={RY - 34} width={68} height={68} rx={14} fill={C.signal} />
      </svg>
      <div style={{position: 'absolute', left: EX - 120, width: 240, top: RY + 52, textAlign: 'center', fontFamily: FONT.body, fontWeight: 500, fontSize: 32, color: C.ink2, opacity: fadeSmall(t, B(K.cause) + 0.6)}}>electrode</div>
      {t < tDrain ? (
        <div style={{position: 'absolute', left: RX - 150, width: 300, top: RY + 205, textAlign: 'center', fontFamily: FONT.body, fontWeight: 500, fontSize: 32, color: C.ink2, opacity: fadeSmall(t, B(K.cause) + 0.6)}}>fluid</div>
      ) : null}
      <div style={{position: 'absolute', left: hx - 200, width: 400, top: hy - 60, height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT.head, fontWeight: 700, fontSize: 104, lineHeight: 1, color: C.focus, transform: `rotate(${-theta}deg)`}}>
        heart
      </div>
      {readoutOn ? (
        <div style={{position: 'absolute', left: 0, width: 1080, top: 1290, height: 190, display: 'flex', justifyContent: 'center', alignItems: 'flex-end'}}>
          <span style={{display: 'inline-block', fontFamily: FONT.head, fontWeight: 700, fontSize: tall ? 170 : 84, lineHeight: 1, color: C.signal, transform: `scale(${ease(t, B(k), 0.25, 1.1, 1)})`, transformOrigin: '50% 100%'}}>QRS</span>
        </div>
      ) : null}
      {readoutOn ? <div style={{position: 'absolute', left: 340, width: 400, top: 1486, height: 5, borderRadius: 3, background: C.divider}} /> : null}
    </>
  );
};

/** 6. Recap: the hook again on one line, then what to think and do. */
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
      <Scene t={t} t0={0} t1={B(K.row)} grow={false}><Hook t={t} /></Scene>
      <Scene t={t} t0={B(K.row)} t1={B(K.title)}><Row t={t} /></Scene>
      <Scene t={t} t0={B(K.title)} t1={B(K.cause)}><Title t={t} /></Scene>
      <Scene t={t} t0={B(K.cause)} t1={B(K.recap)}><Cause t={t} /></Scene>
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
