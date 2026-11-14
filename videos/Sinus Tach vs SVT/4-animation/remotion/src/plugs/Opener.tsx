// Opener.tsx: "This video is brought to you by Kardiograph", no VO, 9.3 s, with simple sounds.
// Cut into v8 after the title card (v8 frame 370, 0:12.33, inside the VO pause 11.91-12.43 s).
// It starts on v8's frame 370, which shrinks into a point; it ends by growing that same frame back out of the
// point, and v8 carries on from frame 371. Motion: Comma Clinical (snap and settle, grow from points, no fades).
import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, staticFile} from 'remotion';
import {ease, overshoot, progress, stagger} from '../style/comma';
import {C, FONT} from '../style/theme';
import {BG, Card, CORAL, EcgStrip, kicker, heading, Mark, pill, useT, Wordmark} from './kit';

export const OPENER_FRAMES = 279; // 9.3 s at 30 fps

// Beat times in seconds from the plug's first frame.
// v2 (Mark, Nov 14): the "brought to you by" lockup holds 1 s longer, the practice card 2 s longer,
// with a cursor that clicks SVT, and simple sounds (landing hits, the click, a chime on the score).
const T = {
  inShrink: 0, // v8's frame shrinks into the centre (accelerate)
  markGrow: 0.22, // the mark grows out of that point
  unfold: 0.7, // the mark slides left as the wordmark unfolds from its edge
  kicker: 0.95, // "This video is brought to you by" cuts on
  toPractice: 2.65, // lockup text cuts off; the mark tracks to the corner; the practice card grows
  cursorIn: 3.85, // the cursor grows from its tip, lower right
  cursorMove: 4.05, // it tracks to the SVT chip
  pick: 4.95, // click: SVT is picked; the heading cuts to "Score your read."; the score grows
  out1: 6.75, // the practice frame shrinks into the centre
  regrow: 7.0, // the lockup grows back with the URL and "Try it free"
  out2: 8.6, // the lockup shrinks into the centre
  backIn: 8.85, // v8's frame grows back out of the point
  end: 9.3,
};

// Sounds, at the landing frames above (seconds). Files from scripts/make_sfx.py.
const SFX: [number, string][] = [
  [0.5, 'pop'], // the mark lands
  [1.12, 'pop-soft'], // the wordmark finishes unfolding
  [2.88, 'pop'], // the practice card lands
  [3.27, 'pop-soft'], // the chips land
  [T.pick, 'click'], // the cursor clicks SVT
  [T.pick + 0.2, 'chime'], // the 100% score
  [T.regrow + 0.28, 'pop'], // the mark lands again
  [T.regrow + 0.95, 'pop-soft'], // URL and "Try it free" land
];

const SVT_CHIP = {x: 971, y: 793}; // centre of the SVT chip (measured from a still)
const CURSOR_FROM = {x: 1390, y: 985};
const CURSOR_TO = {x: SVT_CHIP.x + 48, y: SVT_CHIP.y + 12}; // the tip lands in the right of the chip, clear of its label

/** A plain arrow pointer; its tip is at (0, 0). */
const Cursor: React.FC<{t: number}> = ({t}) => {
  const grow = progress(t, T.cursorIn, 0.4, 'snap');
  const x = ease(t, T.cursorMove, 0.8, CURSOR_FROM.x, CURSOR_TO.x, 'cross');
  const y = ease(t, T.cursorMove, 0.8, CURSOR_FROM.y, CURSOR_TO.y, 'cross');
  const press = t < T.pick ? 1 : t < T.pick + 0.06 ? ease(t, T.pick - 0.02, 0.08, 1, 0.84, 'snap') : ease(t, T.pick + 0.06, 0.18, 0.84, 1, 'snap');
  const ring = progress(t, T.pick, 0.3, 'snap');
  return (
    <>
      {t >= T.pick && t < T.pick + 0.3 && (
        <div style={{position: 'absolute', left: x - 26 * (1 + 0.6 * ring), top: y - 26 * (1 + 0.6 * ring), width: 52 * (1 + 0.6 * ring), height: 52 * (1 + 0.6 * ring), borderRadius: '50%', border: `4px solid ${CORAL}`, opacity: 1 - ring}} />
      )}
      <svg width={46} height={60} viewBox="0 0 23 30" style={{position: 'absolute', left: x - 1.5, top: y - 1.5, transform: `scale(${grow * press})`, transformOrigin: '1.5px 1.5px', overflow: 'visible'}}>
        <path d="M1.5 1.5v22.5l6.2-5.6 4.1 9.4 4-1.8-4-9.2 8.4-.6z" fill={C.ink} stroke="#fff" strokeWidth={2} strokeLinejoin="round" />
      </svg>
    </>
  );
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
      {t >= T.cursorIn && <Cursor t={t} />}
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
  return (
    <AbsoluteFill style={{background: BG, fontFamily: FONT.body}}>
      {body}
      {SFX.map(([at, name]) => (
        <Sequence key={`${name}-${at}`} from={Math.round(at * 30)} layout="none">
          <Audio src={staticFile(`sfx/${name}.wav`)} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

