// Card.tsx: the on-screen text. A scene's first card cuts on whole on its time (no fade); later cards use the
// Comma Clinical "text in a card changes" transition: old rows roll up and out (0.25 s, accelerating) and finish
// as the new rows start rolling up into place (0.3 s, snap and settle, 40 px), one frame apart, each clipped to
// its own row. The kicker cuts on with the first card and rolls out at the scene's end.
import React from 'react';
import {progress} from '../style/comma';
import {C, FONT} from '../style/theme';
import {CARD} from '../lib/tl';

export type RowKind = 'kicker' | 'title' | 'heading' | 'tipHead' | 'big' | 'body' | 'bodyStrong' | 'tip' | 'note' | 'sub';
export type Row = {kind: RowKind; text: React.ReactNode};

const ROW: Record<RowKind, {h: number; gap?: number; style: React.CSSProperties}> = {
  kicker: {h: 34, gap: 14, style: {fontFamily: FONT.head, fontWeight: 700, fontSize: 23, letterSpacing: 3, textTransform: 'uppercase', color: C.ink2, lineHeight: '34px'}},
  title: {h: 96, style: {fontFamily: FONT.head, fontWeight: 600, fontSize: 80, lineHeight: '96px', color: C.ink, letterSpacing: -0.5}},
  heading: {h: 68, style: {fontFamily: FONT.head, fontWeight: 600, fontSize: 56, lineHeight: '68px', color: C.ink, letterSpacing: -0.3}},
  tipHead: {h: 68, style: {fontFamily: FONT.head, fontWeight: 600, fontSize: 56, lineHeight: '68px', color: C.normal, letterSpacing: -0.3}},
  big: {h: 150, style: {fontFamily: FONT.head, fontWeight: 700, fontSize: 136, lineHeight: '150px', color: C.ink, fontVariantNumeric: 'tabular-nums', letterSpacing: -2}},
  body: {h: 50, style: {fontFamily: FONT.body, fontWeight: 400, fontSize: 34, lineHeight: '50px', color: C.ink}},
  bodyStrong: {h: 50, style: {fontFamily: FONT.body, fontWeight: 600, fontSize: 34, lineHeight: '50px', color: C.ink}},
  tip: {h: 50, style: {fontFamily: FONT.body, fontWeight: 600, fontSize: 34, lineHeight: '50px', color: C.normal}},
  sub: {h: 46, style: {fontFamily: FONT.body, fontWeight: 400, fontSize: 30, lineHeight: '46px', color: C.ink2}},
  note: {h: 32, style: {fontFamily: FONT.body, fontWeight: 400, fontSize: 22, lineHeight: '32px', color: C.ink2}},
};
const SPACER: Partial<Record<RowKind, number>> = {big: -6, note: 22};

const IN = 0.3;
const OUT = 0.25;
const TRAVEL = 40;

const RowView: React.FC<{t: number; tIn: number; tOut: number; i: number; row: Row; roll: boolean; align: 'left' | 'center'}> = ({t, tIn, tOut, i, row, roll, align}) => {
  const spec = ROW[row.kind];
  const lag = i / 30;
  const start = tIn + (roll ? lag : 0);
  const style: React.CSSProperties = {height: spec.h, overflow: 'hidden', marginTop: SPACER[row.kind] ?? 0, marginBottom: spec.gap ?? 0};
  if (t < start || t >= tOut + OUT) return <div style={style} />;
  const yIn = roll ? TRAVEL * (1 - progress(t, start, IN, 'snap')) : 0;
  const yOut = -(spec.h + 4) * progress(t, tOut + lag * 0.5, OUT - lag * 0.5, 'accel');
  return (
    <div style={style}>
      <div style={{...spec.style, transform: `translateY(${yIn + yOut}px)`, whiteSpace: 'nowrap', textAlign: align}}>{row.text}</div>
    </div>
  );
};

/** A run of cards in one scene. `beats` are card IDs from the timeline, in order; `rows` gives each one's rows. */
export const Cards: React.FC<{
  t: number; beats: string[]; rows: Record<string, Row[]>; kicker?: string;
  x?: number; cy?: number; align?: 'left' | 'center'; width?: number;
}> = ({t, beats, rows, kicker, x = 1090, cy = 540, align = 'left', width = 780}) => {
  const first = CARD(beats[0]);
  // centre the tallest card of the scene on cy, so the kicker never moves between cards
  const hOf = (r: Row) => ROW[r.kind].h + (ROW[r.kind].gap ?? 0) + (SPACER[r.kind] ?? 0);
  const kickH = kicker ? hOf({kind: 'kicker', text: ''}) : 0;
  const top = cy - Math.max(...beats.map((b) => rows[b].reduce((a, r) => a + hOf(r), kickH))) / 2;
  const last = CARD(beats[beats.length - 1]);
  if (t < first.on || t >= last.off + OUT + 0.05) return null;
  let idx = 0;
  for (let i = 0; i < beats.length; i++) if (t >= CARD(beats[i]).on) idx = i;
  const b = beats[idx];
  const c = CARD(b);
  const left = align === 'center' ? x - width / 2 : x;
  return (
    <div style={{position: 'absolute', left, top, width}}>
      {kicker ? <RowView t={t} tIn={first.on} tOut={last.off} i={0} row={{kind: 'kicker', text: kicker}} roll={false} align={align} /> : null}
      {rows[b].map((r, i) => (
        <RowView key={`${b}-${i}`} t={t} tIn={c.on} tOut={c.off} i={i + (kicker ? 1 : 0)} row={r} roll={idx > 0} align={align} />
      ))}
    </div>
  );
};
