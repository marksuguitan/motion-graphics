// Opener.tsx: "This video is brought to you by Kardiograph", no VO, about 6 s.
// Cut into v8 after the title card (v8 frame 370, 0:12.33, inside the VO pause 11.91-12.43 s).
// It starts on v8's frame 370, which shrinks into a point; it ends by growing that same frame back out of the
// point, and v8 carries on from frame 371. Motion: Comma Clinical (snap and settle, grow from points, no fades).
import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {ease, overshoot, progress, stagger} from '../style/comma';
import {C, FONT} from '../style/theme';
import {BG, Card, CORAL, EcgStrip, kicker, heading, Mark, pill, useT, Wordmark} from './kit';

export const OPENER_FRAMES = 189; // 6.3 s at 30 fps

// Beat times in seconds from the plug's first frame
const T = {
  inShrink: 0, // v8's frame shrinks into the centre (accelerate)
  markGrow: 0.22, // the mark grows out of that point
  unfold: 0.7, // the mark slides left as the wordmark unfolds from its edge
  kicker: 0.95, // "This video is brought to you by" cuts on
  toPractice: 1.65, // lockup text cuts off; the mark tracks to the corner; the practice card grows
  pick: 2.95, // SVT is picked; the heading cuts to "Score your read."; the score grows
  out1: 3.75, // the practice frame shrinks into the centre
  regrow: 4.0, // the lockup grows back with the URL and "Try it free"
  out2: 5.6, // the lockup shrinks into the centre
  backIn: 5.85, // v8's frame grows back out of the point
  end: 6.3,
};

const CX = 960;
const LW = 132 + 36 + 584; // lockup width: mark, gap, "Kardiograph" at 104 px Manrope Bold (measured)
const LOCK_Y = 560; // mark centre in the lockup
const MARK_LOCK_X = CX - LW / 2 + 66;
const CORNER = {x: 240 + 32, y: 84 + 32};

const Lockup: React.FC<{t: number; t0: number; withKicker?: boolean}> = ({t, t0, withKicker}) => {
  const grow = overshoot(t, t0, 0.6, 0, 1, 0.08);
  const slide = progress(t, t0 + 0.48, 0.5, 'cross');
  const markX = ease(t, t0 + 0.48, 0.5, CX, MARK_LOCK_X, 'cross');
  return (
    <>
      <div style={{position: 'absolute', left: markX - 66, top: LOCK_Y - 66, transform: `scale(${grow})`}}>
        <Mark size={132} />
      </div>
      {/* the wordmark unfolds from the mark's right edge */}
      <div style={{position: 'absolute', left: markX + 66 + 36, top: LOCK_Y - 78, clipPath: `inset(-10px ${(1 - slide) * 100}% -20px 0)`}}>
        <Wordmark />
      </div>
      {withKicker && t >= t0 + 0.73 && <div style={{...kicker, position: 'absolute', width: '100%', textAlign: 'center', top: LOCK_Y - 160}}>This video is brought to you by</div>}
    </>
  );
};

const Practice: React.FC<{t: number}> = ({t}) => {
  const t0 = T.toPractice;
  const mx = ease(t, t0, 0.6, MARK_LOCK_X, CORNER.x, 'cross');
  const my = ease(t, t0, 0.6, LOCK_Y, CORNER.y, 'cross');
  const ms = ease(t, t0, 0.6, 1, 64 / 132, 'cross');
  const card = progress(t, t0 + 0.1, 0.6, 'snap');
  const picked = t >= T.pick;
  const ping = picked ? ease(t, T.pick, 0.15, 1, 1.08, 'snap') - (t > T.pick + 0.15 ? ease(t, T.pick + 0.15, 0.15, 0, 0.08, 'snap') : 0) : 1;
  const score = overshoot(t, T.pick + 0.15, 0.6, 0, 1, 0.06);
  const chips = ['Sinus', 'Atrial flutter', 'SVT'];
  return (
    <>
      <div style={{position: 'absolute', left: mx - 66, top: my - 66, transform: `scale(${ms})`}}>
        <Mark size={132} />
      </div>
      {t >= t0 + 0.6 && <div style={{...kicker, position: 'absolute', left: CORNER.x + 32 + 20, top: CORNER.y - 15}}>Kardiograph · Practice</div>}
      {t >= t0 + 0.3 && <div style={{...heading, position: 'absolute', left: 240, top: 270}}>{picked ? 'Score your read.' : 'Read the tracing.'}</div>}
      <div style={{position: 'absolute', left: 240, top: 380, transform: `scale(${card})`, transformOrigin: `${CX - 240}px ${560 - 380}px`}}>
        <Card style={{background: '#fff'}}>
          <EcgStrip name="svt" scrollFrom={Math.max(0, t - (t0 + 0.1))} />
        </Card>
      </div>
      <div style={{position: 'absolute', top: 760, width: '100%', display: 'flex', justifyContent: 'center', gap: 16}}>
        {chips.map((c, i) => {
          const s = overshoot(t, t0 + 0.5 + stagger(i), 0.6, 0, 1, 0.06);
          const on = c === 'SVT' && picked;
          return (
            <span key={c} style={{...pill, transform: `scale(${on ? s * ping : s})`, ...(on ? {background: CORAL, borderColor: CORAL, color: '#fff', fontWeight: 600} : {})}}>
              {on ? '✓ ' : ''}
              {c}
            </span>
          );
        })}
        <span style={{...pill, border: 'none', background: '#E7F4F2', borderRadius: 16, marginLeft: 24, transform: `scale(${score})`}}>
          <b style={{color: C.normal, fontWeight: 700}}>100%</b> Rhythm: SVT
        </span>
      </div>
    </>
  );
};

const Url: React.FC<{t: number}> = ({t}) => {
  const a = overshoot(t, T.regrow + 0.75, 0.6, 0, 1, 0.06);
  const b = overshoot(t, T.regrow + 0.75 + stagger(1), 0.6, 0, 1, 0.06);
  return (
    <div style={{position: 'absolute', top: 700, width: '100%', display: 'flex', justifyContent: 'center', gap: 24}}>
      <span style={{...pill, fontWeight: 600, fontSize: 46, padding: '20px 44px', background: '#fff', transform: `scale(${a})`}}>kardiograph.medzcool.com</span>
      <span style={{...pill, fontWeight: 600, fontSize: 40, padding: '24px 44px', background: CORAL, border: 'none', color: '#fff', transform: `scale(${b})`}}>Try it free</span>
    </div>
  );
};

/** Everything in a phase shrinks into the centre point on the accelerate curve. */
const Shrink: React.FC<{t: number; t0: number; children: React.ReactNode}> = ({t, t0, children}) => (
  <AbsoluteFill style={{transform: `scale(${1 - progress(t, t0, 0.25, 'accel')})`, transformOrigin: `${CX}px 540px`}}>{children}</AbsoluteFill>
);

export const Opener: React.FC = () => {
  const t = useT();
  let body: React.ReactNode = null;
  if (t < T.markGrow) {
    body = (
      <Shrink t={t} t0={T.inShrink}>
        <Img src={staticFile('v8-f370.png')} style={{width: 1920, height: 1080}} />
      </Shrink>
    );
  } else if (t < T.toPractice) {
    body = <Lockup t={t} t0={T.markGrow} withKicker />;
  } else if (t < T.regrow) {
    body = (
      <Shrink t={t} t0={T.out1}>
        <Practice t={t} />
      </Shrink>
    );
  } else if (t < T.backIn) {
    body = (
      <Shrink t={t} t0={T.out2}>
        <Lockup t={t} t0={T.regrow} />
        <Url t={t} />
      </Shrink>
    );
  } else {
    const s = progress(t, T.backIn, 0.45, 'snap');
    body = (
      <AbsoluteFill style={{transform: `scale(${s})`, transformOrigin: `${CX}px 540px`}}>
        <Img src={staticFile('v8-f370.png')} style={{width: 1920, height: 1080}} />
      </AbsoluteFill>
    );
  }
  return <AbsoluteFill style={{background: BG, fontFamily: FONT.body}}>{body}</AbsoluteFill>;
};

