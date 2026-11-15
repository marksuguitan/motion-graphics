// EndPlug.tsx: what Kardiograph is and why it helps, with VO (Mark's wording, 19.6 s read), about 21.5 s.
// Cut into v8 on its blank paper frames between the last scene and the Subscribe card (v8 frames 5091-5100):
// the plug starts and ends on that same blank paper, so both cuts are invisible.
// Every move lands on a measured word (src/data/end-words.json, from Scribe on the saved take). Never estimate.
import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile} from 'remotion';
import words from '../data/end-words.json';
import {ease, overshoot, progress, stagger} from '../style/comma';
import {C, FONT} from '../style/theme';
import {BG, Card, CORAL, CORAL_SOFT, EcgStrip, heading, Icon, ICON, kicker, Mark, pill, rPeaks, STRIP_PX, stripFs, useT, Wordmark} from './kit';

const LEAD = 0.4; // blank paper before the VO starts
const W = words as {i: number; word: string; t: number; end: number}[];
/** Plug time of the n-th (1-based) occurrence of a word in the narration. Throws rather than guessing. */
function at(word: string, nth = 1): number {
  const hits = W.filter((w) => w.word.toLowerCase().replace(/[.,]/g, '') === word.toLowerCase());
  if (hits.length < nth) throw new Error(`"${word}" (${nth}) is not in end-words.json`);
  return LEAD + hits[nth - 1].t;
}
const endOf = (word: string, nth = 1) => {
  const hits = W.filter((w) => w.word.toLowerCase().replace(/[.,]/g, '') === word.toLowerCase());
  return LEAD + hits[nth - 1].end;
};

// Beats, all from word times
const T = {
  mark: at('kardiograph'), // the mark grows out of the blank paper
  course: at('course'), // Course tile grows
  practiceTile: at('practice'), // Practice tile grows
  out1: at('every') - 0.25, // lockup and tiles shrink into the centre, landing on "Every"
  card: at('every'), // the strip card grows on "Every tracing"
  scale: at('true'), // heading "Drawn at true scale." and the paper speed cut on
  calipers: at('calipers'), // calipers open from one R wave to the next
  newStrip: at('and', 2), // "And every practice strip": the heading changes
  montage: at('procedurally'), // strips swap, one rhythm after another
  out2: at('variety') - 0.25, // the montage card shrinks into the centre
  grid: at('variety'), // six rhythms grow into a grid
  endless: at('endless'), // the New tracing pill pings
  out3: at('try') - 0.25, // the grid shrinks into the centre
  lockup: at('try'), // the lockup grows back
  free: at('free'), // "Try it free" grows
  url: at('kardiograph', 2), // the URL grows ("Kardiograph's" doesn't count)
  out4: endOf('com') + 1.0, // after a 1 s hold, everything shrinks into the centre
};
export const END_FRAMES = Math.ceil((T.out4 + 0.25 + 0.15) * 30);

const CX = 960;
const LW = 132 + 36 + 584;
const MARK_LOCK_X = CX - LW / 2 + 66;
const CORNER = {x: 240 + 32, y: 84 + 32};

const NAMES: Record<string, string> = {
  sinus: 'Normal sinus rhythm',
  afib: 'Atrial fibrillation',
  flutter: 'Atrial flutter',
  avb1: '1st-degree AV block',
  mobitz1: 'Mobitz I',
  svt: 'SVT',
};
const MONTAGE = ['afib', 'flutter', 'avb1', 'mobitz1', 'svt', 'sinus'];
const GRID = ['sinus', 'afib', 'flutter', 'avb1', 'mobitz1', 'svt'];
const SWAP = 0.3; // montage cut, s per strip

const Shrink: React.FC<{t: number; t0: number; children: React.ReactNode}> = ({t, t0, children}) => (
  <AbsoluteFill style={{transform: `scale(${1 - progress(t, t0, 0.25, 'accel')})`, transformOrigin: `${CX}px 540px`}}>{children}</AbsoluteFill>
);

const Lockup: React.FC<{t: number; t0: number; y: number}> = ({t, t0, y}) => {
  const grow = overshoot(t, t0, 0.6, 0, 1, 0.08);
  const slide = progress(t, t0 + 0.4, 0.5, 'cross');
  const markX = ease(t, t0 + 0.4, 0.5, CX, MARK_LOCK_X, 'cross');
  return (
    <>
      <div style={{position: 'absolute', left: markX - 66, top: y - 66, transform: `scale(${grow})`}}>
        <Mark size={132} />
      </div>
      <div style={{position: 'absolute', left: markX + 66 + 36, top: y - 78, clipPath: `inset(-10px ${(1 - slide) * 100}% -20px 0)`}}>
        <Wordmark />
      </div>
    </>
  );
};

const Tile: React.FC<{t: number; t0: number; icon: string[]; title: string; sub: string}> = ({t, t0, icon, title, sub}) => (
  <div style={{display: 'flex', alignItems: 'center', gap: 28, width: 520, padding: '36px 40px', background: '#fff', borderRadius: 24, boxShadow: '0 8px 24px rgba(34,34,34,.08)', transform: `scale(${overshoot(t, t0, 0.6, 0, 1, 0.06)})`}}>
    <div style={{width: 88, height: 88, borderRadius: 22, background: CORAL_SOFT, display: 'grid', placeItems: 'center'}}>
      <Icon d={icon} size={48} color={CORAL} />
    </div>
    <div>
      <div style={{fontFamily: FONT.head, fontWeight: 600, fontSize: 48, color: C.ink}}>{title}</div>
      <div style={{fontFamily: FONT.body, fontSize: 30, color: C.ink2, marginTop: 6}}>{sub}</div>
    </div>
  </div>
);

/** Small corner mark and kicker, grown from the mark's point. */
const Corner: React.FC<{t: number; t0: number; label: string}> = ({t, t0, label}) => (
  <>
    <div style={{position: 'absolute', left: CORNER.x - 32, top: CORNER.y - 32, transform: `scale(${overshoot(t, t0, 0.6, 0, 1, 0.08)})`}}>
      <Mark size={64} />
    </div>
    {t >= t0 + 0.3 && <div style={{...kicker, position: 'absolute', left: CORNER.x + 32 + 20, top: CORNER.y - 15}}>{label}</div>}
  </>
);

const Calipers: React.FC<{t: number}> = ({t}) => {
  const pk = rPeaks('sinus');
  const fs = stripFs('sinus');
  const x = (i: number) => (i / fs) * 25 * STRIP_PX.mm;
  const a = x(pk[2]);
  const b = x(pk[3]);
  const ms = ((pk[3] - pk[2]) / fs) * 1000;
  const open = ease(t, T.calipers, 0.6, a, b, 'cross');
  const legs = progress(t, T.calipers - 0.1, 0.3, 'snap');
  const top = 2.2 * STRIP_PX.mm;
  const bottom = STRIP_PX.h - 2 * STRIP_PX.mm;
  const legLen = (bottom - top) * legs;
  const read = overshoot(t, T.calipers + 0.6, 0.5, 0, 1, 0.06);
  if (t < T.calipers - 0.1) return null;
  return (
    <g>
      <g stroke={CORAL} strokeWidth={3} fill="none">
        <path d={`M${a} ${top}V${top + legLen}M${open} ${top}V${top + legLen}M${a} ${top + 12}H${open}`} />
      </g>
      <g transform={`translate(${(a + b) / 2},${top - 2}) scale(${read})`}>
        <rect x={-150} y={-26} width={300} height={52} rx={26} fill={CORAL} />
        <text textAnchor="middle" y={10} fontFamily="Inter" fontWeight={600} fontSize={28} fill="#fff">
          {`${ms.toFixed(0)} ms · ${(60000 / ms).toFixed(0)} bpm`}
        </text>
      </g>
    </g>
  );
};

const NameChip: React.FC<{name: string; size?: number}> = ({name, size = 26}) => (
  <span style={{fontFamily: FONT.body, fontWeight: 600, fontSize: size, color: C.ink, background: '#fff', border: `2px solid ${C.divider}`, borderRadius: 999, padding: '6px 18px', whiteSpace: 'nowrap'}}>{name}</span>
);

const Strips: React.FC<{t: number}> = ({t}) => {
  const card = progress(t, T.card, 0.6, 'snap');
  const inMontage = t >= T.montage;
  const k = inMontage ? Math.min(MONTAGE.length - 1, Math.floor((t - T.montage) / SWAP)) : -1;
  const name = k >= 0 ? MONTAGE[k] : 'sinus';
  const swapT = k >= 0 ? T.montage + k * SWAP : -1;
  const pillPing = k >= 0 ? 1 + 0.08 * (1 - progress(t, swapT, 0.25, 'snap')) : 1;
  const practice = t >= T.newStrip;
  return (
    <>
      <Corner t={t} t0={T.card} label={practice ? 'Kardiograph · Practice' : 'Kardiograph · True scale'} />
      {t >= T.scale && <div style={{...heading, position: 'absolute', left: 240, top: 250}}>{practice ? 'A new tracing every time.' : 'Drawn at true scale.'}</div>}
      <div style={{position: 'absolute', left: 240, top: 380, transform: `scale(${card})`, transformOrigin: `${CX - 240}px ${560 - 380}px`}}>
        <Card style={{background: '#fff'}}>
          <EcgStrip name={name}>{!practice && <Calipers t={t} />}</EcgStrip>
        </Card>
        {inMontage && (
          <div style={{position: 'absolute', right: 36, top: -26}}>
            <NameChip name={NAMES[name]} />
          </div>
        )}
      </div>
      {t >= T.scale && !practice && <div style={{position: 'absolute', top: 770, width: '100%', textAlign: 'center', fontFamily: FONT.body, fontSize: 30, color: C.ink2}}>25 mm/s · 10 mm/mV</div>}
      {practice && (
        <div style={{position: 'absolute', top: 760, width: '100%', display: 'flex', justifyContent: 'center'}}>
          <span style={{...pill, transform: `scale(${overshoot(t, T.newStrip, 0.6, 0, 1, 0.06) * pillPing})`}}>
            <Icon d={ICON.rotate} size={30} color={C.ink} sw={2.2} /> New tracing
          </span>
        </div>
      )}
    </>
  );
};

const Grid: React.FC<{t: number}> = ({t}) => {
  const ping = 1 + 0.08 * (t >= T.endless ? 1 - progress(t, T.endless, 0.3, 'snap') : 0) * (t >= T.endless ? 1 : 0);
  const S = 0.58; // a 3 s strip at 58%: 418 x 167 px
  return (
    <>
      <Corner t={t} t0={T.grid - 10} label="Kardiograph · Practice" />
      <div style={{...heading, position: 'absolute', left: 240, top: 200}}>A new tracing every time.</div>
      <div style={{position: 'absolute', top: 320, width: '100%', display: 'grid', gridTemplateColumns: 'repeat(3, 458px)', justifyContent: 'center', columnGap: 36, rowGap: 36}}>
        {GRID.map((g, i) => {
          const s = overshoot(t, T.grid + stagger(i), 0.6, 0, 1, 0.06);
          return (
            <div key={g} style={{transform: `scale(${s})`, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14}}>
              <Card style={{background: '#fff', padding: 12}}>
                <div style={{width: 720 * S, height: 288 * S, overflow: 'hidden'}}>
                  <div style={{transform: `scale(${S})`, transformOrigin: '0 0'}}>
                    <EcgStrip name={g} seconds={3} scrollFrom={1} />
                  </div>
                </div>
              </Card>
              <NameChip name={NAMES[g]} size={24} />
            </div>
          );
        })}
      </div>
      <div style={{position: 'absolute', top: 900, width: '100%', display: 'flex', justifyContent: 'center'}}>
        <span style={{...pill, transform: `scale(${ping})`}}>
          <Icon d={ICON.rotate} size={30} color={C.ink} sw={2.2} /> New tracing
        </span>
      </div>
    </>
  );
};

const Cta: React.FC<{t: number}> = ({t}) => (
  <div style={{position: 'absolute', top: 640, width: '100%', display: 'flex', justifyContent: 'center', gap: 24}}>
    <span style={{...pill, fontWeight: 600, fontSize: 46, padding: '20px 44px', background: '#fff', transform: `scale(${overshoot(t, T.url, 0.6, 0, 1, 0.06)})`}}>kardiograph.medzcool.com</span>
    <span style={{...pill, fontWeight: 600, fontSize: 40, padding: '24px 44px', background: CORAL, border: 'none', color: '#fff', transform: `scale(${overshoot(t, T.free, 0.6, 0, 1, 0.06)})`}}>Try it free</span>
  </div>
);

const SFX: [number, string, number][] = [
  [T.mark + 0.28, 'pop', 0.7],
  [T.course + 0.15, 'pop-soft', 0.7],
  [T.practiceTile + 0.15, 'pop-soft', 0.7],
  [T.card + 0.15, 'pop', 0.7],
  [T.calipers + 0.55, 'pop-soft', 0.8],
  ...MONTAGE.slice(1).map((_, k): [number, string, number] => [T.montage + (k + 1) * SWAP, 'click', 0.35]),
  [T.grid + 0.25, 'pop-soft', 0.7],
  [T.lockup + 0.28, 'pop', 0.7],
  [T.free + 0.15, 'pop-soft', 0.7],
  [T.url + 0.15, 'pop-soft', 0.7],
];

export const EndPlug: React.FC = () => {
  const t = useT();
  let body: React.ReactNode = null;
  if (t < T.mark) body = null; // blank paper, as in v8
  else if (t < T.card)
    body = (
      <Shrink t={t} t0={T.out1}>
        <Lockup t={t} t0={T.mark} y={380} />
        <div style={{position: 'absolute', top: 560, width: '100%', display: 'flex', justifyContent: 'center', gap: 36}}>
          <Tile t={t} t0={T.course} icon={ICON.book} title="Course" sub="7 modules, 21 lessons" />
          <Tile t={t} t0={T.practiceTile} icon={ICON.clipboard} title="Practice" sub="5 decks, scored" />
        </div>
      </Shrink>
    );
  else if (t < T.grid)
    body = (
      <Shrink t={t} t0={T.out2}>
        <Strips t={t} />
      </Shrink>
    );
  else if (t < T.lockup)
    body = (
      <Shrink t={t} t0={T.out3}>
        <Grid t={t} />
      </Shrink>
    );
  else if (t < T.out4 + 0.25)
    body = (
      <Shrink t={t} t0={T.out4}>
        <Lockup t={t} t0={T.lockup} y={480} />
        <Cta t={t} />
      </Shrink>
    );
  return (
    <AbsoluteFill style={{background: BG, fontFamily: FONT.body}}>
      {body}
      <Sequence from={Math.round(LEAD * 30)} layout="none">
        <Audio src={staticFile('vo/end-plug.mp3')} />
      </Sequence>
      {SFX.map(([s, name, vol]) => (
        <Sequence key={`${name}-${s}`} from={Math.round(s * 30)} layout="none">
          <Audio src={staticFile(`sfx/${name}.wav`)} volume={vol} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
