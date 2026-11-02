// Caption.tsx: heading + one line, changed with the Comma Clinical "text in a card changes" transition:
// the old rows roll up and out (0.25 s, accelerating) and finish on the new item's time; the new rows roll up
// into place (0.3 s, snap and settle, 40 px), one frame apart, clipped to their row.
import React from 'react';
import {progress} from '../style/comma';
import {M, FONT_BODY, FONT_HEAD} from '../style/mono';

export type CaptionItem = {t: number; head: string; body: string; kicker?: string};

const OUT = 0.25;
const IN = 0.3;
const TRAVEL = 40;

const Row: React.FC<{t: number; tIn: number; tOut: number; i: number; style: React.CSSProperties; h: number; children: React.ReactNode}> = ({t, tIn, tOut, i, style, h, children}) => {
  const dIn = tIn + i / 30;
  if (t < dIn || t >= tOut) return <div style={{height: h}} />;
  const yIn = TRAVEL * (1 - progress(t, dIn, IN, 'snap'));
  const yOut = -h * progress(t, tOut - OUT + i / 30, OUT - i / 30, 'accel');
  return (
    <div style={{height: h, overflow: 'hidden'}}>
      <div style={{...style, transform: `translateY(${yIn + yOut}px)`, whiteSpace: 'nowrap'}}>{children}</div>
    </div>
  );
};

export const Caption: React.FC<{items: CaptionItem[]; t: number; end: number; x: number; y: number; kickerOnly?: boolean}> = ({items, t, end, x, y, kickerOnly}) => {
  let idx = -1;
  for (let i = 0; i < items.length; i++) if (t >= items[i].t) idx = i;
  if (idx < 0 || t >= end) return null;
  const it = items[idx];
  const tOut = idx + 1 < items.length ? items[idx + 1].t : end;
  if (kickerOnly) {
    return (
      <div style={{position: 'absolute', left: x, top: y}}>
        <Row t={t} tIn={it.t} tOut={tOut} i={0} h={34} style={{fontFamily: FONT_HEAD, fontWeight: 700, fontSize: 24, letterSpacing: 3, textTransform: 'uppercase', color: M.ink2, lineHeight: '34px'}}>
          {it.kicker}
        </Row>
      </div>
    );
  }
  return (
    <div style={{position: 'absolute', left: x, top: y}}>
      <Row t={t} tIn={it.t} tOut={tOut} i={0} h={72} style={{fontFamily: FONT_HEAD, fontWeight: 600, fontSize: 60, lineHeight: '72px', color: M.ink}}>
        {it.head}
      </Row>
      <Row t={t} tIn={it.t} tOut={tOut} i={1} h={44} style={{fontFamily: FONT_BODY, fontWeight: 400, fontSize: 32, lineHeight: '44px', color: M.ink2}}>
        {it.body}
      </Row>
    </div>
  );
};
